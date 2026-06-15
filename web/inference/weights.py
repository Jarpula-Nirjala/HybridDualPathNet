"""
Resolve trained checkpoint path (final_model.pth or best_model.pth).
"""

from pathlib import Path

from django.conf import settings


def resolve_weights_path() -> Path:
    """
    Return the first existing weights file.

    Search order:
      1. MODEL_WEIGHTS_PATH from settings / env
      2. weights/final_model.pth
      3. weights/best_model.pth
    """
    candidates = [
        Path(settings.MODEL_WEIGHTS_PATH),
        Path(settings.BASE_DIR) / "weights" / "final_model.pth",
        Path(settings.BASE_DIR) / "weights" / "best_model.pth",
    ]
    seen = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if path.exists():
            return path
    return Path(settings.MODEL_WEIGHTS_PATH)
