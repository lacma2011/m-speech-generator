#!/usr/bin/env python3
"""
Model Loader for XTTS v2

Handles loading either the public XTTS v2 model or a custom fine-tuned model
based on environment variables.

Environment Variables:
    CUSTOM_MODEL_PATH: Path to custom model checkpoint directory
    CUSTOM_CONFIG_PATH: Path to custom model config.json file

If these are not set, the default public XTTS v2 model will be used.
"""

import os
from pathlib import Path

import torch
from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts


def get_device():
    """Determine the best available device."""
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class XTTSModelLoader:
    """Loads and manages XTTS models (public or custom)."""

    def __init__(self):
        self.model = None
        self.device = get_device()
        self.is_custom_model = False

    def load_model(self):
        """Load the appropriate model based on environment configuration."""
        if self.model is not None:
            return self.model

        custom_model_path = os.getenv("CUSTOM_MODEL_PATH")
        custom_config_path = os.getenv("CUSTOM_CONFIG_PATH")

        if custom_model_path and custom_config_path:
            self.model = self._load_custom_model(custom_model_path, custom_config_path)
            self.is_custom_model = True
        else:
            self.model = self._load_public_model()
            self.is_custom_model = False

        return self.model

    def _load_public_model(self):
        """Load the public XTTS v2 model."""
        print(f"Loading public XTTS v2 model on {self.device}...")
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        print("Public model loaded successfully!")
        return tts

    def _load_custom_model(self, checkpoint_dir: str, config_path: str):
        """Load a custom fine-tuned XTTS model."""
        print(f"Loading custom XTTS model on {self.device}...")
        print(f"  Config: {config_path}")
        print(f"  Checkpoint: {checkpoint_dir}")

        # Validate paths
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        if not os.path.exists(checkpoint_dir):
            raise FileNotFoundError(f"Checkpoint directory not found: {checkpoint_dir}")

        # Load config
        config = XttsConfig()
        config.load_json(config_path)

        # Initialize model
        model = Xtts.init_from_config(config)
        model.load_checkpoint(config, checkpoint_dir=checkpoint_dir, use_deepspeed=False)
        model.to(self.device)

        print("Custom model loaded successfully!")
        return model

    def tts_to_file(self, text: str, file_path: str, speaker_wav, language: str = "en"):
        """
        Generate speech and save to file.

        Handles both TTS API objects (public model) and Xtts objects (custom model).
        """
        if self.model is None:
            self.load_model()

        # Public TTS API has tts_to_file method
        if hasattr(self.model, 'tts_to_file'):
            self.model.tts_to_file(
                text=text,
                file_path=file_path,
                speaker_wav=speaker_wav,
                language=language,
            )
        # Custom Xtts model uses inference_with_config
        else:
            # For custom models, we need to handle inference differently
            outputs = self.model.synthesize(
                text=text,
                config=self.model.config,
                speaker_wav=speaker_wav,
                language=language,
            )
            # Save the audio
            import soundfile as sf
            sf.write(file_path, outputs["wav"], 24000)

    def get_model_info(self):
        """Return information about the loaded model."""
        if self.is_custom_model:
            return {
                "type": "custom",
                "checkpoint": os.getenv("CUSTOM_MODEL_PATH"),
                "config": os.getenv("CUSTOM_CONFIG_PATH"),
                "device": self.device,
            }
        else:
            return {
                "type": "public",
                "model": "tts_models/multilingual/multi-dataset/xtts_v2",
                "device": self.device,
            }


# Singleton instance
_model_loader = None


def get_model_loader():
    """Get the global model loader instance."""
    global _model_loader
    if _model_loader is None:
        _model_loader = XTTSModelLoader()
    return _model_loader
