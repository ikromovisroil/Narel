# TechShop

Elektronika va maishiy texnika onlayn do'koni: Django REST API + React (Vite) + PostgreSQL.

| Qism | Papka | Manzil |
|---|---|---|
| Mijozlar sayti | `frontend/` | http://localhost:5173 |
| Admin panel (xodimlar uchun) | `admin/` | http://localhost:5174 |
| API | `backend/` | http://127.0.0.1:8010/api/ |

## Imkoniyatlar

- Ko'p darajali katalog (kategoriya → ichki kategoriya), brendlar
- Mahsulot: bir nechta rasm, xususiyatlar jadvali, chegirma (eski narx), 12 oylik muddatli to'lov narxi
- Qidiruv, narx/brend/chegirma bo'yicha filtr, saralash, sahifalash
- Savat va saralanganlar (brauzerda saqlanadi)
- Ro'yxatdan o'tish / kirish (JWT)
- Buyurtma: yetkazish usuli, to'lov usuli (naqd, karta, muddatli), ombor qoldig'i tekshiruvi
- Alohida admin panel (React + Ant Design):
  - Bosh sahifa: bugungi/oylik savdo, 30 kunlik grafik, eng ko'p sotilganlar, kam qolgan mahsulotlar
  - Buyurtmalar: filtr, tafsilotlar, holatni o'zgartirish, bekor qilganda ombor tiklanadi
  - Mahsulotlar: qo'shish/tahrirlash, xususiyatlar, asosiy rasm va galereya
  - Kategoriyalar (daraxt), brendlar, bannerlar, mijozlar

## Ishga tushirish

### 1. Ma'lumotlar bazasi (Docker)

```bash
docker compose up -d
```

PostgreSQL `localhost:5433` portida ishlaydi.

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env        # SECRET_KEY ni o'zgartiring
venv\Scripts\python manage.py migrate
venv\Scripts\python manage.py seed             # demo mahsulotlar
venv\Scripts\python manage.py seed --orders 40 # + dashboard uchun demo buyurtmalar
venv\Scripts\python manage.py createsuperuser  # admin panelga kirish uchun
venv\Scripts\python manage.py runserver 127.0.0.1:8010
```

Django'ning standart admini ham ishlaydi: http://127.0.0.1:8010/admin/

Testlar: `venv\Scripts\python manage.py test`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Sayt: http://localhost:5173 (`/api` va `/media` so'rovlari backendga proxy qilinadi).

### 4. Admin panel

```bash
cd admin
npm install
npm run dev
```

http://localhost:5174 — `createsuperuser` bilan yaratilgan (yoki `is_staff` belgisi bor) hisob bilan kiriladi.

## API

| Endpoint | Tavsif |
|---|---|
| `GET /api/categories/` | Kategoriyalar daraxti |
| `GET /api/brands/` | Brendlar |
| `GET /api/banners/` | Bosh sahifa bannerlari |
| `GET /api/products/?category=&brand=a,b&price_min=&price_max=&discount=true&search=&ordering=` | Mahsulotlar |
| `GET /api/products/<slug>/` | Mahsulot tafsilotlari |
| `POST /api/auth/register/`, `POST /api/auth/login/`, `POST /api/auth/refresh/`, `GET /api/auth/me/` | Avtorizatsiya |
| `GET/POST /api/orders/` | Foydalanuvchi buyurtmalari |
| `/api/admin/...` | Admin API (faqat xodimlar): `stats`, `products`, `categories`, `brands`, `banners`, `orders`, `customers`; rasm uchun `POST <id>/upload/` |

Do'kon nomi `frontend/src/api.js` faylidagi `SHOP_NAME` da.
