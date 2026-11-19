#!/bin/sh
# nginx ishga tushishidan oldin: Let's Encrypt sertifikati bo'lsa — o'shani ulaydi, bo'lmasa vaqtinchalik
# (o'zi imzolagan) sertifikat yaratadi, shunda nginx ishlaydi va certbot haqiqiysini olishi mumkin.
# Fon jarayon har 6 soatda sertifikatni qayta ulab nginx'ni yangilaydi (certbot yangilaganini oladi).
set -e
LIVE="/etc/letsencrypt/live/${DOMAIN}"
CERTS="/etc/nginx/certs"
mkdir -p "$CERTS"

link_certs() {
  if [ -f "$LIVE/fullchain.pem" ] && [ -f "$LIVE/privkey.pem" ]; then
    ln -sf "$LIVE/fullchain.pem" "$CERTS/fullchain.pem"
    ln -sf "$LIVE/privkey.pem" "$CERTS/privkey.pem"
    return 0
  fi
  return 1
}

if ! link_certs; then
  echo "SSL: Let's Encrypt sertifikati hali yo'q — vaqtinchalik sertifikat yaratilmoqda (deploy/ssl.sh ni ishga tushiring)"
  openssl req -x509 -nodes -newkey rsa:2048 -days 7 -subj "/CN=${DOMAIN}" \
    -keyout "$CERTS/privkey.pem" -out "$CERTS/fullchain.pem" >/dev/null 2>&1
fi

(
  while :; do
    sleep 6h
    link_certs && nginx -s reload || true
  done
) &
