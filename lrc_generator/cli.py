"""
Command-line interface for the LRC Transcriber
"""

import os
import sys
import click
from typing import Dict, Optional
import subprocess # For running FFmpeg

from .utils import (
    validate_audio_file,
    extract_metadata_from_filename, 
    ensure_directory_exists
)
from .whisper_sync import WhisperLyricsSync


@click.group()
def cli():
    """Transcribe audio files to word-level LRC files using Whisper."""
    pass


@cli.command()
@click.option(
    '--audio', '-a',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help='Path to the audio file (e.g., MP3, WAV, FLAC, M4A)'
)
@click.option(
    '--output', '-o',
    type=click.Path(file_okay=True, dir_okay=False, writable=True),
    help='Path where the LRC file will be saved (defaults to same name as audio file with .lrc extension)'
)
@click.option('--title', '-t', help='Title for the LRC metadata (overrides auto-extraction)')
@click.option('--artist', '-r', help='Artist name for the LRC metadata (overrides auto-extraction)')
@click.option('--album', '-b', help='Album name for the LRC metadata (overrides auto-extraction)')
@click.option('--whisper-model', type=click.Choice(['tiny', 'base', 'small', 'medium', 'large', 'large-v1', 'large-v2', 'large-v3']),
              default='base', help='Whisper model size to use (default: base)')
@click.option('--sentence-mode', is_flag=True, default=False, 
              help='Generate sentence-based ASS subtitles where each line shows the full sentence with word-by-word highlighting (default: word-by-word)')
