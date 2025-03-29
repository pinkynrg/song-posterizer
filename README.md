# 🎙️ Lyrics Poster Generator

This script generates a **high-resolution A0-size PDF poster** of an artist's lyrics, automatically fetched from Genius and styled into a typographic layout where the text fills the page, overlaid on a background image and signature.

## ✨ Features

- 🔍 Automatically fetches lyrics from Genius
- 📚 Groups songs by album, sorted by release date
- 📄 Fills exactly one A0 page (1000mm × 1380mm) using dynamic font sizing
- 🖼️ Optional background image and signature watermark
- 📆 Uses disk caching to avoid redundant API calls

## 📦 Dependencies

Install via pip:

```bash
pip install lyricsgenius weasyprint diskcache
```

> ⚠️ WeasyPrint requires additional system packages like `libpangocairo`. See [WeasyPrint installation guide](https://weasyprint.readthedocs.io/en/stable/install.html) for details.

## 🚀 Usage

```bash
python generate_poster.py \
  --api_key YOUR_GENIUS_API_KEY \
  --artist "Lucio Dalla" \
  --background_url "https://example.com/background.jpg" \
  --signature_url "https://example.com/signature.png"
```

### Required Arguments

| Argument     | Description                     |
|--------------|---------------------------------|
| `--api_key`  | Your Genius API token           |
| `--artist`   | Name of the artist              |

### Optional Arguments

| Argument           | Description                            |
|--------------------|----------------------------------------|
| `--background_url` | URL of the background image (A0-sized) |
| `--signature_url`  | URL of a signature overlay             |

## 📸 Output

- The script generates a file called `[artist-name] poster.pdf`
- Dimensions: **1000mm × 1380mm** (A0 portrait)
- Lyrics are formatted and wrapped to fill the page using the largest possible font size

## 🧠 How it Works

1. Fetches artist data via Genius API (cached locally)
2. Cleans and formats lyrics:
   - Removes section headers like `[Chorus]`
   - Replaces line breaks with bullets
   - Normalizes spaces and punctuation
3. Uses **binary search** to find the maximum font size that fits all text on one A0 page
4. Renders the final HTML with WeasyPrint to a PDF

## 🗂 Example

![Preview](https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Lucio_Dalla_firma.svg/1600px-Lucio_Dalla_firma.svg.png)

> You can use images like the artist's face as a **background**, and overlay their signature subtly in the corner.

---

Let me know if you'd like:
- 📁 The script refactored into reusable modules
- 🚲 A `--dry-run` or `--output` flag
- 🧪 Tests or GitHub Actions integration

Happy poster-making 🎶🖼️

