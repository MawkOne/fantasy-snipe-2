#!/usr/bin/env sh
set -e

if [ -z "$NHL_DATABASE_URL" ] && [ -z "$DATABASE_URL" ]; then
  echo "Set DATABASE_URL or NHL_DATABASE_URL before starting." >&2
  exit 1
fi

exec python3 -m uvicorn app:app --app-dir 'prediction-backend' --host 0.0.0.0 --port ${PORT:-8100}


