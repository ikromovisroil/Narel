# Narel API hujjati

Backend: Django + Django REST Framework. Barcha javoblar JSON.

- Asosiy manzil: `https://<domen>/api/` (lokalda `http://127.0.0.1:8010/api/`)
- **Mobil ilovalar uchun: `https://<domen>/api/v1/`** — xuddi shu endpoint'lar, versiyalangan (pastda 0-bo'lim)
- Django admin (texnik panel): `/admin/`
- Admin panel API'si: `/api/admin/` — quyida `{ADMIN}` deb yozilgan
- **Swagger** (sinab ko'rish mumkin): `/api/docs/`
- **ReDoc** (o'qish uchun): `/api/redoc/`
- OpenAPI sxema (Postman, mobil ilova uchun): `/api/schema/`

Swagger/ReDoc `DEBUG=True` da hamma uchun ochiq. Serverda (`DEBUG=False`) faqat xodim ko'radi:
avval `/admin/` ga kiring, keyin `/api/docs/` ni oching. Token bilan sinash: Swagger'da **Authorize** → `access` token.


---

## 0. Mobil ilova (Android, iOS) uchun

**Har doim `/api/v1/` dan foydalaning.** `/api/` — sayt va admin panel uchun, u bilan bir xil, lekin versiyasiz.
Kelajakda mos kelmaydigan o'zgarish bo'lsa `/api/v2/` ochiladi va eski ilovalar `v1` da ishlashda davom etadi.
Swagger va OpenAPI sxemasi faqat `/api/v1/` yo'llarini ko'rsatadi — undan Kotlin/Swift klient kodini avtomatik yaratish mumkin
(masalan, `openapi-generator`).

| Mavzu | Qanday |
|---|---|
| Kirish | SMS kod (`auth/code/send/` → `auth/code/verify/`) yoki Google (`auth/google/`). Tokenlarni xavfsiz joyda saqlang (Android Keystore / iOS Keychain) |
| Google | Ilovaning iOS/Android Client ID'si admin panelda kiritilgan bo'lishi kerak (Sozlamalar → Integratsiyalar → Google). Android'da odatda `serverClientId` sifatida sayt (Web) Client ID beriladi |
| Sevimlilar va savat | Serverda: `favorites/`, `cart/` (8-bo'lim). Sayt bilan bir xil — mijoz telefonda qo'shganini saytda ko'radi |
| Buyurtma | `POST orders/` — buyurtma qilingan mahsulotlar savatdan avtomatik chiqadi |
| SMS kodni avtomatik o'qish | iOS: kod maydoniga `textContentType = .oneTimeCode`. Android (SMS Retriever) uchun SMS matniga ilova kodini qo'shish kerak — backend'da hali yo'q |
| Rasm manzillari | To'liq URL (`https://…/media/…`) |
| Til | `Accept-Language: uz` yoki `ru` |

## 1. Umumiy qoidalar

### Avtorizatsiya (JWT)

Kirgandan keyin ikki token beriladi:

| Token | Muddati | Vazifasi |
|---|---|---|
| `access` | 1 soat | Har bir so'rovda: `Authorization: Bearer <access>` |
| `refresh` | 7 kun | `access` eskirganda yangisini olish |

`access` eskirsa server `401` qaytaradi → `POST /api/auth/refresh/` bilan yangilang.

### Til

O'zbekcha (standart) yoki ruscha. Ikki usul:
- `?lang=ru` parametri
- `Accept-Language: ru` sarlavhasi

Ruscha matn bo'sh bo'lsa, o'zbekchasi qaytadi. Xato xabarlari ham shu tilda.

### Sahifalash

Ro'yxatlar sahifalarga bo'lingan (`?page=2`):

```json
{ "count": 99, "next": "…?page=3", "previous": "…?page=1", "results": [ … ] }
```

| Joy | Bir sahifada |
|---|---|
| Mahsulotlar (sayt) | 12 |
| Mening buyurtmalarim | 5 |
| Mahsulot izohlari | 10 |
| Admin jadvallari | 20 (`?page_size=` bilan 200 gacha) |

Kategoriya, brend, banner, filial, to'lov usullari va xodimlar — sahifalanmaydi (oddiy massiv).

### Xatolar

| Kod | Ma'nosi |
|---|---|
| `400` | Noto'g'ri ma'lumot. Javob: `{"maydon": ["xato matni"]}` yoki `{"detail": "…"}` |
| `401` | Kirilmagan yoki token eskirgan |
| `403` | Ruxsat yo'q |
| `404` | Topilmadi |
| `429` | Juda ko'p urinish (`resend_in` — necha soniyadan keyin) |
| `503` | SMS xizmati ishlamayapti |

### So'rovlar cheklovi

| Nima | Chegara |
|---|---|
| SMS kod yuborish | 5 / daqiqa; bitta raqamga kuniga 10; bitta IP'dan kuniga 30 |
| Kodni tekshirish, telefonni almashtirish | 10 / daqiqa |
| Google orqali kirish, xodim kirishi | 10 / daqiqa |
| Izoh yozish | 10 / daqiqa |

---

## 2. Kirish (mijozlar)

Mijoz faqat **telefon + SMS kod** yoki **Google** orqali kiradi. Parol yo'q.

### `POST /api/auth/code/send/` — SMS kod yuborish

```json
{ "phone": "+998 90 123 45 67", "agree": true }
```

`agree` — ommaviy ofertaga rozilik, `true` bo'lishi shart.

Javob:
```json
{ "phone": "+998 90 123 45 67", "expires_in": 120, "resend_in": 60 }
```

- Raqam ro'yxatdan o'tganmi — xavfsizlik uchun aytilmaydi. Yangi hisob ochilgani kodni tasdiqlash javobida (`created`) bilinadi.
- Kod 120 soniya amal qiladi, qayta yuborish 60 soniyadan keyin.
- Sinov rejimida (DEBUG va Eskiz sozlanmagan) javobda `debug_code` ham keladi.

### `POST /api/auth/code/verify/` — kodni tasdiqlash va kirish

```json
{ "phone": "+998 90 123 45 67", "code": "123456" }
```

Javob:
```json
{ "access": "…", "refresh": "…", "created": false }
```

`created: true` — yangi hisob ochildi (profilni to'ldirishga yo'naltiring).
5 marta xato kiritilsa kod bekor bo'ladi; xatoda `attempts_left` qaytadi.

### `POST /api/auth/google/` — Google orqali kirish

```json
{ "credential": "<Google ID token>" }
```

Javob: `{ "access", "refresh", "created" }`. Email bo'yicha mavjud hisobga bog'lanadi yoki yangisi ochiladi.
`GOOGLE_CLIENT_ID` sozlanmagan bo'lsa `400`.

### `POST /api/auth/refresh/` — tokenni yangilash

```json
{ "refresh": "…" }  →  { "access": "…", "refresh": "…" }   // yangi refresh'ni saqlang, eskisi bekor bo'ladi
```

---

## 3. Profil (kirgan foydalanuvchi)

### `GET /api/auth/me/`

```json
{
  "id": 7, "username": "998901234567", "first_name": "Aziz", "last_name": "Karimov",
  "email": "aziz@mail.uz", "phone": "+998 90 123 45 67", "address": "Toshkent, Chilonzor 5",
  "is_staff": false, "is_superuser": false, "permissions": {}, "date_joined": "…"
}
```

### `PATCH /api/auth/me/` — ma'lumotlarni o'zgartirish

O'zgartirsa bo'ladi: `first_name`, `last_name`, `email`, `address`.
`phone` bu yerda o'zgarmaydi (pastga qarang). Email boshqa hisobda band bo'lsa `400`.

### `POST /api/auth/phone/` — telefonni almashtirish yoki qo'shish

Avval yangi raqamga `POST /api/auth/code/send/` bilan kod yuboriladi, keyin:

```json
{ "phone": "+998 93 000 00 00", "code": "123456" }  →  { "phone": "+998 93 000 00 00" }
```

Raqam boshqa mijozda bo'lsa `400`.

---

## 4. Katalog (hamma uchun)

### `GET /api/categories/`

Faqat yuqori darajadagi kategoriyalar, ichida `children` (3 darajagacha).
`GET /api/categories/<slug>/` — bitta kategoriya.

```json
[{ "id": 1, "name": "Maishiy texnika", "slug": "maishiy-texnika", "icon": "…", "parent": null, "children": [ … ] }]
```

### `GET /api/brands/` va `GET /api/brands/<slug>/`

```json
[{ "id": 3, "name": "Samsung", "slug": "samsung", "logo": "…" }]
```

### `GET /api/banners/`

Faqat faol bannerlar: `id, title, subtitle, image, link`.

### `GET /api/products/` — mahsulotlar ro'yxati

Faqat faol mahsulotlar. Parametrlar:

| Parametr | Misol | Ma'nosi |
|---|---|---|
| `category` | `televizorlar` | Kategoriya va uning ichidagilari |
| `brand` | `samsung,lg` | Brend slug'lari (vergul bilan) |
| `price_min`, `price_max` | `1000000` | Narx oralig'i |
| `discount` | `true` | Faqat chegirmadagilar |
| `is_hit`, `is_new` | `true` | Xit / yangi |
| `search` | `muzlatgich` | Nomi, tavsifi, brendi, kodi bo'yicha. Kirillcha so'z lotinchadan ham qidiriladi |
| `ordering` | `price`, `-price`, `-created_at`, `name` | Saralash |

Ro'yxatdagi bitta mahsulot:
```json
{
  "id": 12, "name": "Samsung UE55", "slug": "samsung-ue55", "price": "8290000", "old_price": "8990000",
  "discount_percent": 7, "monthly_price": 690833, "stock": 5, "image": "…",
  "brand": { "id": 3, "name": "Samsung", "slug": "samsung", "logo": "…" },
  "category": "televizorlar", "is_hit": true, "is_new": false
}
```

### `GET /api/products/<slug>/` — mahsulot sahifasi

Yuqoridagilar + `sku`, `description`, `images` (`[{id, image}]`), `specs` (`[{name, value}]`).

### `GET /api/products/<slug>/similar/`

O'xshash 10 ta mahsulot (avval shu kategoriya va brend, keyin narxi yaqini; faqat sotuvda borlari).

---

## 5. Izohlar

### `GET /api/products/<slug>/comments/`

Yashirilmagan izohlar va ularga javoblar, 10 tadan. Javobda `summary` ham bor: o'rtacha baho (`rating`) va baholar soni (`ratings_count`).
Muallif nomi: ism-familiya; bo'lmasa "Xaridor" (do'kon javobi — "Narel"). Telefon yoki login hech qachon ko'rinmaydi.

### `POST /api/products/<slug>/comments/` — izoh yoki javob yozish (kirgan foydalanuvchi)

```json
{ "text": "Zo'r mahsulot", "rating": 5 }          // yangi izoh (baho 1–5, ixtiyoriy)
{ "text": "Rahmat!", "parent": 41 }                // javob
```

### `DELETE /api/comments/<id>/` — o'z izohini o'chirish

---

## 6. Buyurtmalar (kirgan mijoz)

### `GET /api/orders/` — mening buyurtmalarim

Yangisidan eskisiga, 5 tadan (`?page=2` — keyingi 5 ta).

### `GET /api/orders/<id>/` — bitta buyurtma

### `POST /api/orders/` — buyurtma berish

```json
{
  "cart": [{ "product": 12, "quantity": 1 }, { "product": 40, "quantity": 2 }],
  "payment_method": "cash",
  "delivery_method": "courier",
  "address": "Toshkent, Chilonzor 5",
  "note": "Kechqurun qo'ng'iroq qiling"
}
```

| Maydon | Izoh |
|---|---|
| `cart` | Majburiy. Faqat faol mahsulotlar; omborda yetmasa `400` |
| `payment_method` | Faol to'lov usuli kodi (`GET /api/payment-methods/`) |
| `delivery_method` | `courier` (kuryer) yoki `pickup` (olib ketish) |
| `address` | Kamida 5 belgi. Yuborilmasa profildagi manzil olinadi; u ham bo'lmasa `400` |
| `pickup_branch` | Olib ketishda majburiy — filial `id` (`GET /api/store-settings/` → `branches`) |
| `full_name`, `phone` | Ixtiyoriy. Yuborilmasa profildan olinadi; profilda ham bo'lmasa `400` |

Narx, yetkazish narxi va jami summa serverda hisoblanadi. Mahsulotlar ombordan darhol ayriladi.

Javobdagi asosiy maydonlar:
`id, status, status_display, total, delivery_price, expected_date, original_expected_date, delay_note, is_delayed, pickup_branch_info, items, created_at`.

**Holatlar (`status`):** `new` → `confirmed` → `shipped` → `delivered`, yoki `cancelled`.
`is_delayed: true` — yetkazish sanasi va'da qilingandan surilgan yoki o'tib ketgan.

---

## 6.1. Sevimlilar va savat (kirgan mijoz)

Serverda saqlanadi — sayt va ilovada bir xil. Nofaol (yashirilgan) mahsulotlar ro'yxatlarda chiqmaydi.

| Endpoint | Usul | Ma'nosi |
|---|---|---|
| `favorites/` | GET | Sevimlilar (mahsulot kartochkalari, yangisi birinchi) |
| `favorites/` | POST `{"product": 12}` | Qo'shish; javobda to'liq ro'yxat |
| `favorites/<product_id>/` | DELETE | Olib tashlash (204) |
| `favorites/sync/` | POST `{"products": [12, 40]}` | Kirgandan keyin bir marta: qurilmadagilarni qo'shib, to'liq ro'yxatni qaytaradi |
| `cart/` | GET | Savat |
| `cart/` | PUT `{"items": [{"product": 12, "quantity": 2}]}` | Savatni to'liq almashtirish (`[]` — tozalash) |
| `cart/add/` | POST `{"product": 12, "quantity": 1}` | Qo'shish (bor bo'lsa soni oshadi) |
| `cart/<product_id>/` | DELETE | Olib tashlash |
| `cart/sync/` | POST `{"items": […]}` | Kirgandan keyin bir marta: qurilmadagi savat bilan birlashtirish (kattaroq son olinadi) |

Savat javobi:
```json
{
  "items": [{ "product": { "id": 12, "name": "…", "price": "8290000", "stock": 5, … }, "quantity": 2, "available": true }],
  "total": 16580000, "count": 1
}
```

Son ombordagidan oshmaydi; `available: false` — omborda so'ralgancha qolmagan.

## 7. Do'kon ma'lumotlari (hamma uchun)

### `GET /api/store-settings/`

```json
{
  "delivery_enabled": true, "delivery_price": "30000", "delivery_days": 1, "delivery_note": "Toshkent bo'ylab 1 kunda",
  "pickup_enabled": true, "phone": "+998 71 000 00 00", "address": "…", "working_hours": "…", "map_url": "…",
  "branches": [{ "id": 1, "name": "Chilonzor filiali", "address": "…", "phone": "…", "working_hours": "…", "map_url": "…" }],
  "google_client_id": "…", "sms_test_mode": false
}
```

### `GET /api/payment-methods/` va `GET /api/payment-methods/<code>/`

Faqat faol usullar: `code, title, description, logo, months` (`months` — faqat muddatli to'lovda).
Maxfiy kalitlar hech qachon chiqmaydi.

### `GET /api/offer/` — ommaviy oferta

```json
{ "text": "# 1. Umumiy qoidalar\n…", "updated_at": "…" }
```

Bo'limlar `# ` bilan boshlanadi.

---

## 8. Admin panel API (`{ADMIN}` = `/api/admin/`)

### Kirish (faqat xodimlar)

`POST /api/auth/login/`
```json
{ "username": "<login, email yoki telefon>", "password": "…" }  →  { "access": "…", "refresh": "…" }
```

Mijozlar bu yo'l bilan kira olmaydi. Xodimning ruxsatlari: `GET /api/auth/me/` → `permissions`.

### Ruxsatlar

Har bir bo'limga alohida ruxsat: `view` (ko'rish), `add` (qo'shish), `change` (tahrirlash), `delete` (o'chirish).
Superuser hammasiga kira oladi. Ruxsat bo'lmasa `403`.

| HTTP | Kerakli ruxsat |
|---|---|
| `GET` | `view` |
| `POST` | `add` |
| `PUT`, `PATCH` | `change` |
| `DELETE` | `delete` |

### Endpoint'lar

| Manzil | Usullar | Bo'lim | Izoh |
|---|---|---|---|
| `{ADMIN}stats/` | GET | dashboard | Bugun/oy/jami tushum, holatlar soni, kam qolgan mahsulotlar, top-5, 30 kunlik grafik, oxirgi buyurtmalar |
| `{ADMIN}image-rules/` | GET | har qanday xodim | Rasm o'lchami/formati talablari |
| `{ADMIN}products/` | CRUD | products | Filtr: `category, brand, is_active, is_hit, is_new, low_stock=true`; `search`; `ordering`: `name, price, stock, created_at, sold` |
| `{ADMIN}products/<id>/upload/` | POST, DELETE | products | Asosiy rasm (multipart `file`) |
| `{ADMIN}products/<id>/images/` | POST | products | Galereyaga rasm qo'shish (multipart `file`) |
| `{ADMIN}product-images/<id>/` | DELETE | products (change) | Galereyadan rasm o'chirish |
| `{ADMIN}categories/` | CRUD | categories | `<id>/upload/` — ikonka |
| `{ADMIN}brands/` | CRUD | brands | `<id>/upload/` — logo; `search` |
| `{ADMIN}banners/` | CRUD | banners | `<id>/upload/` — rasm |
| `{ADMIN}orders/` | GET, PATCH | orders | Filtr: `status, payment_method, delivery_method, user, created_at__date__gte/lte`; `search` (raqam, ism, telefon); `ordering`: `created_at, total` |
| `{ADMIN}customers/` | GET | customers | Faqat mijozlar. `search` (ism, email, telefon); `ordering`: `date_joined, orders_count, total_spent` |
| `{ADMIN}comments/` | GET, PATCH, DELETE | comments | `kind=reviews/replies/low/unanswered`; filtr `is_hidden, product, rating, parent`; PATCH faqat `is_hidden` |
| `{ADMIN}comments/<id>/reply/` | POST | comments (add) | Do'kon nomidan javob: `{"text": "…"}` |
| `{ADMIN}staff/` | CRUD | staff | Xodimlar; `staff/sections/` — bo'limlar va amallar ro'yxati |
| `{ADMIN}payment-methods/` | GET, PATCH | settings | Maxfiy kalitlar qaytmaydi; bo'sh yuborilsa eskisi saqlanadi |
| `{ADMIN}store-settings/` | GET, PATCH | settings | Yetkazish, aloqa, oferta matni |
| `{ADMIN}branches/` | CRUD | settings | Filiallar; oxirgi faol filialni o'chirib bo'lmaydi |
| `{ADMIN}integrations/` | GET, PATCH | settings | SMS (Eskiz) va Google kalitlari, yo'riqnomalar, SMS holati/balansi, oxirgi 15 ta SMS. `eskiz_password` qaytmaydi; bo'sh yuborilsa eskisi qoladi |
| `{ADMIN}integrations/sms-check/` | POST | settings (change) | Eskiz'ga ulanib balansni tekshirish |
| `{ADMIN}integrations/sms-test/` | POST | settings (change) | Sinov SMS: `{"phone": "+998 …"}` |

### Buyurtma holatini o'zgartirish

`PATCH {ADMIN}orders/<id>/` — faqat `status`, `expected_date`, `delay_note`:

- Kuryer buyurtmasini qabul qilishda (`new` → `confirmed`/`shipped`) `expected_date` majburiy; u "va'da qilingan sana" bo'lib saqlanadi.
- Sana keyinga surilsa buyurtma "kechikkan" bo'ladi; `delay_note` — ixtiyoriy sabab (mijozga ko'rinadi).
- O'tgan sanani tanlab bo'lmaydi; yakunlangan buyurtma sanasi o'zgarmaydi.
- `cancelled` bo'lganda mahsulotlar omborga qaytadi. Bekor qilinganni qayta tiklab bo'lmaydi.

