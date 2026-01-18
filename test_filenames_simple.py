#!/usr/bin/env python3
"""
Enkelt test av filnamnslogik utan externa dependencies
"""

import re
from datetime import datetime

def sanitize_filename(name: str) -> str:
    """Rensa filnamn från ogiltiga tecken"""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:200]

def generate_filename(episode: dict) -> str:
    """
    Generera filnamn baserat på tillgänglig metadata.
    """
    parts = []

    # 1. Episode/Season prefix
    if episode.get('season') is not None and episode.get('episode') is not None:
        season_str = f"S{episode['season']:02d}"
        ep_num = episode['episode']
        if ep_num < 1000:
            episode_str = f"E{ep_num:03d}"
        else:
            episode_str = f"E{ep_num:04d}"
        parts.append(f"{season_str}{episode_str}")

    elif episode.get('episode') is not None:
        ep_num = episode['episode']
        if ep_num < 1000:
            episode_str = f"E{ep_num:03d}"
        else:
            episode_str = f"E{ep_num:04d}"
        parts.append(episode_str)

    elif episode.get('episode_type') in ['bonus', 'trailer']:
        parts.append(episode['episode_type'].upper())

    # 2. Datum
    if episode.get('published'):
        date_str = episode['published'].strftime("%Y-%m-%d")
        parts.append(date_str)

    # 3. Titel
    title = episode.get('clean_title') or episode.get('title', 'Untitled')
    title_clean = sanitize_filename(title)

    if len(title_clean) > 80:
        title_clean = title_clean[:80]

    parts.append(title_clean)

    return "_".join(parts)

# Test-episoder
test_episodes = [
    {
        'name': 'Magic Tavern - Season 5, Ep 83',
        'episode': {
            'title': 'Season 5, Ep 83 - DQ in Pizza Hell (w/ Tim Ryder)',
            'clean_title': 'DQ in Pizza Hell (w/ Tim Ryder)',
            'season': 5,
            'episode': 83,
            'episode_type': 'full',
            'published': datetime(2026, 1, 12)
        }
    },
    {
        'name': 'Magic Tavern - Bonus',
        'episode': {
            'title': 'Patreon Unlock: Stargazing',
            'clean_title': 'Stargazing',
            'season': None,
            'episode': None,
            'episode_type': 'bonus',
            'published': datetime(2026, 1, 8)
        }
    },
    {
        'name': 'iTunes-taggar (S02E15)',
        'episode': {
            'title': 'The Future of AI',
            'clean_title': 'The Future of AI',
            'season': 2,
            'episode': 15,
            'episode_type': 'full',
            'published': datetime(2024, 3, 21)
        }
    },
    {
        'name': 'Endast episod (E347)',
        'episode': {
            'title': 'Episode 347 - Breaking News',
            'clean_title': 'Breaking News',
            'season': None,
            'episode': 347,
            'episode_type': 'full',
            'published': datetime(2024, 3, 22)
        }
    },
    {
        'name': 'Trailer',
        'episode': {
            'title': 'Season 3 Trailer',
            'clean_title': 'Season 3 Trailer',
            'season': None,
            'episode': None,
            'episode_type': 'trailer',
            'published': datetime(2024, 1, 1)
        }
    },
    {
        'name': 'Ingen metadata (fallback)',
        'episode': {
            'title': 'Random Podcast About Technology',
            'clean_title': 'Random Podcast About Technology',
            'season': None,
            'episode': None,
            'episode_type': None,
            'published': datetime(2024, 2, 14)
        }
    },
    {
        'name': 'Stort episodnummer (1234)',
        'episode': {
            'title': 'Anniversary Special',
            'clean_title': 'Anniversary Special',
            'season': None,
            'episode': 1234,
            'episode_type': 'full',
            'published': datetime(2024, 12, 25)
        }
    }
]

print("\n" + "="*100)
print("FILNAMNSGENERERINGSTEST")
print("="*100 + "\n")

for test in test_episodes:
    filename = generate_filename(test['episode'])

    print(f"📝 {test['name']}")
    print(f"   Titel: {test['episode']['title']}")

    meta = []
    if test['episode'].get('season'):
        meta.append(f"S{test['episode']['season']}")
    if test['episode'].get('episode'):
        meta.append(f"E{test['episode']['episode']}")
    if test['episode'].get('episode_type'):
        meta.append(f"Type: {test['episode']['episode_type']}")

    if meta:
        print(f"   Metadata: {', '.join(meta)}")

    print(f"   → MP3:  {filename}.mp3")
    print(f"   → TXT:  {filename}.txt")
    print()

print("="*100)
print("✓ Test klart!\n")
