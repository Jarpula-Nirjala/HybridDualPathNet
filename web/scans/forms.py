from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Scan

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


class ScanUploadForm(forms.ModelForm):
    class Meta:
        model = Scan
        fields = ("original_image",)

    def clean_original_image(self):
        image = self.cleaned_data["original_image"]
        max_bytes = settings.SCAN_MAX_UPLOAD_MB * 1024 * 1024

        if image.size > max_bytes:
            raise ValidationError(
                f"Image must be {settings.SCAN_MAX_UPLOAD_MB} MB or smaller."
            )

        content_type = getattr(image, "content_type", "")
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationError("Only JPG and PNG images are allowed.")

        ext = "." + image.name.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError("Only JPG and PNG images are allowed.")

        return image
