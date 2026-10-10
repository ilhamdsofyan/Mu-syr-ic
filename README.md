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

## ⚡ One-Click Install

Just clone the repo and run the installer for your OS — **no prior knowledge needed!** The installer handles Python, FFmpeg, virtual environments, and all dependencies for you.

```bash
git clone https://github.com/ilhamdsofyan/Mu-syr-ic.git
cd Mu-syr-ic
```

### 🪟 Windows
Double-click **`install.bat`** or run it from the terminal:
```cmd
install.bat
```

### 🍎 macOS
Double-click **`install.command`** in Finder, or run in Terminal:
```bash
chmod +x install.sh && bash install.sh
```

### 🐧 Linux
```bash
chmod +x install.sh && bash install.sh
```

After installation, **double-click the launcher** to open the app:

| OS | Double-click this file |
|----|----------------------|
| 🪟 Windows | **`start.bat`** |
| 🍎 macOS | **`start.command`** |
| 🐧 Linux | **`start.sh`** |

The app opens as an interactive terminal with a main menu — search artists, pick albums, download, and loop back. No commands to memorize.

You can also use the CLI directly:
```bash
# Windows
musyric.bat download "Coldplay"

# macOS / Linux
./musyric.sh download "Coldplay"
# (or simply: musyric download "Coldplay" if installed globally)
```

## 📖 Manual Installation

<details>
<summary>Click to expand manual setup instructions</summary>

### Prerequisites

- **Python 3.9+**
- **FFmpeg**: Must be installed on your system.
  - Windows: `winget install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### Steps

```bash
# Create virtual environment and install dependencies
python -m venv .venv
# On Windows
.\.venv\Scripts\Activate.ps1
# On macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```
</details>

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
