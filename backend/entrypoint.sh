#!/bin/sh
# Konteyner har ishga tushganda: migratsiya va statik fayllar (Django admin, Swagger), keyin gunicorn
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput --verbosity 0
exec "$@"
