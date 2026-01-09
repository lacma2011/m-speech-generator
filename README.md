# Voice Generator - Text-to-Speech with Voice Cloning

A Docker-based voice cloning system using **XTTS v2** from Coqui TTS. Clone any voice with just 6+ seconds of audio!

## Quick Start

### 1. Build and Start the Container

```bash
# Build the container
docker compose build

# Start an interactive session (CPU)
docker compose run --rm voice-generator

# OR with GPU support (requires nvidia-docker)
docker compose --profile gpu run --rm voice-generator-gpu
```

### 2. Clone a Voice (inside container)

```bash
# Basic voice cloning
python clone_voice.py \
    --text "Hello, this is a test of voice cloning technology." \
    --speaker /app/voice_samples/your_sample.wav \
    --output /app/output/generated.wav

# Multiple reference samples (better quality)
python clone_voice.py \
    --text "Your text here" \
    --speaker sample1.wav sample2.wav sample3.wav \
    --output output.wav
```

### 3. Web Interface

```bash
# Start the web server
python web_server.py

# Access at http://localhost:5002
```

## Usage Options

### Command Line

```bash
# Inside the container
python clone_voice.py --help
```

Options:
- `--text, -t`: Text to convert to speech (required)
- `--speaker, -s`: Path(s) to speaker audio files (required)
- `--output, -o`: Output file path (default: output/cloned_speech.wav)
- `--language, -l`: Language code (default: en)

Supported languages: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko

### Web API

```bash
# Clone voice via API
curl -X POST http://localhost:5002/api/clone \
    -F "voice_sample=@your_sample.wav" \
    -F "text=Hello world" \
    -F "language=en"
```

## Voice Sample Tips

For best results:
- **Duration**: 6-30 seconds of clear speech
- **Quality**: Clean audio without background noise
- **Format**: WAV preferred (also supports MP3, OGG, FLAC)
- **Content**: Natural conversational speech works best
- **Multiple samples**: Using 2-5 samples improves quality

## Project Structure

```
speech_generator/
├── Dockerfile           # CPU version
├── Dockerfile.gpu       # GPU/CUDA version
├── docker-compose.yml   # Container orchestration
├── requirements.txt     # Python dependencies
├── clone_voice.py       # Main voice cloning script
├── train_voice.py       # Fine-tuning utilities
├── web_server.py        # Web interface
├── voice_samples/       # Your voice samples go here
└── output/              # Generated audio output
```

## Fine-Tuning (Advanced)

For higher quality on a specific voice, you can fine-tune the model:

```bash
# Prepare dataset (requires audio files with transcripts)
python train_voice.py prepare \
    --audio-dir /app/voice_samples/training_data \
    --output-dir /app/datasets/prepared

# See training guide
python train_voice.py train --help
```

## GPU Support

For faster inference, use the GPU-enabled container:

```bash
# Ensure nvidia-docker is installed
docker compose --profile gpu build
docker compose --profile gpu run --rm voice-generator-gpu
```

## Model Information

This project uses **XTTS v2** from Coqui TTS:
- Zero-shot voice cloning (no training required)
- Multilingual support (16+ languages)
- High-quality neural TTS
- ~1.5GB model download on first run

## Troubleshooting

**First run is slow**: The model (~1.5GB) downloads on first use. Subsequent runs are faster.

**Out of memory**: Try reducing text length or use CPU mode. GPU requires ~4GB VRAM.

**Audio quality issues**: Use longer/cleaner voice samples, or try multiple samples.

## License

XTTS v2 model is released under the Coqui Public Model License 1.0.0
