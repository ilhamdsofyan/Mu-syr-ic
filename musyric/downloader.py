import time
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from . import config, utils
from .itunes_client import search_album, get_tracks, download_cover_art
from .youtube_client import search_track, download_audio
from .metadata import embed_metadata
from .lyrics_client import fetch_lyrics

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
    
    # Ask which tracks to download using interactive checkbox
    import questionary
    
    choices = []
    total_album_ms = 0
    for t in tracks:
        total_album_ms += t.duration_ms
        est_size = utils.calculate_estimated_size(t.duration_ms)
        duration_fmt = utils.format_duration(t.duration_ms)
        label = f"{t.track_number:02d}. {t.title} ({duration_fmt}, {est_size})"
        choices.append(questionary.Choice(title=label, value=t, checked=True))
    
    total_album_size = utils.calculate_estimated_size(total_album_ms)
    console.print(f"Total Album Estimated Size: [bold yellow]{total_album_size}[/]")
    console.print()
    selected_tracks = questionary.checkbox(
        "Select the tracks you want to download (Space to select/deselect, Enter to confirm):",
        choices=choices
    ).ask()
    
    if not selected_tracks:
        console.print("[bold yellow]No tracks selected. Download cancelled.[/]")
        return
        
    console.print()
    
    # Show summary of selected tracks
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title")
    table.add_column("Duration", justify="right")
    table.add_column("Est. Size", justify="right", style="cyan")
    
    total_ms = 0
    for t in selected_tracks:
        total_ms += t.duration_ms
        table.add_row(
            str(t.track_number), 
            t.title, 
            utils.format_duration(t.duration_ms),
            utils.calculate_estimated_size(t.duration_ms)
        )
        
    console.print(table)
    total_size = utils.calculate_estimated_size(total_ms)
    console.print(f"Total Selected Estimated Size: [bold yellow]{total_size}[/]")
    console.print(f"Output directory: [bold cyan]{album_dir}[/]\n")
    
    import typer
    if not typer.confirm("Do you want to proceed with the download?"):
        console.print("[bold yellow]Download cancelled by user.[/]")
        return
        
    console.print()
    
    # 4. Process selected tracks
    success_count = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        album_task = progress.add_task("[bold green]Downloading Selected Tracks...", total=len(selected_tracks))
        
        for track in selected_tracks:
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
                
            # Fetch lyrics
            progress.update(track_task, description=f"[magenta]Fetching lyrics:[/] {track_desc}")
            lyrics_data = fetch_lyrics(
                track_name=track.title,
                artist_name=album_info.artist,
                album_name=album_info.album,
                duration_s=track.duration_ms // 1000 if track.duration_ms else None
            )
            
            # Embed metadata & lyrics
            progress.update(track_task, description=f"[blue]Embedding tags:[/] {track_desc}")
            embed_metadata(
                file_path=file_path, 
                track=track, 
                cover_path=cover_path, 
                total_tracks=len(tracks),
                plain_lyrics=lyrics_data.plain_lyrics,
                synced_lyrics=lyrics_data.synced_lyrics
            )
            
            progress.update(track_task, completed=100, description=f"[green]✓ Completed:[/] {track_desc}")
            progress.advance(album_task)
            success_count += 1
            
            # Small sleep to be polite to the APIs
            time.sleep(1)

    console.print(f"\n[bold green]✅ Download complete! Downloaded {success_count}/{len(selected_tracks)} tracks.[/]")
    console.print(f"Check your files at: [bold cyan]{album_dir}[/]")
