# Mu(syr)ic 🎵

A sleek Python CLI tool to download full music albums. It uses the **iTunes Search API** to fetch accurate metadata (tracklist, cover art, tags) and **YouTube Music** (via yt-dlp) to download the audio.

Features:
- **Zero Config**: No API keys or authentication required.
- **Interactive Album Picker**: Type just the artist name to browse and pick an album interactively.
- **Downloaded Album & Track Detection**: Automatically detects already downloaded albums and tracks via SQLite database (`~/.musyric/history.db`) and disk scanner.
- **Interactive Track Selection**: Choose specific tracks using interactive checkboxes (already downloaded tracks are un-checked by default).
- **Auto Lyrics**: Automatically embeds tags and generates synchronized `.lrc` files (via LRCLIB) for players like AIMP.
- **High Quality**: Downloads audio as M4A (AAC 256kbps).
- **Smart Search**: iTunes API + YouTube Music matching.

## Prerequisites

- **Python 3.9+**
- **FFmpeg**: Must be installed on your system.
  - Windows: `winget install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

## Installation

```bash
# Clone the repository
git clone https://github.com/ilhamdsofyan/Mu-syr-ic.git
cd Mu-syr-ic

# Create virtual environment and install dependencies
python -m venv .venv
# On Windows
.\.venv\Scripts\Activate.ps1
# On macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Usage

### 1. Interactive Mode (Browse Albums)
Just provide the artist name, browse their discography, and see which albums are already downloaded:
```bash
python -m musyric.cli download "Coldplay"
```

### 2. Direct Mode (Specific Album)
Provide both artist and album to download directly:
```bash
python -m musyric.cli download "Radiohead" "OK Computer"
```

### 3. View Download History
View all albums and tracks you have downloaded:
```bash
python -m musyric.cli history
```

The downloaded album will be saved in your `~/Music` directory by default, organized as `~/Music/Artist/Album/`.
