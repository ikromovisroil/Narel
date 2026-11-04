"""Mijoz kirishi: telefon + SMS kod; telefonni almashtirish va ommaviy oferta."""
import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView

from audit.log import record
from audit.models import AuditLog

from catalog.i18n import get_lang, localized

from .models import CustomerProfile, PhoneCode, StoreSettings
from .security import client_ip, login_locked
from .serializers import normalize_phone
from .sms import SmsError, send_sms, test_mode

User = get_user_model()

CODE_TTL = 120        # kod amal qilish muddati, soniya
RESEND_AFTER = 60     # qayta yuborish oralig'i
MAX_ATTEMPTS = 5      # bitta kodga xato urinishlar
DAILY_PER_PHONE = 10  # bir raqamga kuniga SMS
DAILY_PER_IP = 30     # bir IP dan kuniga SMS

MESSAGES = {
    "phone": {"uz": "Telefon raqamini to'liq kiriting: +998 XX XXX XX XX.", "ru": "Укажите номер полностью: +998 XX XXX XX XX."},
    "agree": {"uz": "Shartlarga rozilikni tasdiqlang.", "ru": "Подтвердите согласие с условиями."},
    "wait": {"uz": "Yangi kodni {0} soniyadan keyin so'rash mumkin.", "ru": "Новый код можно запросить через {0} сек."},
    "limit": {"uz": "Bugun juda ko'p kod so'raldi. Ertaga urinib ko'ring.", "ru": "Слишком много запросов кода сегодня. Попробуйте завтра."},
    "sms": {"uz": "SMS yuborib bo'lmadi. Birozdan keyin urinib ko'ring.", "ru": "Не удалось отправить SMS. Попробуйте позже."},
    "code": {"uz": "Kod noto'g'ri.", "ru": "Неверный код."},
    "expired": {"uz": "Kod eskirgan. Yangi kod oling.", "ru": "Код устарел. Запросите новый."},
    "attempts": {"uz": "Urinishlar tugadi. Yangi kod oling.", "ru": "Попытки закончились. Запросите новый код."},
    "staff": {
        "uz": "Xodimlar login va parol bilan kiradi.",
        "ru": "Сотрудники входят по логину и паролю.",
    },
    "inactive": {"uz": "Bu hisob bloklangan.", "ru": "Этот аккаунт заблокирован."},
    "locked": {
        "uz": "Juda ko'p noto'g'ri urinish. 15 daqiqadan keyin qayta urinib ko'ring.",
        "ru": "Слишком много неудачных попыток. Попробуйте через 15 минут.",
    },
    "phone_taken": {
        "uz": "Bu raqam boshqa hisobga bog'langan.",
        "ru": "Этот номер привязан к другому аккаунту.",
    },
}


def msg(request, key, *args):
    return MESSAGES[key][get_lang(request)].format(*args)


def sms_text(request, code):
    from .integrations import sms_config, sms_text as build
    return build(get_lang(request), code, sms_config().otp_domain)


def bad(request, key, *args, field=None, code=status.HTTP_400_BAD_REQUEST, **extra):
    text = msg(request, key, *args)
    return Response({field: [text], **extra} if field else {"detail": text, **extra}, status=code)


