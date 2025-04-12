"""
Whisper-based lyrics synchronization module
"""

import os
import re
import torch
import whisper
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from rapidfuzz import fuzz, process
import warnings
from pydub import AudioSegment
import emoji

# Warning filters are set globally in __init__.py

class WhisperLyricsSync:
    """
    Class for syncing lyrics using OpenAI's Whisper model
    """

    def __init__(self, model_size: str = "base"):
        """
        Initialize the Whisper model for lyrics synchronization

        Args:
            model_size: Size of Whisper model to use ('tiny', 'base', 'small', 'medium', 'large')
                        Larger models are more accurate but slower and require more memory
        """
        self.model_size = model_size
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
            warnings.warn("Falling back to librosa-based sync")
            self.model = None

    def is_available(self) -> bool:
        """Check if Whisper model is available"""
        return self.model is not None

    def transcribe_audio(self, audio_path: str) -> Dict:
        """
        Transcribe audio file with word-level timestamps

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary containing transcription data
        """
        if not self.is_available():
            raise RuntimeError("Whisper model not available")

        # Some audio files might need conversion - use pydub to handle this
        try:
            # For MP3 files that might be problematic for whisper
            audio = AudioSegment.from_file(audio_path)
            # Convert to WAV temporarily if needed
            if not audio_path.lower().endswith('.wav'):
                temp_wav_path = os.path.join(os.path.dirname(audio_path),
                                             f"temp_{os.path.basename(audio_path)}.wav")
                audio.export(temp_wav_path, format="wav")
                audio_path_to_use = temp_wav_path
            else:
                audio_path_to_use = audio_path

            # Transcribe with word timestamps
            options = {
                "word_timestamps": True,
                "verbose": None
            }

            # Use the model's default device settings
            result = self.model.transcribe(audio_path_to_use, **options)

            # Save transcription results to file
            output_dir = os.path.dirname(audio_path)
            transcription_path = os.path.join(output_dir, "whisper_transcription.txt")
            
            with open(transcription_path, 'w', encoding='utf-8') as f:
                f.write("=== Whisper Transcription Results ===\n\n")
                for segment in result["segments"]:
                    start_time = segment["start"]
                    end_time = segment["end"]
                    text = segment["text"]
                    f.write(f"[{start_time:.2f} - {end_time:.2f}] {text}\n")
            
            print(f"Transcription saved to: {transcription_path}")

            # Clean up temp file if created
            if 'temp_wav_path' in locals():
                os.remove(temp_wav_path)

            return result
        except Exception as e:
            raise RuntimeError(f"Failed to transcribe audio: {str(e)}")

    def extract_word_timestamps(self, transcription: Dict) -> List[Tuple[str, float]]:
        """
        Extract words with their timestamps from Whisper transcription

        Args:
            transcription: Whisper transcription result

        Returns:
            List of (word, timestamp) tuples
        """
        words_with_times = []

        # Process each segment
        for segment in transcription["segments"]:
            start_time = segment["start"]
            text = segment["text"].strip().lower()
            
            # Skip empty segments and common filler words
            if text and text not in ['um', 'uh', 'eh']:
                words_with_times.append((text, start_time))

        return words_with_times

    def clean_text(self, text: str) -> str:
        """
        Clean text by removing punctuation and converting to lowercase

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Remove punctuation and convert to lowercase
        text = re.sub(r'[^\w\s]', '', text).lower()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def find_matches_for_line(
            self,
            line: str,
            words_with_times: List[Tuple[str, float]],
            threshold: int = 70
    ) -> Tuple[Optional[float], float]:
        """
        Find the best timestamp match for a lyrics line

        Args:
            line: Lyrics line to match
            words_with_times: List of (word, timestamp) tuples from transcription
            threshold: Minimum fuzzy matching score (0-100)

        Returns:
            Tuple of (timestamp, confidence_score)
        """
        cleaned_line = self.clean_text(line)

        # If the line is too short, it might be a section marker
        if len(cleaned_line.split()) <= 2:
            return None, 0

        best_score = 0
        best_timestamp = None
        window_size = 3  # Consider adjacent paragraphs

        # Iterate through each possible starting point
        for i in range(len(words_with_times)):
            # Get text within a time window
            window_end = min(i + window_size, len(words_with_times))
            window_text = " ".join([text for text, _ in words_with_times[i:window_end]])
            window_text = self.clean_text(window_text)

            # Calculate similarity score
            score = fuzz.token_sort_ratio(cleaned_line, window_text)

            # If we found a better match
            if score > best_score and score >= threshold:
                best_score = score
                # Use the timestamp of the first paragraph in the window
                best_timestamp = words_with_times[i][1]

                # If the score is very high, we can end the search early
                if score >= 95:
                    break

        # If no good match was found
        if best_timestamp is None:
            return None, 0

        return best_timestamp, best_score

    def count_exact_word_matches(self, text1: str, text2: str) -> Tuple[int, int]:
        """
        Count the number of exact word matches between two texts

        Args:
            text1: First text
            text2: Second text

        Returns:
            Tuple[matched_words_count, total_words_count]
        """
        # Clean and tokenize
        words1 = set(self.clean_text(text1).split())
        words2 = set(self.clean_text(text2).split())
        
        # Calculate matched words
        matched_words = len(words1.intersection(words2))
        total_words = len(words1)
        
        return matched_words, total_words

    def align_segments_to_lyrics(self, transcription: Dict, lyrics: List[str]) -> List[Tuple[str, float, float]]:
        """
        Align transcription segments with lyrics lines and assign timestamps.
        Reformat transcription segments based on lyrics text.

        Args:
            transcription: Whisper transcription result
            lyrics: List of lyrics lines (in time order, including repeated sections)

        Returns:
            List of (lyrics_line, timestamp, confidence) tuples
        """
        segments = transcription["segments"]
        aligned_lyrics = []
        debug_file = "debug_segments.txt"
        
        if not segments:
            return [(line, i * 3.0, 0) for i, line in enumerate(lyrics)]

        # Step 1: Collect all word-level timestamp information
        all_words = []  # [(word, start_time, end_time)]
        for segment in segments:
            if 'words' in segment:
                for word_info in segment['words']:
                    word = self.clean_text(word_info.get('word', ''))
                    if word and word not in ['um', 'uh', 'eh']:
                        all_words.append({
                            'word': word,
                            'start': word_info.get('start', segment['start']),
                            'end': word_info.get('end', segment['end'])
                        })

        # Step 2: Find matching word sequences for each lyrics line in order
        reformatted_segments = []  # [(lyrics_line, start_time, end_time, words_info, best_match_ratio)]
        current_word_index = 0
        
        # Write all debug information in a single file operation
        with open(debug_file, 'w', encoding='utf-8') as f:
            # Write original segments information
            f.write("=== Original Segments Information ===\n\n")
            f.write(f"Total segments: {len(segments)}\n\n")
            for i, segment in enumerate(segments):
                f.write(f"Segment {i}:\n")
                f.write(f"  Start time: {segment['start']:.2f}\n")
                f.write(f"  End time: {segment['end']:.2f}\n")
                f.write(f"  Text: {segment['text']}\n")
                if 'words' in segment:
                    f.write("  Words:\n")
                    for word in segment['words']:
                        f.write(f"    - {word.get('word', '')}: {word.get('start', 0):.2f} - {word.get('end', 0):.2f}\n")
                f.write("\n")

            # Write all words information
            f.write("\n=== All Words ===\n\n")
            f.write(f"Total words: {len(all_words)}\n")
            for word in all_words:
                f.write(f"Word: {word['word']}, Start: {word['start']:.2f}, End: {word['end']:.2f}\n")
            f.write("\n")

            # Write matching process
            f.write("\n=== Matching Process ===\n\n")
            
            for lyrics_index, lyrics_line in enumerate(lyrics):
                lyrics_words = self.clean_text(lyrics_line).split()
                window_size = len(lyrics_words)  # Use the number of words in the lyrics line as window size
                best_window = None
                best_match_ratio = 0
                search_range = min(50, len(all_words) - current_word_index)  # Limit forward search range
                
                f.write(f"Processing line {lyrics_index}: {lyrics_line}\n")
                f.write(f"Words in line: {lyrics_words}\n")
                f.write(f"Current word index: {current_word_index}\n")
                f.write(f"Search range: {search_range}\n")
                f.write(f"Window size: {window_size}\n\n")
                
                # Search for the best matching window within a range
                match_indx = 0
                for start_idx in range(current_word_index, current_word_index + search_range):
                    if start_idx + window_size > len(all_words):
                        break
                        
                    # Get words in the current window
                    window_words = all_words[start_idx:start_idx + window_size]
                    window_text = " ".join(w['word'] for w in window_words)
                    
                    # Calculate exact match ratio
                    lyrics_set = set(lyrics_words)
                    window_set = set(window_text.split())
                    matched_words = len(lyrics_set.intersection(window_set))
                    match_ratio = matched_words / len(lyrics_words)
                    
                    f.write(f"  Trying window at index {start_idx}:\n")
                    f.write(f"    Window text: {window_text}\n")
                    f.write(f"    Match ratio: {match_ratio:.2f}\n\n")
                    
                    # If we found a better match
                    if match_ratio > best_match_ratio:
                        best_match_ratio = match_ratio
                        best_window = window_words
                        match_indx = start_idx
                        
                        # If match ratio is very high, end search early
                        if match_ratio >= 0.90:  # 90% exact word match
                            break
                
                # Record matching results
                f.write(f"Final match for line {lyrics_index}:\n")
                
                if best_window and best_match_ratio >= 0.5:  # At least 50% word match required
                    start_time = best_window[0]['start']
                    end_time = best_window[-1]['end']
                    f.write(f"  Matched from {start_time:.2f} to {end_time:.2f} (match ratio: {best_match_ratio:.2f})\n")
                    f.write("  Matched words:\n")
                    for word in best_window:
                        f.write(f"    - {word['word']}: {word['start']:.2f} - {word['end']:.2f}\n")
                    
                    reformatted_segments.append((
                        lyrics_line,
                        start_time,
                        end_time,
                        best_window,
                        best_match_ratio
                    ))
                    
                    # Update search starting point
                    if best_match_ratio >= 0.90:
                        # For high quality matches, move directly to the end of the window
                        current_word_index = start_idx + window_size
                    else:
                        # For lower quality matches, move to the end of the window but allow small backtracking
                        backtrack = min(3, int(window_size * 0.2))  # Backtrack at most 3 words or 20% of window size
                        current_word_index = match_indx + window_size - backtrack
                    
                    f.write(f"Updated current_word_index to: {current_word_index}\n")
                else:
                    f.write("No good match found\n")
                    # If no match found, use estimated time point
                    # total_duration = segments[-1]["end"]
                    # estimated_time = (lyrics_index / len(lyrics)) * total_duration
                    if len(reformatted_segments) > 0:
                        reformatted_segments.append((
                            lyrics_line,
                            reformatted_segments[-1][2] + 0.1,
                            reformatted_segments[-1][2] + 2.0,  # Estimated 2 seconds duration
                            [],
                            best_match_ratio
                        ))
                    else:
                        reformatted_segments.append((
                            lyrics_line,
                            0.0,
                            2.0,  # Estimated 2 seconds duration
                            [],
                            best_match_ratio
                        ))
                f.write("\n")
        
        # Step 3: Ensure timestamps are monotonically increasing
        prev_end_time = 0
        for i, (line, start_time, end_time, words, best_match_ratio) in enumerate(reformatted_segments):
            # Ensure timestamps are at least 0.1 seconds apart
            adjusted_start = max(start_time, prev_end_time + 0.1)
            adjusted_end = max(end_time, adjusted_start + 0.5)  # Ensure each line lasts at least 0.5 seconds
            prev_end_time = adjusted_end
            
            aligned_lyrics.append((line, adjusted_start, best_match_ratio))
        
        return aligned_lyrics

    def align_lyrics(
            self,
            audio_path: str,
            lyrics: List[str],
            min_confidence: int = 60
    ) -> List[Tuple[str, float, float]]:
        """
        Align lyrics with audio

        Args:
            audio_path: Path to audio file
            lyrics: List of lyrics lines
            min_confidence: Minimum confidence threshold (parameter kept but no longer used)

        Returns:
            List of (lyrics_line, timestamp, confidence) tuples
        """
        # Transcribe audio
        transcription = self.transcribe_audio(audio_path)
        
        # Align in sequence
        return self.align_segments_to_lyrics(transcription, lyrics)

    def generate_lrc(
            self,
            audio_path: str,
            lyrics_path: str,
            output_path: Optional[str] = None,
            metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate LRC file using Whisper-based synchronization

        Args:
            audio_path: Path to audio file
            lyrics_path: Path to lyrics file
            output_path: Optional path to output LRC file. If not provided, 
                        will use lyrics file name with .lrc extension
            metadata: Optional dictionary with metadata (title, artist, album)

        Returns:
            Path to generated LRC file
        """
        # # Load lyrics with UTF-8 encoding
        # with open(lyrics_path, 'r', encoding='utf-8') as f:
        #     lyrics_text = f.read()
    # Read the input file
        with open(lyrics_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Process each line
        lyrics = []
        for line in lines:
            # Remove content inside square brackets and parentheses, including the brackets
            line = re.sub(r'\[.*?\]|\(.*?\)', '', line)

            if line.strip():
                # Remove emojis dynamically using the emoji library
                line = emoji.replace_emoji(line, replace='')
            
                # Strip leading/trailing whitespace
                line = line.strip()
            
                # Add the line even if it's empty after cleaning
                lyrics.append(line)


        # Align lyrics
        print("Aligning lyrics using Whisper speech recognition...")
        aligned_lyrics = self.align_lyrics(audio_path, lyrics)
        # Calculate the mean value of the best_match_ratio
        mean_match_ratio = sum(t[2] for t in aligned_lyrics) / len(aligned_lyrics)
        print(f"ℹ️ Mean Match Ratio: {mean_match_ratio:.2f}")
        if mean_match_ratio > 0.5:
            # Calculate audio duration (for metadata)
            audio = AudioSegment.from_file(audio_path)
            duration_seconds = len(audio) / 1000.0

            # Always use lyrics filename as output filename
            lyrics_dir = os.path.dirname(lyrics_path)
            lyrics_filename = os.path.splitext(os.path.basename(lyrics_path))[0]
            output_path = os.path.join(lyrics_dir, f"{lyrics_filename}.lrc")
            print(f"Will generate LRC file at: {output_path}")

            # Write LRC file with UTF-8-BOM encoding
            with open(output_path, 'wb') as f:
                # Write BOM
                f.write(b'\xef\xbb\xbf')
                
                # Prepare all content
                content = []
                
                # Write metadata
                if metadata:
                    if 'title' in metadata:
                        content.append(f"[ti:{self._normalize_text(metadata['title'])}]")
                    if 'artist' in metadata:
                        content.append(f"[ar:{self._normalize_text(metadata['artist'])}]")
                    if 'album' in metadata:
                        content.append(f"[al:{self._normalize_text(metadata['album'])}]")

                # Write length metadata
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                content.append(f"[length:{minutes:02d}:{seconds:02d}]")
                content.append("")  # Empty line

                # Write timestamped lyrics
                for line, timestamp, confidence in aligned_lyrics:
                    minutes = int(timestamp // 60)
                    seconds = timestamp % 60
                    normalized_line = self._normalize_text(line)
                    # Even if the line is empty, still write the timestamp
                    content.append(f"[{minutes:02d}:{seconds:05.2f}]{normalized_line}")

                # Write all content to file
                f.write('\n'.join(content).encode('utf-8'))

            print(f"✅ Whisper-synced LRC file generated at: {output_path}")
        else:
            print("💔 Whisper sync failed due to low match ratio.")
        return output_path

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text by replacing special characters
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Replace various quotes with standard quotes
        replacements = {
            ''': "'",
            ''': "'",
            '"': '"',
            '"': '"',
            '…': '...',
            '–': '-',
            '—': '-',
            '′': "'",
            '‛': "'"
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        return text