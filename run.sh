#!/usr/bin/env bash
set -e
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_questions
python manage.py collectstatic --noinput
gunicorn core.wsgi:application
