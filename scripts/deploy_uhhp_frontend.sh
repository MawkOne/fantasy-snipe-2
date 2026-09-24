#!/usr/bin/env bash
# Build and deploy the UHHP auction frontend (Next.js) on the Coolify host.
#
# Usage: run on the host as root:
#   bash /root/scripts/deploy_uhhp_frontend.sh
set -euo pipefail

REPO_DIR="/opt/fantasy-snipe-2"
CONTAINER="uhhp-auction-frontend"
IMAGE="uhhp-auction-frontend:latest"
NETWORK="coolify"
DOMAIN="uhhp.hendo-s-agency.vibnai.com"

echo "==> Pulling latest code (${REPO_DIR})"
git -C "${REPO_DIR}" pull --no-edit

echo "==> Building ${IMAGE} from test-website/"
docker build -t "${IMAGE}" -f "${REPO_DIR}/scripts/Dockerfile.uhhp-frontend" "${REPO_DIR}/test-website"

echo "==> Recreating ${CONTAINER}"
# Clean up the accidentally deployed legacy typo name too. Two containers
# using the same Traefik router caused alternating HTML/asset builds.
docker rm -f "uhp-auction-frontend" >/dev/null 2>&1 || true
docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
docker run -d --name "${CONTAINER}" \
  --network "${NETWORK}" \
  --restart unless-stopped \
  -l "traefik.docker.network=${NETWORK}" \
  -l "traefik.enable=true" \
  -l "traefik.http.routers.uhhp-frontend.entrypoints=https" \
  -l "traefik.http.routers.uhhp-frontend.rule=Host(\"${DOMAIN}\")" \
  -l "traefik.http.routers.uhhp-frontend.tls=true" \
  -l "traefik.http.routers.uhhp-frontend.tls.certresolver=letsencrypt" \
  -l "traefik.http.services.uhhp-frontend.loadbalancer.server.port=3000" \
  "${IMAGE}"

echo "==> Done."
docker ps --filter "name=${CONTAINER}" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"