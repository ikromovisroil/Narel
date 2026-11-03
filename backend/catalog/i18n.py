"""Tillar: uz (asosiy) va ru (admin kiritadi).

Til so'rovdan olinadi: ?lang=ru yoki Accept-Language: ru / uz.
"""
import re

LANGS = ("uz", "ru")

# Kirillcha qidiruv so'rovini lotinga o'girish uchun ("музлатгич" -> "muzlatgich")
CYR2LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh",
    "ъ": "'", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o'", "қ": "q", "ғ": "g'",
    "ҳ": "h",
}
CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")


def get_lang(request):
    if request is None:
        return "uz"
    raw = ""
    if hasattr(request, "query_params"):
        raw = request.query_params.get("lang", "")
    raw = (raw or request.headers.get("Accept-Language", "")).split(",")[0].strip().lower()
    return "ru" if raw.startswith("ru") else "uz"


def localized(obj, field, lang):
    """Ruscha so'ralsa `<field>_ru`, bo'sh bo'lsa o'zbekcha qiymat."""
    base = getattr(obj, field, "") or ""
    if lang == "ru":
        return getattr(obj, f"{field}_ru", "") or base
    return base


def to_latin(text):
    """Kirill yozuvini lotinga — qidiruv uchun."""
    out = []
    for c in text:
        lo = c.lower()
        r = CYR2LAT.get(lo, c)
        out.append(r.capitalize() if c != lo and r else r)
    return "".join(out)


def has_cyrillic(text):
    return bool(CYRILLIC_RE.search(text or ""))
