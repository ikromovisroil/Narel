#!/bin/sh
# Birinchi marta SSL sertifikat olish (Let's Encrypt, bepul). Oldin: DNS da domen va www serverga qaragan
# bo'lishi va "docker compose -f docker-compose.prod.yml up -d" ishlab turishi kerak.
# Ishlatish (loyiha papkasida):  sh deploy/ssl.sh
set -e
cd "$(dirname "$0")/.."
. ./.env

if [ -z "$DOMAIN" ] || [ -z "$CERTBOT_EMAIL" ]; then
  echo ".env da DOMAIN va CERTBOT_EMAIL to'ldirilishi kerak"
  exit 1
fi

COMPOSE="docker compose -f docker-compose.prod.yml"

$COMPOSE run --rm --entrypoint certbot certbot certonly --webroot -w /var/www/certbot \
  --cert-name "$DOMAIN" -d "$DOMAIN" -d "www.$DOMAIN" \
  --email "$CERTBOT_EMAIL" --agree-tos --no-eff-email --non-interactive

# nginx yangi sertifikatni ulaydi
$COMPOSE restart nginx
echo "Tayyor: https://$DOMAIN (admin panel: https://$DOMAIN/seller/)"
