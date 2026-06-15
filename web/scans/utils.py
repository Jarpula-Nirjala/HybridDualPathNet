"""Utilities for reading uploaded scan images from local or S3/R2 storage."""

import tempfile
from pathlib import Path


def get_readable_image_path(image_field) -> str:
    """
    Return a filesystem path to the image.

    For local FileSystemStorage, returns image_field.path directly.
    For remote storage (S3/R2), downloads to a temporary file.
    """
    try:
        return image_field.path
    except NotImplementedError:
        suffix = Path(image_field.name).suffix or ".jpg"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        with image_field.open("rb") as src:
            tmp.write(src.read())
        tmp.close()
        return tmp.name
