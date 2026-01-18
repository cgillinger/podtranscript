# Quick Start 🚀

Get started with Podcast Transcriber in 5 minutes!

## 1️⃣ Clone the project

```bash
# Clone from GitHub
git clone https://github.com/cgillinger/podtranscript.git
cd podtranscript
```

## 2️⃣ Install dependencies

```bash
# Install Python and pip (if you don't have it)
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

## 3️⃣ Run the script

```bash
python3 podcast_transcriber.py
```

## 4️⃣ Follow the instructions

1. Enter RSS URL (example: `https://feeds.example.com/podcast.xml`)
2. Choose filtering (All / New / Date range)
3. Choose sorting order (Oldest first / Newest first)
4. Confirm and wait!

## 📁 Results

Each podcast gets its own folder:
```
podcasts/
├── Hello_From_The_Magic_Tavern/
│   ├── audio/          # MP3 files
│   ├── transcripts/    # Text files
│   └── transcribed_episodes.json
└── Another_Podcast/
    ├── audio/
    ├── transcripts/
    └── transcribed_episodes.json
```

**Advantage:** Multiple podcasts stay separate and organized!

### Filename Format

The script creates **smart filenames** based on metadata:

- **With season/episode**: `S05E083_2026-01-12_Episode_Title.mp3`
- **Episode only**: `E347_2024-03-22_Episode_Title.mp3`
- **Bonus episodes**: `BONUS_2026-01-08_Episode_Title.mp3`
- **Fallback**: `2024-02-14_Episode_Title.mp3`

Reads from iTunes tags OR parses title automatically!

## 💡 Tips

### First time
Choose **"Only new"** - the first time all episodes will be "new"!

### Subsequent runs
Use **"Only new"** again to transcribe only new episodes.

### Specific date range
Want only episodes from March 2024?
- From: `01-03-2024`
- To: `31-03-2024`

## ❓ Problems?

See [README.md](README.md) for detailed troubleshooting!

---

**Let's go! 🎙️→📝**
