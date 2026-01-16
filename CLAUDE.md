# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Docker-based voice cloning system using **XTTS v2** from Coqui TTS. The system can clone any voice with just 6+ seconds of audio and provides both CLI and web interfaces.

## Architecture

### Core Components

1. **model_loader.py** - Unified model loading system
   - Handles both public XTTS v2 and custom fine-tuned models
   - Uses environment variables for configuration:
     - `CUSTOM_MODEL_PATH`: Path to custom checkpoint directory
     - `CUSTOM_CONFIG_PATH`: Path to custom config.json
   - Automatic device selection (CUDA/MPS/CPU)
   - Singleton pattern ensures model loads only once
   - Falls back to public model if custom paths not set

2. **clone_voice.py** - Main voice cloning script for CLI usage
   - Uses model_loader for flexible model selection
   - Supports single or multiple speaker audio files for better quality
   - Language support: 16+ languages (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko)

3. **web_server.py** - Flask-based web interface
   - Provides REST API (`/api/clone`, `/api/models`) and HTML UI
   - Uses model_loader for flexible model selection
   - Global model loaded once and reused via singleton
   - Handles file uploads (WAV, MP3, OGG, FLAC)
   - Generates unique IDs for uploaded/generated files
   - Serves generated audio via `/audio/<filename>` endpoint
   - `/api/models` endpoint shows current model type (public/custom)

4. **train_voice.py** - Fine-tuning utilities (advanced usage)
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

### Using Custom Fine-Tuned Models

After training a custom model, you can deploy it using environment variables:

```bash
# CLI with custom model
docker compose run --rm \
    -e CUSTOM_MODEL_PATH=/app/models/my_custom_model \
    -e CUSTOM_CONFIG_PATH=/app/models/my_custom_model/config.json \
    voice-generator python clone_voice.py \
    --text "Your text" \
    --speaker sample.wav \
    --output output.wav

# Web server with custom model
docker compose run --rm \
    -e CUSTOM_MODEL_PATH=/app/models/my_custom_model \
    -e CUSTOM_CONFIG_PATH=/app/models/my_custom_model/config.json \
    voice-generator python web_server.py
```

**Training and Deployment Workflow:**

1. **Train on powerful machine** (12GB+ VRAM required)
   - Use Coqui's official training scripts from https://github.com/coqui-ai/TTS
   - Or use XTTS fine-tuning demo: `TTS/demos/xtts_ft_demo/xtts_demo.py`
   - Training produces checkpoint files and config.json

2. **Copy model files to deployment machine**
   - Transfer checkpoint directory
   - Transfer config.json file

3. **Deploy with environment variables**
   - Set `CUSTOM_MODEL_PATH` to checkpoint directory
   - Set `CUSTOM_CONFIG_PATH` to config.json path
   - Both CLI and web server will automatically use custom model

4. **Verification**
   - Check logs on startup - shows "Model type: custom"
   - Call `/api/models` endpoint - shows custom model info
   - If env vars not set, falls back to public XTTS v2

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

- **Model Loading**: Both CLI and web server use `model_loader.py` for unified model management
  - Singleton pattern ensures model loads only once per process
  - Automatically detects custom vs public model based on environment variables
  - Web server pre-loads model on startup to avoid per-request loading
- **Custom Models**: Use `CUSTOM_MODEL_PATH` and `CUSTOM_CONFIG_PATH` environment variables
  - If not set, automatically falls back to public XTTS v2 model
  - Useful for deploying fine-tuned models trained on powerful machines
- File uploads use unique IDs to prevent conflicts
- Audio samples should be 6-30 seconds of clear speech for best results
- Multiple speaker samples improve cloning quality significantly
- First run will be slow due to model download (~1.5GB for public model)

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
