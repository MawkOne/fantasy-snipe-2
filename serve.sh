#!/usr/bin/env sh
set -e

# Optional: start Cloud SQL Auth Proxy if GOOGLE_CREDENTIALS_JSON and INSTANCE_CONNECTION_NAME are provided
if [ -n "${GOOGLE_CREDENTIALS_JSON}" ] && [ -n "${INSTANCE_CONNECTION_NAME}" ]; then
  echo "Starting Cloud SQL Auth Proxy for ${INSTANCE_CONNECTION_NAME}..."
  # Write credentials to a file at runtime
  echo "${GOOGLE_CREDENTIALS_JSON}" > /tmp/gcp-sa.json
  chmod 600 /tmp/gcp-sa.json
  # Start proxy on 127.0.0.1:5432 in background
  /usr/local/bin/cloud-sql-proxy ${INSTANCE_CONNECTION_NAME} \
    --address 127.0.0.1 \
    --port 5432 \
    --credentials-file /tmp/gcp-sa.json \
    &
  # If NHL_DATABASE_URL not set, default to local proxy target
  if [ -z "${NHL_DATABASE_URL}" ]; then
    export NHL_DATABASE_URL="postgresql://${DB_USER:-postgres}:${DB_PASS:-postgres}@127.0.0.1:5432/${DB_NAME:-postgres}?sslmode=disable"
  fi
fi

# Run API
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
