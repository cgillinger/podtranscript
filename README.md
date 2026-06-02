# Podcast Transcriber 🎙️→📝

A Python script to automatically download and transcribe podcasts from RSS feeds using OpenAI Whisper.

> This is a personal hobby project I build for my own use and publish in case it's useful to someone else. I work on it in my spare time, so issues and PRs are welcome but replies may be slow. Use at your own risk.

## Features

✅ **RSS Feed Support** - Fetch episodes from any podcast RSS feed
✅ **Automatic Download** - Downloads MP3 files automatically
✅ **Whisper Transcription** - Uses OpenAI Whisper for high-quality transcription
✅ **Auto Language Detection** - Whisper automatically recognizes all languages
✅ **Smart Filenames** - Intelligent S##E### naming based on iTunes metadata
✅ **Metadata Extraction** - Extracts season/episode from RSS tags OR title parsing
✅ **Flexible Filtering** - Choose all, new, or specific date ranges
✅ **European Date Format** - DD-MM-YYYY format support
✅ **State Management** - Keeps track of already transcribed episodes
✅ **Progress Tracking** - Shows download and transcription progress
✅ **Multi-Podcast Support** - Each podcast gets its own organized folder

## System Requirements

- **OS**: Linux Mint (or other Linux distribution)
- **Python**: 3.8 or later
- **Disk Space**: Sufficient space for audio files and transcriptions
- **RAM**: At least 4GB recommended (Whisper uses some memory)

## Installation

### Step 1: Install Python and pip

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Step 2: Clone the project from GitHub

```bash
cd ~
git clone https://github.com/cgillinger/podtranscript.git
cd podtranscript
```

### Step 3: Create virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

**NOTE**: The first time you run the script, Whisper will download its model (~140MB for the "base" model).

### Step 5: Make the script executable

```bash
chmod +x podcast_transcriber.py
```

## Usage

### Basic usage

```bash
python3 podcast_transcriber.py
```

If using virtual environment:

```bash
source venv/bin/activate
python3 podcast_transcriber.py
```

### Step-by-step guide

1. **Run the script**
   ```bash
   python3 podcast_transcriber.py
   ```

2. **Enter RSS URL**
   ```
   Enter RSS URL for the podcast: https://example.com/podcast/feed.xml
   ```

3. **Choose filtering mode**
   - **All episodes** - Download and transcribe all episodes
   - **Only new** - Only episodes not previously transcribed
   - **Date range** - Specify from and to dates

4. **Enter dates (if you chose date range)**
   ```
   From date: 01-01-2024
   To date: 31-12-2024
   ```
   Accepted formats:
   - DD-MM-YYYY (e.g. 15-03-2024)
   - DD/MM/YYYY (e.g. 15/03/2024)
   - DD.MM.YYYY (e.g. 15.03.2024)

5. **Choose sorting order**
   - **Start with oldest episode** - Process from first to latest (chronological order)
   - **Start with latest episode** - Process from latest to first (reverse order)

   The script shows which episodes will be processed first and last:
   ```
   Sorting: oldest → newest
   First episode to process: Season 1, Ep 1 - Pilot
     Date: 15-03-2015
   Last episode to process: Season 5, Ep 83 - Latest Episode
     Date: 12-01-2026
   ```

6. **Confirm and wait**
   - The script shows how many episodes will be processed
   - Confirm with 'j' to continue
   - Wait while downloading and transcription is in progress

### Usage Examples

#### Example 1: All episodes
```bash
$ python3 podcast_transcriber.py

Enter RSS URL for the podcast: https://podcast.example.com/feed.xml

Fetching RSS feed...
✓ Found 50 episodes with audio files

Which episodes do you want to transcribe?
  1. All episodes
  2. Only new (not previously transcribed)
  3. Specific date range

Your choice: 1

50 episodes will be downloaded and transcribed.
Continue? (y/n): y
```

#### Example 2: Only new episodes
```bash
Your choice: 2

✓ 5 new episodes (out of 50 total)
5 episodes will be downloaded and transcribed.
```

#### Example 3: Date range
```bash
Your choice: 3

Enter date range (format: DD-MM-YYYY or DD/MM/YYYY)
From date: 01-01-2024
To date: 31-03-2024

✓ 12 episodes in the date range
```

## File Structure

After running, the following structure is created:

```
podcasts/
├── Hello_From_The_Magic_Tavern/     # Each podcast gets its own folder
│   ├── audio/                       # Audio files for this podcast
│   │   ├── S05E083_2026-01-12_DQ_in_Pizza_Hell.mp3
│   │   ├── S05E082_2026-01-05_Previous_Episode.mp3
│   │   └── ...
│   ├── transcripts/                 # Transcriptions for this podcast
│   │   ├── S05E083_2026-01-12_DQ_in_Pizza_Hell.txt
│   │   ├── S05E082_2026-01-05_Previous_Episode.txt
│   │   └── ...
│   └── transcribed_episodes.json    # State file for this podcast
│
├── Another_Podcast/                 # Another podcast in its own folder
│   ├── audio/
│   │   ├── E347_2024-03-22_Breaking_News.mp3
│   │   └── ...
│   ├── transcripts/
│   │   ├── E347_2024-03-22_Breaking_News.txt
│   │   └── ...
│   └── transcribed_episodes.json
│
└── Swedish_Podcast/                 # Third podcast
    ├── audio/
    ├── transcripts/
    └── transcribed_episodes.json
```

**Folder structure advantages:**
- ✅ Each podcast stays separate and organized
- ✅ Easy to find specific podcasts
- ✅ Each podcast has its own history (state file)
- ✅ Can transcribe multiple different podcasts without mixing them up

### Smart Filenames

