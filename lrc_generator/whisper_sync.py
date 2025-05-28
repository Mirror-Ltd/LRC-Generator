"""
Whisper-based lyrics synchronization module
"""

import os
import re
import torch
import whisper
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import warnings
from pydub import AudioSegment
from .ass_formatter import AssFormatter # Added import
import click

# Warning filters are set globally in __init__.py

class WhisperLyricsSync:
    """
    Class for generating word-level timed lyrics directly from audio using OpenAI's Whisper model.
    """

    def __init__(self, model_size: str = "base", sentence_mode: bool = False):
        """
        Initialize the Whisper model.

        Args:
            model_size: Size of Whisper model to use ('tiny', 'base', 'small', 'medium', 'large')
                        Larger models are more accurate but slower and require more memory
            sentence_mode: If True, generates sentence-based ASS subtitles with word highlighting
        """
        self.model_size = model_size
        self.sentence_mode = sentence_mode
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the Whisper model"""
        try:
            print(f"Loading Whisper {self.model_size} model...")
            self.model = whisper.load_model(self.model_size)
            print(f"Whisper {self.model_size} model loaded successfully")
        except Exception as e:
            warnings.warn(f"Failed to load Whisper model: {str(e)}")
            # No fallback, as Whisper is essential for transcription
            self.model = None

    def is_available(self) -> bool:
        """Check if Whisper model is available"""
        return self.model is not None

    def transcribe_audio(self, audio_path: str) -> Dict:
        """
        Transcribe audio file with word-level timestamps.

        Args:
            audio_path: Path to audio file.

        Returns:
            Dictionary containing transcription data from Whisper.
        """
        if not self.is_available():
            raise RuntimeError("Whisper model not available or failed to load.")

        temp_wav_path = None # Initialize here to ensure it's always defined for the finally block
        try:
            audio = AudioSegment.from_file(audio_path)
            audio_path_to_use = audio_path

            if not audio_path.lower().endswith('.wav'):
                # Create a unique temp file name
                base, ext = os.path.splitext(os.path.basename(audio_path))
                temp_wav_filename = f"temp_{base}_{os.getpid()}.wav" # Added PID for uniqueness
                temp_wav_path = os.path.join(os.path.dirname(audio_path), temp_wav_filename)
                audio.export(temp_wav_path, format="wav")
                audio_path_to_use = temp_wav_path
            
            options = {"word_timestamps": True, "verbose": None}
            result = self.model.transcribe(audio_path_to_use, **options)

            # Save full transcription results to file (can be helpful for users)
            output_dir = os.path.dirname(audio_path)
            # Use a more descriptive name for the transcription file
            transcription_log_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(audio_path))[0]}_transcription_log.txt")
            
            with open(transcription_log_path, 'w', encoding='utf-8') as f:
                f.write("=== Whisper Full Transcription Log ===\n\n")
                f.write(f"Audio File: {audio_path}\n")
                f.write(f"Whisper Model: {self.model_size}\n\n")
                f.write("--- Segments ---\n")
                for i, segment in enumerate(result.get("segments", [])):
                    start_time = segment.get("start", 0)
                    end_time = segment.get("end", 0)
                    text = segment.get("text", "")
                    f.write(f"Segment {i} [{start_time:.2f}s - {end_time:.2f}s]: {text}\n")
                    if "words" in segment:
                        f.write("  Words:\n")
                        for word_info in segment["words"]:
                            w_text = word_info.get('word', '')
                            w_start = word_info.get('start', 0)
                            w_end = word_info.get('end', 0)
                            w_prob = word_info.get('probability', 0) # Whisper can provide word probability
                            f.write(f"    - '{w_text}' ({w_start:.2f}s - {w_end:.2f}s, prob: {w_prob:.2f})\n")
                f.write("\n--- Full Text ---\n")
                f.write(result.get("text", "No text transcribed."))

            print(f"Full transcription log saved to: {transcription_log_path}")

            return result
        except Exception as e:
            # Catch specific pydub/ffmpeg errors if possible, or more general ones
            raise RuntimeError(f"Failed to transcribe audio: {str(e)}. Ensure FFmpeg is installed and accessible.")
        finally:
            # Clean up temp file if created
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                except OSError as e_remove:
                    warnings.warn(f"Could not remove temporary WAV file {temp_wav_path}: {e_remove}")
    
    # clean_text might still be useful if we want to apply it to Whisper's output words before LRC generation.
    # For now, we'll use Whisper's words as-is, but keep the method.
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing punctuation and converting to lowercase.
        (Currently not used in the pure transcription flow but kept for potential future use)
        """
        text = re.sub(r'[^\\w\\s\']', '', text).lower() # Kept apostrophe
        text = re.sub(r'\\s+', ' ', text).strip()
        return text

    # align_segments_to_lyrics and align_lyrics methods are removed as we are no longer matching.

    def generate_lrc(
            self,
            audio_path: str,
            output_path: Optional[str] = None, # This is for LRC, ASS will follow its base name
            metadata: Optional[Dict[str, str]] = None
    ) -> Tuple[str, Optional[str]]: # Return paths to both LRC and ASS
        """
        Generate word-level LRC file and an ASS subtitle file directly from audio transcription.

        Args:
            audio_path: Path to audio file.
            output_path: Optional path to output LRC file. If not provided,
                         will use audio file name with .lrc extension.
            metadata: Optional dictionary with metadata (title, artist, album).

        Returns:
            A tuple containing:
                - Path to generated LRC file.
                - Path to generated ASS file (or None if generation failed).
        """
        print(f"Starting transcription for LRC and ASS generation: {audio_path}")
        transcription_result = self.transcribe_audio(audio_path)

        # Determine output path for LRC
        final_lrc_output_path = output_path
        audio_dir = os.path.dirname(audio_path)
        audio_filename_base = os.path.splitext(os.path.basename(audio_path))[0]
        
        if final_lrc_output_path is None:
            final_lrc_output_path = os.path.join(audio_dir, f"{audio_filename_base}.lrc")
        
        # Determine output path for ASS (same base name and dir as LRC)
        final_ass_output_path = os.path.join(os.path.dirname(final_lrc_output_path), f"{os.path.splitext(os.path.basename(final_lrc_output_path))[0]}.ass")

        print(f"Will generate word-level LRC at: {final_lrc_output_path}")
        print(f"Will generate word-level ASS at: {final_ass_output_path}")

        # Calculate audio duration for metadata
        try:
            audio_segment = AudioSegment.from_file(audio_path)
            duration_seconds = len(audio_segment) / 1000.0
        except Exception as e:
            warnings.warn(f"Could not read audio duration from {audio_path}: {e}. LRC/ASS metadata might be affected.")
            duration_seconds = 0.0

        # --- Generate LRC file ---
        lrc_word_count = 0
        try:
            with open(final_lrc_output_path, 'wb') as f:
                f.write(b'\xef\xbb\xbf')  # BOM for UTF-8

                lrc_content_lines = []
                # Write metadata
                processed_title_for_lrc = self._normalize_text(os.path.splitext(os.path.basename(audio_path))[0]) # Default title
                if metadata:
                    if 'title' in metadata and metadata['title']:
                        processed_title_for_lrc = self._normalize_text(metadata['title'])
                    lrc_content_lines.append(f"[ti:{processed_title_for_lrc}]")
                    if 'artist' in metadata and metadata['artist']:
                        lrc_content_lines.append(f"[ar:{self._normalize_text(metadata['artist'])}]")
                    if 'album' in metadata and metadata['album']:
                        lrc_content_lines.append(f"[al:{self._normalize_text(metadata['album'])}]")
                else:
                     lrc_content_lines.append(f"[ti:{processed_title_for_lrc}]")


                if duration_seconds > 0:
                    minutes = int(duration_seconds // 60)
                    seconds_meta = int(duration_seconds % 60)
                    lrc_content_lines.append(f"[length:{minutes:02d}:{seconds_meta:02d}]")
                lrc_content_lines.append("")

                if "segments" in transcription_result:
                    for segment in transcription_result["segments"]:
                        if "words" in segment:
                            for word_info in segment["words"]:
                                word_text = word_info.get('word', '').strip()
                                start_time = word_info.get('start')

                                if word_text and start_time is not None:
                                    minutes = int(start_time // 60)
                                    seconds_val = start_time % 60
                                    normalized_word_for_lrc = self._normalize_text(word_text)
                                    if normalized_word_for_lrc:
                                        lrc_content_lines.append(f"[{minutes:02d}:{seconds_val:05.2f}]{normalized_word_for_lrc}")
                                        lrc_word_count += 1
                
                if not lrc_content_lines or lrc_word_count == 0:
                    print(f"⚠️ No words were transcribed or written to LRC for {audio_path}. The LRC file might be empty or metadata-only.")
                    if not lrc_content_lines and duration_seconds == 0:
                        f.write(f"[ti:No transcription for {os.path.basename(audio_path)}]\n".encode('utf-8'))

                f.write('\n'.join(lrc_content_lines).encode('utf-8'))
            
            if lrc_word_count > 0:
                print(f"✅ Word-level LRC file generated with {lrc_word_count} words at: {final_lrc_output_path}")
            else:
                print(f"ℹ️ LRC file generated (possibly metadata-only or empty) at: {final_lrc_output_path}")
        except Exception as e_lrc:
            warnings.warn(f"Error generating LRC file {final_lrc_output_path}: {e_lrc}")
            final_lrc_output_path = None # Indicate failure


        # --- Generate ASS file ---
        ass_file_generated_path: Optional[str] = None
        try:
            # Prepare segment-based data for ASS generation
            segment_data_for_ass = []
            if "segments" in transcription_result:
                for segment in transcription_result["segments"]:
                    if "words" in segment:
                        segment_words = []
                        for word_info in segment["words"]:
                            word = word_info.get('word', '').strip()
                            start = word_info.get('start')
                            end = word_info.get('end')
                            if word and start is not None and end is not None:
                                segment_words.append((word, float(start), float(end)))
                        if segment_words:
                            segment_data_for_ass.append(segment_words)
            
            if not segment_data_for_ass:
                print(f"⚠️ No segment data extracted for ASS generation from {audio_path}.")
            else:
                formatter = AssFormatter(sentence_mode=self.sentence_mode) # Pass sentence_mode to formatter
                
                # Prepare title for ASS
                ass_title = metadata.get('title') if metadata and metadata.get('title') else audio_filename_base

                ass_content = formatter.create_ass_file_content_from_segments(
                    segment_data_for_ass,
                    title=ass_title,
                    audio_file_name=os.path.basename(audio_path)
                    # Video dimensions will use AssFormatter defaults
                )
                
                actual_ass_path = os.path.splitext(final_lrc_output_path)[0] + ".ass"
                try:
                    # Write with LF line endings. Python's text mode with newline='' 
                    # should preserve this. Encoding is utf-8-sig (with BOM).
                    with open(actual_ass_path, 'w', encoding='utf-8-sig', newline='') as f: 
                        f.write(ass_content) # Write ass_content directly
                    # click.echo(f"DEBUG: ASS content written to {actual_ass_path} with UTF-8-SIG (with BOM) and LF line endings.")
                except IOError as e:
                    click.echo(f"Error writing ASS file {actual_ass_path}: {e}", err=True)
                    actual_ass_path = None # Ensure path is None if write failed
                ass_file_generated_path = actual_ass_path

        except Exception as e_ass:
            warnings.warn(f"Error generating ASS file {final_ass_output_path}: {e_ass}")
            # Do not set final_ass_output_path to None here, its initial value is None if not set
            # ass_file_generated_path remains None or its value

        return final_lrc_output_path, ass_file_generated_path # Return both paths

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text by replacing special characters for LRC compatibility.
        
        Args:
            text: Input text.
            
        Returns:
            Normalized text.
        """
        # Replace various quotes with standard quotes, and other common characters
        replacements = {
            '': "'", '"': '"', '…': '...', '–': '-', '—': '-', '′': "'", '‛': "'",
            '⁄': '/', # fraction slash
            '々': '' # common Japanese iteration mark, often not needed in lyrics
        }
        # Remove or replace characters that might be problematic in LRC or not typically sung
        # This is a basic set, can be expanded.
        # Example: removing all non-alphanumeric, non-space, non-basic-punctuation
        # text = re.sub(r"[^a-zA-Z0-9À-ÿĀ-ž\s'\-\.\?!,]", "", text) # More aggressive cleaning

        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Basic whitespace normalization
        text = re.sub(r'\\s+', ' ', text).strip()
        return text