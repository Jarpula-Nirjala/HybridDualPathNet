"""Development settings — SQLite fallback, DEBUG on, optional eager Celery."""

from decouple import Csv, config

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Override with Postgres if DATABASE_URL is provided locally
_database_url = config("DATABASE_URL", default="")
if _database_url:
    import dj_database_url

    DATABASES["default"] = dj_database_url.parse(_database_url)

# Run Celery tasks synchronously when no worker is available
CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", default=False, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
