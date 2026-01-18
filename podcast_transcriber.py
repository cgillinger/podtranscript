#!/usr/bin/env python3
"""
Podcast Transcriber - Download and transcribe podcasts from RSS feeds

This script automatically downloads podcast episodes from RSS feeds and transcribes
them using OpenAI's Whisper speech recognition model. It supports:
- Smart filename generation based on iTunes metadata (S##E### format)
- Multiple podcasts in separate folders
- State tracking to avoid re-transcribing episodes
- Flexible filtering (all episodes, new only, date ranges)
- Automatic language detection
- Progress tracking for downloads and transcription

Author: Podcast Transcriber Contributors
License: MIT
"""

# Standard library imports
import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse

# Third-party library imports with error handling
try:
    import feedparser      # RSS/Atom feed parsing
    import requests        # HTTP requests for downloading
    import whisper         # OpenAI Whisper for speech-to-text
    from dateutil import parser as date_parser  # Flexible date parsing
    from tqdm import tqdm  # Progress bars for downloads
except ImportError as e:
    print(f"Error: Missing required library. Run: pip install -r requirements.txt")
    print(f"Details: {e}")
    sys.exit(1)


class PodcastTranscriber:
    """
    Main class for podcast transcription workflow.

    This class handles the complete lifecycle of podcast transcription:
    1. RSS feed fetching and parsing
    2. Metadata extraction (season/episode numbers from iTunes tags or titles)
    3. File organization (separate folders per podcast)
    4. Audio file downloading
    5. Speech-to-text transcription using Whisper
    6. State management (tracking which episodes are already transcribed)

    Attributes:
        base_dir: Base directory for all podcasts
        work_dir: Working directory for current podcast
        audio_dir: Directory for downloaded audio files
        transcripts_dir: Directory for transcription text files
        state_file: JSON file tracking transcribed episodes
        state: Dictionary of transcribed episodes (loaded from state_file)
        whisper_model: Lazy-loaded Whisper model for transcription
    """

    def __init__(self, work_dir: str = "podcasts", podcast_name: Optional[str] = None):
        """
        Initialize the podcast transcriber.

        Sets up directory structure for storing audio files, transcripts, and state.
        Each podcast can have its own subdirectory to keep things organized.

        Args:
            work_dir: Base directory for all podcasts (default: "podcasts")
            podcast_name: Name of the podcast (used as subdirectory name).
                         If None, files go directly in work_dir.
                         If provided, creates a sanitized subfolder.

        Directory structure created:
            podcasts/
            └── Podcast_Name/
                ├── audio/                    # Downloaded MP3 files
                ├── transcripts/              # Transcription text files
                └── transcribed_episodes.json # State tracking
        """
        self.base_dir = Path(work_dir)

        # Create podcast-specific subfolder if podcast name is provided
        # This allows multiple podcasts to be managed separately
        if podcast_name:
            # Sanitize the podcast name to make it a valid directory name
            # (removes invalid characters, replaces spaces with underscores)
            safe_name = self._sanitize_filename(podcast_name)
            self.work_dir = self.base_dir / safe_name
        else:
            self.work_dir = self.base_dir

        # Define subdirectories for audio and transcripts
        self.audio_dir = self.work_dir / "audio"
        self.transcripts_dir = self.work_dir / "transcripts"
        self.state_file = self.work_dir / "transcribed_episodes.json"

        # Create directories if they don't exist
        # parents=True creates parent directories as needed
        # exist_ok=True prevents errors if directories already exist
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

        # Load state from JSON file (tracks which episodes are already transcribed)
        self.state = self._load_state()

        # Whisper model is loaded lazily (on first transcription)
        # This saves memory and startup time if only downloading
        self.whisper_model = None

    def _load_state(self) -> Dict:
        """
        Load transcription state from JSON file.

        The state file tracks which episodes have already been transcribed,
        preventing duplicate work. Each episode is identified by its GUID.

        Returns:
            Dictionary mapping episode GUIDs to transcription metadata,
            or empty dict if file doesn't exist or is corrupted.
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Warning: Could not read state file, creating new one...")
                return {}
        return {}

    def _save_state(self):
        """
        Save transcription state to JSON file.

        Persists the current state to disk, recording which episodes have been
        transcribed along with their metadata (title, dates, filenames, etc.).
        """
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string to make it safe for use as a filename.

        Removes or replaces characters that are invalid in filenames on
        most filesystems (Windows, macOS, Linux).

        Args:
            name: Raw string (podcast name, episode title, etc.)

        Returns:
            Sanitized string safe for use as filename/directory name.
            Limited to 200 characters.

        Examples:
            "Hello: World?" -> "Hello_World"
            "Season 5 / Episode 3" -> "Season_5__Episode_3"
        """
        # Remove invalid filename characters: < > : " / \ | ? *
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace whitespace sequences with single underscore
        name = re.sub(r'\s+', '_', name.strip())
        # Limit length to prevent filesystem issues
        return name[:200]

    def _extract_episode_metadata(self, entry) -> Dict[str, Optional[str]]:
        """
        Extract episode/season metadata from RSS entry.

        Tries multiple methods to extract metadata in order of preference:
        1. iTunes podcast tags (<itunes:season>, <itunes:episode>)
        2. Title parsing (e.g., "Season 5, Ep 83 - Title")
        3. Episode type detection (bonus, trailer)

        This dual approach ensures compatibility with podcasts that:
        - Use proper iTunes tags (ideal)
        - Include metadata in titles (common)
        - Have minimal metadata (fallback)

        Args:
            entry: feedparser entry object representing one episode

        Returns:
            Dictionary with keys:
                'season': Season number (int) or None
                'episode': Episode number (int) or None
                'episode_type': Type string ('bonus', 'trailer', 'full') or None
                'clean_title': Episode title with season/episode info removed

        Examples:
            Input: "Season 5, Ep 83 - Pizza Hell"
            Output: {'season': 5, 'episode': 83, 'clean_title': 'Pizza Hell'}

            Input: Entry with <itunes:season>2</itunes:season>
            Output: {'season': 2, 'episode': 15, ...}
        """
        metadata = {
            'season': None,
            'episode': None,
            'episode_type': None,
            'clean_title': entry.get('title', 'Untitled')
        }

        # 1. Försök iTunes-taggar först
        if hasattr(entry, 'itunes_season') and entry.itunes_season:
            try:
                metadata['season'] = int(entry.itunes_season)
            except (ValueError, TypeError):
                pass

        if hasattr(entry, 'itunes_episode') and entry.itunes_episode:
            try:
                metadata['episode'] = int(entry.itunes_episode)
            except (ValueError, TypeError):
                pass

        if hasattr(entry, 'itunes_episodetype') and entry.itunes_episodetype:
            metadata['episode_type'] = entry.itunes_episodetype.lower()

        # 2. Om iTunes-taggar saknas, försök parsa titeln
        if metadata['season'] is None or metadata['episode'] is None:
            title = entry.get('title', '')

            # Mönster för olika titelformat:
            # "Season 5, Ep 83 - Title"
            # "S05E83 - Title"
            # "5x83 - Title"
            # "Episode 123 - Title"

            patterns = [
                # "Season 5, Ep 83 - Title" eller "Season 5, Episode 83 - Title"
                r'Season\s+(\d+),?\s+Ep(?:isode)?\s+(\d+)\s*[-:–]\s*(.*)',
                # "S05E83 - Title" eller "S5E83 - Title"
                r'S(\d+)E(\d+)\s*[-:–]\s*(.*)',
                # "5x83 - Title"
                r'(\d+)x(\d+)\s*[-:–]\s*(.*)',
                # Bara "Episode 123 - Title" (ingen säsong)
                r'Ep(?:isode)?\s+(\d+)\s*[-:–]\s*(.*)',
            ]

            for pattern in patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    groups = match.groups()

                    if len(groups) == 3:
                        # Season + Episode + Title
                        metadata['season'] = int(groups[0])
                        metadata['episode'] = int(groups[1])
                        metadata['clean_title'] = groups[2].strip()
                    elif len(groups) == 2:
                        # Endast Episode + Title (ingen säsong)
                        metadata['episode'] = int(groups[0])
                        metadata['clean_title'] = groups[1].strip()
                    break

        # 3. Kolla efter speciella episodtyper i titeln
        if metadata['episode_type'] is None:
            title_lower = metadata['clean_title'].lower()
            if any(word in title_lower for word in ['bonus', 'patreon unlock']):
                metadata['episode_type'] = 'bonus'
            elif 'trailer' in title_lower:
                metadata['episode_type'] = 'trailer'

        return metadata

    def fetch_feed(self, rss_url: str) -> Tuple[str, List[Dict]]:
        """
        Hämta och parsa RSS-feed.

        Returns:
            Tuple med (podcast_title, episodes_list)
        """
        print(f"\nHämtar RSS-feed från {rss_url}...")

        try:
            feed = feedparser.parse(rss_url)

            if feed.bozo:
                print(f"Varning: RSS-feeden kan ha problem: {feed.bozo_exception}")

            if not feed.entries:
                print("Fel: Inga avsnitt hittades i feeden")
                return ("Unknown Podcast", [])

            # Extrahera podcast-titel från feed
            podcast_title = feed.feed.get('title', 'Unknown Podcast')
            print(f"📻 Podcast: {podcast_title}")

            episodes = []
            for entry in feed.entries:
                # Hitta MP3-länk
                audio_url = None
                for link in entry.get('links', []):
                    if 'audio' in link.get('type', '') or link.get('href', '').endswith('.mp3'):
                        audio_url = link['href']
                        break

                # Fallback: kolla enclosures
                if not audio_url and hasattr(entry, 'enclosures'):
                    for enclosure in entry.enclosures:
                        if 'audio' in enclosure.get('type', '') or enclosure.get('href', '').endswith('.mp3'):
                            audio_url = enclosure['href']
                            break

                if not audio_url:
                    continue

                # Parsa publiceringsdatum
                pub_date = None
                if hasattr(entry, 'published'):
                    try:
                        pub_date = date_parser.parse(entry.published)
                    except:
                        pass

                # Extrahera episode/season metadata
                metadata = self._extract_episode_metadata(entry)

                episode = {
                    'title': entry.get('title', 'Untitled'),
                    'audio_url': audio_url,
                    'published': pub_date,
                    'guid': entry.get('id', audio_url),  # Unik identifierare
                    'description': entry.get('summary', ''),
                    # Ny metadata
                    'season': metadata['season'],
                    'episode': metadata['episode'],
                    'episode_type': metadata['episode_type'],
                    'clean_title': metadata['clean_title']
                }
                episodes.append(episode)

            # Sortera efter datum (nyast först)
            episodes.sort(key=lambda x: x['published'] or datetime.min, reverse=True)

            print(f"✓ Hittade {len(episodes)} avsnitt med ljudfiler")
            return (podcast_title, episodes)

        except Exception as e:
            print(f"Fel vid hämtning av RSS-feed: {e}")
            return ("Unknown Podcast", [])

    def filter_episodes(self, episodes: List[Dict], mode: str,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[Dict]:
        """Filtrera avsnitt baserat på användarens val"""

        if mode == "all":
            return episodes

        elif mode == "new":
            # Filtrera bort redan transkriberade
            new_episodes = [ep for ep in episodes if ep['guid'] not in self.state]
            print(f"✓ {len(new_episodes)} nya avsnitt (av {len(episodes)} totalt)")
            return new_episodes

        elif mode == "date":
            if not start_date or not end_date:
                print("Fel: Datumintervall saknas")
                return []

            filtered = [
                ep for ep in episodes
                if ep['published'] and start_date <= ep['published'] <= end_date
            ]
            print(f"✓ {len(filtered)} avsnitt i datumintervallet")
            return filtered

        return []

    def _generate_filename(self, episode: Dict) -> str:
        """
        Generera filnamn baserat på tillgänglig metadata.

        Prioritetsordning:
        1. S##E### + Datum + Titel (om både säsong och episod finns)
        2. E### + Datum + Titel (om bara episod finns)
        3. EPISODTYP + Datum + Titel (om speciell typ utan nummer)
        4. Datum + Titel (fallback)
        """
        parts = []

        # 1. Episode/Season prefix
        if episode.get('season') is not None and episode.get('episode') is not None:
            # Både säsong och episod: S05E083
            season_str = f"S{episode['season']:02d}"
            # Dynamisk padding för episod (minst 3 siffror, mer om behövs)
            ep_num = episode['episode']
            if ep_num < 1000:
                episode_str = f"E{ep_num:03d}"
            else:
                episode_str = f"E{ep_num:04d}"
            parts.append(f"{season_str}{episode_str}")

        elif episode.get('episode') is not None:
            # Bara episod: E083
            ep_num = episode['episode']
            if ep_num < 1000:
                episode_str = f"E{ep_num:03d}"
            else:
                episode_str = f"E{ep_num:04d}"
            parts.append(episode_str)

        elif episode.get('episode_type') in ['bonus', 'trailer']:
            # Speciell typ utan nummer: BONUS eller TRAILER
            parts.append(episode['episode_type'].upper())

        # 2. Datum
        if episode.get('published'):
            date_str = episode['published'].strftime("%Y-%m-%d")
            parts.append(date_str)

        # 3. Titel (använd clean_title om tillgänglig, annars title)
        title = episode.get('clean_title') or episode.get('title', 'Untitled')
        title_clean = self._sanitize_filename(title)

        # Begränsa titellängd (max 80 tecken för själva titeln)
        if len(title_clean) > 80:
            title_clean = title_clean[:80]

        parts.append(title_clean)

        # Kombinera alla delar med understreck
        return "_".join(parts)

    def download_audio(self, episode: Dict) -> Optional[Path]:
        """Ladda ner ljudfil"""
        filename = self._generate_filename(episode)
        audio_path = self.audio_dir / f"{filename}.mp3"

        # Skippa om redan nedladdat
        if audio_path.exists():
            print(f"  ↳ Ljudfil finns redan: {audio_path.name}")
            return audio_path

        try:
            print(f"  ↳ Laddar ner: {episode['title'][:60]}...")
            response = requests.get(episode['audio_url'], stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(audio_path, 'wb') as f, tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                desc="    Nedladdning"
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))

            print(f"  ✓ Nedladdad: {audio_path.name}")
            return audio_path

        except Exception as e:
            print(f"  ✗ Fel vid nedladdning: {e}")
            if audio_path.exists():
                audio_path.unlink()
            return None

    def transcribe_audio(self, audio_path: Path, episode: Dict) -> Optional[Path]:
        """Transkribera ljudfil med Whisper"""
        filename = audio_path.stem
        transcript_path = self.transcripts_dir / f"{filename}.txt"

        # Skippa om redan transkriberad
        if episode['guid'] in self.state:
            print(f"  ↳ Redan transkriberad tidigare")
            return transcript_path if transcript_path.exists() else None

        try:
            # Ladda Whisper-modell (lazy loading)
            if self.whisper_model is None:
                print("  ↳ Laddar Whisper-modell (kan ta en stund första gången)...")
                self.whisper_model = whisper.load_model("base")

            print(f"  ↳ Transkriberar: {audio_path.name}...")
            result = self.whisper_model.transcribe(
                str(audio_path),
                verbose=False  # Auto-detekterar språk
            )

            # Spara transkription
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(f"Titel: {episode['title']}\n")

                # Episode/Season info
                if episode.get('season') and episode.get('episode'):
                    f.write(f"Säsong: {episode['season']}, Avsnitt: {episode['episode']}\n")
                elif episode.get('episode'):
                    f.write(f"Avsnitt: {episode['episode']}\n")

                if episode.get('episode_type'):
                    f.write(f"Typ: {episode['episode_type'].title()}\n")

                if episode['published']:
                    f.write(f"Publicerad: {episode['published'].strftime('%d-%m-%Y')}\n")

                f.write(f"Källa: {episode['audio_url']}\n")
                f.write("\n" + "="*80 + "\n\n")
                f.write(result['text'])

            print(f"  ✓ Transkriberad: {transcript_path.name}")

            # Uppdatera state
            self.state[episode['guid']] = {
                'title': episode['title'],
                'season': episode.get('season'),
                'episode': episode.get('episode'),
                'episode_type': episode.get('episode_type'),
                'published': episode['published'].isoformat() if episode['published'] else None,
                'transcribed_date': datetime.now().isoformat(),
                'audio_file': audio_path.name,
                'transcript_file': transcript_path.name
            }
            self._save_state()

            return transcript_path

        except Exception as e:
            print(f"  ✗ Fel vid transkribering: {e}")
            return None

    def process_episodes(self, episodes: List[Dict]):
        """Bearbeta lista av avsnitt"""
        if not episodes:
            print("\nInga avsnitt att bearbeta.")
            return

        print(f"\n{'='*80}")
        print(f"Startar bearbetning av {len(episodes)} avsnitt")
        print(f"{'='*80}\n")

        success_count = 0
        for i, episode in enumerate(episodes, 1):
            print(f"\n[{i}/{len(episodes)}] {episode['title']}")

            # Ladda ner
            audio_path = self.download_audio(episode)
            if not audio_path:
                continue

            # Transkribera
            transcript_path = self.transcribe_audio(audio_path, episode)
            if transcript_path:
                success_count += 1

        print(f"\n{'='*80}")
        print(f"✓ Klart! {success_count}/{len(episodes)} avsnitt transkriberade")
        print(f"{'='*80}")
        print(f"\nLjudfiler: {self.audio_dir}")
        print(f"Transkriptioner: {self.transcripts_dir}")