### O'chirish = yashirish

Admin panelda mahsulot, kategoriya yoki brend o'chirilsa (`DELETE`), bazadan o'chmaydi — `deleted_at` belgilanadi:
saytda, mobil ilovada va admin panelda ko'rinmaydi, lekin **buyurtmalar, izohlar va tarix saqlanadi**.
Django admin'da "o'chirilganmi" filtri va **"Qaytarish"** amali bor.

- Kategoriya ichki kategoriyalari bilan yashiriladi; ichida mahsulot bo'lsa — `400`.
- Brendda mahsulot bo'lsa — `400`.
- Buyurtma qatorida mahsulot nomi buyurtma paytidagicha saqlanadi (`product_name`); mahsulot o'chirilgan
  yoki yashirilgan bo'lsa `product_slug: null` (havola berilmaydi).

---

## 9. Django admin (`/admin/`)

Zaxira va texnik panel — barcha 14 model shu yerda: mahsulotlar (rasm, xususiyatlar), kategoriyalar, brendlar,
bannerlar, buyurtmalar, filiallar, do'kon sozlamalari, mijoz profillari, SMS kodlar, to'lov usullari, izohlar,
xodim profillari, foydalanuvchilar, guruhlar.

- Kirish: faqat superuser (yoki Django ruxsati berilgan xodim). Yangi superuser: `python manage.py createsuperuser`.
- Buyurtmada React admin bilan bir xil qoidalar: bekor qilinganda ombor qaytadi, qayta tiklanmaydi,
  mahsulot soni o'zgartirilsa ombor va jami summa avtomatik qayta hisoblanadi, omborda yetmasa saqlanmaydi.
