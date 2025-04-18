#!/usr/bin/env python3
"""
Standalone script to clean lyrics files by removing section markers, 
performance notes, emojis, and empty lines.
"""

import re
import sys
import os
import unicodedata
import argparse
import emoji

def clean_lyrics_file(input_path, output_path=None):
    """
    Clean a lyrics file by removing:
    - Section markers in square brackets like [Verse 1], [Chorus]
    - Performance notes in parentheses like (Dramatic, Latin-inspired chanting)
    - Emojis and special characters
    - All empty lines

    Args:
        input_path (str): Path to the input lyrics file
        output_path (str, optional): Path to save the cleaned lyrics file. 
                                    If None, will overwrite the input file.

    Returns:
        str: Path to the cleaned lyrics file
    """
    # If no output path is provided, use the input path
    if output_path is None:
        output_path = input_path

    # Read the input file
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Process each line
    cleaned_lines = []
    for line in lines:
        # Remove content inside square brackets and parentheses, including the brackets
        line = re.sub(r'\[.*?\]|\(.*?\)', '', line)

        # Process the line only if it has actual content after cleaning
        if line.strip():
            # Remove emojis dynamically using the emoji library
            line = emoji.replace_emoji(line, replace='')
            
            # Strip leading/trailing whitespace
            line = line.strip()
            
            # Add the line only if it's not empty after cleaning
            if line:
                cleaned_lines.append(line)
    
    # Write the cleaned lyrics to the output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))

    return output_path

def main():
    parser = argparse.ArgumentParser(description='Clean lyrics files by removing section markers, performance notes, emojis, and empty lines.')
    parser.add_argument('--input', '-i', required=True, help='Path to input lyrics file')
    parser.add_argument('--output', '-o', help='Path to output cleaned lyrics file (optional)')
    
    args = parser.parse_args()
    
    try:
        output_path = clean_lyrics_file(args.input, args.output)
        print(f"Cleaned lyrics saved to: {output_path}")
    except Exception as e:
        print(f"Error cleaning lyrics: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 