def parse_date(date_str: str) -> Optional[datetime]:
    """Parsa datum i europeiskt format"""
    formats = [
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%Y-%m-%d"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    return None


def get_user_choice(prompt: str, options: List[str]) -> str:
    """Få användarval från lista"""
    while True:
        print(f"\n{prompt}")
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt}")

        choice = input("\nDitt val (nummer): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass

        print("Ogiltigt val, försök igen.")


def main():
    """Huvudfunktion"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         PODCAST TRANSCRIBER - RSS till Text med Whisper      ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Få RSS-URL
    rss_url = input("Ange RSS-URL för podcasten: ").strip()

    if not rss_url:
        print("Fel: Ingen URL angiven")
        return

    # Skapa temporär transcriber för att hämta feed-info
    temp_transcriber = PodcastTranscriber()

    # Hämta podcast-titel och avsnitt
    podcast_title, episodes = temp_transcriber.fetch_feed(rss_url)

    if not episodes:
        print("Inga avsnitt att bearbeta.")
        return

    # Skapa transcriber med podcast-specifik mapp
    print(f"\n📁 Skapar mapp för: {podcast_title}")
    transcriber = PodcastTranscriber(podcast_name=podcast_title)

    # Visa sammanfattning
    print(f"\nÄldsta avsnitt: {episodes[-1]['published'].strftime('%d-%m-%Y') if episodes[-1]['published'] else 'Okänt datum'}")
    print(f"Senaste avsnitt: {episodes[0]['published'].strftime('%d-%m-%Y') if episodes[0]['published'] else 'Okänt datum'}")

    # Fråga användaren hur de vill filtrera
    mode_choice = get_user_choice(
        "Vilka avsnitt vill du transkribera?",
        ["Alla avsnitt", "Endast nya (ej tidigare transkriberade)", "Specifikt datumintervall"]
    )

    filtered_episodes = []

    if mode_choice == "Alla avsnitt":
        filtered_episodes = transcriber.filter_episodes(episodes, "all")

    elif mode_choice == "Endast nya (ej tidigare transkriberade)":
        filtered_episodes = transcriber.filter_episodes(episodes, "new")

        if not filtered_episodes:
            print("\n✓ Alla avsnitt är redan transkriberade!")
            return

    elif mode_choice == "Specifikt datumintervall":
        print("\nAnge datumintervall (format: DD-MM-ÅÅÅÅ eller DD/MM/ÅÅÅÅ)")

        while True:
            start_str = input("Från datum: ").strip()
            start_date = parse_date(start_str)
            if start_date:
                break
            print("Ogiltigt datum, försök igen.")

        while True:
            end_str = input("Till datum: ").strip()
            end_date = parse_date(end_str)
            if end_date:
                # Sätt till slutet av dagen
                end_date = end_date.replace(hour=23, minute=59, second=59)
                break
            print("Ogiltigt datum, försök igen.")

        filtered_episodes = transcriber.filter_episodes(episodes, "date", start_date, end_date)

        if not filtered_episodes:
            print("\nInga avsnitt hittades i det datumintervallet.")
            return

    # Fråga om sorteringsordning
    sort_choice = get_user_choice(
        "I vilken ordning vill du bearbeta avsnitten?",
        ["Börja med äldsta avsnittet", "Börja med senaste avsnittet"]
    )

    if sort_choice == "Börja med äldsta avsnittet":
        # Sortera äldst först (stigande datum)
        filtered_episodes.sort(key=lambda x: x['published'] or datetime.min, reverse=False)
        sort_info = "äldsta → senaste"
    else:
        # Sortera nyast först (fallande datum) - redan sorterat så, men gör det explicit
        filtered_episodes.sort(key=lambda x: x['published'] or datetime.min, reverse=True)
        sort_info = "senaste → äldsta"

    # Visa information
    if filtered_episodes:
        first_ep = filtered_episodes[0]
        last_ep = filtered_episodes[-1]
        print(f"\nSortering: {sort_info}")
        print(f"Första avsnittet som bearbetas: {first_ep['title']}")
        if first_ep.get('published'):
            print(f"  Datum: {first_ep['published'].strftime('%d-%m-%Y')}")
        print(f"Sista avsnittet som bearbetas: {last_ep['title']}")
        if last_ep.get('published'):
            print(f"  Datum: {last_ep['published'].strftime('%d-%m-%Y')}")

    # Bekräftelse
    print(f"\n{len(filtered_episodes)} avsnitt kommer att laddas ner och transkriberas.")
    confirm = input("Fortsätt? (j/n): ").strip().lower()

    if confirm not in ['j', 'ja', 'y', 'yes']:
        print("Avbrutet.")
        return

    # Kör transkribering
    transcriber.process_episodes(filtered_episodes)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAvbrutet av användare.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nOväntat fel: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
