#!/bin/bash
# =============================================================================
# TSBot SSL Setup Script
# =============================================================================
# Dùng script này để cấp SSL certificate trước khi khởi động production stack.
#
# Option A: Let's Encrypt (khuyến nghị — domain thật, có internet)
# Option B: Self-signed   (dev/intranet không có internet)
#
# Cách dùng:
#   chmod +x scripts/setup-ssl.sh
#   ./scripts/setup-ssl.sh --domain yourdomain.com [--email admin@yourdomain.com]
#   ./scripts/setup-ssl.sh --self-signed --domain yourdomain.com
# =============================================================================

set -euo pipefail

DOMAIN=""
EMAIL=""
SELF_SIGNED=false
CERT_DIR="/etc/letsencrypt/live"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain)    DOMAIN="$2"; shift 2 ;;
        --email)     EMAIL="$2"; shift 2 ;;
        --self-signed) SELF_SIGNED=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$DOMAIN" ]]; then
    echo "ERROR: --domain là bắt buộc"
    echo "  Ví dụ: ./scripts/setup-ssl.sh --domain tsbot.example.com --email admin@example.com"
    exit 1
fi

echo "=== TSBot SSL Setup ==="
echo "Domain: $DOMAIN"
echo "Mode: $([ "$SELF_SIGNED" = true ] && echo 'Self-signed' || echo 'Let'\''s Encrypt')"
echo ""

# ── Option B: Self-signed (dev/intranet) ─────────────────────────────────
if [[ "$SELF_SIGNED" = true ]]; then
    echo "[B] Tạo self-signed certificate..."
    CERT_PATH="$CERT_DIR/$DOMAIN"
    mkdir -p "$CERT_PATH"

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$CERT_PATH/privkey.pem" \
        -out "$CERT_PATH/fullchain.pem" \
        -subj "/CN=$DOMAIN/O=TSBot/C=VN" \
        -addext "subjectAltName=DNS:$DOMAIN,DNS:www.$DOMAIN"

    echo "OK Certificate đã tạo tại: $CERT_PATH"
    echo ""
    echo "LƯU Ý: Self-signed certificate sẽ gây cảnh báo trình duyệt."
    echo "Chỉ dùng cho môi trường dev/intranet."
    exit 0
fi

# ── Option A: Let's Encrypt ───────────────────────────────────────────────
echo "[A] Xin Let's Encrypt certificate via certbot..."

if ! command -v certbot &>/dev/null; then
    echo "Certbot chưa được cài. Cài đặt..."
    if command -v apt-get &>/dev/null; then
        apt-get update -q && apt-get install -y certbot
    elif command -v yum &>/dev/null; then
        yum install -y certbot
    else
        echo "ERROR: Không tìm thấy package manager. Cài certbot thủ công."
        exit 1
    fi
fi

# Tạo thư mục webroot cho ACME challenge
mkdir -p /var/www/certbot

EMAIL_FLAG=""
if [[ -n "$EMAIL" ]]; then
    EMAIL_FLAG="--email $EMAIL"
else
    EMAIL_FLAG="--register-unsafely-without-email"
fi

# Chạy certbot standalone (port 80 phải free)
# Nếu nginx đang chạy, dùng webroot thay vì standalone:
#   certbot certonly --webroot -w /var/www/certbot -d "$DOMAIN" $EMAIL_FLAG --agree-tos

certbot certonly \
    --standalone \
    --preferred-challenges http \
    -d "$DOMAIN" \
    $EMAIL_FLAG \
    --agree-tos \
    --non-interactive

echo ""
echo "OK Certificate đã cấp tại: $CERT_DIR/$DOMAIN/"
echo ""
echo "Bước tiếp theo:"
echo "  1. Đặt DOMAIN=$DOMAIN trong .env.production"
echo "  2. Khởi động stack: docker compose -f docker/docker-compose.prod.yml up -d"
echo ""
echo "Auto-renewal (cron):"
echo "  0 3 * * * certbot renew --quiet && docker exec tsbot-nginx nginx -s reload"
