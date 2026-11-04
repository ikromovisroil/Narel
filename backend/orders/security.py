"""Xavfsizlik yordamchilari: mijozning haqiqiy IP manzili va parolni tanlab buzishdan himoya."""
from django.conf import settings
from django.core.cache import cache

# Xodim kirishi: 15 daqiqada bitta login uchun 5 ta, bitta IP uchun 20 ta noto'g'ri urinish — keyin 15 daqiqa blok
LOCK_WINDOW = 15 * 60
MAX_FAILS_PER_USER = 5
MAX_FAILS_PER_IP = 20


def client_ip(request):
    """Haqiqiy IP. Server proksi (nginx) ortida bo'lsa NUM_PROXIES=1 qo'yiladi va IP X-Forwarded-For dan olinadi.
    NUM_PROXIES=0 bo'lsa sarlavha e'tiborga olinmaydi — uni soxtalashtirib limitlarni aylanib o'tib bo'lmaydi."""
    if request is None:
        return None
    remote = request.META.get("REMOTE_ADDR")
    proxies = settings.NUM_PROXIES
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if not proxies or not xff:
        return remote
    parts = [p.strip() for p in xff.split(",") if p.strip()]
    # Har bir ishonchli proksi o'zidan oldingi manzilni oxiriga qo'shadi
    return parts[-proxies] if len(parts) >= proxies else (parts[0] if parts else remote)


def _keys(username, ip):
    keys = [f"login-fail:u:{(username or '').strip().lower()}"]
    if ip:
        keys.append(f"login-fail:ip:{ip}")
    return keys


def login_locked(request, username):
    """Juda ko'p noto'g'ri urinish bo'lsa True."""
    user_key, *ip_key = _keys(username, client_ip(request))
    if (cache.get(user_key) or 0) >= MAX_FAILS_PER_USER:
        return True
    return bool(ip_key) and (cache.get(ip_key[0]) or 0) >= MAX_FAILS_PER_IP


def login_failed(request, username):
    for key in _keys(username, client_ip(request)):
        cache.add(key, 0, LOCK_WINDOW)
        try:
            cache.incr(key)
        except ValueError:  # kalit shu orada o'chib ketgan
            cache.set(key, 1, LOCK_WINDOW)


def login_succeeded(request, username):
    cache.delete(_keys(username, None)[0])