The script uses a **smart filename system** based on podcast RSS metadata (iTunes tags and title parsing):

#### Format Priority

1. **With season and episode**: `S05E083_2026-01-12_Episode_Title.mp3`
   - Extracts from `<itunes:season>` and `<itunes:episode>` tags
   - Or parses title like "Season 5, Ep 83 - Title"
   - Example: `S02E015_2024-03-21_The_Future_of_AI.mp3`

2. **Episode number only**: `E347_2024-03-22_Episode_Title.mp3`
   - When only episode number is available
   - Example: `E347_2024-03-22_Breaking_News.mp3`

3. **Special types** (bonus/trailer): `BONUS_2026-01-08_Episode_Title.mp3`
   - For episodes marked as bonus or trailer
   - Example: `TRAILER_2024-01-01_Season_3_Trailer.mp3`

4. **Fallback** (date + title): `2024-02-14_Episode_Title.mp3`
   - When no episode/season metadata is available
   - Example: `2024-02-14_Random_Podcast.mp3`

#### Number Padding

- **Seasons**: 2 digits (S01, S02, ..., S99)
- **Episodes**: 3-4 digits (E001, E023, E1234)
  - Automatic expansion for episodes over 999

#### Title Sanitization

Filenames are automatically sanitized:
- Invalid characters removed (`<>:"/\|?*`)
- Spaces replaced with underscores
- Max title length: 80 characters
- Date in ISO 8601 format: `YYYY-MM-DD`

#### Real-world Examples

**Hello From The Magic Tavern** (title contains "Season 5, Ep 83"):
```
Original: Season 5, Ep 83 - DQ in Pizza Hell (w/ Tim Ryder)
Filename: S05E083_2026-01-12_DQ_in_Pizza_Hell_(w_Tim_Ryder).mp3
```

**Same podcast, bonus episode**:
```
Original: Patreon Unlock: Stargazing
Filename: BONUS_2026-01-08_Stargazing.mp3
```

**Podcast with iTunes tags**:
```
Original: The Future of AI
iTunes:   <itunes:season>2</itunes:season> <itunes:episode>15</itunes:episode>
Filename: S02E015_2024-03-21_The_Future_of_AI.mp3
```

**Daily news podcast** (episode number only):
```
Original: Episode 347 - Breaking News
Filename: E347_2024-03-22_Breaking_News.mp3
```

### Transcript File Contents

Transcript files contain metadata + transcription:

```
Title: Season 5, Ep 83 - DQ in Pizza Hell (w/ Tim Ryder)
Season: 5, Episode: 83
Type: Full
Published: 12-01-2026
Source: https://example.com/episode.mp3

================================================================================

[Transcription from Whisper comes here...]
```

## Language Handling

Whisper **automatically auto-detects** the language spoken in the podcast!

- ✅ **No configuration needed** - Works out of the box
- ✅ **Supports 99+ languages** - Swedish, English, Spanish, etc.
- ✅ **High accuracy** - Whisper's language detection is extremely reliable
- ✅ **Mixed content** - Can transcribe both Swedish and English podcasts with the same installation

**Examples:**
- Swedish podcast → Transcribed in Swedish automatically
- English podcast (e.g. Magic Tavern) → Transcribed in English automatically
- Multilingual podcast → Whisper chooses the primary language

## Whisper Models

The script uses the "base" model by default, which provides a good balance between speed and quality.

Available models:
- **tiny** - Fastest, lowest quality (~1GB RAM)
- **base** - Fast, good quality (~1GB RAM) ⭐ **Default**
- **small** - Slower, better quality (~2GB RAM)
- **medium** - Slow, very good quality (~5GB RAM)
- **large** - Slowest, best quality (~10GB RAM)

To change the model, edit `podcast_transcriber.py` line ~219:
```python
self.whisper_model = whisper.load_model("small")  # Change "base" to desired model
```

## Tips and Tricks

### 💡 Run in background

For long transcription jobs:
```bash
nohup python3 podcast_transcriber.py > transcribe.log 2>&1 &
```

### 💡 Only new episodes

Run regularly with "Only new" mode to automatically stay updated:
```bash
# Add to crontab for automatic execution
0 6 * * * cd /path/to/podtranscript && ./podcast_transcriber.py
```

### 💡 Batch processing

The script can handle many episodes - just confirm and let it run!

### 💡 Save disk space

If disk space is limited, delete audio files after transcription:
```bash
rm -rf podcasts/*/audio/*
```
Transcriptions remain and the state file knows what's already done.

## Troubleshooting

### Problem: "Error: Missing required library"

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Problem: "No episodes found in feed"

**Solutions**:
- Check that the RSS URL is correct
- Test the URL in a web browser
- Some feeds require specific headers

### Problem: Whisper is slow

**Solutions**:
- Use a smaller model ("tiny" or "base")
- Close other programs to free up RAM
- Consider GPU acceleration (requires CUDA-compatible graphics card)

### Problem: "Memory Error" during transcription

**Solutions**:
- Use a smaller model ("tiny" instead of "base")
- Close other programs
- Transcribe fewer episodes at a time

### Problem: Download fails

**Solutions**:
- Check internet connection
- Some podcasts may have geographic restrictions
- Try again later (server may be busy)

## Security and Privacy

- The script only downloads publicly available podcast episodes
- No data is sent to third parties (except downloading from the RSS feed)
- Whisper runs locally on your computer
- The state file is saved locally only

## License

MIT License - Free to use and modify

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## Support

If you encounter problems:
1. Check the troubleshooting section above
2. Ensure all dependencies are installed
3. Verify Python version is 3.8+
4. Open an issue on GitHub

## Author

Created for automatic podcast transcription.

---

**Happy transcribing! 🎧📝**
