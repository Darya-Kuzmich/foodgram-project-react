#!/bin/bash
echo "running makemigrations"
python manage.py makemigrations users
python manage.py makemigrations recipes
python manage.py migrate --noinput
echo "collecting static"
python manage.py collectstatic --no-input
echo "starting gunicorn"
exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
