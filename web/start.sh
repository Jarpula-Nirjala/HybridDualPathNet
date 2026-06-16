#!/bin/bash
celery -A config worker --loglevel=info --concurrency=1 &
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
