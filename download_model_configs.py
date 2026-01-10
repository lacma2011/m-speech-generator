#!/usr/bin/env python3
"""
Manual model config downloader for XTTS v2
Use this if automatic download fails due to DNS/network issues
"""

import os
import urllib.request
from pathlib import Path

# XTTS v2 config files from Hugging Face
BASE_URL = "https://huggingface.co/coqui/XTTS-v2/resolve/main/"
MODEL_DIR = Path(os.getenv("TTS_HOME", "models")) / "tts" / "tts_models--multilingual--multi-dataset--xtts_v2"

CONFIG_FILES = [
    "config.json",
    "vocab.json",
    "speakers_xtts.pth",
    "mel_stats.pth",
]

def download_file(url: str, dest_path: Path):
    """Download a file with progress indicator."""
    print(f"Downloading {dest_path.name}...", end=" ")
    try:
        urllib.request.urlretrieve(url, dest_path)
        print(f"✓ ({dest_path.stat().st_size // 1024} KB)")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    return True

def main():
    print("XTTS v2 Config File Downloader")
    print("=" * 50)
    print(f"Target directory: {MODEL_DIR}")
    print()

    # Create directory if it doesn't exist
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Download each config file
    success_count = 0
    for filename in CONFIG_FILES:
        dest_path = MODEL_DIR / filename

        # Skip if already exists
        if dest_path.exists():
            print(f"Skipping {filename} (already exists)")
            success_count += 1
            continue

        url = BASE_URL + filename
        if download_file(url, dest_path):
            success_count += 1

    print()
    print(f"Downloaded {success_count}/{len(CONFIG_FILES)} files")

    if success_count == len(CONFIG_FILES):
        print("✓ All config files ready!")
    else:
        print("⚠ Some files failed to download. Check your internet connection.")

if __name__ == "__main__":
    main()
