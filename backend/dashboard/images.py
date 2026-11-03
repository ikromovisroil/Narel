"""Yuklanadigan rasmlar uchun talablar.

Shu yerda bir marta yoziladi: backend tekshiradi, admin panel esa
/api/admin/image-rules/ orqali olib, foydalanuvchiga ko'rsatadi.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

FORMATS = {"JPEG": "JPG", "PNG": "PNG", "WEBP": "WEBP"}
MAX_SIDE = 4000

RULES = {
    "product": {
        "title": "Mahsulot rasmi",
        "recommended": [1000, 1000],
        "min": [600, 600],
        "ratio": [1, 1],          # kvadrat
        "max_mb": 5,
        "hint": "Kvadrat (1:1), oq yoki shaffof fon, mahsulot markazda",
    },
    "category": {
        "title": "Kategoriya ikonkasi",
        "recommended": [256, 256],
        "min": [96, 96],
        "ratio": [1, 1],
        "max_mb": 1,
        "hint": "Kvadrat (1:1), PNG, shaffof fon",
    },
    "brand": {
        "title": "Brend logosi",
        "recommended": [400, 160],
        "min": [200, 80],
        "ratio": [5, 2],          # 2.5:1
        "max_mb": 1,
        "hint": "Gorizontal (5:2), PNG, shaffof fon, atrofida ortiqcha bo'sh joy yo'q",
    },
    "payment_logo": {
        "title": "To'lov tizimi logosi",
        "recommended": [256, 256],
        "min": [64, 64],
        "ratio": [1, 1],
        "max_mb": 1,
        "hint": "Kvadrat (1:1), PNG. To'lov tizimining rasmiy ikonkasi",
    },
    "banner": {
        "title": "Banner",
        "recommended": [1280, 400],
        "min": [1200, 375],
        "ratio": [16, 5],         # 3.2:1
        "max_mb": 5,
        "hint": "Keng (16:5), muhim matn va rasm o'rtada",
    },
}

# Nisbatdan qancha chetga chiqishga ruxsat (10%)
RATIO_TOLERANCE = 0.10


def public_rules():
    return {
        key: {**rule, "formats": list(FORMATS.values()), "max_side": MAX_SIDE}
        for key, rule in RULES.items()
    }


def _fail(message):
    raise serializers.ValidationError({"file": [message]})


def _ratio_text(w, h):
    from math import gcd
    g = gcd(w, h) or 1
    return f"{w // g}:{h // g}"


def validate_image(file, rule_key):
    """Faylni tekshiradi va saqlashga tayyor faylni qaytaradi."""
    rule = RULES[rule_key]
    rec = "{}×{} px".format(*rule["recommended"])
    if not file:
        _fail("Fayl tanlanmagan.")

    if file.size > rule["max_mb"] * 1024 * 1024:
        _fail(f"Fayl hajmi {rule['max_mb']} MB dan oshmasligi kerak "
              f"(sizniki {file.size / 1024 / 1024:.1f} MB).")

    try:
        file = serializers.ImageField().to_internal_value(file)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"file": exc.messages})

    image = file.image  # Django tekshiruvdan keyin PIL rasmni shu yerga qo'yadi
    if image.format not in FORMATS:
        _fail(f"Faqat {', '.join(FORMATS.values())} formatlari qabul qilinadi.")

    w, h = image.size
    min_w, min_h = rule["min"]
    if w < min_w or h < min_h:
        _fail(f"Rasm juda kichik: kamida {min_w}×{min_h} px bo'lishi kerak "
              f"(sizniki {w}×{h} px). Tavsiya: {rec}.")
    if w > MAX_SIDE or h > MAX_SIDE:
        _fail(f"Rasm juda katta: tomonlari {MAX_SIDE} px dan oshmasin (sizniki {w}×{h} px).")

    rw, rh = rule["ratio"]
    target = rw / rh
    if abs(w / h - target) / target > RATIO_TOLERANCE:
        _fail(f"Rasm nisbati {rw}:{rh} bo'lishi kerak (sizniki {w}×{h} px, ya'ni {_ratio_text(w, h)}). "
              f"Tavsiya: {rec}.")
    return file
