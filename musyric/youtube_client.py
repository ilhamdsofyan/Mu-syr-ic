import yt_dlp
from thefuzz import fuzz
from pathlib import Path
from typing import Optional

def search_track(artist: str, track: str) -> Optional[str]:
    """
    Searches YouTube Music for the track and returns the best video URL.
    We use yt-dlp to search and then filter results using fuzzy matching.
    """
    query = f"{artist} {track} auto-generated" # Adding auto-generated often yields official audio
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extract_flat': 'in_playlist',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch5', # Search and return 5 results
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
                    # We want to match artist and track name
                    target = f"{artist} {track}".lower()
                    
                    # Fuzzy match title with target
                    ratio = fuzz.token_set_ratio(target, title.lower())
                    
                    if ratio > highest_ratio:
                        highest_ratio = ratio
                        best_match = entry.get('url') or entry.get('webpage_url')
                
                if best_match:
                    # yt-dlp search might return ID or direct URL depending on extract_flat
                    if not best_match.startswith('http'):
                        best_match = f"https://www.youtube.com/watch?v={best_match}"
                    return best_match
                
                # Fallback to first if fuzzy matching fails to find a good one
                first_entry = info['entries'][0]
                url = first_entry.get('url') or first_entry.get('webpage_url')
                if url and not url.startswith('http'):
                     url = f"https://www.youtube.com/watch?v={url}"
                return url
        except Exception:
            return None
    return None

def download_audio(url: str, output_path: Path) -> bool:
    """
    Downloads audio using yt-dlp and converts to M4A.
    """
    # yt-dlp needs the base name without extension for the outtmpl, it adds it based on format
    # But since we force m4a, we can give it exactly
    
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': str(output_path.with_suffix('')), # yt-dlp will append .m4a 
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '256',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            return True
        except Exception as e:
            return False
