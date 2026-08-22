import time
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from . import config, utils
from .itunes_client import search_album, get_tracks, download_cover_art
from .youtube_client import search_track, download_audio
from .metadata import embed_metadata

console = Console()

def download_album(artist: str, album_name: str):
    """Orchestrates the entire album download process."""
    console.print(f"[bold blue]🔍 Searching iTunes API for:[/] {artist} - {album_name}")
    
    # 1. Search iTunes
    album_info = search_album(artist, album_name)
    if not album_info:
        console.print("[bold red]❌ Album not found on iTunes.[/]")
        return
        
    console.print(f"[bold green]📀 Found album:[/] {album_info.album} by {album_info.artist} ({album_info.track_count} tracks)")
    
    # Setup directories
    base_dir = config.get_output_dir()
    artist_dir = base_dir / utils.sanitize_filename(album_info.artist)
    album_dir = artist_dir / utils.sanitize_filename(album_info.album)
    utils.ensure_dir(album_dir)
    
    # 2. Get Tracklist
    tracks = get_tracks(album_info.collection_id)
    if not tracks:
        console.print("[bold red]❌ Could not retrieve tracklist.[/]")
        return
        
    # 3. Download Cover Art
    cover_path = album_dir / "cover.jpg"
    if not cover_path.exists():
        console.print("[dim]Downloading cover art...[/]")
        download_cover_art(album_info.cover_url_hq, cover_path)
    
    # Show tracks table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title")
    table.add_column("Duration", justify="right")
    table.add_column("Est. Size", justify="right", style="cyan")
    
    total_ms = 0
    for t in tracks:
        total_ms += t.duration_ms
        table.add_row(
            str(t.track_number), 
            t.title, 
            utils.format_duration(t.duration_ms),
            utils.calculate_estimated_size(t.duration_ms)
        )
        
    console.print(table)
    total_size = utils.calculate_estimated_size(total_ms)
    console.print(f"Total Estimated Size: [bold yellow]{total_size}[/]")
    console.print(f"Output directory: [bold cyan]{album_dir}[/]\n")
    
    # Ask for confirmation
    import typer
    if not typer.confirm("Do you want to proceed with the download?"):
        console.print("[bold yellow]Download cancelled by user.[/]")
        return
        
    console.print()
    
    # 4. Process each track
    success_count = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        album_task = progress.add_task("[bold green]Downloading Album...", total=len(tracks))
        
        for track in tracks:
            track_desc = f"{track.track_number:02d}. {track.title}"
            track_task = progress.add_task(f"Downloading [cyan]{track_desc}[/]...", total=100)
            
            # Formulate filename
            filename = config.TRACK_NAMING_TEMPLATE.format(
                track_number=track.track_number,
                title=utils.sanitize_filename(track.title),
                ext=config.AUDIO_FORMAT
            )
            file_path = album_dir / filename
            
            # Check if file exists (resume support)
            if file_path.exists():
                progress.update(track_task, completed=100, description=f"[green]✓ Skiped (exists): {track_desc}[/]")
                progress.advance(album_task)
                success_count += 1
                continue
                
            # Search YouTube
            progress.update(track_task, description=f"[cyan]Searching YT:[/] {track_desc}")
            yt_url = search_track(album_info.artist, track.title)
            
            if not yt_url:
                progress.update(track_task, description=f"[red]❌ Not found on YT:[/] {track_desc}")
                progress.advance(album_task)
                continue
                
            # Download audio
            progress.update(track_task, description=f"[yellow]Downloading:[/] {track_desc}")
            dl_success = download_audio(yt_url, file_path)
            
            if not dl_success:
                progress.update(track_task, description=f"[red]❌ Download failed:[/] {track_desc}")
                progress.advance(album_task)
                continue
                
            # Embed metadata
            progress.update(track_task, description=f"[blue]Embedding tags:[/] {track_desc}")
            embed_metadata(file_path, track, cover_path, len(tracks))
            
            progress.update(track_task, completed=100, description=f"[green]✓ Completed:[/] {track_desc}")
            progress.advance(album_task)
            success_count += 1
            
            # Small sleep to be polite to the APIs
            time.sleep(1)

    console.print(f"\n[bold green]✅ Album complete! Downloaded {success_count}/{len(tracks)} tracks.[/]")
    console.print(f"Check your files at: [bold cyan]{album_dir}[/]")
