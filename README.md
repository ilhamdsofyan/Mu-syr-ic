# Mu(syr)ic 🎵

A sleek Python CLI tool to download full music albums. It uses the **iTunes Search API** to fetch accurate metadata (tracklist, cover art, tags) and **YouTube Music** (via yt-dlp) to download the audio.

Features:
- **Zero Config**: No API keys or authentication required.
- **High Quality**: Downloads audio as M4A (AAC 256kbps).
- **Auto Tagging**: Automatically embeds ID3/MP4 tags and cover art.
- **Smart Search**: Just type the artist and album name.

## Prerequisites

- **Python 3.9+**
- **FFmpeg**: Must be installed on your system.
  - Windows: `winget install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/musyric.git
cd musyric

# Create virtual environment and install dependencies
python -m venv .venv
# On Windows
.\.venv\Scripts\Activate.ps1
# On macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Usage

Run the CLI tool by passing the artist and album name:

```bash
python -m musyric.cli "Radiohead" "OK Computer"
```

The downloaded album will be saved in your `~/Music` directory by default, organized as `~/Music/Artist/Album/`.
