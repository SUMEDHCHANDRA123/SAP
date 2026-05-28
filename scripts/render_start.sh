#!/usr/bin/env bash
set -euo pipefail

python manage.py migrate --noinput

if [ "${RUN_SEED:-false}" = "true" ]; then
  python seed.py
fi

exec gunicorn breathe_esg_backend.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120
