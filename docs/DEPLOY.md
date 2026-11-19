# Rendershop — serverga o'rnatish

Natija:

| Manzil | Nima |
|---|---|
| `https://rendershop.uz` | Do'kon |
| `https://rendershop.uz/seller/` | Admin panel |
| `https://rendershop.uz/admin/` | Django admin |
| `https://rendershop.uz/api/` | API (sayt va mobil ilova) |
| `https://www.rendershop.uz` | → `rendershop.uz` ga yo'naltiriladi |
| `https://rendershop.uz/api/docs/` | Swagger (faqat xodimlar uchun) |

Hammasi Docker'da ishlaydi: `db` (PostgreSQL), `backend` (Django + Gunicorn), `nginx` (do'kon, admin panel, HTTPS),
`certbot` (SSL sertifikatini avtomatik yangilaydi), `backup` (bazaning kundalik nusxasi).

Server: Ubuntu 24.04, kamida 2 yadro / 4 GB RAM (Contabo Cloud VPS 4 yetadi).

---

## 1. DNS (domen panelida)

Serverning IP manziliga 2 ta **A** yozuv:

| Turi | Nomi | Qiymati |
|---|---|---|
| A | `@` | server IP |
| A | `www` | server IP |

Tekshirish (kompyuterda): `nslookup rendershop.uz` — server IP chiqishi kerak. Tarqalishi bir necha daqiqadan bir necha soatgacha.

## 2. Serverni tayyorlash (bir marta)

SSH orqali kiring (`ssh root@SERVER_IP`) va:

```bash
apt update && apt upgrade -y
# Docker
curl -fsSL https://get.docker.com | sh
# Firewall: faqat SSH, HTTP, HTTPS
ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw --force enable
```

## 3. Loyihani yuklab olish va sozlash

```bash
cd /opt
git clone https://github.com/ikromovisroil/Narel.git rendershop
cd rendershop
cp .env.prod.example .env
nano .env
```

`.env` da to'ldiriladi:

- `SECRET_KEY` va `POSTGRES_PASSWORD` — tasodifiy qiymatlar. Yaratish:
  `docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(50))"`
- `DJANGO_ADMIN_URL` — Django admin manzili (`admin` → `https://rendershop.uz/admin/`).
- `CERTBOT_EMAIL` — SSL ogohlantirishlari uchun email.

## 4. Ishga tushirish

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Birinchi build 3–5 daqiqa (do'kon va admin panel build qilinadi). Migratsiya va statik fayllar avtomatik.
Holat: `docker compose -f docker-compose.prod.yml ps` — hammasi `Up` bo'lishi kerak.

## 5. SSL sertifikat (bir marta)

DNS server IP ga qaragandan keyin:

```bash
sh deploy/ssl.sh
```

Skript Let's Encrypt shartlariga rozilik bilan bepul sertifikat oladi va nginx'ni qayta ishga tushiradi.
Sertifikat 90 kunlik, `certbot` servisi uni o'zi yangilaydi.

## 6. Birinchi admin

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

Keyin `https://rendershop.uz/seller/` (admin panel) yoki `https://rendershop.uz/admin/` (Django admin) ga shu login bilan kiring. Test ma'lumotlar bo'lsa, ishga tushirishdan oldin:
`docker compose -f docker-compose.prod.yml exec backend python manage.py seed_test_data --clear`.

## 7. Tashqi xizmatlarda domenni yangilash

- **Google kirish** — Google Cloud Console → Credentials → OAuth Client → *Authorized JavaScript origins*:
  `https://rendershop.uz`. Client ID ni admin panelda: Sozlamalar → Integratsiyalar.
- **SMS (Eskiz)** — admin panel: Sozlamalar → Integratsiyalar. SMS matni shabloni Eskiz'da tasdiqlangan bo'lishi kerak:
  `Rendershop: kirish kodi {kod}. Hech kimga bermang.`
- **To'lov tizimlari (Click, Payme, Uzum)** — ularga yangi domenni bering.
- **Ommaviy oferta** — admin panelda `[MChJ nomi]` kabi joylarni to'ldiring.

---

## Kundalik ishlar

| Nima | Buyruq |
|---|---|
| Yangi versiyani o'rnatish | `sh deploy/update.sh` |
| Loglar | `docker compose -f docker-compose.prod.yml logs -f backend` |
| Qayta ishga tushirish | `docker compose -f docker-compose.prod.yml restart` |
| To'xtatish | `docker compose -f docker-compose.prod.yml down` (ma'lumotlar saqlanadi) |
| Harakatlar jurnalini tozalash | `docker compose -f docker-compose.prod.yml exec backend python manage.py prune_audit` |

### Zaxira nusxa (backup)

`backup` servisi har kuni bazaning nusxasini `/opt/rendershop/backups/shop-YYYY-MM-DD.sql.gz` ga yozadi (14 kun saqlanadi).
Nusxalarni vaqti-vaqti bilan **boshqa joyga** ham ko'chiring (server butunlay ishdan chiqsa ham qolishi uchun).

Mahsulot rasmlari (`media`) nusxasi:

```bash
docker run --rm -v rendershop_media:/m -v /opt/rendershop/backups:/b alpine tar czf /b/media-$(date +%F).tar.gz -C /m .
```

Bazani nusxadan tiklash (diqqat: joriy ma'lumotlar almashtiriladi):

```bash
gunzip -c backups/shop-2026-01-01.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U shop -d shop
```

### Muammo bo'lsa

- **Sayt ochilmayapti** — `docker compose -f docker-compose.prod.yml ps` va `logs nginx` / `logs backend`.
- **"Xavfsiz emas" (SSL) ogohlantirishi** — `sh deploy/ssl.sh` hali bajarilmagan yoki DNS server IP ga qaramayapti.
- **Backend ishga tushmayapti, `SECRET_KEY` xatosi** — `.env` da kalit kamida 40 belgi bo'lishi kerak.
