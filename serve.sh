#!/usr/bin/env sh
set -e

# Simple wrapper to ensure ${PORT} is expanded by a shell in PaaS environments
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info


