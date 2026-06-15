from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .forms import ScanUploadForm
from .models import Scan
from .tasks import run_scan_inference


@login_required
@require_http_methods(["GET", "POST"])
def upload_scan(request):
    if request.method == "POST":
        form = ScanUploadForm(request.POST, request.FILES)
        if form.is_valid():
            scan = form.save(commit=False)
            scan.user = request.user
            scan.status = Scan.Status.PENDING
            scan.save()
            run_scan_inference.delay(scan.pk)
            return redirect("scans:processing", pk=scan.pk)
    else:
        form = ScanUploadForm()

    return render(request, "scans/upload.html", {"form": form})


@login_required
def processing_scan(request, pk):
    scan = get_object_or_404(Scan, pk=pk, user=request.user)
    return render(request, "scans/processing.html", {"scan": scan})


@login_required
def result_scan(request, pk):
    scan = get_object_or_404(Scan, pk=pk, user=request.user)
    if scan.status not in (Scan.Status.DONE, Scan.Status.FAILED):
        return redirect("scans:processing", pk=scan.pk)
    return render(request, "scans/result.html", {"scan": scan})


@login_required
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def scan_status(request, pk):
    """JSON endpoint polled by HTMX every 2 seconds."""
    scan = get_object_or_404(Scan, pk=pk, user=request.user)
    data = {
        "id": scan.pk,
        "status": scan.status,
        "predicted_class": scan.predicted_class,
        "error_message": scan.error_message,
        "redirect_url": request.build_absolute_uri(
            f"/scans/{scan.pk}/result/"
        ),
    }
    return Response(data)


@login_required
def scan_history(request):
    scans = Scan.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(scans, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "scans/history.html", {"page_obj": page_obj})


def _is_staff(user):
    return user.is_staff


@login_required
@user_passes_test(_is_staff)
def admin_stats(request):
    """Staff-only dashboard: scan counts, class distribution, averages."""
    total_scans = Scan.objects.count()
    done_scans = Scan.objects.filter(status=Scan.Status.DONE)

    class_distribution = (
        done_scans.values("predicted_class")
        .annotate(count=Count("id"))
        .order_by("predicted_class")
    )

    avg_confidence = done_scans.aggregate(
        avg_ad=Avg("confidence_ad"),
        avg_pd=Avg("confidence_pd"),
        avg_control=Avg("confidence_control"),
    )
    avg_processing = done_scans.aggregate(avg_time=Avg("processing_time_seconds"))

    # Build chart-friendly lists
    class_labels = []
    class_counts = []
    for row in class_distribution:
        if row["predicted_class"]:
            label = Scan.PredictedClass(row["predicted_class"]).label
            class_labels.append(label)
            class_counts.append(row["count"])

    context = {
        "total_scans": total_scans,
        "done_scans": done_scans.count(),
        "failed_scans": Scan.objects.filter(status=Scan.Status.FAILED).count(),
        "class_labels": class_labels,
        "class_counts": class_counts,
        "avg_confidence_ad_pct": (avg_confidence["avg_ad"] or 0) * 100,
        "avg_confidence_pd_pct": (avg_confidence["avg_pd"] or 0) * 100,
        "avg_confidence_control_pct": (avg_confidence["avg_control"] or 0) * 100,
        "avg_processing": avg_processing.get("avg_time") or 0,
    }
    return render(request, "scans/admin_stats.html", context)
