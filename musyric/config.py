from pathlib import Path
import os

# Default output directory: ~/Music
DEFAULT_MUSIC_DIR = Path.home() / "Music"

# File format settings
AUDIO_FORMAT = "m4a"
AUDIO_BITRATE = "256k"

# Naming template for tracks
TRACK_NAMING_TEMPLATE = "{track_number:02d} - {title}.{ext}"

def get_output_dir() -> Path:
    """Returns the base output directory for downloaded music."""
    return DEFAULT_MUSIC_DIR
