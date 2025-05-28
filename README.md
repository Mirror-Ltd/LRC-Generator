# LRC Word Transcriber (Formerly LRC Generator)

This tool transcribes audio files directly into word-level timestamped LRC files using OpenAI Whisper. Each word recognized in the audio is output on a new line in the LRC file with its corresponding start time.

## Features

- Supports multiple audio formats (MP3, WAV, M4A, FLAC, etc.) via FFmpeg.
- Uses OpenAI Whisper for accurate speech-to-text transcription with word-level timestamps.
- Generates standard LRC format files where each line is a single word with its timestamp.
- Generates ASS subtitle files for video creation with word-level timing.
- Creates videos by combining audio, static images, and ASS subtitles using FFmpeg.
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

**Using Sentence Mode for Better ASS Subtitles:**

```bash
lrc-gen generate --audio "./audio/my_track.wav" \
                 --title "My Awesome Track" \
                 --artist "The Transcribers" \
                 --whisper-model small \
                 --sentence-mode
```

**Available Whisper Models:**

The `--whisper-model` option allows you to choose the size of the Whisper model. Smaller models are faster but less accurate; larger models are more accurate but significantly slower and require more VRAM/RAM.

-   `tiny`
-   `base` (default)
-   `small`
-   `medium`
-   `large` (and its variants like `large-v1`, `large-v2`, `large-v3`)

Refer to OpenAI Whisper documentation for details on model differences.

**Creating Videos with Subtitles**

The tool also provides a `create-video` command that combines audio, a static image, and ASS subtitle files to create videos with embedded subtitles using FFmpeg.

**Basic Video Creation:**

```bash
lrc-gen create-video --audio "./path/to/song.mp3" --image "./path/to/cover.jpg"
```

This will automatically look for a matching ASS file (e.g., `song.ass`) and create a video file (`song.mp4`).

**Specifying All Parameters:**

```bash
lrc-gen create-video --audio "./audio/track.mp3" \
                     --image "./images/album_cover.png" \
                     --ass "./subtitles/track.ass" \
                     --output "./videos/track_with_lyrics.mp4" \
                     --ffmpeg-path "/usr/local/bin/ffmpeg"
```

**Available Options for create-video:**

- `--audio, -a`: Path to the audio file (required)
- `--image, -i`: Path to the static image file (required) - supports JPG, PNG, etc.
- `--ass`: Path to the ASS subtitle file (optional - if not provided, looks for a file with the same name as the audio file)
- `--output, -o`: Output path for the video file (optional - defaults to same name as audio file with .mp4 extension)
- `--ffmpeg-path`: Path to FFmpeg executable (optional - defaults to "ffmpeg" in system PATH)

## ASS Subtitle Modes

The tool supports two different modes for generating ASS subtitle files:

### 1. Word-by-Word Mode (Default)
Each word appears individually with its own timing. This creates a traditional karaoke effect where words appear one at a time.

```bash
lrc-gen generate --audio "./song.mp3" --title "My Song"
```

### 2. Sentence Mode
Each line shows a complete sentence with word-by-word highlighting. This provides better context while still showing the timing progression through each word.

```bash
lrc-gen generate --audio "./song.mp3" --title "My Song" --sentence-mode
```

**Benefits of Sentence Mode:**
- Viewers can see the full context of each sentence
- Better readability for longer phrases
- Maintains word-level timing precision
- More suitable for educational or sing-along videos

**Example Output Comparison:**

*Word-by-Word Mode:*
```
Line 1: "Hello" (0.5s - 1.0s)
Line 2: "world" (1.2s - 1.8s)
Line 3: "this" (2.0s - 2.3s)
Line 4: "is" (2.4s - 2.6s)
Line 5: "amazing" (2.8s - 3.5s)
```

*Sentence Mode:*
```
Line 1: "Hello world this is amazing" (0.5s - 3.5s)
        - "Hello" highlights from 0.5s-1.0s
        - "world" highlights from 1.0s-1.8s
        - "this" highlights from 1.8s-2.3s
        - "is" highlights from 2.3s-2.6s
        - "amazing" highlights from 2.6s-3.5s
```

**Prerequisites for Video Creation:**

1. An audio file (MP3, WAV, etc.)
2. A static image file (JPG, PNG, etc.) that will be used as the video background
3. An ASS subtitle file (generated by the `generate` command or provided separately)
4. FFmpeg installed and accessible

**Workflow Example:**

```bash
# Step 1: Generate LRC and ASS files from audio (using sentence mode for better video subtitles)
lrc-gen generate --audio "./song.mp3" --title "My Song" --artist "My Artist" --sentence-mode

# Step 2: Create video with subtitles
lrc-gen create-video --audio "./song.mp3" --image "./cover.jpg"
```

This will create:
- `song.lrc` (LRC subtitle file)
- `song.ass` (ASS subtitle file with sentence-based highlighting)
- `song.mp4` (Video with embedded subtitles)

**Handling Filenames with Spaces or Special Characters:**

If your audio filename contains spaces or special characters, enclose the path in quotes:
```bash
lrc-gen generate --audio "./my songs/amazing song with spaces.mp3"
lrc-gen create-video --audio "./my songs/amazing song with spaces.mp3" --image "./covers/album art.jpg"
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

2.  **ASS Subtitle File (`.ass`)**:
    -   Generated alongside the LRC file, containing word-level timestamps in ASS format.
    -   Location: Same directory and basename as the input audio file, with an `.ass` extension.
    -   Format: Advanced SubStation Alpha (ASS) format, suitable for video subtitle embedding.
    -   Used by the `create-video` command to embed subtitles into videos.
    -   Contains styling information and precise timing for each word.

3.  **Transcription Log File (`*_transcription_log.txt`)**:
    -   A text file saved in the same directory as the input audio, with the original audio filename plus `_transcription_log.txt`.
    -   Contains the full output from the Whisper model, including all recognized segments, words within those segments, their start/end times, and (if available) recognition probabilities.
    -   This log is useful for understanding the raw transcription quality and for debugging if the LRC output seems incorrect.

## How It Works

1.  **Audio Loading & Conversion**: The input audio file is loaded. If it's not in WAV format, it's temporarily converted to WAV using FFmpeg (via `pydub`).
2.  **Whisper Transcription**: The audio is fed into the selected OpenAI Whisper model, which performs speech-to-text transcription and provides word-level timestamps for each recognized word.
3.  **LRC & ASS File Generation**: The list of recognized words and their start timestamps are formatted into both:
    - Standard LRC file format with metadata (title, artist, album, length)
    - ASS subtitle format for video creation with styling and precise timing
4.  **Video Creation** (optional): When using the `create-video` command, FFmpeg combines the audio, static image, and ASS subtitle file to create a video with embedded subtitles.

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