def code_hash(phone, code):
    return hmac.new(settings.SECRET_KEY.encode(), f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


class StaffLoginView(TokenObtainPairView):
    """Xodim kirishi (login/email/telefon + parol). Daqiqalik limit va ko'p xatodan keyin 15 daqiqalik blok."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password"

    def post(self, request, *args, **kwargs):
        username = str(request.data.get("username") or "")
        if username and login_locked(request, username):
            record(request, AuditLog.Action.LOGIN_FAILED, details=f"login: {username[:150]} — bloklangan", section="admin-panel")
            return Response({"detail": msg(request, "locked")}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            from .auth import LoginEmailPhoneBackend
            record(request, AuditLog.Action.LOGIN, user=LoginEmailPhoneBackend.find_user(username.strip()),
                   section="admin-panel", details="login va parol")
        # Noto'g'ri parol — user_login_failed signali orqali yoziladi
        return response


class LogoutView(TokenBlacklistView):
    """Chiqish: refresh token bekor qilinadi va jurnalga yoziladi."""

    def post(self, request, *args, **kwargs):
        user = None
        try:
            user = User.objects.filter(pk=RefreshToken(request.data.get("refresh"))["user_id"]).first()
        except Exception:  # noqa: BLE001 — yaroqsiz token: shunchaki bekor qilishga urinamiz
            pass
        response = super().post(request, *args, **kwargs)
        if user and response.status_code == 200:
            record(request, AuditLog.Action.LOGOUT, user=user, section="admin-panel" if user.is_staff else "sayt")
        return response


def login_response(request, user, created):
    """Kirish tokenlari. Xodimlar va bloklanganlar bu yo'l bilan kira olmaydi."""
    if user.is_staff:
        return bad(request, "staff")
    if not user.is_active:
        return bad(request, "inactive")
    refresh = RefreshToken.for_user(user)
    record(request, AuditLog.Action.LOGIN, user=user, section="sayt",
           details="SMS kod" + (" — yangi hisob ochildi" if created else ""))
    return Response({"access": str(refresh.access_token), "refresh": str(refresh), "created": created})


def free_username(base):
    name, n = base[:140], 1
    while User.objects.filter(username__iexact=name).exists():
        n += 1
        name = f"{base[:140]}_{n}"
    return name


# ---------- Telefon + SMS kod ----------

class SendCodeSerializer(serializers.Serializer):
    phone = serializers.CharField()
    agree = serializers.BooleanField(default=False)


class SendCodeView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def post(self, request):
        s = SendCodeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        phone = normalize_phone(s.validated_data["phone"])
        if not phone:
            return bad(request, "phone", field="phone")
        if not s.validated_data["agree"]:
            return bad(request, "agree", field="agree")

        now = timezone.now()
        last = PhoneCode.objects.filter(phone=phone).first()
        if last and (now - last.created_at).total_seconds() < RESEND_AFTER:
            left = RESEND_AFTER - int((now - last.created_at).total_seconds())
            return bad(request, "wait", left, code=status.HTTP_429_TOO_MANY_REQUESTS, resend_in=left)
        day = now - timedelta(days=1)
        ip = client_ip(request)
        if (PhoneCode.objects.filter(phone=phone, created_at__gte=day).count() >= DAILY_PER_PHONE
                or (ip and PhoneCode.objects.filter(ip=ip, created_at__gte=day).count() >= DAILY_PER_IP)):
            return bad(request, "limit", code=status.HTTP_429_TOO_MANY_REQUESTS)

        code = f"{secrets.randbelow(1_000_000):06d}"
        try:
            send_sms(phone, sms_text(request, code), safe_text=sms_text(request, "******"))
        except SmsError:
            return bad(request, "sms", code=status.HTTP_503_SERVICE_UNAVAILABLE)
        # Oldingi kodlar bekor
        PhoneCode.objects.filter(phone=phone, used=False).update(used=True)
        PhoneCode.objects.create(phone=phone, code_hash=code_hash(phone, code), ip=ip)

        # Raqam ro'yxatdan o'tganmi — aytilmaydi (begona odam bilib olmasin); verify javobida "created" bor
        data = {"phone": phone, "expires_in": CODE_TTL, "resend_in": RESEND_AFTER}
        if test_mode():
            data["debug_code"] = code  # faqat DEBUG va SMS xizmati sozlanmaganda
        return Response(data)


def consume_code(request, phone, code):
    """Kodni tekshiradi va ishlatilgan deb belgilaydi. Xato bo'lsa Response, to'g'ri bo'lsa None.
    transaction.atomic ichida chaqiriladi."""
    otp = PhoneCode.objects.select_for_update().filter(phone=phone, used=False).first()
    if not otp or (timezone.now() - otp.created_at).total_seconds() > CODE_TTL:
        return bad(request, "expired", field="code")
    if not hmac.compare_digest(otp.code_hash, code_hash(phone, code)):
        otp.attempts += 1
        otp.used = otp.attempts >= MAX_ATTEMPTS
        otp.save(update_fields=["attempts", "used"])
        return bad(request, "attempts" if otp.used else "code", field="code", attempts_left=MAX_ATTEMPTS - otp.attempts)
    otp.used = True
    otp.save(update_fields=["used"])
    return None


class VerifyCodeSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField(max_length=10)


class VerifyCodeView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_verify"

    def post(self, request):
        s = VerifyCodeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        phone = normalize_phone(s.validated_data["phone"])
        code = "".join(c for c in s.validated_data["code"] if c.isdigit())
        if not phone:
            return bad(request, "phone", field="phone")

        with transaction.atomic():
            error = consume_code(request, phone, code)
            if error:
                record(request, AuditLog.Action.LOGIN_FAILED, details=f"{phone} — noto'g'ri yoki eskirgan kod", section="sayt")
                return error
            profile = CustomerProfile.objects.select_related("user").filter(phone=phone).first()
            if profile:
                return login_response(request, profile.user, False)
            user = User.objects.create_user(username=free_username("".join(c for c in phone if c.isdigit())))
            user.set_unusable_password()
            user.save(update_fields=["password"])
            CustomerProfile.objects.create(user=user, phone=phone)
        return login_response(request, user, True)


class ChangePhoneView(APIView):
    """Profilda telefonni almashtirish yoki qo'shish (Google mijozlari) — yangi raqamga kelgan kod bilan."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_verify"

    def post(self, request):
        s = VerifyCodeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        phone = normalize_phone(s.validated_data["phone"])
        if not phone:
            return bad(request, "phone", field="phone")
        if CustomerProfile.objects.filter(phone=phone).exclude(user=request.user).exists():
            return bad(request, "phone_taken", field="phone")
        code = "".join(c for c in s.validated_data["code"] if c.isdigit())
        with transaction.atomic():
            error = consume_code(request, phone, code)
            if error:
                return error
            request.user.profile, _ = CustomerProfile.objects.update_or_create(user=request.user, defaults={"phone": phone})
        return Response({"phone": phone})


# ---------- Ommaviy oferta ----------

class OfferView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        store = StoreSettings.load()
        return Response({"text": localized(store, "offer_text", get_lang(request)), "updated_at": store.updated_at})
