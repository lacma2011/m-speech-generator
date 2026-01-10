# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Docker-based voice cloning system using **XTTS v2** from Coqui TTS. The system can clone any voice with just 6+ seconds of audio and provides both CLI and web interfaces.

## Architecture

### Core Components

1. **clone_voice.py** - Main voice cloning script for CLI usage
   - Uses XTTS v2 model from Coqui TTS
   - Handles device selection (CUDA/MPS/CPU)
   - Supports single or multiple speaker audio files for better quality
   - Language support: 16+ languages (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko)

2. **web_server.py** - Flask-based web interface
   - Provides REST API (`/api/clone`, `/api/models`) and HTML UI
   - Global TTS model loaded once and reused
   - Handles file uploads (WAV, MP3, OGG, FLAC)
   - Generates unique IDs for uploaded/generated files
   - Serves generated audio via `/audio/<filename>` endpoint

3. **train_voice.py** - Fine-tuning utilities (advanced usage)
   - Dataset preparation (`prepare` command)
   - Training guidance (`train` command)
   - Note: Full fine-tuning requires 12GB+ VRAM and is mostly a guide script

### Docker Architecture

- **Dockerfile** - CPU version
- **Dockerfile.gpu** - GPU/CUDA version for faster inference
- **docker-compose.yml** - Orchestration with volume mounts:
  - `voice_models` volume: Persists downloaded models between restarts
  - `./voice_samples`: Input audio samples
  - `./output`: Generated audio output
  - Port 5002 exposed for web interface

### Key Directories

- `voice_samples/` - Place voice samples here for cloning
- `output/` - Generated audio files are saved here
- Models are auto-downloaded (~1.5GB) on first run to `models/` (persisted via Docker volume)

## Development Commands

### Docker Operations

```bash
# Build CPU version
docker compose build

# Run interactive session (CPU)
docker compose run --rm voice-generator

# Build and run GPU version
docker compose --profile gpu build
docker compose --profile gpu run --rm voice-generator-gpu
```

### Voice Cloning (inside container)

```bash
# Basic voice cloning
python clone_voice.py \
    --text "Your text here" \
    --speaker /app/voice_samples/sample.wav \
    --output /app/output/generated.wav \
    --language en

# Multiple reference samples (better quality)
python clone_voice.py \
    --text "Your text here" \
    --speaker sample1.wav sample2.wav sample3.wav \
    --output output.wav
```

### Web Server

```bash
# Start web server (inside container)
python web_server.py

# Access at http://localhost:5002
```

### Fine-Tuning (Advanced)

```bash
# Prepare dataset
python train_voice.py prepare \
    --audio-dir /app/voice_samples/training_data \
    --output-dir /app/datasets/prepared

# Training guidance
python train_voice.py train --help
```

## Technical Details

### Model Information

- **Model**: XTTS v2 (tts_models/multilingual/multi-dataset/xtts_v2)
- **Size**: ~1.5GB (downloads on first run)
- **Capabilities**: Zero-shot voice cloning, multilingual TTS
- **GPU Requirements**: ~4GB VRAM recommended for GPU mode
- **License**: Coqui Public Model License 1.0.0

### Device Selection Logic

The system automatically selects the best available device:
1. CUDA (if available)
2. MPS (Apple Silicon, if available)
3. CPU (fallback)

### API Endpoints

- `GET /` - Web UI
- `POST /api/clone` - Clone voice (multipart/form-data with voice_sample, text, language)
- `GET /audio/<filename>` - Serve generated audio
- `GET /api/models` - List current model and supported languages

## Important Implementation Notes

- The web server loads the TTS model globally on startup to avoid reloading on each request
- File uploads use unique IDs to prevent conflicts
- Audio samples should be 6-30 seconds of clear speech for best results
- Multiple speaker samples improve cloning quality significantly
- First run will be slow due to model download (~1.5GB)

## Dependency Requirements & Known Issues

### Critical Version Pins

The project requires specific version constraints to work correctly:

1. **PyTorch < 2.6.0** - PyTorch 2.6+ changed `torch.load` security defaults which break XTTS model loading
2. **transformers >= 4.33.0, < 4.40.0** - TTS library depends on `BeamSearchScorer` which was moved in newer versions
3. **TTS >= 0.22.0** - Core library for XTTS v2 model

These are already configured in `requirements.txt`. Always rebuild the container after dependency changes:
```bash
docker compose build
```

### Docker DNS Configuration

The `docker-compose.yml` includes explicit DNS servers (8.8.8.8, 8.8.4.4, 1.1.1.1) to prevent model download failures from `coqui.gateway.scarf.sh`. If DNS issues persist, the `download_model_configs.py` script provides a fallback to download config files directly from Hugging Face.

## Quick Setup for New Developers

```bash
# 1. Clone the repository
git clone <repo-url>
cd speech_generator

# 2. Build the Docker container (downloads ~2-3GB of dependencies)
docker compose build

# 3. Start the web server (downloads ~1.5GB XTTS model on first run)
docker compose run --rm voice-generator python web_server.py

# 4. Open http://localhost:5002 and start cloning voices!
```
