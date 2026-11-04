"""SMS yuborish (Eskiz.uz). Sozlanmagan bo'lsa va DEBUG — test rejimi: kod server konsoliga chiqadi.

Har bir urinish SmsLog'ga yoziladi (kodning o'zi emas — "******" bilan yashiriladi).
Eskiz API: https://documenter.getpostman.com/view/663428/RzfmES4z
"""
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.cache import cache

log = logging.getLogger("narel.sms")
ESKIZ = "https://notify.eskiz.uz/api"
TIMEOUT = 15
BALANCE_CACHE = 10 * 60  # balans 10 daqiqada bir so'raladi
FAIL_CACHE = 2 * 60  # Eskiz javob bermasa, sahifalar har safar kutib qolmasin


class SmsError(Exception):
    pass


def config():
    from .integrations import sms_config
    return sms_config()


def sms_configured():
    return config().configured


def test_mode():
    """Haqiqiy SMS yo'q (sozlanmagan yoki o'chirilgan), lekin DEBUG — kod konsolga (va javobga) chiqadi."""
    cfg = config()
    return settings.DEBUG and not (cfg.enabled and cfg.configured)


def forget_token():
    """Login yoki parol o'zgarganda eski token va balansni unutish."""
    cache.delete_many(["eskiz_token", "eskiz_balance", "eskiz_balance_failed"])


def _request(path, data=None, token=None, method="POST"):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(f"{ESKIZ}{path}", data=body, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        # Eskiz xato sababini javob tanasida yozadi (masalan, balans yetmaydi yoki matn moderatsiyadan o'tmagan)
        try:
            reason = json.loads(e.read().decode() or "{}")
        except ValueError:
            reason = {}
        e.eskiz_reason = reason.get("message") or reason.get("detail") or reason.get("status") or e.reason
        raise


def _token(refresh=False):
    token = None if refresh else cache.get("eskiz_token")
    if not token:
        cfg = config()
        res = _request("/auth/login", {"email": cfg.email, "password": cfg.password})
        token = (res.get("data") or {}).get("token")
        if not token:
            raise SmsError(f"Eskiz'ga kirib bo'lmadi: {res.get('message') or res}")
        cache.set("eskiz_token", token, 60 * 60 * 24 * 25)  # token 30 kun amal qiladi
    return token


def _authorized(path, data=None, method="POST"):
    """Token eskirgan bo'lsa (401) bir marta yangilab qayta urinadi."""
    try:
        return _request(path, data, _token(), method)
    except urllib.error.HTTPError as e:
        if e.code != 401:
            raise
        return _request(path, data, _token(refresh=True), method)


def _error_text(e):
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP {e.code}: {getattr(e, 'eskiz_reason', e.reason)}"
    if isinstance(e, urllib.error.URLError):
        return f"Eskiz bilan aloqa yo'q: {e.reason}"
    return str(e)


def send_sms(phone, text, safe_text=None):
    """phone: "+998 90 123 45 67". safe_text — tarixga yoziladigan matn (kodsiz). Xato bo'lsa SmsError."""
    from .models import SmsLog

    entry = SmsLog(phone=phone, text=safe_text if safe_text is not None else text)
    if test_mode():
        log.warning("SMS (test rejimi) %s: %s", phone, text)
        print(f"[SMS test rejimi] {phone}: {text}", flush=True)
        entry.status = SmsLog.Status.TEST
        entry.save()
        return entry
    cfg = config()
    if not (cfg.enabled and cfg.configured):
        entry.status = SmsLog.Status.FAILED
        entry.error = "SMS o'chirilgan" if not cfg.enabled else "SMS xizmati sozlanmagan (Sozlamalar → Integratsiyalar)"
        entry.save()
        raise SmsError(entry.error)

    digits = "".join(c for c in phone if c.isdigit())
    data = {"mobile_phone": digits, "message": text, "from": cfg.sender}
    try:
        res = _authorized("/message/sms/send", data)
        # Muvaffaqiyatli javob: {"id": "...", "message": "Waiting for SMS provider", "status": "waiting"}
        if not res.get("id") or str(res.get("status", "")).lower() in ("error", "failed", "rejected"):
            raise SmsError(f"Eskiz rad etdi: {res.get('message') or res}")
    except Exception as e:  # tarmoq, Eskiz yoki javob xatosi
        entry.status, entry.error = SmsLog.Status.FAILED, _error_text(e)[:500]
        entry.save()
        log.error("SMS yuborilmadi %s: %s", phone, entry.error)
        raise SmsError(entry.error) from e

    entry.status, entry.provider_id = SmsLog.Status.SENT, str(res["id"])[:64]
    entry.save()
    cache.delete("eskiz_balance")
    return entry


def check_balance():
    """Eskiz'ga ulanib balansni so'raydi. Xato bo'lsa SmsError (sababi bilan)."""
    if not sms_configured():
        raise SmsError("Login va parol kiritilmagan")
    try:
        res = _authorized("/user/get-limit", method="GET")
    except SmsError:
        raise
    except Exception as e:
        raise SmsError(_error_text(e)) from e
    balance = (res.get("data") or {}).get("balance")
    if balance is None:
        raise SmsError(f"Eskiz javobi tushunarsiz: {res}")
    balance = int(float(balance))
    cache.set("eskiz_balance", balance, BALANCE_CACHE)
    cache.delete("eskiz_balance_failed")
    return balance


def get_balance():
    """Balans (keshdan, 10 daqiqa) yoki None — sozlanmagan yoki so'rab bo'lmadi."""
    if not sms_configured():
        return None
    cached = cache.get("eskiz_balance")
    if cached is not None:
        return cached
    if cache.get("eskiz_balance_failed"):
        return None
    try:
        return check_balance()
    except SmsError as e:
        log.error("Eskiz balansini olib bo'lmadi: %s", e)
        cache.set("eskiz_balance_failed", str(e)[:300], FAIL_CACHE)
        return None


def sms_status():
    """Admin panel uchun. mode: live — ishlayapti, test — DEBUG sinov rejimi, off — o'chiq yoki sozlanmagan."""
    cfg = config()
    base = {"enabled": cfg.enabled, "configured": cfg.configured, "threshold": cfg.low_balance,
            "balance": None, "low": False, "unreachable": False}
    if cfg.enabled and cfg.configured:
        balance = get_balance()
        return {**base, "mode": "live", "balance": balance,
                "low": balance is not None and balance < cfg.low_balance, "unreachable": balance is None,
                "error": cache.get("eskiz_balance_failed") or ""}
    return {**base, "mode": "test" if settings.DEBUG else "off"}
