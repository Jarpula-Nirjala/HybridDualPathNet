"""
Model singleton — loads PyTorch weights once per Celery worker process.

The model is cached at module level so subsequent inference tasks reuse the
same in-memory weights instead of reloading from disk.
"""

import logging
import threading

import torch
from django.conf import settings

from .architecture import HybridDualPathModel
from .weights import resolve_weights_path

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_instance = None


class ModelSingleton:
    """Thread-safe lazy loader for HybridDualPathModel."""

    def __init__(self):
        self.device = torch.device("cpu")
        self.weights_path = resolve_weights_path()
        self.model = None
        self._load()

    def _load(self):
        if not self.weights_path.exists():
            raise FileNotFoundError(
                f"Model weights not found.\n"
                f"  Expected: {self.weights_path}\n"
                f"  Also tried: weights/final_model.pth, weights/best_model.pth\n\n"
                f"Export from Colab (see scripts/export_weights_from_colab.py) or copy your\n"
                f"trained .pth file into the weights/ folder."
            )

        logger.info("Loading HybridDualPathModel from %s", self.weights_path)
        model = HybridDualPathModel(num_classes=3)
        checkpoint = torch.load(self.weights_path, map_location=self.device)

        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        else:
            state_dict = checkpoint

        model.load_state_dict(state_dict, strict=True)
        model.to(self.device)
        model.eval()

        # Warm-up forward pass to allocate buffers
        with torch.no_grad():
            dummy = torch.randn(1, 3, 224, 224, device=self.device)
            model(dummy)

        self.model = model
        logger.info("Model loaded and warmed up on %s", self.device)

    def get_model(self):
        return self.model


def get_model_singleton() -> ModelSingleton:
    """Return the module-level singleton, creating it on first access."""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = ModelSingleton()
    return _instance
