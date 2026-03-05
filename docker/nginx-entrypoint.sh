#!/bin/sh
# Thay thế ${DOMAIN} trong nginx config template
# Chạy tự động bởi nginx image tại /docker-entrypoint.d/

set -e

DOMAIN="${DOMAIN:-localhost}"
TEMPLATE="/etc/nginx/templates/default.conf.template"
OUTPUT="/etc/nginx/conf.d/default.conf"

if [ ! -f "$TEMPLATE" ]; then
    echo "ERROR: nginx template not found: $TEMPLATE"
    exit 1
fi

envsubst '${DOMAIN}' < "$TEMPLATE" > "$OUTPUT"
echo "nginx config generated for domain: $DOMAIN"
