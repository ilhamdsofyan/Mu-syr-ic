import yt_dlp
from thefuzz import fuzz
from pathlib import Path
from typing import Optional
import time

def search_track(artist: str, track: str) -> Optional[str]:
    query = f"{artist} {track} auto-generated"
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extract_flat': 'in_playlist',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch5',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'socket_timeout': 30,
        'retries': 3,
        'fragment_retries': 3,
        'nocheckcertificate': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info and info['entries']:
                best_match = None
                highest_ratio = -1
                for entry in info['entries']:
                    if not entry: continue
                    title = entry.get('title', '')
                    target = f"{artist} {track}".lower()
                    ratio = fuzz.token_set_ratio(target, title.lower())
                    if ratio > highest_ratio:
                        highest_ratio = ratio
                        best_match = entry.get('url') or entry.get('webpage_url')
                if best_match:
                    if not best_match.startswith('http'):
                        best_match = f"https://www.youtube.com/watch?v={best_match}"
                    return best_match
                first_entry = info['entries'][0]
                url = first_entry.get('url') or first_entry.get('webpage_url')
                if url and not url.startswith('http'):
                     url = f"https://www.youtube.com/watch?v={url}"
                return url
        except Exception:
            return None
    return None

def download_audio(url: str, output_path: Path) -> bool:
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': str(output_path.with_suffix('')),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '256',
        }],
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'socket_timeout': 30,
        'retries': 3,
        'fragment_retries': 3,
        'nocheckcertificate': True,
    }
    
    max_attempts = 3
    for attempt in range(max_attempts):
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
                return True
            except Exception as e:
                print(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2 ** (attempt + 1))  # 2s, 4s, 8s backoff
    
    return False
