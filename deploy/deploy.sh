#!/usr/bin/env bash
# Production deploy / update on the server.   Usage:  ./deploy.sh          (git pull + rebuild + restart)
#                                                      ./deploy.sh --no-git (rebuild only)
set -euo pipefail
cd "$(dirname "$0")"

[ -f .env ] || { echo "ERROR: deploy/.env missing. Run:  cp .env.example .env  and fill it in."; exit 1; }
grep -q "CHANGE_ME" .env && { echo "ERROR: .env still has CHANGE_ME values. Edit it first."; exit 1; }
set -a; . ./.env; set +a

if [ "${1:-}" != "--no-git" ]; then git -C .. pull --ff-only; fi

docker compose up -d --build
docker image prune -f >/dev/null

echo "Waiting for the site..."
for i in $(seq 1 30); do
  if curl -fsS -o /dev/null "https://${DOMAIN}/api/"; then echo "OK: https://${DOMAIN} is live"; docker compose ps; exit 0; fi
  sleep 5
done
echo "Site did not respond in time. Check:  docker compose logs --tail=100"; docker compose ps; exit 1
