import sys
import typer
from rich.console import Console

# Fix for Windows UnicodeEncodeError with emojis
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from . import __version__
from .downloader import download_album

app = typer.Typer(
    name="musyric",
    help="Download full music albums with metadata from iTunes and audio from YouTube Music.",
    add_completion=False,
)
console = Console()

@app.command()
def download(
    artist: str = typer.Argument(..., help="Name of the artist"),
    album: str = typer.Argument(..., help="Name of the album")
):
    """Download an entire album."""
    try:
        download_album(artist, album)
    except KeyboardInterrupt:
        console.print("\n[bold red]❌ Download cancelled by user.[/]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ An unexpected error occurred:[/] {e}")
        raise typer.Exit(1)

@app.command()
def version():
    """Print the version number."""
    console.print(f"Mu(syr)ic version: [bold cyan]{__version__}[/]")

if __name__ == "__main__":
    app()
