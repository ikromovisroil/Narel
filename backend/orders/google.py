"""Google orqali kirish / ro'yxatdan o'tish (Google Identity Services ID token)."""
import json
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from audit.log import record
from audit.models import AuditLog

from .integrations import google_client_ids
from .models import CustomerProfile

User = get_user_model()
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}

MESSAGES = {
    "off": {"uz": "Google orqali kirish sozlanmagan.", "ru": "Вход через Google не настроен."},
    "bad": {"uz": "Google orqali kirib bo'lmadi. Qaytadan urinib ko'ring.", "ru": "Не удалось войти через Google. Попробуйте ещё раз."},
    "staff": {
        "uz": "Xodim hisoblari Google orqali kira olmaydi. Login va parol bilan kiring.",
        "ru": "Сотрудники не могут входить через Google. Войдите по логину и паролю.",
    },
    "inactive": {"uz": "Bu hisob bloklangan.", "ru": "Этот аккаунт заблокирован."},
}


def verify_google_token(credential):
    """Tokenni Google'ning o'zida tekshiradi; yaroqli bo'lsa ma'lumotlarini qaytaradi, aks holda None."""
    url = f"{TOKENINFO_URL}?{urllib.parse.urlencode({'id_token': credential})}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            info = json.loads(r.read().decode())
    except Exception:
        return None
    ok = (
        info.get("aud") in google_client_ids()
        and info.get("iss") in GOOGLE_ISSUERS
        and str(info.get("email_verified")).lower() == "true"
        and info.get("email")
    )
    return info if ok else None


def _msg(request, key):
    from catalog.i18n import get_lang
    return MESSAGES[key][get_lang(request)]


class GoogleLoginSerializer(serializers.Serializer):
    credential = serializers.CharField()


class GoogleLoginView(APIView):
    """Google tokeni bilan kirish. Hisob bo'lmasa — yaratiladi (email bo'yicha bog'lanadi)."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password"

    def post(self, request):
        if not google_client_ids():
            return Response({"detail": _msg(request, "off")}, status=status.HTTP_400_BAD_REQUEST)
        s = GoogleLoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        info = verify_google_token(s.validated_data["credential"])
        if not info:
            return Response({"detail": _msg(request, "bad")}, status=status.HTTP_400_BAD_REQUEST)

        email = info["email"].strip().lower()
        user = User.objects.filter(email__iexact=email).select_related("profile").order_by("id").first()
        if user is not None and user.is_staff:
            return Response({"detail": _msg(request, "staff")}, status=status.HTTP_400_BAD_REQUEST)
        if user is not None and not getattr(getattr(user, "profile", None), "email_verified", False):
            # Bu email boshqa hisobda qo'lda yozilgan, egasi tasdiqlanmagan. Unga bog'lanmaymiz — aks holda
            # begona odam profiliga birovning Gmail'ini yozib, uning Google orqali kirishini o'z hisobiga
            # tushirishi mumkin edi. Google egalikni tasdiqladi: email o'sha hisobdan olinadi, yangi hisob ochiladi.
            User.objects.filter(pk=user.pk).update(email="")
            user = None
        created = False
        if user is None:
            user, created = self._create(email, info), True
        if not user.is_active:
            return Response({"detail": _msg(request, "inactive")}, status=status.HTTP_400_BAD_REQUEST)
        # Ism-familiya bo'sh bo'lsa Google'dagisini olamiz
        changed = []
        for field, key in (("first_name", "given_name"), ("last_name", "family_name")):
            if not getattr(user, field) and info.get(key):
                setattr(user, field, info[key][:150])
                changed.append(field)
        if changed:
            user.save(update_fields=changed)

        refresh = RefreshToken.for_user(user)
        record(request, AuditLog.Action.LOGIN, user=user, section="sayt",
               details="Google" + (" — yangi hisob ochildi" if created else ""))
        return Response({"access": str(refresh.access_token), "refresh": str(refresh), "created": created})

    @transaction.atomic
    def _create(self, email, info):
        username = email if not User.objects.filter(username__iexact=email).exists() else f"g{info.get('sub', '')}"[:150]
        user = User.objects.create_user(
            username=username, email=email,
            first_name=(info.get("given_name") or "")[:150], last_name=(info.get("family_name") or "")[:150],
        )
        user.set_unusable_password()  # parol yo'q — xohlasa profilda o'rnatadi
        user.save(update_fields=["password"])
        CustomerProfile.objects.create(user=user, email_verified=True)
        return user
