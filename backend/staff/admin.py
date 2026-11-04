import json

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from orders.models import CustomerProfile

from .models import SECTIONS, StaffProfile, clean_permissions

PERMISSIONS_HELP = "Masalan: {\"orders\": [\"view\", \"change\"], \"products\": [\"view\"]}. Bo'limlar: " + ", ".join(
    f"{code} ({'/'.join(actions)})" for code, _, actions in SECTIONS
) + ". Superuser hamma bo'limga kira oladi."


class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ["user", "position", "permissions"]
        help_texts = {"permissions": PERMISSIONS_HELP}

    def clean_permissions(self):
        raw = self.cleaned_data.get("permissions") or {}
        if not isinstance(raw, dict):
            raise forms.ValidationError("Ruxsatlar {bo'lim: [amallar]} ko'rinishida bo'lishi kerak.")
        return clean_permissions(raw)


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    form = StaffProfileForm
    list_display = ["user", "full_name", "position", "sections", "is_active", "updated_at"]
    list_select_related = ["user"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "position"]
    list_filter = ["user__is_active"]

    def get_readonly_fields(self, request, obj=None):
        return ["user"] if obj else []

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(is_staff=True, staff_profile__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description="F.I.Sh.")
    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or "—"

    @admin.display(description="Ruxsatlar")
    def sections(self, obj):
        return json.dumps(obj.permissions, ensure_ascii=False)[:120] or "—"

    @admin.display(description="Faol", boolean=True)
    def is_active(self, obj):
        return obj.user.is_active


# ---------- Foydalanuvchilar: mijoz va xodim ma'lumotlari bir joyda ----------

class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    extra = 0
    max_num = 1
    verbose_name_plural = "Mijoz ma'lumotlari (telefon — kirish uchun ishlatiladi)"


class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    form = StaffProfileForm
    can_delete = False
    extra = 0
    max_num = 1
    verbose_name_plural = "Xodim: lavozim va admin panel ruxsatlari"


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [CustomerProfileInline, StaffProfileInline]
    list_display = ["username", "first_name", "last_name", "phone", "email", "is_staff", "is_superuser",
                    "is_active", "date_joined"]
    list_select_related = ["profile"]
    list_filter = ["is_staff", "is_superuser", "is_active", "date_joined"]
    search_fields = ["username", "first_name", "last_name", "email", "profile__phone"]
    list_per_page = 50

    @admin.display(description="Telefon", ordering="profile__phone")
    def phone(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.phone if profile else "—"
