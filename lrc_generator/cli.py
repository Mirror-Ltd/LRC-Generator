"""
Command-line interface for the LRC generator
"""

import os
import sys
import click
from typing import Dict, Optional

from .utils import (
    validate_audio_file,
    validate_lyrics_file,
    extract_metadata_from_filename, 
    ensure_directory_exists
)
from .whisper_sync import WhisperLyricsSync


@click.group()
def cli():
    """Generate synchronized lyrics (.lrc) files for your songs."""
    pass


@cli.command()
@click.option(
    '--audio', '-a',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help='Path to the audio file (MP3, WAV, FLAC, OGG)'
)
@click.option(
    '--lyrics', '-l',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help='Path to the lyrics text file'
)
@click.option(
    '--output', '-o',
    type=click.Path(file_okay=True, dir_okay=False, writable=True),
    help='Path where the LRC file will be saved (defaults to same location as lyrics file)'
)
@click.option('--title', '-t', help='Title of the song')
@click.option('--artist', '-r', help='Artist name')
@click.option('--album', '-b', help='Album name')
@click.option('--whisper-model', type=click.Choice(['tiny', 'base', 'small', 'medium', 'large']),
              default='base', help='Whisper model size to use (default: base)')
def generate(
        audio: str,
        lyrics: str,
        output: Optional[str] = None,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        whisper_model: str = "base"
):
    """Generate an LRC file from an audio file and lyrics text file using Whisper speech recognition."""
    # Validate input files
    if not validate_audio_file(audio):
        click.echo(f"Error: Invalid or unsupported audio file: {audio}", err=True)
        sys.exit(1)

    if not validate_lyrics_file(lyrics):
        click.echo(f"Error: Invalid or empty lyrics file: {lyrics}", err=True)
        sys.exit(1)

    # Extract metadata from filename if not provided
    metadata: Dict[str, str] = {}
    if not all([title, artist, album]):
        extracted = extract_metadata_from_filename(audio)

        if title:
            metadata['title'] = title
        elif 'title' in extracted:
            metadata['title'] = extracted['title']

        if artist:
            metadata['artist'] = artist
        elif 'artist' in extracted:
            metadata['artist'] = extracted['artist']

        if album:
            metadata['album'] = album
        elif 'album' in extracted:
            metadata['album'] = extracted['album']
    else:
        if title:
            metadata['title'] = title
        if artist:
            metadata['artist'] = artist
        if album:
            metadata['album'] = album

    # Generate the LRC file
    try:
        click.echo(f"Generating Whisper-synced LRC file for {os.path.basename(audio)}...")
        click.echo(f"Using Whisper {whisper_model} model for speech recognition")

        # Initialize Whisper sync
        whisper_sync = WhisperLyricsSync(model_size=whisper_model)
        lrc_path = whisper_sync.generate_lrc(audio, lyrics, output, metadata)

    except Exception as e:
        click.echo(f"Error generating LRC file: {str(e)}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()