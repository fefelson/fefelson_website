#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# ✅ Seed the database (your custom management command)
python manage.py seed_data || true

# ✅ Create superuser non-interactively (only if it doesn't exist)
python manage.py createsuperuser --noinput || true