- SMS kodlar faqat ko'riladi (kodning o'zi saqlanmaydi). Mijoz kunlik limitga yetsa, uning yozuvlarini o'chirib limitni bo'shatish mumkin.

---

## 10. SMS va Google (admin panelda sozlanadi)

Admin panel → **Sozlamalar → Integratsiyalar**. Har biri yo'riqnoma bilan:

- **SMS (Eskiz.uz)**: login, parol, jo'natuvchi nomi, balans ogohlantirishi, Android'da kodni avtomatik to'ldirish domeni.
  "Ulanishni tekshirish" (balans) va "Sinov SMS" tugmalari. Eskiz'da moderatsiyaga beriladigan matnlar nusxa olishga tayyor holda ko'rsatiladi.
- **Google orqali kirish**: sayt Client ID'si, mobil ilovalar uchun iOS va Android Client ID'lari.

Har bir SMS tarixga yoziladi (kod "******" bilan yashiriladi): holati, Eskiz ID, xato sababi.
Balans kam qolsa yoki Eskiz'ga ulanib bo'lmasa — admin bosh sahifasida ogohlantirish.
Admin panelda bo'sh qoldirilgan maydon o'rniga `.env` dagi qiymat ishlatiladi.

## 11. Xavfsizlik

| Himoya | Qanday |
|---|---|
| Xodim parolini tanlab buzish | 15 daqiqada bitta login uchun 5 ta (bitta IP'dan 20 ta) noto'g'ri urinishdan keyin 15 daqiqa blok (`429`). Django admin'da ham. Daqiqasiga 10 ta so'rov |
| Tokenlar | `access` 1 soat, `refresh` 7 kun. Har yangilashda **yangi refresh** qaytadi va eskisi bekor bo'ladi. `POST auth/logout/ {"refresh"}` — chiqishda bekor qilish |
| SMS kod | Bazada xeshi; 2 daqiqa, 5 urinish, raqamga kuniga 10, IP'dan kuniga 30. Raqam ro'yxatdan o'tganmi — aytilmaydi |
| Google | Faqat egasi tasdiqlangan emailga bog'lanadi (Google orqali ochilgan). Profilda qo'lda yozilgan emailga bog'lanmaydi |
| IP | `NUM_PROXIES` — nginx ortida 1. Aks holda `X-Forwarded-For` e'tiborga olinmaydi (soxtalashtirib bo'lmaydi) |
| HTTPS | Serverda majburiy: yo'naltirish, HSTS, xavfsiz cookie, `X-Frame-Options: DENY` |
| Maxfiy kalitlar | API orqali qaytmaydi; Django admin'da ham `********` |

