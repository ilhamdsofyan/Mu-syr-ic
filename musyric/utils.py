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
