#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate

echo "Setting up tenant structure..."
python manage.py setup_tenant_structure

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 main.wsgi:application

echo "Setup Complete"
