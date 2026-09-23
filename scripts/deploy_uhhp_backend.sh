#!/usr/bin/env bash
# Redeploy the UHHP auction FastAPI backend on the Coolify host.
#
# Usage: run on the host as root:
#   bash /root/scripts/deploy_uhhp_backend.sh
#
# Flow: pull latest code -> rebuild image from data-digging/ -> recreate the
# container on the coolify Docker network with the same Traefik labels/env.
set -euo pipefail

REPO_DIR="/opt/fantasy-snipe-2"
CONTAINER="uhhp-auction-backend"
IMAGE="uhhp-auction-backend:latest"
NETWORK="coolify"
DOMAIN="uhhp-api.hendo-s-agency.vibnai.com"
DB_URL="postgresql://postgres:Q3EkMnoAuEBmx1dHgUy1j87h7gLMvL9G0T8IjQo7P4w=@uhhp-auction-db:5432/uhhp_auction"

echo "==> Pulling latest code (${REPO_DIR})"
git -C "${REPO_DIR}" pull --no-edit

echo "==> Building ${IMAGE} from data-digging/"
docker build -t "${IMAGE}" -f - "${REPO_DIR}/data-digging" <<'DOCKERFILE'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKERFILE

echo "==> Recreating ${CONTAINER}"
docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
docker run -d --name "${CONTAINER}" \
  --network "${NETWORK}" \
  --restart unless-stopped \
  -e "FANTASY_DATABASE_URL=${DB_URL}" \
  -e "DATABASE_URL=${DB_URL}" \
  -e "ALLOWED_ORIGINS=*" \
  -l "traefik.docker.network=${NETWORK}" \
  -l "traefik.enable=true" \
  -l "traefik.http.routers.uhhp-api.entrypoints=https" \
  -l "traefik.http.routers.uhhp-api.rule=Host(\"${DOMAIN}\")" \
  -l "traefik.http.routers.uhhp-api.tls=true" \
  -l "traefik.http.routers.uhhp-api.tls.certresolver=letsencrypt" \
  -l "traefik.http.services.uhhp-api.loadbalancer.server.port=8000" \
  "${IMAGE}"

echo "==> Done. Container:"
docker ps --filter "name=${CONTAINER}" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"