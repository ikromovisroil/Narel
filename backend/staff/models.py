from django.conf import settings
from django.db import models

# Amallar: ko'rish, qo'shish, tahrirlash, o'chirish
ACTIONS = ["view", "add", "change", "delete"]
ALL = ACTIONS
VIEW = ["view"]

# Admin panel bo'limlari va ularda mavjud amallar: (kod, nomi, amallar)
SECTIONS = [
    ("dashboard", "Bosh sahifa (statistika)", VIEW),
    ("orders", "Buyurtmalar", ["view", "change"]),
    ("products", "Mahsulotlar", ALL),
    ("categories", "Kategoriyalar", ALL),
    ("brands", "Brendlar", ALL),
    ("banners", "Bannerlar", ALL),
    ("customers", "Mijozlar", VIEW),
    ("comments", "Izohlar (moderatsiya)", ["view", "change", "delete"]),
    ("staff", "Xodimlar", ALL),
    ("settings", "Sozlamalar (to'lov usullari)", ["view", "change"]),
]

SECTION_CODES = [code for code, _, _ in SECTIONS]
SECTION_ACTIONS = {code: actions for code, _, actions in SECTIONS}


class StaffProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile")
    position = models.CharField("Lavozimi", max_length=100, blank=True)
    # {"products": ["view", "add", "change"], ...}
    permissions = models.JSONField("Ruxsatlar", default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Xodim profili"
        verbose_name_plural = "Xodim profillari"

    def __str__(self):
        return self.user.username


def clean_permissions(raw):
    """Faqat ma'lum bo'lim va amallar qoladi. Har qanday amal "ko'rish"ni ham beradi.
    Eski format ham qabul qilinadi: "view" -> ko'rish, "edit" -> barcha amallar."""
    result = {}
    for code in SECTION_CODES:
        value = (raw or {}).get(code)
        if value == "view":
            value = ["view"]
        elif value == "edit":
            value = list(ACTIONS)
        if not isinstance(value, (list, tuple)):
            continue
        allowed = SECTION_ACTIONS[code]
        chosen = [a for a in ACTIONS if a in value and a in allowed]
        if chosen and "view" not in chosen:
            chosen.insert(0, "view")
        if chosen:
            result[code] = chosen
    return result


def effective_permissions(user):
    """Foydalanuvchining amaldagi ruxsatlari: {bo'lim: [amallar]}."""
    if not user or not user.is_authenticated or not user.is_staff or not user.is_active:
        return {}
    if user.is_superuser:
        return {code: list(actions) for code, _, actions in SECTIONS}
    profile = getattr(user, "staff_profile", None)
    return clean_permissions(profile.permissions if profile else {})


def has_section(user, section, action="view"):
    return action in effective_permissions(user).get(section, [])
