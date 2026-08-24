import time
from typing import Optional
from pathlib import Path
import questionary
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from . import config, utils, db
from .itunes_client import search_album, get_artist_albums, get_tracks, download_cover_art, AlbumInfo
from .youtube_client import search_track, download_audio
from .metadata import embed_metadata
from .lyrics_client import fetch_lyrics

console = Console()

def download_album(artist: str, album_name: Optional[str] = None):
    """Orchestrates the entire album download process with interactive navigation and back options."""
    current_artist = artist
    current_album_name = album_name

    while True:
        # Step 1: Resolve Album
        if current_album_name:
            console.print(f"[bold blue]🔍 Searching iTunes API for:[/] {current_artist} - {current_album_name}")
            album_info = search_album(current_artist, current_album_name)
            if not album_info:
                console.print(f"[bold red]❌ Album '{current_album_name}' not found on iTunes.[/]")
                action = questionary.select(
                    "What would you like to do?",
                    choices=[
                        questionary.Choice(title=f"💿 Browse all albums by '{current_artist}'", value="browse_albums"),
                        questionary.Choice(title="👤 Search another artist", value="change_artist"),
                        questionary.Choice(title="❌ Cancel", value="cancel"),
                    ]
                ).ask()
                
                if action == "browse_albums":
                    current_album_name = None
                    continue
                elif action == "change_artist":
                    new_art = questionary.text("Enter artist name:").ask()
                    if not new_art or not new_art.strip():
                        console.print("[yellow]Cancelled.[/]")
                        return
                    current_artist = new_art.strip()
                    current_album_name = None
                    continue
                else:
                    console.print("[bold yellow]Cancelled by user.[/]")
                    return
        else:
            console.print(f"[bold blue]🔍 Searching albums by artist:[/] {current_artist}")
            albums = get_artist_albums(current_artist)
            if not albums:
                console.print(f"[bold red]❌ No albums found for artist '{current_artist}' on iTunes.[/]")
                action = questionary.select(
                    "What would you like to do?",
                    choices=[
                        questionary.Choice(title="👤 Search another artist", value="change_artist"),
                        questionary.Choice(title="❌ Cancel", value="cancel"),
                    ]
                ).ask()
                if action == "change_artist":
                    new_art = questionary.text("Enter artist name:").ask()
                    if not new_art or not new_art.strip():
                        console.print("[yellow]Cancelled.[/]")
                        return
                    current_artist = new_art.strip()
                    continue
                else:
                    console.print("[bold yellow]Cancelled by user.[/]")
                    return
                
            choices = []
            for alb in albums:
                year_str = f", {alb.year}" if alb.year else ""
                status = db.get_album_download_status(alb.collection_id, alb.track_count, artist=alb.artist, album=alb.album)
                if status["is_complete"]:
                    badge = " [✓ Downloaded]"
                elif status["downloaded_count"] > 0:
                    badge = f" [{status['downloaded_count']}/{alb.track_count} downloaded]"
                else:
                    badge = ""
                label = f"{alb.album} ({alb.track_count} tracks{year_str}){badge}"
                choices.append(questionary.Choice(title=label, value=alb))
                
            choices.append(questionary.Separator())
            choices.append(questionary.Choice(title="👤 Search another artist", value="__CHANGE_ARTIST__"))
            choices.append(questionary.Choice(title="❌ Cancel", value="__CANCEL__"))
            
            console.print()
            selected = questionary.select(
                f"Select an album by {current_artist} (Use arrow keys to move, Enter to confirm):",
                choices=choices
            ).ask()
            
            if not selected or selected == "__CANCEL__":
                console.print("[bold yellow]Download cancelled.[/]")
                return
            elif selected == "__CHANGE_ARTIST__":
                new_art = questionary.text("Enter artist name:").ask()
                if not new_art or not new_art.strip():
                    console.print("[yellow]Cancelled.[/]")
                    return
                current_artist = new_art.strip()
                current_album_name = None
                continue
                
            album_info = selected

        # Step 2: Tracklist & Setup Directories
        console.print(f"[bold green]📀 Selected album:[/] {album_info.album} by {album_info.artist} ({album_info.track_count} tracks)")
        
        base_dir = config.get_output_dir()
        artist_dir = base_dir / utils.sanitize_filename(album_info.artist)
        album_dir = artist_dir / utils.sanitize_filename(album_info.album)
        utils.ensure_dir(album_dir)
        
        tracks = get_tracks(album_info.collection_id)
        if not tracks:
            console.print("[bold red]❌ Could not retrieve tracklist.[/]")
            current_album_name = None
            continue
            
        cover_path = album_dir / "cover.jpg"
        if not cover_path.exists():
            console.print("[dim]Downloading cover art...[/]")
            download_cover_art(album_info.cover_url_hq, cover_path)
            
        # Step 3: Track Selection & Confirmation Loop
        exit_to_outer = False
        while True:
            downloaded_tracks = db.get_downloaded_track_numbers(album_info.collection_id)
            choices = []
            total_album_ms = 0
            for t in tracks:
                total_album_ms += t.duration_ms
                est_size = utils.calculate_estimated_size(t.duration_ms)
                duration_fmt = utils.format_duration(t.duration_ms)
                
                # Check if already downloaded on disk or db
                filename = config.TRACK_NAMING_TEMPLATE.format(
                    track_number=t.track_number,
                    title=utils.sanitize_filename(t.title),
                    ext=config.AUDIO_FORMAT
                )
                file_path = album_dir / filename
                is_downloaded = (t.track_number in downloaded_tracks) or file_path.exists()
                
                badge = " [✓ Downloaded]" if is_downloaded else ""
                label = f"{t.track_number:02d}. {t.title} ({duration_fmt}, {est_size}){badge}"
                choices.append(questionary.Choice(title=label, value=t, checked=not is_downloaded))
            
            total_album_size = utils.calculate_estimated_size(total_album_ms)
            console.print(f"Total Album Estimated Size: [bold yellow]{total_album_size}[/]")
            console.print()
            
            selected_tracks = questionary.checkbox(
                "Select the tracks you want to download (Space to select/deselect, Enter to confirm):",
                choices=choices
            ).ask()
            
            if selected_tracks is None:
                console.print("[bold yellow]Download cancelled.[/]")
                return
                
            if not selected_tracks:
                console.print("[bold yellow]⚠️ No tracks selected.[/]")
                action_empty = questionary.select(
                    "What would you like to do?",
                    choices=[
                        questionary.Choice(title="✏️  Reselect Tracks", value="reselect"),
                        questionary.Choice(title="💿 Choose Another Album", value="change_album"),
                        questionary.Choice(title="👤 Search Another Artist", value="change_artist"),
                        questionary.Choice(title="❌ Cancel", value="cancel")
                    ]
                ).ask()
                
                if action_empty == "reselect":
                    continue
                elif action_empty == "change_album":
                    current_album_name = None
                    exit_to_outer = True
                    break
                elif action_empty == "change_artist":
                    new_art = questionary.text("Enter artist name:").ask()
                    if not new_art or not new_art.strip():
                        console.print("[yellow]Cancelled.[/]")
                        return
                    current_artist = new_art.strip()
                    current_album_name = None
                    exit_to_outer = True
                    break
                else:
                    console.print("[bold yellow]Cancelled by user.[/]")
                    return
                    
            # Show summary table
            console.print()
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
            
            # Step 4: Interactive Confirmation with Back / Reselect options
            action = questionary.select(
                "Confirm download action:",
                choices=[
                    questionary.Choice(title="🚀 Start Download", value="start"),
                    questionary.Choice(title="✏️  Reselect Tracks (Checkbox)", value="reselect"),
                    questionary.Choice(title="💿 Choose Another Album", value="change_album"),
                    questionary.Choice(title="👤 Search Another Artist", value="change_artist"),
                    questionary.Choice(title="❌ Cancel", value="cancel"),
                ]
            ).ask()
            
            if action == "reselect":
                continue
            elif action == "change_album":
                current_album_name = None
                exit_to_outer = True
                break
            elif action == "change_artist":
                new_art = questionary.text("Enter artist name:").ask()
                if not new_art or not new_art.strip():
                    console.print("[yellow]Cancelled.[/]")
                    return
                current_artist = new_art.strip()
                current_album_name = None
                exit_to_outer = True
                break
            elif action == "cancel" or not action:
                console.print("[bold yellow]Download cancelled by user.[/]")
                return
            elif action == "start":
                console.print()
                # Run download engine
                success_count = 0
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    album_task = progress.add_task("[bold green]Overall Progress...", total=len(selected_tracks))
                    track_task = progress.add_task("[cyan]Preparing...", total=100)
                    
                    for track in selected_tracks:
                        track_desc = f"{track.track_number:02d}. {track.title}"
                        
                        filename = config.TRACK_NAMING_TEMPLATE.format(
                            track_number=track.track_number,
                            title=utils.sanitize_filename(track.title),
                            ext=config.AUDIO_FORMAT
                        )
                        file_path = album_dir / filename
                        
                        if file_path.exists():
                            db.record_download(
                                collection_id=album_info.collection_id,
                                artist=album_info.artist,
                                album=album_info.album,
                                track_count=album_info.track_count,
                                year=album_info.year,
                                folder_path=album_dir,
                                track_number=track.track_number,
                                title=track.title,
                                file_path=file_path
                            )
                            progress.update(track_task, completed=100, description=f"[dim green]Skipping:[/] {track_desc}")
                            progress.console.print(f"[dim green]✓ Skipped (exists):[/] {track_desc}")
                            progress.advance(album_task)
                            success_count += 1
                            continue
                            
                        progress.update(track_task, completed=10, description=f"[cyan]Searching YT:[/] {track_desc}")
                        yt_url = search_track(album_info.artist, track.title)
                        
                        if not yt_url:
                            progress.console.print(f"[red]❌ Not found on YT:[/] {track_desc}")
                            progress.advance(album_task)
                            continue
                            
                        progress.update(track_task, completed=40, description=f"[yellow]Downloading:[/] {track_desc}")
                        dl_success = download_audio(yt_url, file_path)
                        
                        if not dl_success:
                            progress.console.print(f"[red]❌ Download failed:[/] {track_desc}")
                            progress.advance(album_task)
                            continue
                            
                        progress.update(track_task, completed=75, description=f"[magenta]Fetching lyrics:[/] {track_desc}")
                        lyrics_data = fetch_lyrics(
                            track_name=track.title,
                            artist_name=album_info.artist,
                            album_name=album_info.album,
                            duration_s=track.duration_ms // 1000 if track.duration_ms else None
                        )
                        
                        progress.update(track_task, completed=90, description=f"[blue]Embedding tags:[/] {track_desc}")
                        embed_metadata(
                            file_path=file_path, 
                            track=track, 
                            cover_path=cover_path, 
                            total_tracks=len(tracks),
                            plain_lyrics=lyrics_data.plain_lyrics,
                            synced_lyrics=lyrics_data.synced_lyrics
                        )
                        
                        db.record_download(
                            collection_id=album_info.collection_id,
                            artist=album_info.artist,
                            album=album_info.album,
                            track_count=album_info.track_count,
                            year=album_info.year,
                            folder_path=album_dir,
                            track_number=track.track_number,
                            title=track.title,
                            file_path=file_path
                        )
                        
                        progress.update(track_task, completed=100, description=f"[green]Completed:[/] {track_desc}")
                        progress.console.print(f"[green]✓ Completed:[/] {track_desc}")
                        progress.advance(album_task)
                        success_count += 1
                        
                        time.sleep(1)

                console.print(f"\n[bold green]✅ Download complete! Downloaded {success_count}/{len(selected_tracks)} tracks.[/]")
                console.print(f"Check your files at: [bold cyan]{album_dir}[/]")
                return

        if exit_to_outer:
            continue
