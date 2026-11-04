"""Jurnalga yozish. Maxfiy qiymatlar (parol, kod, token, kalit) hech qachon yozilmaydi."""
import json
import logging
import re

from orders.security import client_ip

log = logging.getLogger("narel.audit")

# Kalit nomida shular bo'lsa qiymati yashiriladi
SECRET_WORDS = ("password", "parol", "secret", "token", "refresh", "access", "credential", "code", "key", "otp")
MAX_DETAILS = 2000


def who_of(user):
    if not user or not getattr(user, "is_authenticated", False):
        return ""
    name = f"{user.first_name} {user.last_name}".strip()
    phone = getattr(getattr(user, "profile", None), "phone", "") if not user.is_staff else ""
    label = user.username if user.is_staff else (phone or user.email or f"id {user.pk}")
    return f"{name} ({label})" if name else label


def mask(value):
    """Lug'at/ro'yxat ichidagi maxfiy maydonlarni "***" bilan almashtiradi."""
    if isinstance(value, dict):
        return {k: ("***" if any(w in str(k).lower() for w in SECRET_WORDS) and v not in ("", None) else mask(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [mask(v) for v in value[:50]]
    if isinstance(value, str) and len(value) > 300:
        return value[:300] + "…"
    return value


def details_text(data):
    if data in (None, "", {}, []):
        return ""
    try:
        text = json.dumps(mask(data), ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = str(data)
    return text[:MAX_DETAILS]


def record(request, action, user=None, section="", object_id="", details="", status_code=None):
    """Bitta yozuv. Jurnalga yozib bo'lmasa ham asosiy ish to'xtamaydi."""
    from .models import AuditLog
    try:
        user = user if user is not None else getattr(request, "user", None)
        authed = bool(user and getattr(user, "is_authenticated", False))
        AuditLog.objects.create(
            user=user if authed else None,
            who=who_of(user) if authed else (details if action == AuditLog.Action.LOGIN_FAILED else ""),
            is_staff=bool(authed and user.is_staff),
            action=action, section=section[:60], object_id=str(object_id)[:64],
            details=(details if isinstance(details, str) else details_text(details))[:MAX_DETAILS],
            method=(getattr(request, "method", None) or "")[:10],
            path=(getattr(request, "path", None) or "")[:300],
            status_code=status_code,
            ip=client_ip(request) if request else None,
            user_agent=(request.META.get("HTTP_USER_AGENT", "")[:300] if request else ""),
        )
    except Exception:  # noqa: BLE001 — jurnal xatosi saytni to'xtatmasin
        log.exception("Jurnalga yozib bo'lmadi")


# /api/v1/admin/products/12/upload/ -> ("products", "12")
PATH_RE = re.compile(r"^/api/(?:v\d+/)?(?:(?P<admin>admin)/)?(?P<section>[\w-]+)/(?:(?P<id>[\w-]+)/)?")


def section_of(path):
    m = PATH_RE.match(path)
    if not m:
        return "", ""
    section = m.group("section")
    if m.group("admin"):
        section = f"admin/{section}"
    return section, m.group("id") or ""