def generate(
        audio: str,
        output: Optional[str] = None,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        whisper_model: str = "base",
        sentence_mode: bool = False
):
    """Generate a word-level LRC file by transcribing an audio file using Whisper."""
    
    if not validate_audio_file(audio):
        click.echo(f"Error: Invalid or unsupported audio file: {audio}", err=True)
        sys.exit(1)

    # Prepare metadata for LRC file
    metadata: Dict[str, Optional[str]] = {}
    if title:
        metadata['title'] = title
    if artist:
        metadata['artist'] = artist
    if album:
        metadata['album'] = album
    
    try:
        click.echo(f"Starting transcription of {os.path.basename(audio)} to LRC...")
        click.echo(f"Using Whisper {whisper_model} model for speech recognition.")
        if sentence_mode:
            click.echo("ASS subtitle mode: Sentence-based with word highlighting")
        else:
            click.echo("ASS subtitle mode: Word-by-word")

        whisper_transcriber = WhisperLyricsSync(model_size=whisper_model, sentence_mode=sentence_mode)
        
        # Call generate_lrc, which now returns paths for both LRC and ASS files
        lrc_path, ass_path = whisper_transcriber.generate_lrc(
            audio_path=audio, 
            output_path=output, # This 'output' path is for the LRC file
            metadata=metadata
        )
        
        if lrc_path:
            click.echo(f"✅ Word-level LRC file generation process completed. Output: {lrc_path}")
        else:
            click.echo(f"⚠️ LRC file generation failed or was skipped. Check logs for details.", err=True)

        if ass_path:
            if sentence_mode:
                click.echo(f"✅ Sentence-based ASS subtitle file generation process completed. Output: {ass_path}")
            else:
                click.echo(f"✅ Word-level ASS subtitle file generation process completed. Output: {ass_path}")
        else:
            click.echo(f"⚠️ ASS subtitle file generation failed or was skipped. Check logs for details.", err=True)
            
        # Exit successfully if at least one file was generated, or if no fatal error occurred before this.
        # The generate_lrc method itself would raise an error for critical failures.
        # If we reach here, it means the transcription process itself (within whisper_sync) didn't halt catastrophically.

    except RuntimeError as e: # Catching specific RuntimeError from whisper_sync
        click.echo(f"Error during transcription: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="create-video")
@click.option(
    '--audio', '-a',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help='Path to the audio file (e.g., MP3, WAV).'
)
@click.option(
    '--image', '-i',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help='Path to the static image file (e.g., JPG, PNG).'
)
@click.option(
    '--ass',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help='Path to the .ass subtitle file. If not provided, attempts to find one matching the audio filename.'
)
@click.option(
    '--output', '-o',
    type=click.Path(file_okay=True, dir_okay=False, writable=True),
    help='Path where the output video file will be saved (e.g., video.mp4). Defaults to same name as audio file with .mp4 extension.'
)
@click.option(
    '--ffmpeg-path',
    default='ffmpeg',
    help='Path to the FFmpeg executable. Defaults to "ffmpeg" (assumes it is in system PATH).'
)
def create_video(
    audio: str,
    image: str,
    ass: Optional[str],
    output: Optional[str],
    ffmpeg_path: str
):
    """Create a video by combining audio, a static image, and an .ass subtitle file using FFmpeg."""
    click.echo("Starting video creation process...")

    # 1. Determine actual .ass file path
    actual_ass_path = ass
    if not actual_ass_path:
        base, _ = os.path.splitext(audio)
        potential_ass_path = base + ".ass"
        if os.path.exists(potential_ass_path):
            actual_ass_path = potential_ass_path
            click.echo(f"Found associated .ass file: {actual_ass_path}")
        else:
            click.echo(f"Error: No .ass file provided and could not find an associated .ass file '{potential_ass_path}'. Please generate it first using the 'generate' command or provide it with --ass.", err=True)
            sys.exit(1)
    
    if not os.path.exists(actual_ass_path): # Check again in case user provided a non-existent path
        click.echo(f"Error: Provided .ass file not found: {actual_ass_path}", err=True)
        sys.exit(1)

    # 2. Determine output video path
    actual_output_path = output
    if not actual_output_path:
        base, _ = os.path.splitext(audio)
        actual_output_path = base + ".mp4"
    
    click.echo(f"Audio input: {audio}")
    click.echo(f"Image input: {image}")
    click.echo(f"ASS subtitles: {actual_ass_path}")
    click.echo(f"Output video: {actual_output_path}")
    click.echo(f"Using FFmpeg from: {ffmpeg_path}")

    # 3. Construct FFmpeg command

    # Path strategy: Use a relative path from the CWD (project root) for FFmpeg.
    # This matches the manually successful command.

    # actual_ass_path is already determined (e.g., from --ass or auto-derived)
    click.echo(f"DEBUG: actual_ass_path (original): {actual_ass_path}")

    # Normalize the path (e.g., convert mixed slashes, handle . and ..)
    path_for_ffmpeg = os.path.normpath(actual_ass_path)
    click.echo(f"DEBUG: path_for_ffmpeg (normalized): {path_for_ffmpeg}")

    # Convert all backslashes to forward slashes for FFmpeg
    path_for_ffmpeg = path_for_ffmpeg.replace('\\', '/')
    click.echo(f"DEBUG: path_for_ffmpeg (forward slashes): {path_for_ffmpeg}")

    # Ensure it's explicitly relative if it's not absolute, to match the working command form e.g. './path/to/file'
    # (os.getcwd() would be the project root where ffmpeg is launched from)
    # If actual_ass_path was absolute, normpath and replace will keep it absolute.
    # If it was relative, it will remain relative.
    # The successful manual command used an explicit './' for a path in a subdirectory.
    if not os.path.isabs(path_for_ffmpeg):
        # Check if it's already in the form './xxx' or '../xxx'
        if not (path_for_ffmpeg.startswith('./') or path_for_ffmpeg.startswith('../')):
            # If it's just 'music/file.ass', prepend './'
            path_for_ffmpeg = './' + path_for_ffmpeg
            click.echo(f"DEBUG: path_for_ffmpeg (prepended ./): {path_for_ffmpeg}")
    else:
        # If it's an absolute path, we are back to the escaping hell for absolute paths.
        # For now, let's assume the relative path strategy is what we want based on manual success.
        # If an absolute path is given by the user, this strategy might fail unless FFmpeg CWD is the FS root.
        # A more robust solution for absolute paths would be needed if this relative approach isn't universal.
        click.echo(f"WARNING: Absolute path detected for subtitles. The relative path strategy might not apply cleanly: {path_for_ffmpeg}")
        # Fallback to a simple version for absolute paths (convert to forward slashes, hope for the best)
        # This part might need the old complex escaping if used often.
        pass # Path is already absolute and has forward slashes. Potentially problematic.

    subtitles_filter_argument = f"subtitles=filename='{path_for_ffmpeg}'"
    click.echo(f"DEBUG: subtitles_filter_argument: {subtitles_filter_argument}")

    ffmpeg_command = [
        ffmpeg_path,
        '-y',                 # Overwrite output files without asking
        '-loop', '1',         # Loop the image
        '-i', image,          # Input image
        '-i', audio,          # Input audio
        '-vf', subtitles_filter_argument, # Use the constructed filter string
        '-c:v', 'libx264',    # Video codec
        '-c:a', 'aac',        # Audio codec
        '-shortest',          # Ensure video length matches audio length
        actual_output_path
    ]

    click.echo(f"Executing FFmpeg command: {' '.join(ffmpeg_command)}")

    # 4. Execute FFmpeg command
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(actual_output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            click.echo(f"Created output directory: {output_dir}")

        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8')
        
        # Print FFmpeg output in real-time
        if process.stdout:
            for line in process.stdout:
                click.echo(f"ffmpeg: {line.strip()}")
        
        process.wait() # Wait for FFmpeg to complete

        if process.returncode == 0:
            click.echo(f"✅ Video successfully created: {actual_output_path}")
        else:
            click.echo(f"❌ Error during FFmpeg execution. Return code: {process.returncode}", err=True)
            click.echo("Please check FFmpeg output above for details.", err=True)
            # Optionally, you might want to delete a potentially corrupted/incomplete output file here
            # if os.path.exists(actual_output_path):
            #     os.remove(actual_output_path)
            sys.exit(1)

    except FileNotFoundError:
        click.echo(f"Error: FFmpeg executable not found at '{ffmpeg_path}'. Please ensure FFmpeg is installed and in your PATH, or specify the correct path using --ffmpeg-path.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"An unexpected error occurred during video creation: {str(e)}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI transcriber."""
    cli()


if __name__ == "__main__":
    main()