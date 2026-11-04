from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "audit"
    verbose_name = "Xavfsizlik"

    def ready(self):
        from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed

        from .log import record
        from .models import AuditLog

        # Django admin (sessiya) orqali kirish/chiqish. API kirishlari view'larda yoziladi.
        def on_login(sender, request, user, **kwargs):
            record(request, AuditLog.Action.LOGIN, user=user, section="django-admin", details="Django admin")

        def on_logout(sender, request, user, **kwargs):
            if user:
                record(request, AuditLog.Action.LOGOUT, user=user, section="django-admin", details="Django admin")

        # Parol bilan har qanday noto'g'ri kirish (Django admin ham, /api/auth/login/ ham)
        def on_failed(sender, credentials, request=None, **kwargs):
            tried = str(credentials.get("username") or credentials.get("email") or "")[:150]
            record(request, AuditLog.Action.LOGIN_FAILED, details=f"login: {tried}", section="parol")

        user_logged_in.connect(on_login, dispatch_uid="audit_login")
        user_logged_out.connect(on_logout, dispatch_uid="audit_logout")
        user_login_failed.connect(on_failed, dispatch_uid="audit_failed")
