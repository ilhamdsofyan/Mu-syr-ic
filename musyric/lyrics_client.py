import requests
from typing import Optional, Tuple
from dataclasses import dataclass

USER_AGENT = "Musyric/0.1.0 (https://github.com/ilhamdsofyan/Mu-syr-ic)"

@dataclass
class LyricsData:
    plain_lyrics: Optional[str] = None
    synced_lyrics: Optional[str] = None

def fetch_lyrics(track_name: str, artist_name: str, album_name: Optional[str] = None, duration_s: Optional[int] = None) -> LyricsData:
    """
    Fetches plain and synced lyrics from LRCLIB.
    """
    url = "https://lrclib.net/api/get"
    headers = {"User-Agent": USER_AGENT}
    
    # Try exact get
    params = {
        "track_name": track_name,
        "artist_name": artist_name,
    }
    if album_name:
        params["album_name"] = album_name
    if duration_s:
        params["duration"] = str(duration_s)
        
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return LyricsData(
                plain_lyrics=data.get("plainLyrics"),
                synced_lyrics=data.get("syncedLyrics")
            )
    except Exception:
        pass
        
    # Fallback to search endpoint
    search_url = "https://lrclib.net/api/search"
    search_params = {
        "q": f"{artist_name} {track_name}"
    }
    try:
        resp = requests.get(search_url, params=search_params, headers=headers, timeout=5)
        if resp.status_code == 200:
            results = resp.json()
            if results and isinstance(results, list):
                # Pick the first result that has lyrics
                for res in results:
                    plain = res.get("plainLyrics")
                    synced = res.get("syncedLyrics")
                    if plain or synced:
                        return LyricsData(
                            plain_lyrics=plain,
                            synced_lyrics=synced
                        )
    except Exception:
        pass

    return LyricsData()
