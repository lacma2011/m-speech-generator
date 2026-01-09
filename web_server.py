#!/usr/bin/env python3
"""
Simple Web Interface for Voice Cloning

Provides a REST API and basic web UI for voice cloning.
"""

import os
import uuid
from pathlib import Path

import torch
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from werkzeug.utils import secure_filename

from TTS.api import TTS

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = "voice_samples"
OUTPUT_FOLDER = "output"
ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "flac"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global TTS model (loaded once)
tts_model = None


def get_device():
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_tts():
    global tts_model
    if tts_model is None:
        device = get_device()
        print(f"Loading XTTS v2 model on {device}...")
        tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    return tts_model


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Voice Cloning - XTTS v2</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }
        h1 { color: #00d4ff; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea, select, button {
            width: 100%;
            padding: 12px;
            border: 1px solid #333;
            border-radius: 8px;
            background: #16213e;
            color: #eee;
            font-size: 16px;
        }
        textarea { min-height: 100px; resize: vertical; }
        button {
            background: #00d4ff;
            color: #000;
            cursor: pointer;
            font-weight: bold;
            border: none;
        }
        button:hover { background: #00b8e6; }
        button:disabled { background: #666; cursor: not-allowed; }
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #16213e;
            border-radius: 8px;
        }
        audio { width: 100%; margin-top: 10px; }
        .status { color: #ffd700; margin-top: 10px; }
        .error { color: #ff6b6b; }
        .info { background: #0f3460; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Voice Cloning with XTTS v2</h1>

    <div class="info">
        <strong>How to use:</strong>
        <ol>
            <li>Upload a voice sample (6+ seconds of clear speech recommended)</li>
            <li>Enter the text you want to generate</li>
            <li>Click "Generate Speech"</li>
        </ol>
    </div>

    <form id="cloneForm" enctype="multipart/form-data">
        <div class="form-group">
            <label for="voice_sample">Voice Sample (WAV, MP3, OGG, FLAC)</label>
            <input type="file" id="voice_sample" name="voice_sample" accept=".wav,.mp3,.ogg,.flac" required>
        </div>

        <div class="form-group">
            <label for="text">Text to Speak</label>
            <textarea id="text" name="text" placeholder="Enter the text you want to convert to speech..." required></textarea>
        </div>

        <div class="form-group">
            <label for="language">Language</label>
            <select id="language" name="language">
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
                <option value="pt">Portuguese</option>
                <option value="pl">Polish</option>
                <option value="tr">Turkish</option>
                <option value="ru">Russian</option>
                <option value="nl">Dutch</option>
                <option value="cs">Czech</option>
                <option value="ar">Arabic</option>
                <option value="zh-cn">Chinese</option>
                <option value="ja">Japanese</option>
                <option value="hu">Hungarian</option>
                <option value="ko">Korean</option>
            </select>
        </div>

        <button type="submit" id="submitBtn">Generate Speech</button>
    </form>

    <div id="status" class="status"></div>

    <div id="result" class="result" style="display: none;">
        <h3>Generated Audio</h3>
        <audio id="audioPlayer" controls></audio>
        <br><br>
        <a id="downloadLink" href="#" download>Download Audio</a>
    </div>

    <script>
        const form = document.getElementById('cloneForm');
        const status = document.getElementById('status');
        const result = document.getElementById('result');
        const audioPlayer = document.getElementById('audioPlayer');
        const downloadLink = document.getElementById('downloadLink');
        const submitBtn = document.getElementById('submitBtn');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            submitBtn.disabled = true;
            status.textContent = 'Processing... This may take a minute...';
            status.className = 'status';
            result.style.display = 'none';

            const formData = new FormData(form);

            try {
                const response = await fetch('/api/clone', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    status.textContent = 'Success!';
                    audioPlayer.src = data.audio_url;
                    downloadLink.href = data.audio_url;
                    result.style.display = 'block';
                } else {
                    status.textContent = 'Error: ' + data.error;
                    status.className = 'status error';
                }
            } catch (error) {
                status.textContent = 'Error: ' + error.message;
                status.className = 'status error';
            }

            submitBtn.disabled = false;
        });
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/clone", methods=["POST"])
def clone_voice():
    try:
        # Check for voice sample
        if "voice_sample" not in request.files:
            return jsonify({"success": False, "error": "No voice sample provided"})

        file = request.files["voice_sample"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"})

        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type"})

        # Get text and language
        text = request.form.get("text", "").strip()
        if not text:
            return jsonify({"success": False, "error": "No text provided"})

        language = request.form.get("language", "en")

        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{filename}")
        file.save(input_path)

        # Generate output path
        output_filename = f"{unique_id}_output.wav"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Generate speech
        tts = get_tts()
        tts.tts_to_file(
            text=text,
            file_path=output_path,
            speaker_wav=input_path,
            language=language,
        )

        return jsonify({
            "success": True,
            "audio_url": f"/audio/{output_filename}",
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_file(
        os.path.join(OUTPUT_FOLDER, filename),
        mimetype="audio/wav"
    )


@app.route("/api/models")
def list_models():
    """List available TTS models."""
    return jsonify({
        "current_model": "tts_models/multilingual/multi-dataset/xtts_v2",
        "supported_languages": [
            "en", "es", "fr", "de", "it", "pt", "pl", "tr",
            "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"
        ]
    })


if __name__ == "__main__":
    print("Starting Voice Cloning Web Server...")
    print("Loading model (this may take a moment)...")
    get_tts()  # Pre-load model
    print("Server ready!")
    print("Open http://localhost:5002 in your browser")
    app.run(host="0.0.0.0", port=5002, debug=False)
