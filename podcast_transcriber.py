#!/usr/bin/env python3
"""
Podcast Transcriber - Ladda ner och transkribera podcasts från RSS-feed
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse

try:
    import feedparser
    import requests
    import whisper
    from dateutil import parser as date_parser
    from tqdm import tqdm
except ImportError as e:
    print(f"Fel: Saknar nödvändigt bibliotek. Kör: pip install -r requirements.txt")
    print(f"Detaljer: {e}")
    sys.exit(1)


class PodcastTranscriber:
    """Huvudklass för podcast-transkribering"""

    def __init__(self, work_dir: str = "podcasts"):
        self.work_dir = Path(work_dir)
        self.audio_dir = self.work_dir / "audio"
        self.transcripts_dir = self.work_dir / "transcripts"
        self.state_file = self.work_dir / "transcribed_episodes.json"

        # Skapa mappar
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

        # Ladda state
        self.state = self._load_state()

        # Whisper modell (lazy load)
        self.whisper_model = None

    def _load_state(self) -> Dict:
        """Ladda sparat tillstånd från JSON-fil"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Varning: Kunde inte läsa state-fil, skapar ny...")
                return {}
        return {}

    def _save_state(self):
        """Spara tillstånd till JSON-fil"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def _sanitize_filename(self, name: str) -> str:
        """Rensa filnamn från ogiltiga tecken"""
        # Ta bort/ersätt ogiltiga tecken
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        name = re.sub(r'\s+', '_', name.strip())
        # Begränsa längd
        return name[:200]

    def fetch_feed(self, rss_url: str) -> List[Dict]:
        """Hämta och parsa RSS-feed"""
        print(f"\nHämtar RSS-feed från {rss_url}...")

        try:
            feed = feedparser.parse(rss_url)

            if feed.bozo:
                print(f"Varning: RSS-feeden kan ha problem: {feed.bozo_exception}")

            if not feed.entries:
                print("Fel: Inga avsnitt hittades i feeden")
                return []

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

                episode = {
                    'title': entry.get('title', 'Untitled'),
                    'audio_url': audio_url,
                    'published': pub_date,
                    'guid': entry.get('id', audio_url),  # Unik identifierare
                    'description': entry.get('summary', '')
                }
                episodes.append(episode)

            # Sortera efter datum (nyast först)
            episodes.sort(key=lambda x: x['published'] or datetime.min, reverse=True)

            print(f"✓ Hittade {len(episodes)} avsnitt med ljudfiler")
            return episodes

        except Exception as e:
            print(f"Fel vid hämtning av RSS-feed: {e}")
            return []

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
        """Generera filnamn baserat på datum och titel"""
        date_str = ""
        if episode['published']:
            date_str = episode['published'].strftime("%Y-%m-%d") + "_"

        title_clean = self._sanitize_filename(episode['title'])
        return f"{date_str}{title_clean}"

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
                language="sv",  # Svenskt språk
                verbose=False
            )

            # Spara transkription
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(f"Titel: {episode['title']}\n")
                if episode['published']:
                    f.write(f"Publicerad: {episode['published'].strftime('%d-%m-%Y')}\n")
                f.write(f"Källa: {episode['audio_url']}\n")
                f.write("\n" + "="*80 + "\n\n")
                f.write(result['text'])

            print(f"  ✓ Transkriberad: {transcript_path.name}")

            # Uppdatera state
            self.state[episode['guid']] = {
                'title': episode['title'],
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

    # Skapa transcriber
    transcriber = PodcastTranscriber()

    # Hämta avsnitt
    episodes = transcriber.fetch_feed(rss_url)

    if not episodes:
        print("Inga avsnitt att bearbeta.")
        return

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
