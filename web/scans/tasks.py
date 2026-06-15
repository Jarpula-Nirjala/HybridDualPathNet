import logging
import time
import traceback

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import Scan

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def run_scan_inference(self, scan_id: int):
    """
    Celery task: load model once per worker, run TTA inference + Grad-CAM++,
    then persist results on the Scan record.
    """
    from inference.predictor import predict_scan

    try:
        scan = Scan.objects.get(pk=scan_id)
    except Scan.DoesNotExist:
        logger.error("Scan %s not found", scan_id)
        return

    scan.status = Scan.Status.PROCESSING
    scan.error_message = ""
    scan.save(update_fields=["status", "error_message"])

    started = time.perf_counter()
    try:
        from scans.utils import get_readable_image_path

        image_path = get_readable_image_path(scan.original_image)
        result = predict_scan(image_path)
        elapsed = time.perf_counter() - started

        scan.predicted_class = result["predicted_class"]
        scan.confidence_ad = result["confidence_ad"]
        scan.confidence_pd = result["confidence_pd"]
        scan.confidence_control = result["confidence_control"]
        scan.processing_time_seconds = round(elapsed, 2)

        heatmap_bytes = result["heatmap_bytes"]
        heatmap_name = f"heatmap_{scan_id}.jpg"
        scan.heatmap_image.save(heatmap_name, ContentFile(heatmap_bytes), save=False)

        scan.status = Scan.Status.DONE
        scan.save()
        logger.info("Scan %s completed in %.2fs", scan_id, elapsed)

    except Exception as exc:
        elapsed = time.perf_counter() - started
        scan.status = Scan.Status.FAILED
        scan.error_message = str(exc)
        scan.processing_time_seconds = round(elapsed, 2)
        scan.save()
        logger.exception("Scan %s failed after %.2fs", scan_id, elapsed)
        raise exc
