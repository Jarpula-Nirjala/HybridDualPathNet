from django.urls import path

from . import views

app_name = "scans"

urlpatterns = [
    path("upload/", views.upload_scan, name="upload"),
    path("<int:pk>/processing/", views.processing_scan, name="processing"),
    path("<int:pk>/result/", views.result_scan, name="result"),
    path("<int:pk>/status/", views.scan_status, name="status"),
    path("history/", views.scan_history, name="history"),
    path("admin-stats/", views.admin_stats, name="admin_stats"),
]
