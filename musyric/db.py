import sqlite3
from pathlib import Path
from typing import Optional, Set, List, Dict, Any
from . import config

def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with row_factory set."""
    db_path = config.get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database schema."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS albums (
                collection_id INTEGER PRIMARY KEY,
                artist TEXT NOT NULL,
                album TEXT NOT NULL,
                track_count INTEGER,
                year TEXT,
                folder_path TEXT,
                last_downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER NOT NULL,
                track_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                file_path TEXT NOT NULL,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(collection_id, track_number),
                FOREIGN KEY(collection_id) REFERENCES albums(collection_id) ON DELETE CASCADE
            )
        """)
        conn.commit()

def record_download(
    collection_id: int,
    artist: str,
    album: str,
    track_count: int,
    year: str,
    folder_path: Path,
    track_number: int,
    title: str,
    file_path: Path
):
    """Records or updates a downloaded track and its parent album in SQLite."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        # Insert or ignore/update album
        cursor.execute("""
            INSERT INTO albums (collection_id, artist, album, track_count, year, folder_path, last_downloaded_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(collection_id) DO UPDATE SET
                folder_path = excluded.folder_path,
                last_downloaded_at = CURRENT_TIMESTAMP
        """, (collection_id, artist, album, track_count, year, str(folder_path)))
        
        # Insert or replace track
        cursor.execute("""
            INSERT INTO tracks (collection_id, track_number, title, file_path, downloaded_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(collection_id, track_number) DO UPDATE SET
                title = excluded.title,
                file_path = excluded.file_path,
                downloaded_at = CURRENT_TIMESTAMP
        """, (collection_id, track_number, title, str(file_path)))
        conn.commit()

def get_album_download_status(collection_id: int, total_expected: int = 0, artist: Optional[str] = None, album: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns download status for an album.
    Status dict: {"downloaded_count": int, "total_count": int, "is_complete": bool}
    Also checks if the files actually exist on disk and scans directory if not yet in DB.
    """
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT track_number, file_path FROM tracks WHERE collection_id = ?
        """, (collection_id,))
        rows = cursor.fetchall()
        
        valid_downloaded = 0
        for r in rows:
            f_path = Path(r["file_path"])
            if f_path.exists():
                valid_downloaded += 1
                
        # If not recorded in DB yet, check the actual filesystem directory
        if valid_downloaded == 0 and artist and album:
            from .utils import sanitize_filename
            from .config import get_output_dir
            album_dir = get_output_dir() / sanitize_filename(artist) / sanitize_filename(album)
            if album_dir.exists():
                m4a_files = list(album_dir.glob("*.m4a"))
                valid_downloaded = len(m4a_files)
                
        is_complete = (valid_downloaded >= total_expected and total_expected > 0)
        return {
            "downloaded_count": valid_downloaded,
            "total_count": total_expected,
            "is_complete": is_complete
        }

def get_downloaded_track_numbers(collection_id: int) -> Set[int]:
    """Returns a set of track numbers that have already been downloaded for this album and exist on disk."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT track_number, file_path FROM tracks WHERE collection_id = ?
        """, (collection_id,))
        rows = cursor.fetchall()
        
        existing_tracks = set()
        for r in rows:
            if Path(r["file_path"]).exists():
                existing_tracks.add(r["track_number"])
        return existing_tracks

import hashlib

def sync_from_disk():
    """Scans the music directory on disk and populates SQLite database with existing audio files and tags."""
    init_db()
    music_dir = config.get_output_dir()
    if not music_dir.exists():
        return
        
    try:
        from mutagen.mp4 import MP4
    except ImportError:
        return
        
    with get_connection() as conn:
        cursor = conn.cursor()
        for m4a_file in music_dir.glob("*/*/*.m4a"):
            try:
                audio = MP4(m4a_file)
                title = str(audio.get("\xa9nam", [m4a_file.stem])[0])
                artist = str(audio.get("\xa9ART", [m4a_file.parent.parent.name])[0])
                album = str(audio.get("\xa9alb", [m4a_file.parent.name])[0])
                year = str(audio.get("\xa9day", [""])[0]) if audio.get("\xa9day") else ""
                trkn = audio.get("trkn", [(0, 0)])[0]
                track_number = trkn[0] if isinstance(trkn, (tuple, list)) else 0
                total_tracks = trkn[1] if isinstance(trkn, (tuple, list)) and len(trkn) > 1 else 0
                
                # Check if album already exists in DB by artist and album name
                cursor.execute(
                    "SELECT collection_id FROM albums WHERE LOWER(artist) = ? AND LOWER(album) = ?",
                    (artist.lower(), album.lower())
                )
                existing_row = cursor.fetchone()
                if existing_row:
                    cid = existing_row["collection_id"]
                else:
                    # Deterministic MD5 hash to integer
                    key = f"{artist.lower().strip()}:{album.lower().strip()}".encode("utf-8")
                    cid = int(hashlib.md5(key).hexdigest()[:8], 16)
                
                record_download(
                    collection_id=cid,
                    artist=artist,
                    album=album,
                    track_count=total_tracks,
                    year=year,
                    folder_path=m4a_file.parent,
                    track_number=track_number,
                    title=title,
                    file_path=m4a_file
                )
            except Exception:
                continue

def get_all_history() -> List[Dict[str, Any]]:
    """Returns all downloaded albums with their track counts from SQLite."""
    init_db()
    sync_from_disk()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.collection_id, a.artist, a.album, a.track_count, a.year, a.folder_path, a.last_downloaded_at,
                   COUNT(t.id) as downloaded_tracks
            FROM albums a
            LEFT JOIN tracks t ON a.collection_id = t.collection_id
            GROUP BY a.collection_id
            ORDER BY a.last_downloaded_at DESC
        """)
        return [dict(r) for r in cursor.fetchall()]
