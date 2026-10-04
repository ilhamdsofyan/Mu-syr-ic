"""
Mu(syr)ic Interactive App Mode
A persistent terminal application with a main menu loop.
"""
import sys
import os

# Fix for Windows UnicodeEncodeError with emojis and box-drawing chars
if sys.platform == "win32":
    os.system("")  # Enable ANSI/VT100 escape sequences on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__, db
from .downloader import download_album

console = Console()

BANNER = r"""
[bold cyan]
  ███╗   ███╗██╗   ██╗    ███████╗██╗   ██╗██████╗     ██╗ ██████╗
  ████╗ ████║██║   ██║    ██╔════╝╚██╗ ██╔╝██╔══██╗    ██║██╔════╝
  ██╔████╔██║██║   ██║    ███████╗ ╚████╔╝ ██████╔╝    ██║██║     
  ██║╚██╔╝██║██║   ██║    ╚════██║  ╚██╔╝  ██╔══██╗    ██║██║     
  ██║ ╚═╝ ██║╚██████╔╝    ███████║   ██║   ██║  ██║    ██║╚██████╗
  ╚═╝     ╚═╝ ╚═════╝     ╚══════╝   ╚═╝   ╚═╝  ╚═╝    ╚═╝ ╚═════╝
[/bold cyan]"""

def show_banner():
    """Display the app banner."""
    console.clear()
    console.print(BANNER)
    console.print(
        Panel(
            f"[bold white]Music Album Downloader[/]  •  v{__version__}\n"
            "[dim]iTunes metadata  •  YouTube Music audio  •  Auto lyrics[/]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()

def show_history():
    """Display download history in a table."""
    records = db.get_all_history()
    if not records:
        console.print("[yellow]  No download history yet. Go download some music! 🎶[/]\n")
        return

    table = Table(title="🎵 Download History", show_header=True, header_style="bold magenta", padding=(0, 1))
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Artist", style="cyan")
    table.add_column("Album", style="bold white")
    table.add_column("Year", justify="center", style="dim")
    table.add_column("Tracks", justify="right", style="green")
    table.add_column("Downloaded", style="dim")

    for i, r in enumerate(records, 1):
        track_str = f"{r['downloaded_tracks']}/{r['track_count'] or '?'}"
        table.add_row(
            str(i),
            r["artist"],
            r["album"],
            r["year"] or "-",
            track_str,
            str(r["last_downloaded_at"])[:16],
        )

    console.print(table)
    console.print()

def do_search_and_download():
    """Prompt for artist name and start the interactive download flow."""
    console.print()
    artist = questionary.text(
        "🔍 Enter artist name:",
        qmark="",
        validate=lambda val: True if val.strip() else "Please enter an artist name",
    ).ask()

    if not artist or not artist.strip():
        console.print("[yellow]  Cancelled.[/]\n")
        return

    try:
        download_album(artist.strip())
    except KeyboardInterrupt:
        console.print("\n[bold red]  ❌ Interrupted.[/]\n")
    except Exception as e:
        console.print(f"\n[bold red]  ❌ Error:[/] {e}\n")

def main_menu():
    """Show the main menu and return the user's choice."""
    return questionary.select(
        "What would you like to do?",
        qmark="🎵",
        choices=[
            questionary.Choice(title="🔍  Search & Download Music", value="download"),
            questionary.Choice(title="📋  View Download History",   value="history"),
            questionary.Choice(title="❌  Exit",                    value="exit"),
        ],
    ).ask()

def run():
    """Main entry point for the interactive app mode."""
    show_banner()

    while True:
        try:
            choice = main_menu()

            if choice == "download":
                do_search_and_download()
                # After download finishes, re-show banner for clean look
                show_banner()

            elif choice == "history":
                console.print()
                show_history()

            elif choice == "exit" or choice is None:
                console.print("\n[bold cyan]👋 Thanks for using Mu(syr)ic! Enjoy your music. 🎶[/]\n")
                break

        except KeyboardInterrupt:
            console.print("\n[bold cyan]👋 Bye! 🎶[/]\n")
            break
        except EOFError:
            break

if __name__ == "__main__":
    run()
