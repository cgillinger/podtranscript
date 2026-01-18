# Snabbstart 🚀

Kom igång med Podcast Transcriber på 5 minuter!

## 1️⃣ Klona projektet

```bash
# Klona från GitHub
git clone https://github.com/cgillinger/podtranscript.git
cd podtranscript
```

## 2️⃣ Installera dependencies

```bash
# Installera Python och pip (om du inte har det)
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Skapa virtuell miljö
python3 -m venv venv
source venv/bin/activate

# Installera required packages
pip install -r requirements.txt
```

## 3️⃣ Kör skriptet

```bash
python3 podcast_transcriber.py
```

## 4️⃣ Följ instruktionerna

1. Ange RSS-URL (exempel: `https://feeds.example.com/podcast.xml`)
2. Välj filtrering (Alla / Nya / Datum)
3. Välj sorteringsordning (Äldsta först / Senaste först)
4. Bekräfta och vänta!

## 📁 Resultat

Dina filer hamnar i:
- **Ljudfiler**: `podcasts/audio/`
- **Transkriptioner**: `podcasts/transcripts/`

### Filnamnsformat

Skriptet skapar **intelligenta filnamn** baserat på metadata:

- **Med säsong/episod**: `S05E083_2026-01-12_Episodtitel.mp3`
- **Bara episod**: `E347_2024-03-22_Episodtitel.mp3`
- **Bonus-avsnitt**: `BONUS_2026-01-08_Episodtitel.mp3`
- **Fallback**: `2024-02-14_Episodtitel.mp3`

Läser från iTunes-taggar ELLER parsar titel automatiskt!

## 💡 Tips

### Första gången
Välj **"Endast nya"** - första gången kommer alla avsnitt vara "nya"!

### Kommande gånger
Använd **"Endast nya"** igen för att bara transkribera nya avsnitt.

### Specifikt datum
Vill du bara ha avsnitt från mars 2024?
- Från: `01-03-2024`
- Till: `31-03-2024`

## ❓ Problem?

Se [README.md](README.md) för detaljerad felsökning!

---

**Nu kör vi! 🎙️→📝**
