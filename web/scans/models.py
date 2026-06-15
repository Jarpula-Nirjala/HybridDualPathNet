from django.db import models
from django.contrib.auth.models import User


class Scan(models.Model):
    """Brain MRI scan upload and inference result."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    class PredictedClass(models.TextChoices):
        AD = "AD", "Alzheimer's Disease"
        PD = "PD", "Parkinson's Disease"
        CONTROL = "CONTROL", "Healthy Control"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scans")
    original_image = models.ImageField(upload_to="scans/originals/%Y/%m/%d/")
    heatmap_image = models.ImageField(
        upload_to="scans/heatmaps/%Y/%m/%d/", blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    predicted_class = models.CharField(
        max_length=10, choices=PredictedClass.choices, blank=True, null=True
    )
    confidence_ad = models.FloatField(blank=True, null=True)
    confidence_pd = models.FloatField(blank=True, null=True)
    confidence_control = models.FloatField(blank=True, null=True)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processing_time_seconds = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Scan #{self.pk} — {self.user.username} — {self.status}"

    @property
    def confidence_dict(self):
        return {
            "AD": self.confidence_ad or 0.0,
            "PD": self.confidence_pd or 0.0,
            "CONTROL": self.confidence_control or 0.0,
        }

    @property
    def predicted_label(self):
        if self.predicted_class:
            return self.PredictedClass(self.predicted_class).label
        return "—"
