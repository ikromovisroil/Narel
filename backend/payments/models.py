from django.db import models

# Har bir to'lov usuli uchun kerakli sozlamalar va admin uchun izohlar.
#   secret=True   — maxfiy qiymat: API orqali hech qachon qaytarilmaydi.
#   required=True — usulni yoqishdan oldin to'ldirilishi shart.
#   hint          — maydon ostida ko'rinadigan qisqa izoh.
#   about         — usul nima ekanligi (sozlash oynasida).
#   where         — kalitlar qayerdan olinadi (qadamlar).
PROVIDERS = {
    "cash": {
        "about": "Mijoz buyurtmani qabul qilganda kuryerga yoki do'konda naqd pul bilan to'laydi.",
        "where": [],
        "fields": [],
    },
    "card": {
        "about": "Mijoz buyurtmani qabul qilganda kuryerning terminali orqali Uzcard yoki Humo kartasi bilan to'laydi. "
                 "Kuryerlarda terminal bo'lishi kerak.",
        "where": [],
        "fields": [],
    },
    "click": {
        # Manba: business.click.uz (2026-11 tekshirilgan)
        "contacts": [
            {"label": "Ulanish uchun ariza", "value": "click.uz/ru/register", "url": "https://click.uz/ru/register"},
            {"label": "Merchant kabineti", "value": "merchant.click.uz", "url": "https://merchant.click.uz"},
            {"label": "Dasturchilar hujjatlari", "value": "docs.click.uz", "url": "https://docs.click.uz"},
            {"label": "Qo'llab-quvvatlash", "value": "+998 71 231 08 80", "url": "tel:+998712310880"},
            {"label": "Email", "value": "info@click.uz", "url": "mailto:info@click.uz"},
        ],
        "documents": [
            "Direktor pasporti nusxasi",
            "Korxona guvohnomasi",
            "Istalgan bankdagi hisob raqami va MFO",
        ],
        "about": "Mijoz saytda Click orqali onlayn to'laydi (Click ilovasi yoki karta bilan).",
        "where": [
            "Click bilan shartnoma tuzing (yuridik shaxs yoki YaTT nomidan).",
            "Click merchant kabinetiga kiring va xizmat (servis) yarating.",
            "Kabinetdagi Service ID, Merchant ID, Merchant user ID va Secret key ni shu yerga ko'chiring.",
        ],
        "fields": [
            {"key": "service_id", "label": "Service ID", "required": True,
             "hint": "Click kabinetidagi xizmat raqami"},
            {"key": "merchant_id", "label": "Merchant ID", "required": True,
             "hint": "Do'koningizning Click'dagi raqami"},
            {"key": "merchant_user_id", "label": "Merchant user ID", "required": True,
             "hint": "Click kabinetidagi foydalanuvchi raqami"},
            {"key": "secret_key", "label": "Secret key", "required": True, "secret": True,
             "hint": "Maxfiy kalit. Hech kimga bermang"},
        ],
    },
    "payme": {
        # Manba: business.help.paycom.uz (2026-11 tekshirilgan)
        "contacts": [
            {"label": "Payme Business qo'llanmasi", "value": "business.help.paycom.uz", "url": "https://business.help.paycom.uz"},
            {"label": "Dasturchilar hujjatlari", "value": "developer.help.paycom.uz", "url": "https://developer.help.paycom.uz"},
            {"label": "Call-markaz", "value": "1350", "url": "tel:1350"},
            {"label": "Telefon", "value": "+998 71 150 22 24", "url": "tel:+998711502224"},
            {"label": "Email", "value": "info@payme.uz", "url": "mailto:info@payme.uz"},
        ],
        "documents": [],
        "about": "Mijoz saytda Payme orqali onlayn to'laydi (Payme ilovasi yoki karta bilan).",
        "where": [
            "Payme bilan shartnoma tuzing (yuridik shaxs yoki YaTT nomidan).",
            "Payme Business kabinetida kassa yarating.",
            "Kassa sozlamalaridan kassa ID (Merchant ID) va kassa kalitini oling.",
            "Sinab ko'rish uchun test kaliti ham beriladi — uni \"Test kaliti\" maydoniga yozing.",
        ],
        "fields": [
            {"key": "merchant_id", "label": "Merchant ID (kassa ID)", "required": True,
             "hint": "Payme Business kabinetidagi kassa raqami"},
            {"key": "secret_key", "label": "Kassa kaliti", "required": True, "secret": True,
             "hint": "Haqiqiy to'lovlar uchun kalit"},
            {"key": "test_key", "label": "Test kaliti (sandbox)", "secret": True,
             "hint": "Sinov rejimida ishlatiladi. Majburiy emas"},
        ],
    },
    "paynet": {
        # Manba: paynet.uz (2026-11 tekshirilgan)
        "contacts": [
            {"label": "Hamkorlar uchun", "value": "paynet.uz/uz/for-partners", "url": "https://paynet.uz/uz/for-partners"},
            {"label": "Aloqa", "value": "paynet.uz/uz/contacts", "url": "https://paynet.uz/uz/contacts"},
            {"label": "Telefon", "value": "+998 71 202 07 07", "url": "tel:+998712020707"},
            {"label": "Hamkorlik bo'yicha email", "value": "marketing@paynet.uz", "url": "mailto:marketing@paynet.uz"},
        ],
        "documents": [],
        "about": "Mijoz buyurtma raqamini Paynet ilovasi yoki Paynet shoxobchasida kiritib to'laydi.",
        "where": [
            "Paynet bilan shartnoma tuzing.",
            "Ulanish ma'lumotlarini (Service ID, login, parol) Paynet menejeri beradi.",
        ],
        "fields": [
            {"key": "service_id", "label": "Service ID", "required": True,
             "hint": "Paynet bergan xizmat raqami"},
            {"key": "username", "label": "Login", "required": True,
             "hint": "Paynet bergan login"},
            {"key": "password", "label": "Parol", "required": True, "secret": True,
             "hint": "Paynet bergan parol"},
        ],
    },
    "uzum": {
        "contacts": [
            {"label": "Rasmiy sayt", "value": "uzumbank.uz", "url": "https://uzumbank.uz"},
        ],
        "contacts_note": "Onlayn do'konlar uchun ulanish sahifasi rasmiy saytda topilmadi. "
                         "Uzum Bank qo'llab-quvvatlash xizmati yoki Uzum Business ilovasi orqali internet-ekvayring haqida so'rang.",
        "documents": [],
        "about": "Mijoz saytda Uzum Bank orqali onlayn to'laydi.",
        "where": [
            "Uzum Bank bilan internet-ekvayring shartnomasini tuzing.",
            "Terminal ID va API kalitni Uzum Bank beradi.",
        ],
        "fields": [
            {"key": "terminal_id", "label": "Terminal ID", "required": True,
             "hint": "Uzum Bank bergan terminal raqami"},
            {"key": "api_key", "label": "API kalit", "required": True, "secret": True,
             "hint": "Uzum Bank bergan maxfiy kalit"},
        ],
    },
    "installment": {
        "contacts": [
            {"label": "Uzum Nasiya (rasmiy sayt)", "value": "uzum.uz", "url": "https://uzum.uz"},
            {"label": "Hamkorlar ilovasi", "value": "Uzum Nasiya Business", "url": "https://apps.apple.com/us/app/id1634143199"},
        ],
        "contacts_note": "Boshqa nasiya xizmati bilan ishlasangiz (masalan, Alif), uning hamkorlar bo'limiga murojaat qiling.",
        "documents": [],
        "about": "Mijoz mahsulotni bo'lib to'lash (nasiya) orqali oladi. Pulni do'konga nasiya xizmati to'laydi, "
                 "mijoz esa nasiya xizmatiga oylik to'lab boradi. Yoqilsa saytda \"× N oy\" narxlari ko'rinadi.",
        "where": [
            "Nasiya xizmati bilan hamkorlik shartnomasini tuzing (masalan, Uzum Nasiya, Alif).",
            "Merchant ID va API kalitni o'sha xizmat beradi.",
            "\"Muddat (oy)\" — saytda ko'rsatiladigan oylar soni, masalan 12.",
        ],
        "fields": [
            {"key": "provider", "label": "Nasiya xizmati", "required": True,
             "hint": "Masalan: Uzum Nasiya"},
            {"key": "merchant_id", "label": "Merchant ID", "required": True,
             "hint": "Nasiya xizmati bergan do'kon raqami"},
            {"key": "api_key", "label": "API kalit", "required": True, "secret": True,
             "hint": "Nasiya xizmati bergan maxfiy kalit"},
            {"key": "months", "label": "Muddat (oy)", "required": True,
             "hint": "Saytda \"8 290 000 so'm ÷ N oy\" shu son bilan hisoblanadi"},
        ],
    },
}


class PaymentMethod(models.Model):
    code = models.CharField("Kod", max_length=20, unique=True)
    title = models.CharField("Nomi", max_length=100)
    title_ru = models.CharField("Nomi (ruscha)", max_length=100, blank=True)
    description = models.CharField("Izoh", max_length=200, blank=True)
    description_ru = models.CharField("Izoh (ruscha)", max_length=200, blank=True)
    logo = models.ImageField("Logo", upload_to="payments/", blank=True)
    is_active = models.BooleanField("Faol", default=False)
    test_mode = models.BooleanField("Sinov rejimi", default=True)
    config = models.JSONField("Sozlamalar", default=dict, blank=True)
    order = models.PositiveIntegerField("Tartib", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "To'lov usuli"
        verbose_name_plural = "To'lov usullari"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def provider(self):
        return PROVIDERS.get(self.code, {})

    @property
    def fields(self):
        return self.provider.get("fields", [])

    @property
    def missing_fields(self):
        return [f["label"] for f in self.fields if f.get("required") and not str(self.config.get(f["key"], "")).strip()]

    @property
    def is_configured(self):
        return not self.missing_fields

    @classmethod
    def active_codes(cls):
        return set(cls.objects.filter(is_active=True).values_list("code", flat=True))
