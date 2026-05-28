#!/usr/bin/env bash
set -euo pipefail

exec celery -A breathe_esg_backend worker --loglevel=info
