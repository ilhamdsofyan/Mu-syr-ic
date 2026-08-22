from pathlib import Path
from mutagen.mp4 import MP4, MP4Cover
from typing import Optional
from .itunes_client import TrackInfo

def embed_metadata(file_path: Path, track: TrackInfo, cover_path: Optional[Path] = None, total_tracks: int = 0) -> bool:
    """Embeds ID3/MP4 metadata and cover art into the audio file."""
    if not file_path.exists():
        return False
        
    try:
        audio = MP4(file_path)
        
        # Standard MP4 tags
        audio["\xa9nam"] = track.title
        audio["\xa9ART"] = track.artist
        audio["\xa9alb"] = track.album
        audio["\xa9day"] = track.year
        audio["\xa9gen"] = track.genre
        
        # Track number is a tuple (track_number, total_tracks)
        audio["trkn"] = [(track.track_number, total_tracks)]
        
        # Embed cover art if available
        if cover_path and cover_path.exists():
            with open(cover_path, "rb") as f:
                cover_data = f.read()
                # Use JPEG format for cover art
                audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
                
        audio.save()
        return True
    except Exception as e:
        print(f"Error embedding metadata: {e}")
        return False
