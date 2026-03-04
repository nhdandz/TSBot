#!/bin/bash
# =============================================================================
# TSBot Deploy Script — chạy trên MÁY APPLICATION SERVER
# Dùng: bash deploy.sh
# =============================================================================
set -e

COMPOSE="docker compose -f docker/docker-compose.prod.yml --env-file .env.production"

echo "=== [1/4] Pull code mới từ git ==="
git pull origin main

echo "=== [2/4] Rebuild images ==="
$COMPOSE build tsbot-api nginx

echo "=== [3/4] Restart services ==="
$COMPOSE up -d --remove-orphans

echo "=== [4/4] Kiểm tra health ==="
sleep 10
curl -sf http://localhost/health && echo "" && echo "✓ Deploy thành công!" || echo "✗ Health check thất bại, xem log: docker logs tsbot-api"
