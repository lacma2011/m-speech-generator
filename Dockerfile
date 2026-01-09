# Voice Generator with Coqui TTS / XTTS v2
# Supports voice cloning and fine-tuning on custom voices

FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TTS_HOME=/app/models

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for voice samples and output
RUN mkdir -p /app/voice_samples /app/output /app/models

# Expose port for optional web interface
EXPOSE 5002

# Default command - start interactive shell
CMD ["/bin/bash"]
