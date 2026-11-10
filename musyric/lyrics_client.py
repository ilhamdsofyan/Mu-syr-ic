import requests
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
import os
import re

USER_AGENT = "Musyric/0.1.0 (https://github.com/ilhamdsofyan/Mu-syr-ic)"
DEFAULT_APP_ID = "hLXGc55SAtWqDgr2Kt5qCroLi79mTQSYihdGcx9mfIQ"
DEFAULT_API_KEY = "lrclib_sk_FTuCcPRZt9EzZGTOFlpm5ad6zG8xxKhWOqGWzjdoh5s"

@dataclass
class LyricsData:
    plain_lyrics: Optional[str] = None
    synced_lyrics: Optional[str] = None

def clean_track_title(title: str) -> str:
    """Strip common noise from track titles that may prevent lyrics lookup."""
    t = re.sub(r'\(feat\..*?\)', '', title, flags=re.IGNORECASE)
    t = re.sub(r'\[feat\..*?\]', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\(remaster.*?\)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\[remaster.*?\]', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\(official.*?\)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\(from\s+".*?"\)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+-\s+.*remaster.*', '', t, flags=re.IGNORECASE)
    return t.strip(' .-_')

def fetch_lyrics(track_name: str, artist_name: str, album_name: Optional[str] = None, duration_s: Optional[int] = None) -> LyricsData:
    """
    Fetches plain and synced lyrics from LRCLIB using multi-tiered fallback
    with authenticated headers for high-reliability and zero rate-limiting.
    """
    base_url = "https://lrclib.net/api"
    app_id = os.getenv("LRCLIB_APP_ID", DEFAULT_APP_ID)
    api_key = os.getenv("LRCLIB_API_KEY", DEFAULT_API_KEY)

    headers = {
        "User-Agent": USER_AGENT,
        "Lrclib-App-Id": app_id,
        "Lrclib-Api-Key": api_key,
    }

    cleaned_title = clean_track_title(track_name)
    titles_to_try = [track_name]
    if cleaned_title and cleaned_title.lower() != track_name.lower():
        titles_to_try.append(cleaned_title)

    # 1. Try exact /api/get
    # 1a. With album & duration
    for t in titles_to_try:
        params = {"track_name": t, "artist_name": artist_name}
        if album_name:
            params["album_name"] = album_name
        if duration_s:
            params["duration"] = str(duration_s)
        try:
            resp = requests.get(f"{base_url}/get", params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("plainLyrics") or data.get("syncedLyrics"):
                    return LyricsData(plain_lyrics=data.get("plainLyrics"), synced_lyrics=data.get("syncedLyrics"))
        except Exception:
            pass

    # 1b. Without album restriction (loose get)
    for t in titles_to_try:
        params = {"track_name": t, "artist_name": artist_name}
        if duration_s:
            params["duration"] = str(duration_s)
        try:
            resp = requests.get(f"{base_url}/get", params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("plainLyrics") or data.get("syncedLyrics"):
                    return LyricsData(plain_lyrics=data.get("plainLyrics"), synced_lyrics=data.get("syncedLyrics"))
        except Exception:
            pass

    # 2. Try /api/search with specific fields & query
    search_queries = [
        {"track_name": cleaned_title, "artist_name": artist_name},
        {"q": f"{artist_name} {cleaned_title}"},
    ]
    if cleaned_title.lower() != track_name.lower():
        search_queries.append({"q": f"{artist_name} {track_name}"})

    for s_params in search_queries:
        try:
            resp = requests.get(f"{base_url}/search", params=s_params, headers=headers, timeout=5)
            if resp.status_code == 200:
                results = resp.json()
                if results and isinstance(results, list):
                    # Sort candidates: prefer syncedLyrics, then duration proximity
                    def sort_key(item):
                        has_synced = 1 if item.get("syncedLyrics") else 0
                        has_plain = 1 if item.get("plainLyrics") else 0
                        dur_diff = abs(item.get("duration", 0) - (duration_s or 0)) if duration_s else 0
                        return (has_synced, has_plain, -dur_diff)

                    results.sort(key=sort_key, reverse=True)
                    for res in results:
                        plain = res.get("plainLyrics")
                        synced = res.get("syncedLyrics")
                        if plain or synced:
                            return LyricsData(plain_lyrics=plain, synced_lyrics=synced)
        except Exception:
            pass

    return LyricsData()
