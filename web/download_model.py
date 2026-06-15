#!/usr/bin/env python
"""
Download model weights at deploy time if MODEL_WEIGHTS_URL is set.

Usage:
    python download_model.py

Skips download if the target file already exists.
Supports Google Drive links via gdown (pip install gdown).
"""

import os
import re
import sys
from pathlib import Path


def _extract_gdrive_id(url: str) -> str | None:
    patterns = [
        r"id=([a-zA-Z0-9_-]+)",
        r"/d/([a-zA-Z0-9_-]+)",
        r"^([a-zA-Z0-9_-]{20,})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def main():
    weights_path = Path(os.environ.get("MODEL_WEIGHTS_PATH", "weights/final_model.pth"))
    weights_url = os.environ.get("MODEL_WEIGHTS_URL", "").strip()

    if weights_path.exists() and weights_path.stat().st_size > 1_000_000:
        print(f"Model weights already present at {weights_path}")
        return 0

    if not weights_url:
        print(
            "MODEL_WEIGHTS_URL not set and weights file missing.\n"
            "Download manually from:\n"
            "  https://drive.google.com/file/d/1rDF-vTOgMSIrpE3rV1OXukyhXiVNxxRq/view\n"
            "Or run: gdown 1rDF-vTOgMSIrpE3rV1OXukyhXiVNxxRq -O weights/final_model.pth",
            file=sys.stderr,
        )
        return 1

    weights_path.parent.mkdir(parents=True, exist_ok=True)
    gdrive_id = _extract_gdrive_id(weights_url)

    if gdrive_id:
        try:
            import gdown
        except ImportError:
            print("Installing gdown for Google Drive download...", file=sys.stderr)
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown", "-q"])
            import gdown

        print(f"Downloading from Google Drive (id={gdrive_id}) → {weights_path}")
        gdown.download(id=gdrive_id, output=str(weights_path), quiet=False)
    else:
        from urllib.request import urlretrieve

        print(f"Downloading model weights from {weights_url} → {weights_path}")

        def _progress(block_num, block_size, total_size):
            if total_size > 0:
                pct = min(100, block_num * block_size * 100 / total_size)
                sys.stdout.write(f"\r  Progress: {pct:.1f}%")
                sys.stdout.flush()

        urlretrieve(weights_url, weights_path, reporthook=_progress)

    if not weights_path.exists() or weights_path.stat().st_size < 1_000_000:
        print("Download failed or file too small — check MODEL_WEIGHTS_URL.", file=sys.stderr)
        return 1

    print(f"\nDownload complete: {weights_path.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
