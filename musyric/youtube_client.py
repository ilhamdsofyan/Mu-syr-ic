import yt_dlp
from thefuzz import fuzz
from pathlib import Path
from typing import Optional, List, Dict, Any
import time
import re

BAD_KEYWORDS = [
    'cover', 'karaoke', 'live', 'tribute', 'remix', 'parodi', 'parody',
    'reaction', 'tutorial', 'chord', 'sped up', 'slowed', 'reverb',
    'ai cover', 'instrumental', 'guitar lesson', 'drum cover', 'vocal cover',
    'acoustic session', 'radio session'
]

def normalize_text(text: str) -> str:
    """Normalize text and common Indonesian historical orthography variations."""
    t = text.lower()
    t = t.replace('ch', 'h').replace('dj', 'j').replace('tj', 'c').replace('oe', 'u')
    t = re.sub(r'[^\w\s]', ' ', t)
    return ' '.join(t.split())

def score_candidate(entry: Dict[str, Any], artist: str, track: str, expected_duration_s: Optional[int] = None) -> float:
    """
    Score a YouTube search result candidate based on:
    - Title match ratio
    - Artist presence in channel or title
    - Official release indicators (Topic, VEVO, Official Audio)
    - Penalty for cover, live, remix, karaoke
    - Duration proximity to the official track duration
    """
    title = entry.get('title', '')
    channel = entry.get('channel') or entry.get('uploader') or ''
    dur = entry.get('duration') or 0

    norm_artist = normalize_text(artist)
    norm_track = normalize_text(track)
    norm_title = normalize_text(title)
    norm_channel = normalize_text(channel)

    score = 0.0

    # 1. Title matching with track
    track_ratio = fuzz.token_set_ratio(norm_track, norm_title)
    score += track_ratio * 0.4

    # 2. Artist presence in Title or Channel
    artist_in_channel = fuzz.partial_ratio(norm_artist, norm_channel) >= 80 or norm_artist in norm_channel
    artist_in_title = fuzz.partial_ratio(norm_artist, norm_title) >= 80 or norm_artist in norm_title

    if artist_in_channel:
        score += 30.0
    if artist_in_title:
        score += 15.0

    # 3. Official / Topic Channel Indicators
    if 'topic' in norm_channel:
        score += 25.0
    if 'vevo' in norm_channel:
        score += 25.0
    if 'official' in norm_channel or 'official' in norm_title:
        score += 15.0
    if 'audio' in norm_title:
        score += 10.0

    # 4. Bad keyword penalties (covers, karaoke, live, etc.)
    for kw in BAD_KEYWORDS:
        if kw in norm_title and kw not in norm_track:
            score -= 50.0
        if kw in norm_channel and kw not in norm_artist:
            score -= 50.0

    # 5. Duration match (essential for studio version vs live / covers)
    if expected_duration_s and dur > 0:
        diff = abs(dur - expected_duration_s)
        if diff <= 3:
            score += 35.0
        elif diff <= 7:
            score += 25.0
        elif diff <= 15:
            score += 10.0
        elif diff > 60:
            score -= 50.0
        elif diff > 30:
            score -= 20.0

    return score

def search_track(artist: str, track: str, expected_duration_s: Optional[int] = None) -> Optional[str]:
    """Search for the best audio track on YouTube, prioritizing official releases and duration proximity."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extract_flat': 'in_playlist',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch10',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'socket_timeout': 30,
        'retries': 3,
        'fragment_retries': 3,
        'nocheckcertificate': True,
    }

    queries = [
        f"{artist} {track} audio",
        f"{artist} {track}"
    ]

    all_scored = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for q in queries:
            try:
                info = ydl.extract_info(q, download=False)
                entries = [e for e in info.get('entries', []) if e]
                if not entries:
                    continue

                for entry in entries:
                    s = score_candidate(entry, artist, track, expected_duration_s)
                    all_scored.append((s, entry))

                all_scored.sort(key=lambda x: x[0], reverse=True)
                top_score, top_entry = all_scored[0]

                # Confident match found on primary search query
                if top_score >= 50.0:
                    best_url = top_entry.get('url') or top_entry.get('webpage_url')
                    if best_url and not best_url.startswith('http'):
                        best_url = f"https://www.youtube.com/watch?v={best_url}"
                    return best_url
            except Exception:
                continue

    if all_scored:
        all_scored.sort(key=lambda x: x[0], reverse=True)
        best_entry = all_scored[0][1]
        best_url = best_entry.get('url') or best_entry.get('webpage_url')
        if best_url and not best_url.startswith('http'):
            best_url = f"https://www.youtube.com/watch?v={best_url}"
        return best_url

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
