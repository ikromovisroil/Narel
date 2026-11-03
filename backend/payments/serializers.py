from rest_framework import serializers

from catalog.i18n import get_lang, localized

from .models import PaymentMethod


class PublicPaymentMethodSerializer(serializers.ModelSerializer):
    """Sayt uchun: faqat nom va izoh. Kalitlar umuman chiqmaydi."""

    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    months = serializers.SerializerMethodField()

    class Meta:
        model = PaymentMethod
        fields = ["code", "title", "description", "logo", "months"]

    def get_title(self, obj):
        return localized(obj, "title", get_lang(self.context.get("request")))

    def get_description(self, obj):
        return localized(obj, "description", get_lang(self.context.get("request")))

    def get_months(self, obj):
        if obj.code != "installment":
            return None
        try:
            return int(obj.config.get("months") or 12)
        except (TypeError, ValueError):
            return 12


class AdminPaymentMethodSerializer(serializers.ModelSerializer):
    """Admin uchun. Maxfiy kalitlar o'qishda qaytarilmaydi, faqat "kiritilganmi" belgisi.
    Saqlashda maxfiy maydon bo'sh yuborilsa — eski qiymat saqlanib qoladi."""

    fields_schema = serializers.SerializerMethodField()
    about = serializers.SerializerMethodField()
    where = serializers.SerializerMethodField()
    contacts = serializers.SerializerMethodField()
    missing_fields = serializers.ListField(read_only=True)
    is_configured = serializers.BooleanField(read_only=True)

    class Meta:
        model = PaymentMethod
        fields = [
            "id", "code", "title", "title_ru", "description", "description_ru", "logo", "is_active",
            "test_mode", "config", "order", "fields_schema", "about", "where", "contacts", "missing_fields", "is_configured",
            "updated_at",
        ]
        read_only_fields = ["code", "logo", "updated_at"]

    def get_about(self, obj):
        return obj.provider.get("about", "")

    def get_where(self, obj):
        return obj.provider.get("where", [])

    def get_contacts(self, obj):
        p = obj.provider
        return {
            "links": p.get("contacts", []),
            "note": p.get("contacts_note", ""),
            "documents": p.get("documents", []),
        }

    def get_fields_schema(self, obj):
        return [{**f, "is_set": bool(str(obj.config.get(f["key"], "")).strip())} for f in obj.fields]

    def to_representation(self, obj):
        data = super().to_representation(obj)
        secrets = {f["key"] for f in obj.fields if f.get("secret")}
        data["config"] = {k: ("" if k in secrets else v) for k, v in (obj.config or {}).items()}
        return data

    def validate_config(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Noto'g'ri format.")
        allowed = {f["key"]: f for f in self.instance.fields} if self.instance else {}
        merged = dict(self.instance.config or {}) if self.instance else {}
        for key, val in value.items():
            if key not in allowed:
                continue  # noma'lum maydonlar e'tiborsiz
            val = "" if val is None else str(val).strip()
            if allowed[key].get("secret") and not val:
                continue  # bo'sh maxfiy maydon — eskisini qoldiramiz
            merged[key] = val
        return merged

    def validate(self, attrs):
        instance = self.instance
        active = attrs.get("is_active", instance.is_active if instance else False)
        config = attrs.get("config", instance.config if instance else {})
        if active and instance:
            missing = [
                f["label"] for f in instance.fields
                if f.get("required") and not str(config.get(f["key"], "")).strip()
            ]
            if missing:
                raise serializers.ValidationError(
                    f"Yoqishdan oldin sozlamalarni to'ldiring: {', '.join(missing)}."
                )
        return attrs
