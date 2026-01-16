#!/usr/bin/env python3
"""
Voice Cloning with XTTS v2

This script clones a voice from audio samples and generates speech.
XTTS v2 can clone a voice with just 6+ seconds of clear audio.
"""

import os
import argparse
from pathlib import Path

from model_loader import get_model_loader


def clone_and_speak(
    text: str,
    speaker_wav: str | list[str],
    output_path: str = "output/cloned_speech.wav",
    language: str = "en",
):
    """
    Clone a voice from audio sample(s) and generate speech.

    Args:
        text: The text to speak
        speaker_wav: Path to speaker audio file(s) for voice cloning
        output_path: Where to save the generated audio
        language: Language code (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko)
    """
    # Load model (public or custom based on environment variables)
    loader = get_model_loader()
    model_info = loader.get_model_info()

    print(f"Using device: {model_info['device']}")
    print(f"Model type: {model_info['type']}")

    if model_info['type'] == 'custom':
        print(f"  Custom config: {model_info['config']}")
        print(f"  Custom checkpoint: {model_info['checkpoint']}")

    loader.load_model()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Handle multiple speaker files
    if isinstance(speaker_wav, list):
        speaker_wav_path = speaker_wav
    else:
        speaker_wav_path = speaker_wav

    print(f"Cloning voice from: {speaker_wav_path}")
    print(f"Generating speech for: '{text[:50]}...'")

    # Generate speech with cloned voice
    loader.tts_to_file(
        text=text,
        file_path=output_path,
        speaker_wav=speaker_wav_path,
        language=language,
    )

    print(f"Audio saved to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Clone a voice and generate speech using XTTS v2"
    )
    parser.add_argument(
        "--text", "-t",
        required=True,
        help="Text to convert to speech"
    )
    parser.add_argument(
        "--speaker", "-s",
        required=True,
        nargs="+",
        help="Path(s) to speaker audio file(s) for voice cloning (WAV format, 6+ seconds recommended)"
    )
    parser.add_argument(
        "--output", "-o",
        default="output/cloned_speech.wav",
        help="Output audio file path"
    )
    parser.add_argument(
        "--language", "-l",
        default="en",
        help="Language code (default: en)"
    )

    args = parser.parse_args()

    # Handle single or multiple speaker files
    speaker_wav = args.speaker[0] if len(args.speaker) == 1 else args.speaker

    clone_and_speak(
        text=args.text,
        speaker_wav=speaker_wav,
        output_path=args.output,
        language=args.language,
    )


if __name__ == "__main__":
    main()
