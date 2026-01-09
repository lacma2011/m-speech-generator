#!/usr/bin/env python3
"""
Fine-tune XTTS v2 on a custom voice dataset.

This script helps you fine-tune the XTTS model on a specific person's voice
for higher quality and more accurate voice cloning.

Requirements:
- 1-3 hours of clean audio recordings
- Transcriptions for each audio file
- GPU with at least 12GB VRAM recommended
"""

import os
import argparse
import json
from pathlib import Path

import torch
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts


def prepare_dataset(audio_dir: str, output_dir: str):
    """
    Prepare a dataset for fine-tuning.

    Expected structure:
    audio_dir/
        speaker_name/
            audio1.wav
            audio1.txt  (transcription)
            audio2.wav
            audio2.txt
            ...
    """
    audio_path = Path(audio_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    metadata = []

    for speaker_dir in audio_path.iterdir():
        if not speaker_dir.is_dir():
            continue

        speaker_name = speaker_dir.name

        for audio_file in speaker_dir.glob("*.wav"):
            transcript_file = audio_file.with_suffix(".txt")

            if not transcript_file.exists():
                print(f"Warning: No transcript for {audio_file}, skipping...")
                continue

            with open(transcript_file, "r") as f:
                transcript = f.read().strip()

            metadata.append({
                "audio_file": str(audio_file),
                "text": transcript,
                "speaker_name": speaker_name,
            })

    # Save metadata
    metadata_file = output_path / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Prepared {len(metadata)} audio samples")
    print(f"Metadata saved to: {metadata_file}")

    return metadata_file


def fine_tune(
    metadata_file: str,
    output_dir: str,
    epochs: int = 10,
    batch_size: int = 2,
    learning_rate: float = 5e-6,
):
    """
    Fine-tune XTTS v2 on the prepared dataset.

    Note: This requires significant GPU memory (12GB+ recommended).
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if device == "cpu":
        print("WARNING: Fine-tuning on CPU is very slow. GPU recommended.")

    print(f"Using device: {device}")
    print(f"Loading metadata from: {metadata_file}")

    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    print(f"Found {len(metadata)} training samples")

    # Load base XTTS model
    print("Loading base XTTS v2 model...")
    config = XttsConfig()
    config.load_json("path_to_config.json")  # Will be downloaded with model

    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir="path_to_checkpoint")
    model.to(device)

    # Training loop would go here
    # Note: Full fine-tuning implementation requires more setup
    # Consider using the TTS trainer API for production use

    print("""
    ============================================================
    FINE-TUNING GUIDE
    ============================================================

    For full fine-tuning, you have several options:

    1. Use Coqui TTS Trainer (recommended):
       - See: https://tts.readthedocs.io/en/latest/training.html

    2. Use the XTTS fine-tuning script:
       - Clone: https://github.com/coqui-ai/TTS
       - Run: python TTS/demos/xtts_ft_demo/xtts_demo.py

    3. Quick voice cloning (no training needed):
       - Use clone_voice.py with 6+ seconds of audio
       - This works well for most use cases!

    Your prepared dataset is at: {metadata_file}
    ============================================================
    """)

    return output_dir


def main():
    parser = argparse.ArgumentParser(
        description="Fine-tune XTTS v2 on a custom voice"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Prepare dataset command
    prep_parser = subparsers.add_parser(
        "prepare",
        help="Prepare audio dataset for training"
    )
    prep_parser.add_argument(
        "--audio-dir", "-a",
        required=True,
        help="Directory containing speaker folders with audio and transcripts"
    )
    prep_parser.add_argument(
        "--output-dir", "-o",
        default="datasets/prepared",
        help="Output directory for prepared dataset"
    )

    # Train command
    train_parser = subparsers.add_parser(
        "train",
        help="Fine-tune the model"
    )
    train_parser.add_argument(
        "--metadata", "-m",
        required=True,
        help="Path to metadata.json from prepare step"
    )
    train_parser.add_argument(
        "--output-dir", "-o",
        default="models/fine_tuned",
        help="Output directory for fine-tuned model"
    )
    train_parser.add_argument(
        "--epochs", "-e",
        type=int,
        default=10,
        help="Number of training epochs"
    )

    args = parser.parse_args()

    if args.command == "prepare":
        prepare_dataset(args.audio_dir, args.output_dir)
    elif args.command == "train":
        fine_tune(args.metadata, args.output_dir, args.epochs)


if __name__ == "__main__":
    main()
