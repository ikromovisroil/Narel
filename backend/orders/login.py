"""Mijoz kirishi: telefon + SMS kod, Apple orqali kirish va ommaviy oferta."""
import base64
import hashlib
import hmac
import json
import secrets
import time
import urllib.request
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

from catalog.i18n import get_lang, localized

from .models import CustomerProfile, PhoneCode, StoreSettings
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
    "phone_taken": {
        "uz": "Bu raqam boshqa hisobga bog'langan.",
        "ru": "Этот номер привязан к другому аккаунту.",
    },
    "apple_off": {"uz": "Apple orqali kirish sozlanmagan.", "ru": "Вход через Apple не настроен."},
    "apple_bad": {"uz": "Apple orqali kirib bo'lmadi. Qaytadan urinib ko'ring.", "ru": "Не удалось войти через Apple. Попробуйте ещё раз."},
    "sms_text": {"uz": "Narel: kirish kodi {0}. Hech kimga bermang.", "ru": "Narel: код для входа {0}. Никому не сообщайте."},
}


def msg(request, key, *args):
    return MESSAGES[key][get_lang(request)].format(*args)


def bad(request, key, *args, field=None, code=status.HTTP_400_BAD_REQUEST, **extra):
    text = msg(request, key, *args)
    return Response({field: [text], **extra} if field else {"detail": text, **extra}, status=code)


def code_hash(phone, code):
    return hmac.new(settings.SECRET_KEY.encode(), f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


def client_ip(request):
    return request.META.get("REMOTE_ADDR")


def login_response(request, user, created):
    """Kirish tokenlari. Xodimlar va bloklanganlar bu yo'l bilan kira olmaydi."""
    if user.is_staff:
        return bad(request, "staff")
    if not user.is_active:
        return bad(request, "inactive")
    refresh = RefreshToken.for_user(user)
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
            send_sms(phone, msg(request, "sms_text", code))
        except SmsError:
            return bad(request, "sms", code=status.HTTP_503_SERVICE_UNAVAILABLE)
        # Oldingi kodlar bekor
        PhoneCode.objects.filter(phone=phone, used=False).update(used=True)
        PhoneCode.objects.create(phone=phone, code_hash=code_hash(phone, code), ip=ip)

        data = {"phone": phone, "expires_in": CODE_TTL, "resend_in": RESEND_AFTER,
                "is_new": not CustomerProfile.objects.filter(phone=phone).exists()}
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
    """Profilda telefonni almashtirish yoki qo'shish (Google/Apple mijozlari) — yangi raqamga kelgan kod bilan."""

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


# ---------- Apple orqali kirish ----------

APPLE_ISSUER = "https://appleid.apple.com"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
# SHA-256 uchun DigestInfo prefiksi (PKCS#1 v1.5)
SHA256_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


def _b64(data):
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _apple_keys():
    with urllib.request.urlopen(APPLE_KEYS_URL, timeout=10) as r:
        return json.loads(r.read().decode())["keys"]


def rsa_verify(message, signature, n, e):
    """RS256 imzosini tekshiradi (RSASSA-PKCS1-v1_5 + SHA-256), qo'shimcha kutubxonasiz."""
    k = (n.bit_length() + 7) // 8
    if len(signature) != k:
        return False
    em = pow(int.from_bytes(signature, "big"), e, n).to_bytes(k, "big")
    digest = SHA256_PREFIX + hashlib.sha256(message).digest()
    expected = b"\x00\x01" + b"\xff" * (k - len(digest) - 3) + b"\x00" + digest
    return hmac.compare_digest(em, expected)


def verify_apple_token(id_token, keys=None):
    """Apple id_token'ini tekshiradi; yaroqli bo'lsa payload, aks holda None."""
    try:
        head_b64, body_b64, sig_b64 = id_token.split(".")
        header = json.loads(_b64(head_b64))
        payload = json.loads(_b64(body_b64))
        if header.get("alg") != "RS256":
            return None
        key = next((k for k in (keys or _apple_keys()) if k.get("kid") == header.get("kid")), None)
        if not key:
            return None
        n = int.from_bytes(_b64(key["n"]), "big")
        e = int.from_bytes(_b64(key["e"]), "big")
        if not rsa_verify(f"{head_b64}.{body_b64}".encode(), _b64(sig_b64), n, e):
            return None
    except Exception:
        return None
    if (payload.get("iss") != APPLE_ISSUER or payload.get("aud") != settings.APPLE_CLIENT_ID
            or int(payload.get("exp", 0)) < time.time() or not payload.get("sub")):
        return None
    return payload


class AppleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)


class AppleLoginView(APIView):
    """Apple bilan kirish. Ism faqat birinchi marta (Apple'dan) keladi."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password"

    def post(self, request):
        if not settings.APPLE_CLIENT_ID:
            return bad(request, "apple_off")
        s = AppleLoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        info = verify_apple_token(s.validated_data["id_token"])
        if not info:
            return bad(request, "apple_bad")

        sub = info["sub"]
        email = (info.get("email") or "").strip().lower()
        verified = str(info.get("email_verified")).lower() == "true"
        profile = CustomerProfile.objects.select_related("user").filter(apple_id=sub).first()
        user, created = (profile.user if profile else None), False
        if user is None and email and verified:
            user = User.objects.filter(email__iexact=email).order_by("id").first()
            if user:
                CustomerProfile.objects.update_or_create(user=user, defaults={"apple_id": sub})
        if user is None:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=free_username(email or f"apple_{sub[:20]}"), email=email,
                    first_name=s.validated_data.get("first_name", ""), last_name=s.validated_data.get("last_name", ""),
                )
                user.set_unusable_password()
                user.save(update_fields=["password"])
                CustomerProfile.objects.create(user=user, apple_id=sub)
            created = True
        return login_response(request, user, created)


# ---------- Ommaviy oferta ----------

class OfferView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        store = StoreSettings.load()
        return Response({"text": localized(store, "offer_text", get_lang(request)), "updated_at": store.updated_at})
