#!/bin/sh
set -e

python manage.py migrate
python manage.py collectstatic --no-input
exec gunicorn cgi_adventure.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
