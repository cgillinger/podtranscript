# Podcast Transcriber 🎙️→📝

Ett Python-skript för att automatiskt ladda ner och transkribera podcasts från RSS-feeds med hjälp av OpenAI Whisper.

## Funktioner

✅ **RSS Feed Support** - Hämta avsnitt från vilken podcast-RSS som helst
✅ **Automatisk Nedladdning** - Laddar ner MP3-filer automatiskt
✅ **Whisper Transkribering** - Använder OpenAI Whisper för högkvalitativ transkribering
✅ **Intelligenta Filnamn** - Smart S##E### namngivning baserat på iTunes-metadata
✅ **Metadata-extraktion** - Extraherar säsong/episod från RSS-taggar ELLER titel
✅ **Flexibel Filtrering** - Välj alla, nya, eller specifika datum
✅ **Europeiskt Datumformat** - DD-MM-ÅÅÅÅ format
✅ **State Management** - Håller koll på vad som redan transkriberarts
✅ **Progress Tracking** - Visar nedladdnings- och transkriberingsframsteg

## Systemkrav

- **OS**: Linux Mint (eller annan Linux-distribution)
- **Python**: 3.8 eller senare
- **Disk**: Tillräckligt utrymme för ljudfiler och transkriptioner
- **RAM**: Minst 4GB rekommenderas (Whisper använder lite minne)

## Installation

### Steg 1: Installera Python och pip

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Steg 2: Klona projektet från GitHub

```bash
cd ~
git clone https://github.com/cgillinger/podtranscript.git
cd podtranscript
```

### Steg 3: Skapa virtuell miljö (rekommenderas)

```bash
python3 -m venv venv
source venv/bin/activate
```

### Steg 4: Installera dependencies

```bash
pip install -r requirements.txt
```

**OBS**: Första gången du kör skriptet kommer Whisper att ladda ner sin modell (ca 140MB för "base"-modellen).

### Steg 5: Gör skriptet körbart

```bash
chmod +x podcast_transcriber.py
```

## Användning

### Grundläggande användning

```bash
python3 podcast_transcriber.py
```

Om du använder virtuell miljö:

```bash
source venv/bin/activate
python3 podcast_transcriber.py
```

### Steg-för-steg guide

1. **Kör skriptet**
   ```bash
   python3 podcast_transcriber.py
   ```

2. **Ange RSS-URL**
   ```
   Ange RSS-URL för podcasten: https://example.com/podcast/feed.xml
   ```

3. **Välj filtreringsläge**
   - **Alla avsnitt** - Laddar ner och transkriberar alla avsnitt
   - **Endast nya** - Bara avsnitt som inte transkriberarts tidigare
   - **Datumintervall** - Ange från- och till-datum

4. **Ange datum (om du valde datumintervall)**
   ```
   Från datum: 01-01-2024
   Till datum: 31-12-2024
   ```
   Accepterade format:
   - DD-MM-ÅÅÅÅ (t.ex. 15-03-2024)
   - DD/MM/ÅÅÅÅ (t.ex. 15/03/2024)
   - DD.MM.ÅÅÅÅ (t.ex. 15.03.2024)

5. **Bekräfta och vänta**
   - Skriptet visar hur många avsnitt som kommer bearbetas
   - Bekräfta med 'j' för att fortsätta
   - Vänta medan nedladdning och transkribering pågår

### Exempel på användning

#### Exempel 1: Alla avsnitt
```bash
$ python3 podcast_transcriber.py

Ange RSS-URL för podcasten: https://podcast.example.com/feed.xml

Hämtar RSS-feed...
✓ Hittade 50 avsnitt med ljudfiler

Vilka avsnitt vill du transkribera?
  1. Alla avsnitt
  2. Endast nya (ej tidigare transkriberade)
  3. Specifikt datumintervall

Ditt val: 1

50 avsnitt kommer att laddas ner och transkriberas.
Fortsätt? (j/n): j
```

#### Exempel 2: Endast nya avsnitt
```bash
Ditt val: 2

✓ 5 nya avsnitt (av 50 totalt)
5 avsnitt kommer att laddas ner och transkriberas.
```

#### Exempel 3: Datumintervall
```bash
Ditt val: 3

Ange datumintervall (format: DD-MM-ÅÅÅÅ eller DD/MM/ÅÅÅÅ)
Från datum: 01-01-2024
Till datum: 31-03-2024

✓ 12 avsnitt i datumintervallet
```

## Filstruktur

Efter körning skapas följande struktur:

```
podcasts/
├── audio/                          # Nedladdade MP3-filer
│   ├── S05E083_2026-01-12_DQ_in_Pizza_Hell.mp3
│   ├── E347_2024-03-22_Breaking_News.mp3
│   ├── BONUS_2026-01-08_Stargazing.mp3
│   └── ...
├── transcripts/                    # Transkriberade textfiler
│   ├── S05E083_2026-01-12_DQ_in_Pizza_Hell.txt
│   ├── E347_2024-03-22_Breaking_News.txt
│   ├── BONUS_2026-01-08_Stargazing.txt
│   └── ...
└── transcribed_episodes.json      # State-fil (spårar vad som transkriberrats)
```

### Intelligenta Filnamn

Skriptet använder ett **smart filnamnssystem** baserat på podcast RSS-metadata (iTunes-taggar och titelanalys):

#### Format-prioritering

1. **Med säsong och episod**: `S05E083_2026-01-12_Episodtitel.mp3`
   - Extraherar från `<itunes:season>` och `<itunes:episode>` taggar
   - Eller parsar titel som "Season 5, Ep 83 - Titel"
   - Exempel: `S02E015_2024-03-21_The_Future_of_AI.mp3`

