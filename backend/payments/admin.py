from django import forms
from django.contrib import admin

from .models import PROVIDERS, PaymentMethod


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = "__all__"

    def clean(self):
        data = super().clean()
        code = data.get("code") or self.instance.code
        config = data.get("config") or {}
        if not isinstance(config, dict):
            self.add_error("config", "Sozlamalar {kalit: qiymat} ko'rinishida bo'lishi kerak.")
            return data
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
