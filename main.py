import re
import hashlib
import json
import argparse
from itertools import chain
import diskcache
import lyricsgenius
from weasyprint import HTML, CSS
from datetime import datetime

cache = diskcache.Cache("./artist_cache")

def _make_cache_key(artist):
    key_data = {"artist": artist}
    return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

def fetch_raw_artist(api_key, artist):
    key = _make_cache_key(artist)
    if key in cache:
        return cache[key]
    
    genius = lyricsgenius.Genius(
        api_key,
        timeout=60,
        remove_section_headers=True,
        skip_non_songs=True,
        verbose=True
    )

    raw_artist = genius.search_artist(artist, sort="popularity")
    cache[key] = raw_artist
    return raw_artist

def parse_sortable_date(s):
    for fmt in ("%B %d, %Y", "%Y"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None

def fetch_artist(api_key, artist): 

    raw_artist = fetch_raw_artist(api_key, artist)

    # Group songs by album
    albums = {}
    for song in raw_artist.songs:
        if song.lyrics and ("(" not in song.title and "(" not in song.album.name if song.album else "Inedite"):
          
          album_title = song.album.name if song.album else "Inedite"
          
          if album_title not in albums:
              albums[album_title] = {
                  "album_title": album_title,
                  "songs": []
              }

          if not albums[album_title].get("album_release_date", None):
              albums[album_title]["album_release_date"] = parse_sortable_date(song.to_dict().get('release_date_for_display'))

          albums[album_title]["songs"].append({
              "title": song.title,
              "lyrics": song.lyrics,
          })

    album_list = list(albums.values())
    return album_list

def format_album(album):
    def cleanup_lyrics(lyrics):
      # Rimuove sezioni tipo [Chorus], [Verse 1], ecc.
      lyrics_no_brackets = re.sub(r"\[.*?\]", "", lyrics or "")
      
      # Rimuove newlines e rimpiazza con spazio
      lyrics_one_line = lyrics_no_brackets.replace('\n', ' · ')
      
      # Normalizza gli spazi multipli
      lyrics_cleaned = re.sub(r'\s+', ' ', lyrics_one_line).strip()

      # Sostituisce più di 3 puntini consecutivi con solo "..."
      lyrics_cleaned = re.sub(r"\.{4,}", "...", lyrics_cleaned)

      # Se il testo è per lo più in maiuscolo, rendilo tutto minuscolo
      upper_chars = sum(1 for c in lyrics_cleaned if c.isupper())
      letter_chars = sum(1 for c in lyrics_cleaned if c.isalpha())
      if letter_chars > 0 and upper_chars / letter_chars > 0.7:
          lyrics_cleaned = lyrics_cleaned.lower()

      return lyrics_cleaned
    
    return ["<span class='album_title'>{title} ({date})</span>".format(title=album["album_title"], date=album.get('album_release_date').strftime("%Y"))] + ["<span class='song_title'> • {title} • </span> {lyrics}".format(title=song.get('title'), lyrics=cleanup_lyrics(song.get('lyrics'))) for song in album["songs"]]

def find_optimal_font_size(content, min_size=1.0, max_size=20.0, precision=0.01):
    best_size = min_size

    while round(max_size - min_size, 4) > precision:
        mid_size = round((min_size + max_size) / 2, 2)
        print("Trying font size: {}".format(mid_size))
        html = HTML(string=content)
        css = CSS(string=f'''
            @page {{
                size: 1000mm 1380mm;
                margin: 0mm;
            }}
            html {{
                font-size: {mid_size}pt;
            }}
        ''')

        document = html.render(stylesheets=[css])
        num_pages = len(document.pages)

        if num_pages > 1:
            max_size = mid_size  # Too big, decrease
        else:
            best_size = mid_size  # Fits on one page, try to increase
            min_size = mid_size

    return best_size

def main(api_key, artist, background_url, signature_url):

  albums = fetch_artist(api_key, artist)
  filtered_albums = [album for album in albums if len(album["songs"]) > 0 and album["album_release_date"] is not None]
  sorted_albums = sorted(filtered_albums, key=lambda x: x["album_release_date"])
  formatted_albums = list(chain.from_iterable(format_album(album) for album in sorted_albums))
  content = " ".join(formatted_albums)
  html_text = f'''
    <html>
    <head>
        <title>Song Lyrics</title>
        <style>
          body {{
            font-family: Courier New, monospace;
            text-align: justify;
          }}
          .background {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url("{background_url}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            opacity: 0.4;
            z-index: -1;
          }}
          .signature {{
            position: fixed;
            bottom: 60px;
            right: 0px;
            width: 800px;
            height: 400px;
            background-image: url("{signature_url}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            opacity: 0.2;
            z-index: -1;
          }}
          .album_title {{
            font-weight: bolder;
            color: #ef0000;
          }}
          .song_title {{
            font-weight: bold;
          }}
          .content {{
            padding: 70px;
          }}
        </style>
    </head>
    <body>
      <div class="background"></div>
      <div class="signature"></div>
      <div class="content">{content}</div>
    </body>
    </html>
  '''
  
  font_size = find_optimal_font_size(html_text, min_size=1.0, max_size=20.0, precision=0.01)

  html = HTML(string=html_text)
  css = CSS(string=f'''
              @page {{
                  size: 1000mm 1380mm;
                  margin: 0mm;
              }}
              html {{
                  font-size: {font_size}pt;
              }}
          ''')
  document = html.render(stylesheets=[css])
  document.write_pdf(f'{artist} poster.pdf')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate poster PDF.")
    parser.add_argument("--api_key", type=str, help="Set api key", required=True)
    parser.add_argument("--artist", type=str, help="Set the artist", required=True)
    parser.add_argument("--background_url", type=str, help="Set the background", required=False)
    parser.add_argument("--signature_url", type=str, help="Set the signature", required=False)
    args = parser.parse_args()
    
    main(args.api_key, args.artist, args.background_url, args.signature_url)