2. **Endast episodnummer**: `E347_2024-03-22_Episodtitel.mp3`
   - När bara episodnummer finns tillgängligt
   - Exempel: `E347_2024-03-22_Breaking_News.mp3`

3. **Speciella typer** (bonus/trailer): `BONUS_2026-01-08_Episodtitel.mp3`
   - För avsnitt markerade som bonus eller trailer
   - Exempel: `TRAILER_2024-01-01_Season_3_Trailer.mp3`

4. **Fallback** (datum + titel): `2024-02-14_Episodtitel.mp3`
   - När ingen episode/season-metadata finns
   - Exempel: `2024-02-14_Random_Podcast.mp3`

#### Nummerpaddning

- **Säsonger**: 2 siffror (S01, S02, ..., S99)
- **Episoder**: 3-4 siffror (E001, E023, E1234)
  - Automatisk expansion för episoder över 999

#### Titelrensning

Filnamnen rensas automatiskt:
- Ogiltiga tecken tas bort (`<>:"/\|?*`)
- Mellanslag ersätts med understreck
- Max titellängd: 80 tecken
- Datum i ISO 8601-format: `ÅÅÅÅ-MM-DD`

#### Verkliga exempel

**Hello From The Magic Tavern** (titeln innehåller "Season 5, Ep 83"):
```
Original: Season 5, Ep 83 - DQ in Pizza Hell (w/ Tim Ryder)
Filnamn:  S05E083_2026-01-12_DQ_in_Pizza_Hell_(w_Tim_Ryder).mp3
```

**Samma podcast, bonus-avsnitt**:
```
Original: Patreon Unlock: Stargazing
Filnamn:  BONUS_2026-01-08_Stargazing.mp3
```

**Podcast med iTunes-taggar**:
```
Original: The Future of AI
iTunes:   <itunes:season>2</itunes:season> <itunes:episode>15</itunes:episode>
Filnamn:  S02E015_2024-03-21_The_Future_of_AI.mp3
```

**Daglig nyhetspodcast** (bara episodnummer):
```
Original: Episode 347 - Breaking News
Filnamn:  E347_2024-03-22_Breaking_News.mp3
```

### Transkriptionsfil-innehåll

Transkriptionsfiler innehåller metadata + transkription:

```
Titel: Season 5, Ep 83 - DQ in Pizza Hell (w/ Tim Ryder)
Säsong: 5, Avsnitt: 83
Typ: Full
Publicerad: 12-01-2026
Källa: https://example.com/episode.mp3

================================================================================

[Här kommer transkriberingen från Whisper...]
```

## Whisper-modeller

Skriptet använder "base"-modellen som standard, vilket ger en bra balans mellan hastighet och kvalitet.

Tillgängliga modeller:
- **tiny** - Snabbast, lägst kvalitet (~1GB RAM)
- **base** - Snabb, god kvalitet (~1GB RAM) ⭐ **Standard**
- **small** - Långsammare, bättre kvalitet (~2GB RAM)
- **medium** - Långsam, mycket bra kvalitet (~5GB RAM)
- **large** - Långsammast, bäst kvalitet (~10GB RAM)

För att ändra modell, redigera `podcast_transcriber.py` rad ~174:
```python
self.whisper_model = whisper.load_model("small")  # Ändra "base" till önskad modell
```

## Tips och tricks

### 💡 Kör i bakgrunden

För långa transkriberingsjobb:
```bash
nohup python3 podcast_transcriber.py > transcribe.log 2>&1 &
```

### 💡 Endast nya avsnitt

Kör regelbundet med "Endast nya"-läget för att automatiskt hålla dig uppdaterad:
```bash
# Lägg till i crontab för automatisk körning
0 6 * * * cd /path/to/podtranscript && ./podcast_transcriber.py
```

### 💡 Batch-bearbetning

Skriptet kan hantera många avsnitt - bara bekräfta och låt det köra!

### 💡 Spara diskutrymme

Om diskutrymme är begränsat, radera ljudfiler efter transkribering:
```bash
rm -rf podcasts/audio/*
```
Transkriptionerna finns kvar och state-filen vet vad som redan gjorts.

## Felsökning

### Problem: "Fel: Saknar nödvändigt bibliotek"

**Lösning**: Installera dependencies
```bash
pip install -r requirements.txt
```

### Problem: "Inga avsnitt hittades i feeden"

**Lösningar**:
- Kontrollera att RSS-URL:en är korrekt
- Testa URL:en i webbläsare
- Vissa feeds kräver specifika headers

### Problem: Whisper är långsamt

**Lösningar**:
- Använd mindre modell ("tiny" eller "base")
- Stäng andra program för att frigöra RAM
- Överväg GPU-acceleration (kräver CUDA-kompatibelt grafikkort)

### Problem: "Memory Error" vid transkribering

**Lösningar**:
- Använd mindre modell ("tiny" istället för "base")
- Stäng andra program
- Transkribera färre avsnitt åt gången

### Problem: Nedladdning misslyckas

**Lösningar**:
- Kontrollera internetanslutning
- Vissa podcasts kan ha geografiska begränsningar
- Prova igen senare (servern kan vara upptagen)

## Säkerhet och integritet

- Skriptet laddar endast ner publikt tillgängliga podcast-avsnitt
- Ingen data skickas till tredje part (förutom nedladdning från RSS-feed)
- Whisper körs lokalt på din dator
- State-filen sparas endast lokalt

## Licens

MIT License - Fri att använda och modifiera

## Support

Om du stöter på problem:
1. Kontrollera felsökningsavsnittet ovan
2. Säkerställ att alla dependencies är installerade
3. Kontrollera att Python-versionen är 3.8+

## Författare

Skapat med hjälp av Claude AI för automatisk podcast-transkribering.

---

**Lycka till med transkriberingen! 🎧📝**
