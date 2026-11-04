"""Kirgan foydalanuvchilarning o'zgartiruvchi so'rovlarini (POST/PUT/PATCH/DELETE) jurnalga yozadi."""
import json

from django.conf import settings

from .log import record, section_of
from .models import AuditLog

WRITE = {"POST", "PUT", "PATCH", "DELETE"}
# Kirish/chiqish alohida yoziladi; savat va sevimlilar — shovqin
SKIP = ("/auth/login/", "/auth/refresh/", "/auth/logout/", "/auth/code/", "/auth/google/", "/cart/", "/favorites/")
# Yozuvni o'zgartirmaydigan qo'shimcha amallar
EXTRA_ACTIONS = ("upload", "images", "reply", "sms-check", "sms-test", "sync")


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_prefix = "/" + settings.DJANGO_ADMIN_URL

    def __call__(self, request):
        if request.method not in WRITE:
            return self.get_response(request)
        api = request.path.startswith("/api/") and not any(s in request.path for s in SKIP)
        django_admin = request.path.startswith(self.admin_prefix) and not request.path.rstrip("/").endswith(("/login", "/logout"))
        body = None
        if api and request.content_type == "application/json":
            try:
                body = json.loads(request.body or b"{}")  # oldindan o'qiladi — view keyin keshdagisini oladi
            except (ValueError, UnicodeDecodeError):
                body = None

        response = self.get_response(request)

        user = getattr(request, "user", None)
        if not (user and user.is_authenticated) or not (api or django_admin):
            return response
        if api:
            section, object_id = section_of(request.path)
            if request.content_type and request.content_type.startswith("multipart/"):
                body = {"fayl": "yuklandi"}
        else:
            section, object_id = self._admin_target(request.path)
            body = {k: v for k, v in request.POST.items() if k != "csrfmiddlewaretoken"}
        record(request, self._action(request), user=user, section=section, object_id=object_id,
               details=body or "", status_code=response.status_code)
        return response

    def _action(self, request):
        last = request.path.rstrip("/").rsplit("/", 1)[-1]
        if last in EXTRA_ACTIONS or (request.method == "POST" and request.POST.get("action")):
            return AuditLog.Action.ACTION
        if request.method == "DELETE" or last == "delete":
            return AuditLog.Action.DELETE
        if request.method == "POST" and (last == "add" or not last.isdigit()) and "/change" not in request.path:
            return AuditLog.Action.CREATE
        return AuditLog.Action.UPDATE

    def _admin_target(self, path):
        # /admin/catalog/product/12/change/ -> ("django-admin/catalog.product", "12")
        parts = [p for p in path[len(self.admin_prefix):].split("/") if p]
        section = "django-admin/" + ".".join(parts[:2]) if parts else "django-admin"
        object_id = parts[2] if len(parts) > 2 and parts[2] not in ("add",) else ""
        return section, object_id
