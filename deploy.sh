#!/bin/bash
# =============================================================================
# TSBot Deploy Script — chạy trên MÁY APPLICATION SERVER
# Dùng: bash deploy.sh
#
# Yêu cầu trước khi chạy lần đầu:
#   1. Đặt đủ biến trong .env.production (DOMAIN, SECRET_KEY, POSTGRES_*, ...)
#   2. Chạy SSL setup: ./scripts/setup-ssl.sh --domain yourdomain.com --email admin@example.com
# =============================================================================
set -e

COMPOSE="docker compose -f docker/docker-compose.prod.yml --env-file .env.production"

# ── Kiểm tra file .env.production tồn tại ────────────────────────────────────
if [ ! -f ".env.production" ]; then
    echo "✗ Không tìm thấy .env.production"
    echo "  Tạo từ template: cp .env.production.example .env.production"
    exit 1
fi

# ── Kiểm tra / tạo SSL cert ───────────────────────────────────────────────────
DOMAIN=$(grep -E '^DOMAIN=' .env.production | cut -d= -f2 | tr -d '"' | tr -d "'" || echo "")
if [ -z "$DOMAIN" ]; then
    echo "✗ DOMAIN chưa được đặt trong .env.production"
    exit 1
fi

CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
if [ ! -f "$CERT_PATH" ]; then
    echo "⚠ Chưa có SSL certificate cho '$DOMAIN'"
    echo "  → Tự động tạo self-signed certificate (dùng tạm cho đến khi có domain thật)"
    bash scripts/setup-ssl.sh --self-signed --domain "$DOMAIN"
    echo ""
fi

echo "=== [1/5] Pull code mới từ git ==="
git pull origin main

echo ""
echo "=== [2/5] Rebuild images ==="
$COMPOSE build tsbot-api nginx

echo ""
echo "=== [3/5] Restart services ==="
$COMPOSE up -d --remove-orphans

echo ""
echo "=== [4/5] Đợi API healthy ==="
echo "  (API cần ~3 phút để load embedding model lần đầu)"

TIMEOUT=300  # 5 phút
ELAPSED=0
INTERVAL=10

while [ $ELAPSED -lt $TIMEOUT ]; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' tsbot-api 2>/dev/null || echo "not_found")
    if [ "$STATUS" = "healthy" ]; then
        echo "  ✓ tsbot-api healthy (${ELAPSED}s)"
        break
    fi
    printf "  Đợi API... (%ss / %ss) status=%s\r" "$ELAPSED" "$TIMEOUT" "$STATUS"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

if [ "$STATUS" != "healthy" ]; then
    echo "  ✗ API không healthy sau ${TIMEOUT}s"
    echo "  Xem log: docker logs tsbot-api --tail 50"
    exit 1
fi

echo ""
echo "=== [5/5] Kiểm tra health ==="
# Dùng /nginx-health (port 80, không redirect) để check nginx
# Dùng /api/v1/health qua HTTPS để check toàn stack
curl -sf http://localhost/nginx-health > /dev/null && echo "  ✓ Nginx OK"
curl -sfk "https://localhost/health" | python3 -m json.tool 2>/dev/null || \
    curl -sf "https://$DOMAIN/health" | python3 -m json.tool 2>/dev/null || \
    echo "  (Bỏ qua HTTPS check — có thể cần DNS đúng)"

echo ""
echo "✓ Deploy hoàn tất!"
echo "  App: https://$DOMAIN"
echo "  Log: docker logs tsbot-api -f"
