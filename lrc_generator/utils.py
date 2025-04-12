"""
Utility functions for the LRC generator
(Including core functionality previously in core.py)
"""

import os
import re
from typing import Dict, List, Optional, Tuple, Union


def extract_metadata_from_filename(filename: str) -> Dict[str, str]:
    """
    Attempt to extract metadata from filename following common patterns.

    Example patterns:
    - Artist - Title.mp3
    - Artist - Album - Title.mp3

    Args:
        filename: Filename to parse

    Returns:
        Dictionary with extracted metadata
    """
    metadata = {}

    # Remove file extension
    basename = os.path.basename(filename)
    name_without_ext, _ = os.path.splitext(basename)

    # Pattern 1: Artist - Title
    pattern1 = r'^(.*?)\s*-\s*(.*?)$'
    # Pattern 2: Artist - Album - Title
    pattern2 = r'^(.*?)\s*-\s*(.*?)\s*-\s*(.*?)$'

    # Try Pattern 2 first (more specific)
    match = re.match(pattern2, name_without_ext)
    if match:
        artist, album, title = match.groups()
        metadata['artist'] = artist.strip()
        metadata['album'] = album.strip()
        metadata['title'] = title.strip()
    else:
        # Try Pattern 1
        match = re.match(pattern1, name_without_ext)
        if match:
            artist, title = match.groups()
            metadata['artist'] = artist.strip()
            metadata['title'] = title.strip()
        else:
            # If no pattern matches, just use the filename as the title
            metadata['title'] = name_without_ext

    return metadata


def format_time(seconds: float) -> str:
    """
    Format time in seconds to LRC format [mm:ss.xx]

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"[{minutes:02d}:{seconds:05.2f}]"


def parse_lrc_line(line: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Parse a line from an LRC file into timestamp and lyrics.

    Args:
        line: Line from an LRC file

    Returns:
        Tuple of (timestamp in seconds, lyrics text)
    """
    # Match LRC timestamp format [mm:ss.xx]
    match = re.match(r'^\[(\d+):(\d+\.\d+)\](.*?)$', line)
    if match:
        minutes, seconds, lyrics = match.groups()
        timestamp = int(minutes) * 60 + float(seconds)
        return timestamp, lyrics.strip()

    # Check if it's a metadata line
    metadata_match = re.match(r'^\[(ti|ar|al|length|by):(.+)\]$', line)
    if metadata_match:
        return None, None

    # No timestamp found
    return None, line.strip()


def ensure_directory_exists(file_path: str) -> None:
    """
    Ensure that the directory for the given file path exists.

    Args:
        file_path: Path to a file
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


# Functions moved from core.py

def validate_audio_file(file_path: str) -> bool:
    """
    Validate that the audio file exists and has a supported extension.

    Args:
        file_path: Path to the audio file

    Returns:
        True if the file is valid, False otherwise
    """
    if not os.path.isfile(file_path):
        return False

    # Check file extension
    supported_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']
    _, ext = os.path.splitext(file_path)
    return ext.lower() in supported_extensions


def validate_lyrics_file(file_path: str) -> bool:
    """
    Validate that the lyrics file exists and is not empty.

    Args:
        file_path: Path to the lyrics file

    Returns:
        True if the file is valid, False otherwise
    """
    if not os.path.isfile(file_path):
        return False

    # Check if file is not empty
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            return len(content) > 0
    except Exception:
        return False