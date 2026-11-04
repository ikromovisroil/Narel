"""Tashqi xizmatlar sozlamalari: admin panelda kiritilgani, bo'lmasa .env dagisi.

Admin paneldagi yo'riqnomalar (GUIDES) ham shu yerda.
"""
from dataclasses import dataclass

from django.conf import settings

from .models import IntegrationSettings


@dataclass
class SmsConfig:
    enabled: bool
    email: str
    password: str
    sender: str
    low_balance: int
    otp_domain: str

    @property
    def configured(self):
        return bool(self.email and self.password)


def clean_domain(value):
    return (value or "").strip().removeprefix("https://").removeprefix("http://").strip("/")


def sms_config():
    s = IntegrationSettings.load()
    return SmsConfig(
        enabled=s.sms_enabled,
        email=(s.eskiz_email or settings.ESKIZ_EMAIL).strip(),
        password=(s.eskiz_password or settings.ESKIZ_PASSWORD).strip(),
        sender=(s.eskiz_from or settings.ESKIZ_FROM or "4546").strip(),
        low_balance=s.sms_low_balance if s.sms_low_balance is not None else settings.ESKIZ_LOW_BALANCE,
        otp_domain=clean_domain(s.sms_otp_domain or settings.SMS_OTP_DOMAIN),
    )


def google_client_id():
    """Sayt uchun Client ID (saytdagi tugma shu bilan ishlaydi)."""
    return (IntegrationSettings.load().google_client_id or settings.GOOGLE_CLIENT_ID).strip()


def google_client_ids():
    """Qabul qilinadigan barcha Client ID'lar: sayt, iOS va Android ilovalar."""
    s = IntegrationSettings.load()
    ids = [s.google_client_id or settings.GOOGLE_CLIENT_ID, s.google_ios_client_id, s.google_android_client_id]
    return {i.strip() for i in ids if i and i.strip()}


SMS_TEXTS = {
    "uz": "Narel: kirish kodi {0}. Hech kimga bermang.",
    "ru": "Narel: код для входа {0}. Никому не сообщайте.",
}


def sms_text(lang, code, domain=""):
    """SMS matni. domain bo'lsa oxirida "@domen #kod" qatori — Android Chrome kodni o'zi to'ldiradi (WebOTP)."""
    text = SMS_TEXTS.get(lang, SMS_TEXTS["uz"]).format(code)
    return f"{text}\n\n@{domain} #{code}" if domain else text


def sms_templates(domain):
    """Eskiz kabinetida moderatsiyaga beriladigan matnlar (kod o'rnida 123456)."""
    return [{"lang": lang, "text": sms_text(lang, "123456", domain)} for lang in SMS_TEXTS]


# Manba: notify.eskiz.uz API hujjati (documenter.getpostman.com/view/663428/RzfmES4z), 2026-11 tekshirilgan
GUIDES = {
    "sms": {
        "title": "SMS (Eskiz.uz)",
        "about": "Mijozlar saytga telefon raqami va SMS kod bilan kiradi. Kodni Eskiz.uz xizmati yuboradi. "
                 "Har bir SMS uchun Eskiz balansidan pul yechiladi.",
        "where": [
            "eskiz.uz saytida ro'yxatdan o'ting va MChJ yoki YaTT nomidan shartnoma tuzing.",
            "my.eskiz.uz kabinetida balansni to'ldiring.",
            "Kabinetdagi \"SMS shablonlar\" bo'limida pastdagi ikkala matnni moderatsiyaga yuboring. "
            "Tasdiqlanmagan matn yuborilmaydi: mijoz \"SMS yuborib bo'lmadi\" xatosini ko'radi.",
            "Kabinetga kiradigan email va parolni (yoki Eskiz bergan maxfiy kalitni) shu yerga kiriting va saqlang.",
            "\"Tekshirish\" tugmasini bosing: ulanish to'g'ri bo'lsa balans ko'rinadi. "
            "Keyin \"Sinov SMS\" bilan o'z raqamingizga kod yuborib ko'ring.",
        ],
        "contacts": {
            "links": [
                {"label": "Rasmiy sayt", "value": "eskiz.uz", "url": "https://eskiz.uz"},
                {"label": "Kabinet", "value": "my.eskiz.uz", "url": "https://my.eskiz.uz"},
                {"label": "API hujjati", "value": "Eskiz API (Postman)",
                 "url": "https://documenter.getpostman.com/view/663428/RzfmES4z"},
            ],
            "documents": [],
            "note": "Shartnoma uchun kerakli hujjatlar va narxlarni Eskiz menejeri aytadi. "
                    "Jo'natuvchi nomini (\"4546\" o'rniga \"Narel\") ro'yxatdan o'tkazish alohida xizmat, Eskiz orqali qilinadi.",
        },
    },
    "google": {
        "title": "Google orqali kirish",
        "about": "Mijoz saytga Google hisobi bilan bir tugmada kiradi. Bepul. Client ID bo'lmasa tugma saytda ko'rinmaydi.",
        "where": [
            "console.cloud.google.com ga kiring va yangi loyiha yarating (masalan, \"Narel\").",
            "\"APIs & Services\" → \"OAuth consent screen\": ilova nomi, email va sayt manzilini to'ldiring, \"External\" ni tanlang.",
            "\"APIs & Services\" → \"Credentials\" → \"Create credentials\" → \"OAuth client ID\", turi \"Web application\".",
            "\"Authorized JavaScript origins\" ga sayt manzilini qo'shing (masalan, https://narel.uz).",
            "Yaratilgan \"Client ID\" ni (…apps.googleusercontent.com bilan tugaydi) shu yerga kiriting. Client secret kerak emas.",
            "Mobil ilova bo'lsa: Credentials'da \"iOS\" va \"Android\" turidagi Client ID'lar ham yarating "
            "(Android uchun ilova paketi nomi va SHA-1 kaliti kerak — ularni mobil dasturchi beradi) va pastdagi maydonlarga kiriting.",
        ],
        "contacts": {
            "links": [
                {"label": "Google Cloud Console", "value": "console.cloud.google.com",
                 "url": "https://console.cloud.google.com/apis/credentials"},
                {"label": "Qo'llanma", "value": "developers.google.com/identity",
                 "url": "https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid"},
            ],
            "documents": [],
            "note": "",
        },
    },
}
