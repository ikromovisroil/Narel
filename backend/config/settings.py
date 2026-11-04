import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_list(name, default=""):
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "catalog",
    "orders",
    "dashboard",
    "payments",
    "staff",
    "comments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "shop"),
        "USER": os.getenv("POSTGRES_USER", "shop"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "shop"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
# Django/DRF xabarlari tili (Accept-Language bo'yicha)
LANGUAGES = [("uz", "O'zbekcha"), ("ru", "Русский")]
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    # Izoh yozish: bir foydalanuvchi daqiqasiga 10 tagacha
    "DEFAULT_THROTTLE_RATES": {"comments": "10/min", "password": "10/min", "otp": "5/min", "otp_verify": "10/min"},
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Swagger (/api/docs/). DEBUG'da hamma uchun ochiq, serverda — faqat /admin/ ga kirgan xodim
SPECTACULAR_SETTINGS = {
    "TITLE": "Narel API",
    "DESCRIPTION": (
        "Narel internet-do'koni API'si. To'liq izohlar: docs/API.md. "
        "Token olish: mijoz — /api/auth/code/send/ + /api/auth/code/verify/, xodim — /api/auth/login/. "
        "Keyin yuqoridagi **Authorize** tugmasiga `access` tokenni kiriting."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # CDN versiyalari qotirilgan (redoc@latest ESM'ga o'tgan va sahifa bo'sh chiqadi)
    "SWAGGER_UI_DIST": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.20.0",
    "SWAGGER_UI_FAVICON_HREF": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.20.0/favicon-32x32.png",
    "REDOC_DIST": "https://cdn.jsdelivr.net/npm/redoc@2.5.0",
    "PREPROCESSING_HOOKS": ["config.schema.only_v1"],
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "config.schema.tag_by_path",
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v1/",
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": True, "displayRequestDuration": True, "filter": True},
    "TAGS": [
        {"name": "auth", "description": "Kirish, tokenlar, profil"},
        {"name": "catalog", "description": "Kategoriya, brend, banner, mahsulotlar"},
        {"name": "orders", "description": "Mijoz buyurtmalari (berilgan mahsulotlar savatdan avtomatik chiqadi)"},
        {"name": "account", "description": "Sevimlilar va savat — serverda, sayt va ilovada bir xil"},
        {"name": "comments", "description": "Mahsulot izohlari"},
        {"name": "store", "description": "Do'kon ma'lumotlari, to'lov usullari, oferta"},
        {"name": "admin", "description": "Admin panel API (xodimlar, bo'lim ruxsatlari bilan)"},
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Xodimlar jadvalidagi "Oxirgi kirish" ustuni uchun
    "UPDATE_LAST_LOGIN": True,
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

# Kirish: login, email yoki telefon raqami bilan
AUTHENTICATION_BACKENDS = ["orders.auth.LoginEmailPhoneBackend"]

# Google orqali kirish: Google Cloud Console -> OAuth Client ID (Web). Bo'sh bo'lsa tugma ko'rinmaydi.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()


# SMS (Eskiz.uz). Bo'sh bo'lsa va DEBUG=True — test rejimi: kod konsolga chiqadi.
ESKIZ_EMAIL = os.getenv("ESKIZ_EMAIL", "").strip()
ESKIZ_PASSWORD = os.getenv("ESKIZ_PASSWORD", "").strip()
ESKIZ_FROM = os.getenv("ESKIZ_FROM", "4546").strip()
# Balans shu qiymatdan kam bo'lsa admin panel bosh sahifasida ogohlantirish chiqadi
ESKIZ_LOW_BALANCE = int(os.getenv("ESKIZ_LOW_BALANCE", "20000") or 0)
# Android Chrome kodni o'zi to'ldirishi uchun sayt domeni (masalan narel.uz). Bo'sh — o'chiq.
# Diqqat: domen qo'shilsa SMS matni o'zgaradi — Eskiz kabinetida yangi matnni ham moderatsiyadan o'tkazing.
SMS_OTP_DOMAIN = os.getenv("SMS_OTP_DOMAIN", "").strip().removeprefix("https://").removeprefix("http://").strip("/")
