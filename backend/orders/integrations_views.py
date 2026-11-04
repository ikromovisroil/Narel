"""Admin panel: Sozlamalar → Integratsiyalar (SMS, Google). Bo'lim: "settings"."""
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings

from staff.permissions import SectionPermission

from .integrations import GUIDES, clean_domain, sms_config, sms_templates
from .models import IntegrationSettings, SmsLog
from .serializers import normalize_phone
from .sms import SmsError, check_balance, forget_token, send_sms, sms_status


class IntegrationSettingsSerializer(serializers.ModelSerializer):
    # Parol hech qachon qaytarilmaydi; bo'sh yuborilsa eskisi saqlanadi
    eskiz_password = serializers.CharField(write_only=True, required=False, allow_blank=True, trim_whitespace=False)
    has_password = serializers.SerializerMethodField()

    class Meta:
        model = IntegrationSettings
        fields = [
            "sms_enabled", "eskiz_email", "eskiz_password", "has_password", "eskiz_from", "sms_low_balance",
            "sms_otp_domain", "google_client_id", "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def get_has_password(self, obj) -> bool:
        return bool(obj.eskiz_password)

    def validate_sms_otp_domain(self, value):
        value = clean_domain(value)
        if value and ("/" in value or " " in value or "." not in value):
            raise serializers.ValidationError("Faqat domen: masalan, narel.uz")
        return value

    def validate_eskiz_from(self, value):
        return value.strip()

    def validate_google_client_id(self, value):
        value = value.strip()
        if value and not value.endswith(".apps.googleusercontent.com"):
            raise serializers.ValidationError("Client ID \".apps.googleusercontent.com\" bilan tugaydi.")
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop("eskiz_password", "")
        if password.strip():
            validated_data["eskiz_password"] = password.strip()
        old = (instance.eskiz_email, instance.eskiz_password)
        instance = super().update(instance, validated_data)
        if (instance.eskiz_email, instance.eskiz_password) != old:
            forget_token()  # boshqa hisob — eski token yaroqsiz
        return instance


def payload(obj):
    cfg = sms_config()
    return {
        **IntegrationSettingsSerializer(obj).data,
        # .env da kiritilgan zaxira qiymatlar (admin panelda bo'sh bo'lsa ishlatiladi)
        "env": {
            "eskiz": bool(settings.ESKIZ_EMAIL and settings.ESKIZ_PASSWORD),
            "google": bool(settings.GOOGLE_CLIENT_ID),
        },
        "sms": sms_status(),
        "sms_sender": cfg.sender,
        "sms_templates": sms_templates(cfg.otp_domain),
        "recent_sms": list(SmsLog.objects.values("id", "phone", "text", "status", "error", "created_at")[:15]),
        "guides": GUIDES,
    }


class AdminIntegrationsView(APIView):
    permission_classes = [SectionPermission]
    section = "settings"

    def get(self, request):
        return Response(payload(IntegrationSettings.load()))

    def patch(self, request):
        serializer = IntegrationSettingsSerializer(IntegrationSettings.load(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(payload(serializer.save()))


class SmsCheckView(APIView):
    """Eskiz'ga ulanib balansni tekshirish (saqlangan login-parol bilan)."""

    permission_classes = [SectionPermission]
    section = "settings"
    write_action = "change"

    def post(self, request):
        forget_token()
        try:
            balance = check_balance()
        except SmsError as e:
            return Response({"detail": f"Ulanib bo'lmadi: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"balance": balance, "sms": sms_status()})


class SmsTestView(APIView):
    """Ko'rsatilgan raqamga sinov kodi yuborish (moderatsiyadan o'tgan kirish matni bilan)."""

    permission_classes = [SectionPermission]
    section = "settings"
    write_action = "change"

    def post(self, request):
        phone = normalize_phone(request.data.get("phone", ""))
        if not phone:
            return Response({"phone": ["Telefon raqamini to'liq kiriting: +998 XX XXX XX XX."]},
                            status=status.HTTP_400_BAD_REQUEST)
        from .integrations import sms_text
        cfg = sms_config()
        if not (cfg.enabled and cfg.configured) and not settings.DEBUG:
            return Response({"detail": "Avval Eskiz login va parolini kiriting va SMS'ni yoqing."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            entry = send_sms(phone, sms_text("uz", "123456", cfg.otp_domain),
                             safe_text=sms_text("uz", "******", cfg.otp_domain))
        except SmsError as e:
            return Response({"detail": f"Yuborilmadi: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        note = ("Test rejimi: SMS yuborilmadi, matn server konsoliga chiqdi."
                if entry.status == SmsLog.Status.TEST else "Yuborildi. Telefoningizni tekshiring.")
        return Response({"detail": note, "status": entry.status})
