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
    year: str = ""

from thefuzz import fuzz

def get_artist_albums(artist: str) -> List[AlbumInfo]:
    """Fetches all albums by an artist from iTunes with storefront fallbacks (ID, US, default)."""
    url = "https://itunes.apple.com/search"
    
    for country in ["ID", "US", None]:
        artist_params = {
            "term": artist,
            "entity": "musicArtist",
            "limit": 10
        }
        if country:
            artist_params["country"] = country
            
        try:
            artist_resp = requests.get(url, params=artist_params, timeout=10)
            if artist_resp.status_code != 200:
                continue
                
            artist_data = artist_resp.json()
            results = artist_data.get("results", [])
            if not results:
                continue
                
            # Find best matching artists using fuzzy ratio
            best_artists = []
            clean_artist = artist.lower().strip('. ')
            for a in results:
                aname = a.get("artistName", "").lower()
                clean_aname = aname.strip('. ')
                ratio = max(fuzz.ratio(artist.lower(), aname), fuzz.ratio(clean_artist, clean_aname))
                if ratio >= 80:
                    best_artists.append((ratio, a.get("artistId")))
                    
            best_artists.sort(key=lambda x: x[0], reverse=True)
            if not best_artists:
                best_artists = [(100, results[0].get("artistId"))]
                
            # Take artists matching the highest tier score
            max_score = best_artists[0][0]
            top_artist_ids = [aid for score, aid in best_artists if score >= max(80, max_score - 10)]
            
            albums = []
            seen_ids = set()
            for aid in top_artist_ids:
                lookup_url = "https://itunes.apple.com/lookup"
                lookup_params = {"id": aid, "entity": "album", "limit": 100}
                if country:
                    lookup_params["country"] = country
                lookup_resp = requests.get(lookup_url, params=lookup_params, timeout=10)
                if lookup_resp.status_code == 200:
                    lookup_data = lookup_resp.json()
                    for item in lookup_data.get("results", []):
                        if item.get("wrapperType") == "collection":
                            cid = item.get("collectionId")
                            if cid and cid not in seen_ids:
                                seen_ids.add(cid)
                                albums.append(_parse_album_result(item))
                                
            if albums:
                # Sort albums by year descending (newest first)
                albums.sort(key=lambda a: a.year, reverse=True)
                return albums
        except Exception:
            continue
            
    return []

def search_album(artist: str, album: str) -> Optional[AlbumInfo]:
    """Searches for an album on iTunes with fallback to fuzzy matching via artist and storefronts."""
    url = "https://itunes.apple.com/search"
    
    # Attempt 1: Direct Search with country fallbacks
    for country in ["ID", "US", None]:
        params = {
            "term": f"{artist} {album}",
            "entity": "album",
            "limit": 5
        }
        if country:
            params["country"] = country
            
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("resultCount", 0) > 0:
                    result = data["results"][0]
                    return _parse_album_result(result)
        except Exception:
            continue
            
    # Attempt 2: Fallback to Artist Search -> Albums -> Fuzzy Match
    all_albums = get_artist_albums(artist)
    if not all_albums:
        return None
        
    # Fuzzy match the requested album name with found albums
    best_match = None
    highest_ratio = -1
    
    for alb in all_albums:
        title = alb.album
        ratio = fuzz.token_set_ratio(album.lower(), title.lower())
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = alb
            
    if best_match and highest_ratio > 60: # Threshold
        return best_match
        
    return None

def _parse_album_result(result: dict) -> AlbumInfo:
    """Helper to parse raw iTunes API result to AlbumInfo."""
    cover_url = result.get("artworkUrl100", "")
    cover_url_hq = cover_url.replace("100x100bb", "600x600bb")
    release_date = result.get("releaseDate", "")
    year = release_date[:4] if release_date else ""
    
    return AlbumInfo(
        collection_id=result["collectionId"],
        artist=result["artistName"],
        album=result["collectionName"],
        cover_url_hq=cover_url_hq,
        track_count=result["trackCount"],
        year=year
    )

def get_tracks(collection_id: int) -> List[TrackInfo]:
    """Gets tracks for a specific album collection ID with storefront fallbacks (ID, US, default)."""
    url = "https://itunes.apple.com/lookup"
    
    for country in ["ID", "US", None]:
        params = {
            "id": collection_id,
            "entity": "song"
        }
        if country:
            params["country"] = country
            
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                continue
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
                    
            if tracks:
                # Sort by track number
                tracks.sort(key=lambda t: t.track_number)
                return tracks
        except Exception:
            continue
            
    return []

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
