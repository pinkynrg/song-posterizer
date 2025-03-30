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

def get_genius(api_key):
    return lyricsgenius.Genius(
        api_key,
        timeout=60,
        remove_section_headers=True,
        skip_non_songs=True,
        verbose=True
    )

def fetch_albums(api_key, artist):
    genius_handle = get_genius(api_key)
    next_page = 1
    result = []
    while next_page:
      respose = genius_handle.search_albums(artist, per_page=50, page=next_page)
      hits = respose['sections'][0]['hits']
      for hit in hits:
          album = hit.get('result')
          local_artist = album.get('artist').get('name')
          local_date = album.get('release_date_components') or {}
          local_year = local_date.get('year') or {}
          local_album_name = album.get('name')
          if local_artist == artist and local_year:
            result += [{ 
                "id": album.get('id'),
                "title": local_album_name, 
                "artist": local_artist, 
                "year": local_year  
            }]
      next_page = respose.get('next_page')
    return sorted(result, key=lambda x: x["year"], reverse=False)

def fetch_album_tracks(api_key, album):
    
    print(f"Fetching album tracks for {album.get('title')}")
    
    key = _make_cache_key(album.get('id'))
    if key in cache:
        return cache[key]
    
    genius_handle = get_genius(api_key)
    response = genius_handle.search_album(album_id=album.get('id'))
    songs = []
    for track in response.tracks:
        song = track.song
        songs += [{"number": track.number, "lyrics": song.lyrics, "title": song.title} ]

    cache[key] = songs

    return songs

def format_album(album):
    def cleanup_lyrics(lyrics):
      # Rimuove sezioni tipo [Chorus], [Verse 1], ecc.
      lyrics_no_brackets = re.sub(r"\[.*?\]", "", lyrics or "")
      
      # Rimuove newlines e rimpiazza con spazio
      lyrics_one_line = re.sub(r'\n+', ' · ', lyrics_no_brackets)
      
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
    
    return [f"<span class='album_title'>{album.get('title')} ({album.get('year')})</span>"] + [f"<span class='song_title'> • {song.get('title')} • </span> {cleanup_lyrics(song.get('lyrics'))}" for song in album["songs"]]

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

  albums = [album for album in fetch_albums(api_key, artist) if "live" not in album.get('title').lower()]
  for album in albums:
      album["songs"] = fetch_album_tracks(api_key, album)

  formatted_albums = list(chain.from_iterable(format_album(album) for album in albums))

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
