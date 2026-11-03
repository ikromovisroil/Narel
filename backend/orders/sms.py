"""SMS yuborish. Eskiz.uz sozlanmagan bo'lsa — test rejimi: kod server konsoliga chiqadi."""
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.cache import cache

log = logging.getLogger("narel.sms")
ESKIZ = "https://notify.eskiz.uz/api"


class SmsError(Exception):
    pass


def sms_configured():
    return bool(settings.ESKIZ_EMAIL and settings.ESKIZ_PASSWORD)


def test_mode():
    """Haqiqiy SMS yo'q, lekin DEBUG — kod konsolga (va javobga) chiqadi."""
    return not sms_configured() and settings.DEBUG


def _post(path, data, token=None):
    req = urllib.request.Request(f"{ESKIZ}{path}", data=urllib.parse.urlencode(data).encode(), method="POST")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def _eskiz_token(refresh=False):
    token = None if refresh else cache.get("eskiz_token")
    if not token:
        res = _post("/auth/login", {"email": settings.ESKIZ_EMAIL, "password": settings.ESKIZ_PASSWORD})
        token = res["data"]["token"]
        cache.set("eskiz_token", token, 60 * 60 * 24 * 25)  # token ~30 kun amal qiladi
    return token


def send_sms(phone, text):
    """phone: "+998 90 123 45 67". Xato bo'lsa SmsError."""
    if test_mode():
        log.warning("SMS (test rejimi) %s: %s", phone, text)
        print(f"[SMS test rejimi] {phone}: {text}", flush=True)
        return
    if not sms_configured():
        raise SmsError("SMS xizmati sozlanmagan")
    digits = "".join(c for c in phone if c.isdigit())
    data = {"mobile_phone": digits, "message": text, "from": settings.ESKIZ_FROM}
    try:
        try:
            _post("/message/sms/send", data, _eskiz_token())
        except urllib.error.HTTPError as e:
            if e.code != 401:
                raise
            _post("/message/sms/send", data, _eskiz_token(refresh=True))  # token eskirgan
    except Exception as e:  # tarmoq yoki Eskiz xatosi
        log.exception("SMS yuborilmadi: %s", phone)
        raise SmsError(str(e)) from e
