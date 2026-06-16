"""Production settings — Postgres, WhiteNoise, S3/R2 media, security headers."""

import os

from decouple import Csv, config

from .base import *  # noqa: F403

DEBUG = False

# Render sets RENDER_EXTERNAL_URL automatically — use it so ALLOWED_HOSTS/CSRF work on first deploy.
_render_url = os.environ.get("RENDER_EXTERNAL_URL", "").strip()
_render_host = ""
_render_origin = ""
if _render_url:
    _render_host = _render_url.replace("https://", "").replace("http://", "").strip("/")
    _render_origin = _render_url if _render_url.startswith("http") else f"https://{_render_host}"

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default=f"{_render_host},.onrender.com" if _render_host else ".onrender.com",
    cast=Csv(),
)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default=_render_origin,
    cast=Csv(),
)

import dj_database_url

DATABASES = {
    "default": dj_database_url.parse(
        config("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Static files via WhiteNoise with hashed filenames
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

USE_S3_MEDIA = config("USE_S3_MEDIA", default=False, cast=bool)
if USE_S3_MEDIA:
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="")
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="auto")
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True
    AWS_S3_FILE_OVERWRITE = False

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    }
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL.rstrip('/')}/{AWS_STORAGE_BUCKET_NAME}/"

# HTTPS / security
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CELERY_TASK_ALWAYS_EAGER = False
