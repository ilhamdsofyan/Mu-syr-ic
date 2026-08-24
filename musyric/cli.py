import sys
from typing import Optional
import typer
from rich.console import Console

# Fix for Windows UnicodeEncodeError with emojis
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from . import __version__, db
from .downloader import download_album
from rich.table import Table

app = typer.Typer(
    name="musyric",
    help="Download full music albums with metadata from iTunes and audio from YouTube Music.",
    add_completion=False,
)
console = Console()

@app.command()
def download(
    artist: str = typer.Argument(..., help="Name of the artist"),
    album: Optional[str] = typer.Argument(None, help="Name of the album (optional, shows album list if omitted)")
):
    """Download an entire album. If album name is omitted, an interactive list of albums by the artist will be displayed."""
    try:
        download_album(artist, album)
    except KeyboardInterrupt:
        console.print("\n[bold red]❌ Download cancelled by user.[/]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ An unexpected error occurred:[/] {e}")
        raise typer.Exit(1)

@app.command()
def history():
    """List all downloaded albums and their tracks tracked in SQLite database."""
    records = db.get_all_history()
    if not records:
        console.print("[yellow]No download history found in database.[/]")
        return
        
    table = Table(title="🎵 Downloaded Albums History", show_header=True, header_style="bold magenta")
    table.add_column("Artist", style="cyan")
    table.add_column("Album", style="bold white")
    table.add_column("Year", justify="center", style="dim")
    table.add_column("Tracks", justify="right", style="green")
    table.add_column("Last Downloaded", style="dim")
    
    for r in records:
        track_str = f"{r['downloaded_tracks']}/{r['track_count'] or '?'}"
        table.add_row(
            r["artist"],
            r["album"],
            r["year"] or "-",
            track_str,
            str(r["last_downloaded_at"])[:16]
        )
        
    console.print(table)

@app.command()
def version():
    """Print the version number."""
    console.print(f"Mu(syr)ic version: [bold cyan]{__version__}[/]")

if __name__ == "__main__":
    app()
