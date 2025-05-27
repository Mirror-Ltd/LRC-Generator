# LRC Word Transcriber (Formerly LRC Generator)

This tool transcribes audio files directly into word-level timestamped LRC files using OpenAI Whisper. Each word recognized in the audio is output on a new line in the LRC file with its corresponding start time.

## Features

- Supports multiple audio formats (MP3, WAV, M4A, FLAC, etc.) via FFmpeg.
- Uses OpenAI Whisper for accurate speech-to-text transcription with word-level timestamps.
- Generates standard LRC format files where each line is a single word with its timestamp.
- Allows specifying Whisper model size for a balance between speed and accuracy.
- Optionally accepts metadata (title, artist, album) for the LRC file.
- Filters out common console warnings for cleaner output.
- Generates a detailed transcription log (`*_transcription_log.txt`) for review.

## Requirements

- Python 3.8 or higher
- FFmpeg (must be installed and accessible in your system's PATH for audio processing)
- PyTorch (Whisper model dependency)

## Installation

1.  **Install FFmpeg**
    If not already installed, download from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your system's PATH, or install via a package manager:
    ```bash
    # macOS (using Homebrew)
    brew install ffmpeg

    # Ubuntu/Debian
    sudo apt update && sudo apt install ffmpeg
    ```

2.  **Clone the Repository**
    ```bash
    git clone [repository-url] # Replace [repository-url] with the actual URL
    cd LRC-Word-Transcriber # Or your repository's directory name
    ```

3.  **Set up a Python Virtual Environment (Recommended)**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```

4.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    The first time you run the tool with a specific Whisper model, the model will be downloaded automatically. This requires an internet connection.

## Usage

The command-line tool is named `lrc-gen` (though a rename to `lrc-transcribe` or similar might be more fitting for the new functionality).

**Basic Usage:**

```bash
lrc-gen generate --audio "./path/to/your/song.mp3"
```
This will create an LRC file named `song.lrc` in the same directory as `song.mp3`.

**Specifying Output Path and Metadata:**

```bash
lrc-gen generate --audio "./audio/my_track.wav" \
                 --output "./lrc_files/my_track_lyrics.lrc" \
                 --title "My Awesome Track" \
                 --artist "The Transcribers" \
                 --album "Whispers in Time" \
                 --whisper-model small
```

**Available Whisper Models:**

The `--whisper-model` option allows you to choose the size of the Whisper model. Smaller models are faster but less accurate; larger models are more accurate but significantly slower and require more VRAM/RAM.

-   `tiny`
-   `base` (default)
-   `small`
-   `medium`
-   `large` (and its variants like `large-v1`, `large-v2`, `large-v3`)

Refer to OpenAI Whisper documentation for details on model differences.

**Handling Filenames with Spaces or Special Characters:**

If your audio filename contains spaces or special characters, enclose the path in quotes:
```bash
lrc-gen generate --audio "./my songs/amazing song with spaces.mp3"
```

## Input File Requirements

-   **Audio Files:**
    -   Supported formats include MP3, WAV, M4A, FLAC, and others supported by FFmpeg.
    -   Higher quality audio generally leads to better transcription accuracy.

## Output Files

1.  **LRC File (`.lrc`)**:
    -   The primary output, containing word-level timestamps.
    -   Location: Specified by `--output`, or defaults to the same directory and basename as the input audio file, with an `.lrc` extension.
    -   Format: Standard LRC format, UTF-8 encoding (with BOM).
    -   Each line in the LRC file will be a single word recognized by Whisper, prefixed by its start timestamp.
        Example:
        ```lrc
        [ti:My Transcribed Song]
        [ar:Whisper]
        [length:00:25]

        [00:00.50]This
        [00:00.80]is
        [00:01.10]an
        [00:01.50]example
        [00:02.00]transcription.
        ```

2.  **Transcription Log File (`*_transcription_log.txt`)**:
    -   A text file saved in the same directory as the input audio, with the original audio filename plus `_transcription_log.txt`.
    -   Contains the full output from the Whisper model, including all recognized segments, words within those segments, their start/end times, and (if available) recognition probabilities.
    -   This log is useful for understanding the raw transcription quality and for debugging if the LRC output seems incorrect.

## How It Works

1.  **Audio Loading & Conversion**: The input audio file is loaded. If it's not in WAV format, it's temporarily converted to WAV using FFmpeg (via `pydub`).
2.  **Whisper Transcription**: The audio is fed into the selected OpenAI Whisper model, which performs speech-to-text transcription and provides word-level timestamps for each recognized word.
3.  **LRC File Generation**: The list of recognized words and their start timestamps are formatted into the standard LRC file format. Metadata (title, artist, album, length) is also included.

## Important Notes

1.  **First Run & Model Download**: The first time you use a specific Whisper model size, it will be downloaded. This requires an internet connection and might take some time depending on the model size and your connection speed.
2.  **Processing Time**: Transcription time depends on the audio length, the chosen Whisper model size, and your hardware (CPU/GPU).
3.  **Transcription Accuracy**: The accuracy of the generated LRC file directly depends on the Whisper model's transcription accuracy for the given audio. Clear audio with minimal noise and clear speech/singing will yield better results.
4.  **Resource Usage**: Larger Whisper models require more RAM and, if a GPU is used, more VRAM.
5.  **FFmpeg Dependency**: Ensure FFmpeg is installed and accessible in your system's PATH. The tool relies on it for broad audio format support.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Issues and Pull Requests are welcome!
