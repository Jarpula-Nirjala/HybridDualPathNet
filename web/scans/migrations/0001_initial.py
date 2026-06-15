# Generated manually for HybridDualPatNet initial schema

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Scan",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "original_image",
                    models.ImageField(upload_to="scans/originals/%Y/%m/%d/"),
                ),
                (
                    "heatmap_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="scans/heatmaps/%Y/%m/%d/",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("done", "Done"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "predicted_class",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("AD", "Alzheimer's Disease"),
                            ("PD", "Parkinson's Disease"),
                            ("CONTROL", "Healthy Control"),
                        ],
                        max_length=10,
                        null=True,
                    ),
                ),
                ("confidence_ad", models.FloatField(blank=True, null=True)),
                ("confidence_pd", models.FloatField(blank=True, null=True)),
                ("confidence_control", models.FloatField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("processing_time_seconds", models.FloatField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scans",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