### Harakatlar jurnali

Django admin → **Xavfsizlik → Harakatlar jurnali** (faqat superuser; API va React admin'da yo'q, o'zgartirib/o'chirib bo'lmaydi):

- kim kirdi / chiqdi / kira olmadi (xodim — login-parol, mijoz — SMS yoki Google), qaysi IP va qurilmadan;
- kim nima qildi: React admin va Django admin'dagi har bir qo'shish, o'zgartirish, o'chirish
  (bo'lim, yozuv ID, yuborilgan ma'lumot, natija kodi); mijozning buyurtma, izoh, profil o'zgarishlari;
- parol, kod, token va kalitlar yozilmaydi (`***`). Ko'rish (GET), savat va sevimlilar yozilmaydi.

Eski yozuvlarni tozalash (cron bilan kuniga bir marta): `python manage.py prune_audit` (`AUDIT_KEEP_DAYS`, sukut 365 kun).

### Serverga chiqarishdan oldin

1. `SECRET_KEY` — yangi tasodifiy kalit (bo'lmasa sayt ishga tushmaydi), `DEBUG=False`, `ALLOWED_HOSTS` — domen.
2. nginx orqasida: `NUM_PROXIES=1` va nginx'da `proxy_set_header X-Forwarded-For $remote_addr; proxy_set_header X-Forwarded-Proto $scheme;`.
3. HTTPS sertifikati (masalan Let's Encrypt). `CSRF_TRUSTED_ORIGINS=https://domen`.
4. `DJANGO_ADMIN_URL` — o'zgacha nom. Superuser paroli kuchli bo'lsin.
5. `python manage.py migrate` va `python manage.py check --deploy`.
6. Bir nechta worker bo'lsa — `REDIS_URL`.

## 12. Sozlamalar (`backend/.env`)

| O'zgaruvchi | Vazifasi |
|---|---|
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Django asosiy sozlamalari |
| `NUM_PROXIES`, `HTTPS`, `SECURE_HSTS_SECONDS`, `CSRF_TRUSTED_ORIGINS`, `DJANGO_ADMIN_URL` | Server xavfsizligi (11-bo'lim) |
| `REDIS_URL`, `AUDIT_KEEP_DAYS` | Kesh va harakatlar jurnali |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | Ma'lumotlar bazasi |
| `CORS_ALLOWED_ORIGINS` | Sayt va admin manzillari |
| `GOOGLE_CLIENT_ID` | Google orqali kirish (zaxira — odatda admin panelda kiritiladi) |
| `ESKIZ_EMAIL`, `ESKIZ_PASSWORD`, `ESKIZ_FROM`, `ESKIZ_LOW_BALANCE`, `SMS_OTP_DOMAIN` | SMS (zaxira — odatda admin panelda kiritiladi) |

Namuna: `backend/.env.example`.
