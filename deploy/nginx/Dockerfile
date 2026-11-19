# Rendershop nginx: do'kon (/) va admin panelni (/seller/) build qiladi; /api va Django adminni backendga uzatadi.
# Kontekst — loyiha ildizi (docker-compose.prod.yml).

FROM node:22-alpine AS shop
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ .
RUN npm run build

FROM node:22-alpine AS admin
WORKDIR /src
COPY admin/package.json admin/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY admin/ .
RUN npm run build

FROM nginx:1.27-alpine
RUN apk add --no-cache openssl
COPY --from=shop /src/dist /usr/share/nginx/shop
COPY --from=admin /src/dist /usr/share/nginx/seller
COPY deploy/nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY deploy/nginx/40-certs.sh /docker-entrypoint.d/40-certs.sh
RUN chmod +x /docker-entrypoint.d/40-certs.sh && rm -f /etc/nginx/conf.d/default.conf
