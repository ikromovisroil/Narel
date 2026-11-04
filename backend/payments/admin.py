from django import forms
from django.contrib import admin

from .models import PROVIDERS, PaymentMethod


MASK = "********"


def secret_keys(code):
    return {f["key"] for f in PROVIDERS.get(code, {}).get("fields", []) if f.get("secret")}


class PaymentMethodForm(forms.ModelForm):
    """Maxfiy kalitlar sahifada "********" bo'lib ko'rinadi; o'zgartirilmasa eski qiymat saqlanadi."""

    class Meta:
        model = PaymentMethod
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and isinstance(self.instance.config, dict):
            secrets = secret_keys(self.instance.code)
            self.initial["config"] = {k: (MASK if k in secrets and v else v) for k, v in self.instance.config.items()}

    def clean(self):
        data = super().clean()
        code = data.get("code") or self.instance.code
        config = data.get("config") or {}
        if not isinstance(config, dict):
            self.add_error("config", "Sozlamalar {kalit: qiymat} ko'rinishida bo'lishi kerak.")
            return data
        old = self.instance.config if self.instance.pk and isinstance(self.instance.config, dict) else {}
        for key in secret_keys(code):
            if config.get(key) == MASK:
                config[key] = old.get(key, "")
        data["config"] = config
        if data.get("is_active"):
            fields = PROVIDERS.get(code, {}).get("fields", [])
            missing = [f["label"] for f in fields if f.get("required") and not str(config.get(f["key"], "")).strip()]
            if missing:
                self.add_error("is_active", "Yoqishdan oldin to'ldiring: " + ", ".join(missing))
        return data


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    form = PaymentMethodForm
    list_display = ["title", "code", "is_active", "test_mode", "configured", "order", "updated_at"]
    list_editable = ["order"]
    list_filter = ["is_active", "test_mode"]
    search_fields = ["title", "code"]
    readonly_fields = ["config_help", "updated_at"]
    fields = ["code", "title", "title_ru", "description", "description_ru", "logo", "is_active", "test_mode",
              "config_help", "config", "order", "updated_at"]

    @admin.display(description="Sozlangan", boolean=True)
    def configured(self, obj):
        return obj.is_configured

    @admin.display(description="Kerakli kalitlar")
    def config_help(self, obj):
        fields = obj.fields if obj and obj.pk else []
        if not fields:
            return "Bu usul uchun kalit kerak emas."
        return "; ".join(
            f"{f['key']} — {f['label']}{' (majburiy)' if f.get('required') else ''}" for f in fields
        )
