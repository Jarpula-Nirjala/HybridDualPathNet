#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Download model weights (uses MODEL_WEIGHTS_URL env var set in Render dashboard)
python download_model.py

# Django setup
python manage.py collectstatic --no-input
python manage.py migrate
