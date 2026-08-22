import requests
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

@dataclass
class TrackInfo:
    title: str
    artist: str
    album: str
    track_number: int
    duration_ms: int
    year: str
    genre: str

@dataclass
class AlbumInfo:
    collection_id: int
    artist: str
    album: str
    cover_url_hq: str
    track_count: int

def search_album(artist: str, album: str) -> Optional[AlbumInfo]:
    """Searches for an album on iTunes."""
    url = "https://itunes.apple.com/search"
    params = {
        "term": f"{artist} {album}",
        "entity": "album",
        "limit": 5
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    if data.get("resultCount", 0) == 0:
        return None
        
    # Get the first result
    result = data["results"][0]
    
    # Get high quality cover (replace 100x100 with 600x600)
    cover_url = result.get("artworkUrl100", "")
    cover_url_hq = cover_url.replace("100x100bb", "600x600bb")
    
    return AlbumInfo(
        collection_id=result["collectionId"],
        artist=result["artistName"],
        album=result["collectionName"],
        cover_url_hq=cover_url_hq,
        track_count=result["trackCount"]
    )

def get_tracks(collection_id: int) -> List[TrackInfo]:
    """Gets tracks for a specific album collection ID."""
    url = "https://itunes.apple.com/lookup"
    params = {
        "id": collection_id,
        "entity": "song"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    tracks = []
    for item in data.get("results", []):
        if item.get("wrapperType") == "track" and item.get("kind") == "song":
            release_date = item.get("releaseDate", "")
            year = release_date[:4] if release_date else ""
            
            track = TrackInfo(
                title=item.get("trackName", "Unknown Title"),
                artist=item.get("artistName", "Unknown Artist"),
                album=item.get("collectionName", "Unknown Album"),
                track_number=item.get("trackNumber", 0),
                duration_ms=item.get("trackTimeMillis", 0),
                year=year,
                genre=item.get("primaryGenreName", "Unknown Genre")
            )
            tracks.append(track)
            
    # Sort by track number
    tracks.sort(key=lambda t: t.track_number)
    return tracks

def download_cover_art(url: str, output_path: Path) -> bool:
    """Downloads the cover art to the specified path."""
    if not url:
        return False
        
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception:
        return False
