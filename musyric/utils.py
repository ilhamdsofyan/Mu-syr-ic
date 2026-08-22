import re
from pathlib import Path

def sanitize_filename(name: str) -> str:
    """Removes invalid characters from a string to make it a valid filename."""
    # Remove invalid characters: \ / : * ? " < > |
    sanitized = re.sub(r'[\\/:*?"<>|]', '', name)
    # Remove leading/trailing whitespaces and dots
    sanitized = sanitized.strip().strip('.')
    # Ensure it's not empty
    if not sanitized:
        sanitized = "Unknown"
    return sanitized

def calculate_estimated_size(duration_ms: int, bitrate_kbps: int = 256) -> str:
    """Calculates estimated file size based on duration and bitrate."""
    if not duration_ms:
        return "0.0 MB"
    
    seconds = duration_ms / 1000
    # Bitrate is kilobits per second. Divide by 8 for kilobytes, 1024 for MB.
    size_mb = (seconds * bitrate_kbps) / 8 / 1024
    return f"{size_mb:.1f} MB"

def format_duration(ms: int) -> str:
    """Formats duration in milliseconds to MM:SS string."""
    if not ms:
        return "00:00"
    
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def ensure_dir(path: Path) -> Path:
    """Ensures a directory exists, creates it if not."""
    path.mkdir(parents=True, exist_ok=True)
    return path
