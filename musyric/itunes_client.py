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

from thefuzz import fuzz

def search_album(artist: str, album: str) -> Optional[AlbumInfo]:
    """Searches for an album on iTunes with fallback to fuzzy matching via artist."""
    url = "https://itunes.apple.com/search"
    
    # Attempt 1: Direct Search
    params = {
        "term": f"{artist} {album}",
        "entity": "album",
        "limit": 5
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("resultCount", 0) > 0:
            result = data["results"][0]
            return _parse_album_result(result)
            
    # Attempt 2: Fallback to Artist Search -> Albums -> Fuzzy Match
    artist_params = {
        "term": artist,
        "entity": "musicArtist",
        "limit": 3
    }
    artist_resp = requests.get(url, params=artist_params)
    if artist_resp.status_code != 200:
        return None
        
    artist_data = artist_resp.json()
    if not artist_data.get("results"):
        return None
        
    # Get top artist IDs
    artist_ids = [a["artistId"] for a in artist_data["results"] if "artistId" in a]
    
    all_albums = []
    for aid in artist_ids:
        lookup_url = "https://itunes.apple.com/lookup"
        lookup_resp = requests.get(lookup_url, params={"id": aid, "entity": "album"})
        if lookup_resp.status_code == 200:
            lookup_data = lookup_resp.json()
            for item in lookup_data.get("results", []):
                if item.get("wrapperType") == "collection":
                    all_albums.append(item)
                    
    if not all_albums:
        return None
        
    # Fuzzy match the requested album name with found albums
    best_match = None
    highest_ratio = -1
    
    for alb in all_albums:
        title = alb.get("collectionName", "")
        ratio = fuzz.token_set_ratio(album.lower(), title.lower())
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = alb
            
    if best_match and highest_ratio > 60: # Threshold
        return _parse_album_result(best_match)
        
    return None

def _parse_album_result(result: dict) -> AlbumInfo:
    """Helper to parse raw iTunes API result to AlbumInfo."""
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
