# LRC Generator

An automatic lyrics timing generator based on OpenAI Whisper. This tool automatically aligns lyrics with audio files to generate timestamped LRC files.

## Features

- Supports multiple audio formats (MP3, WAV, etc.)
- Uses Whisper for accurate speech recognition
- Automatic lyrics-to-audio alignment with word-level matching
- Generates standard LRC format files
- Supports special characters in lyrics
- Handles repeated lyrics sections
- Provides detailed debugging information
- Filters out common warnings for cleaner output

## Requirements

- Python 3.8 or higher
- FFmpeg (for audio processing)
- PyTorch (for Whisper model)

## Installation

1. Install FFmpeg (if not already installed):
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

2. Clone the repository:
   ```bash
   git clone [repository-url]
   cd LRC-Generator
   ```

3. Install dependencies in venv
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Basic usage:
```bash
lrc-gen generate --audio "./songs/my_song.mp3" --lyrics "./lyrics/my_lyrics.txt"
```

if sync failed due to low match ratio, feel free to use the clean_lyrics only for manual operation.
```bash
python clean_lyrics.py --input "./musicians/Arion/Caught in the Moment.txt" --output "./musicians/Arion/Caught in the Moment.txt"
```

### Advanced Options

```bash
lrc-gen generate --audio "path/to/audio" --lyrics "path/to/lyrics" --whisper-model base --title "Song Title" --artist "Artist Name" --album "Album Name"
```

Available Whisper models:
- `tiny`: Fastest, least accurate
- `base`: Good balance of speed and accuracy (default)
- `small`: Better accuracy, slower
- `medium`: High accuracy, slower
- `large`: Highest accuracy, slowest

### Handling Filenames with Spaces or Special Characters

If your filenames contain spaces or special characters, you can:

1. Use quotes:
   ```bash
   lrc-gen generate --audio "./songs/my song.mp3" --lyrics "./lyrics/my lyrics.txt"
   ```

2. Use backslash escaping:
   ```bash
   lrc-gen generate --audio ./songs/my\ song.mp3 --lyrics ./lyrics/my\ lyrics.txt
   ```

## File Format Requirements

### Audio Files
- Supported formats: MP3, WAV, M4A, FLAC, etc.
- High-quality audio recommended for better recognition

### Lyrics Files
- Plain text file (.txt)
- UTF-8 encoding
- One line per lyric
- No timestamps
- Arranged in singing order

Example lyrics file format:
```text
verse 1
First line of lyrics
Second line of lyrics
chorus
This is the chorus
Second line of chorus
```

## Output Files

- Generated LRC file will have the same name as the lyrics file (different extension)
- Location: Same directory as the lyrics file
- Format: Standard LRC format, UTF-8 encoding (with BOM)

Example output:
```text
[ti:Song Title]
[ar:Artist]
[al:Album]
[length:03:45]

[00:01.23]First line of lyrics
[00:05.67]Second line of lyrics
[00:10.89]This is the chorus
```

## How It Works

The LRC Generator uses a sophisticated matching algorithm:

1. **Transcription**: Uses OpenAI's Whisper model to transcribe the audio with word-level timestamps
2. **Word Matching**: Aligns lyrics lines with transcribed words using a sliding window approach
3. **Timestamp Assignment**: Assigns timestamps to each lyrics line based on the best matches
4. **Confidence Calculation**: Calculates match ratio to ensure quality results

The matching process prioritizes:
- Maintaining the original order of lyrics
- Finding exact word matches between lyrics and transcription
- Ensuring timestamps are monotonically increasing

## Debug Information

The program generates two debug files:
1. `whisper_transcription.txt`: Contains Whisper's speech recognition results
2. `debug_segments.txt`: Contains detailed matching process information including:
   - Original transcription segments
   - Word-level timestamp information
   - Matching process for each lyrics line
   - Match ratios and selected timestamps

These files are invaluable for troubleshooting if the synchronization isn't perfect.

## Important Notes

1. First run will download the Whisper model, requiring internet connection
2. Processing time depends on audio length and chosen model size:
   - `tiny` and `base` models work well for most cases
   - Larger models (`medium`, `large`) provide better accuracy but are significantly slower
3. High-quality audio files recommended for better recognition
4. If lyrics matching is not ideal:
   - Check lyrics text accuracy
   - Ensure correct lyrics order
   - Review debug files for detailed matching process
5. The tool automatically filters common warnings (like OpenMP and FP16 warnings)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Issues and Pull Requests are welcome!
