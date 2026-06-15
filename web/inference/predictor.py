"""
Inference pipeline: 7-pass TTA + Grad-CAM++ heatmap generation.
"""

import io
import logging

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from django.conf import settings
from PIL import Image
from pytorch_grad_cam import GradCAMPlusPlus
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

from .model import get_model_singleton
from .preprocessing import CLASS_NAMES, IMG_SIZE, TTA_TRANSFORMS, VAL_TRANSFORMS

logger = logging.getLogger(__name__)


def _load_rgb_image(image_path: str) -> np.ndarray:
    """Load image as RGB uint8 array."""
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"Could not read image: {image_path}")
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


def _transform_image(rgb: np.ndarray, transform) -> torch.Tensor:
    augmented = transform(image=rgb)
    return augmented["image"].unsqueeze(0)


@torch.no_grad()
def run_tta_inference(model, rgb_image: np.ndarray, tta_steps: int) -> np.ndarray:
    """
    Run test-time augmentation inference and return averaged class probabilities.
    Step 0 uses deterministic val transforms; steps 1..N-1 use random TTA.
    """
    device = next(model.parameters()).device
    all_probs = []

    for step in range(tta_steps):
        transform = VAL_TRANSFORMS if step == 0 else TTA_TRANSFORMS
        tensor = _transform_image(rgb_image, transform).to(device)
        logits = model(tensor)
        probs = F.softmax(logits, dim=1).cpu().numpy()[0]
        all_probs.append(probs)

    return np.mean(all_probs, axis=0)


def generate_gradcam_heatmap(model, rgb_image: np.ndarray, target_class_idx: int) -> np.ndarray:
    """Generate Grad-CAM++ overlay for the predicted class."""
    device = next(model.parameters()).device
    img_float = rgb_image.astype(np.float32) / 255.0
    tensor = _transform_image(rgb_image, VAL_TRANSFORMS).to(device)

    target_layers = [model.local_encoder.conv_head]
    cam = GradCAMPlusPlus(model=model, target_layers=target_layers)
    targets = [ClassifierOutputTarget(target_class_idx)]

    grayscale_cam = cam(input_tensor=tensor, targets=targets)[0]
    visualization = show_cam_on_image(
        img_float, grayscale_cam, use_rgb=True, colormap=cv2.COLORMAP_JET
    )
    cam.__del__()
    return visualization


def predict_scan(image_path: str) -> dict:
    """
    Full inference for one scan: TTA prediction + Grad-CAM++ heatmap.

    Returns dict with predicted class, per-class confidences, and heatmap JPEG bytes.
    """
    singleton = get_model_singleton()
    model = singleton.get_model()
    tta_steps = getattr(settings, "TTA_STEPS", 7)

    rgb = _load_rgb_image(image_path)
    rgb = cv2.resize(rgb, (IMG_SIZE, IMG_SIZE))

    avg_probs = run_tta_inference(model, rgb, tta_steps)
    pred_idx = int(np.argmax(avg_probs))
    predicted_class = CLASS_NAMES[pred_idx]

    heatmap_rgb = generate_gradcam_heatmap(model, rgb, pred_idx)

    # Encode heatmap as JPEG bytes for Django ImageField
    heatmap_bgr = cv2.cvtColor(heatmap_rgb, cv2.COLOR_RGB2BGR)
    ok, buffer = cv2.imencode(".jpg", heatmap_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise RuntimeError("Failed to encode heatmap image")

    return {
        "predicted_class": predicted_class,
        "confidence_ad": float(avg_probs[CLASS_NAMES.index("AD")]),
        "confidence_pd": float(avg_probs[CLASS_NAMES.index("PD")]),
        "confidence_control": float(avg_probs[CLASS_NAMES.index("CONTROL")]),
        "heatmap_bytes": buffer.tobytes(),
    }
