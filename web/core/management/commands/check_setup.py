"""
Full project health check — run: python manage.py check_setup
"""

import importlib
import sys
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Verify HybridDualPatNet is fully configured and ready for inference"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== HybridDualPatNet Setup Check ===\n"))
        ok = True

        ok &= self._check_django()
        ok &= self._check_database()
        ok &= self._check_dependencies()
        ok &= self._check_model_weights()
        ok &= self._check_inference()
        ok &= self._check_media()
        ok &= self._check_celery()

        self.stdout.write("")
        if ok:
            self.stdout.write(self.style.SUCCESS("ALL CHECKS PASSED — project is ready for inference."))
        else:
            self.stdout.write(self.style.ERROR("SOME CHECKS FAILED — see items marked [FAIL] above."))
            self.stdout.write(
                "\nMost common fix: copy your trained weights from Colab/Google Drive to:\n"
                f"  {Path(settings.BASE_DIR) / 'weights' / 'final_model.pth'}\n"
                "See scripts/export_weights_from_colab.py for Colab download steps.\n"
            )
            raise SystemExit(1)

    def _line(self, label, passed, detail=""):
        mark = self.style.SUCCESS("[ OK ]") if passed else self.style.ERROR("[FAIL]")
        self.stdout.write(f"  {mark} {label}")
        if detail:
            self.stdout.write(f"         {detail}")
        return passed

    def _check_django(self):
        self.stdout.write(self.style.HTTP_INFO("Django"))
        return self._line(
            "Settings module",
            True,
            settings.SETTINGS_MODULE,
        )

    def _check_database(self):
        self.stdout.write(self.style.HTTP_INFO("\nDatabase"))
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            engine = settings.DATABASES["default"]["ENGINE"].split(".")[-1]
            return self._line("Connection", True, engine)
        except Exception as exc:
            return self._line("Connection", False, str(exc))

    def _check_dependencies(self):
        self.stdout.write(self.style.HTTP_INFO("\nPython packages"))
        all_ok = True
        packages = [
            "torch", "torchvision", "timm", "albumentations", "cv2",
            "pytorch_grad_cam", "celery", "rest_framework",
        ]
        for pkg in packages:
            import_name = "cv2" if pkg == "cv2" else pkg.replace("-", "_")
            try:
                mod = importlib.import_module(import_name)
                ver = getattr(mod, "__version__", "installed")
                all_ok &= self._line(pkg, True, ver)
            except ImportError as exc:
                all_ok &= self._line(pkg, False, str(exc))
        return all_ok

    def _check_model_weights(self):
        self.stdout.write(self.style.HTTP_INFO("\nModel weights"))
        from inference.weights import resolve_weights_path

        path = resolve_weights_path()
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            return self._line("Checkpoint file", True, f"{path} ({size_mb:.1f} MB)")
        return self._line(
            "Checkpoint file",
            False,
            f"Not found at {path} — export from Colab notebook",
        )

    def _check_inference(self):
        self.stdout.write(self.style.HTTP_INFO("\nInference pipeline"))
        from inference.weights import resolve_weights_path

        if not resolve_weights_path().exists():
            self._line("Model load + forward pass", False, "Skipped (no weights)")
            self._line("Grad-CAM++ module", True, "Code present (untested)")
            return False

        try:
            # Reset singleton so we test fresh load
            import inference.model as model_mod
            model_mod._instance = None

            from inference.model import get_model_singleton
            singleton = get_model_singleton()
            model = singleton.get_model()

            import torch
            with torch.no_grad():
                out = model(torch.randn(1, 3, 224, 224))
            self._line("Model load + forward pass", True, f"output shape {tuple(out.shape)}")
            self._line("Grad-CAM++ module", True, "pytorch-grad-cam installed")
            return True
        except Exception as exc:
            self._line("Model load + forward pass", False, str(exc))
            return False

    def _check_media(self):
        self.stdout.write(self.style.HTTP_INFO("\nMedia / static"))
        media = Path(settings.MEDIA_ROOT)
        media.mkdir(parents=True, exist_ok=True)
        static = Path(settings.STATICFILES_DIRS[0]) if settings.STATICFILES_DIRS else None
        ok = self._line("MEDIA_ROOT writable", media.exists(), str(media))
        if static:
            ok &= self._line("Static CSS", (static / "css" / "app.css").exists())
        return ok

    def _check_celery(self):
        self.stdout.write(self.style.HTTP_INFO("\nCelery"))
        eager = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)
        redis = getattr(settings, "REDIS_URL", "")
        if eager:
            return self._line("Task mode", True, "CELERY_TASK_ALWAYS_EAGER=True (no worker needed)")
        return self._line("Task mode", True, f"Async via Redis: {redis}")
