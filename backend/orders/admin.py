from django import forms
from django.contrib import admin
from django.db import transaction
from django.db.models import F, Sum
from django.shortcuts import redirect
from django.urls import reverse

from catalog.models import Product

from .models import (
    Branch, CustomerProfile, IntegrationSettings, Order, OrderItem, PhoneCode, SmsLog, StoreSettings,
)

CLOSED = (Order.Status.DELIVERED, Order.Status.CANCELLED)


# ---------- Buyurtmalar ----------
# React admin bilan bir xil qoidalar: bekor qilinganda mahsulot omborga qaytadi,
# bekor qilingani qayta tiklanmaydi, qabul qilingandagi sana "va'da" sifatida saqlanadi.

class OrderItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        order = self.instance
        if order.pk and order.status == Order.Status.CANCELLED:
            return
        need = {}
        for form in self.forms:
            data = getattr(form, "cleaned_data", None) or {}
            old = form.instance if form.instance.pk else None
            if old:  # eski qator omborga qaytgan deb hisoblaymiz
                old_db = OrderItem.objects.filter(pk=old.pk).values_list("product_id", "quantity").first()
                if old_db:
                    need[old_db[0]] = need.get(old_db[0], 0) - old_db[1]
            if data.get("DELETE") or not data.get("product"):
                continue
            product = data["product"]
            need[product.pk] = need.get(product.pk, 0) + (data.get("quantity") or 0)
        for product in Product.objects.filter(pk__in=[pk for pk, n in need.items() if n > 0]):
            if need[product.pk] > product.stock:
                raise forms.ValidationError(
                    f"«{product.name}» omborda yetarli emas: qoldiq {product.stock} ta, yana {need[product.pk]} ta kerak."
                )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    formset = OrderItemFormSet
    extra = 0
    fields = ["product", "price", "quantity", "subtotal_display"]
    readonly_fields = ["subtotal_display"]
    autocomplete_fields = ["product"]
    verbose_name_plural = "Mahsulotlar (o'zgartirilsa ombor qoldig'i va jami summa avtomatik qayta hisoblanadi)"

    @admin.display(description="Summa")
    def subtotal_display(self, obj):
        return f"{obj.subtotal:,.0f}".replace(",", " ") if obj.pk else "—"

    def _closed(self, obj):
        return obj is not None and obj.status in CLOSED

    def get_readonly_fields(self, request, obj=None):
        if self._closed(obj):
            return ["product", "price", "quantity", "subtotal_display"]
        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request, obj=None):
        return not self._closed(obj) and super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return not self._closed(obj) and super().has_delete_permission(request, obj)


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"

    def clean_status(self):
        status = self.cleaned_data["status"]
        if self.instance.pk and self.instance.status == Order.Status.CANCELLED and status != Order.Status.CANCELLED:
            raise forms.ValidationError("Bekor qilingan buyurtmani qayta tiklab bo'lmaydi.")
        return status


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderForm
    list_display = ["id", "full_name", "phone", "payment_method", "delivery_method", "status",
                    "expected_date", "total", "created_at"]
    list_display_links = ["id", "full_name"]
    list_filter = ["status", "payment_method", "delivery_method", "pickup_branch", "created_at"]
    list_select_related = ["user", "pickup_branch"]
    list_per_page = 50
    search_fields = ["id", "full_name", "phone", "address", "user__profile__phone", "user__email"]
    date_hierarchy = "created_at"
    autocomplete_fields = ["user", "pickup_branch"]
    readonly_fields = ["total", "created_at", "is_delayed_display"]
    inlines = [OrderItemInline]
    actions = ["mark_confirmed", "mark_shipped", "mark_delivered", "mark_cancelled"]
    fieldsets = [
        ("Mijoz", {"fields": ["user", "full_name", "phone", "address", "note"]}),
        ("Holat", {"fields": ["status", "payment_method", "created_at"]}),
        ("Yetkazish", {"fields": ["delivery_method", "delivery_price", "expected_date", "original_expected_date",
                                  "delay_note", "is_delayed_display", "pickup_branch", "pickup_point"]}),
        ("Summa", {"fields": ["total"]}),
    ]

    @admin.display(description="Kechikkan", boolean=True)
    def is_delayed_display(self, obj):
        return obj.is_delayed

    @staticmethod
    def _return_stock(order):
        for item in order.items.all():
            Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        old = Order.objects.filter(pk=obj.pk).first() if change else None
        if old:
            if obj.status == Order.Status.CANCELLED and old.status != Order.Status.CANCELLED:
                self._return_stock(old)
            accepting = old.status == Order.Status.NEW and obj.status in (Order.Status.CONFIRMED, Order.Status.SHIPPED)
            if accepting and obj.expected_date and not obj.original_expected_date:
                obj.original_expected_date = obj.expected_date
        super().save_model(request, obj, form, change)

    @transaction.atomic
    def save_formset(self, request, form, formset, change):
        order = form.instance
        if formset.model is not OrderItem or order.status == Order.Status.CANCELLED:
            return super().save_formset(request, form, formset, change)
        # Ombor qoldig'ini o'zgarishga qarab to'g'rilash
        before = {i.pk: (i.product_id, i.quantity) for i in OrderItem.objects.filter(order=order)}
        instances = formset.save(commit=False)
        for item in formset.deleted_objects:
            product_id, qty = before.get(item.pk, (item.product_id, 0))
            Product.objects.filter(pk=product_id).update(stock=F("stock") + qty)
            item.delete()
        for item in instances:
            if item.pk in before:
                old_product, old_qty = before[item.pk]
                Product.objects.filter(pk=old_product).update(stock=F("stock") + old_qty)
            if not item.price:
                item.price = item.product.price
            Product.objects.filter(pk=item.product_id).update(stock=F("stock") - item.quantity)
            item.save()
        formset.save_m2m()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        order = form.instance
        items = OrderItem.objects.filter(order=order).aggregate(s=Sum(F("price") * F("quantity")))["s"] or 0
        total = items + (order.delivery_price if order.delivery_method == Order.Delivery.COURIER else 0)
        Order.objects.filter(pk=order.pk).update(total=total)

    def _set_status(self, request, queryset, status):
        done = 0
        with transaction.atomic():
            for order in queryset.select_related(None).select_for_update(of=("self",)):
                if order.status == Order.Status.CANCELLED or order.status == status:
                    continue
                if status == Order.Status.CANCELLED:
                    self._return_stock(order)
                order.status = status
                if status in (Order.Status.CONFIRMED, Order.Status.SHIPPED) and order.expected_date \
                        and not order.original_expected_date:
                    order.original_expected_date = order.expected_date
                order.save(update_fields=["status", "original_expected_date"])
                done += 1
        self.message_user(request, f"{done} ta buyurtma holati o'zgartirildi (bekor qilinganlar o'zgarmaydi)")

    @admin.action(description="Holat: Tasdiqlangan")
    def mark_confirmed(self, request, queryset):
        self._set_status(request, queryset, Order.Status.CONFIRMED)

    @admin.action(description="Holat: Yuborilgan")
    def mark_shipped(self, request, queryset):
        self._set_status(request, queryset, Order.Status.SHIPPED)

    @admin.action(description="Holat: Yetkazilgan")
    def mark_delivered(self, request, queryset):
        self._set_status(request, queryset, Order.Status.DELIVERED)

    @admin.action(description="Holat: Bekor qilingan (mahsulotlar omborga qaytadi)")
    def mark_cancelled(self, request, queryset):
        self._set_status(request, queryset, Order.Status.CANCELLED)


# ---------- Filiallar ----------

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "address", "phone", "working_hours", "order", "is_active"]
    list_editable = ["order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "name_ru", "address", "phone"]


# ---------- Do'kon sozlamalari (yagona yozuv) ----------

@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    readonly_fields = ["updated_at"]
    fieldsets = [
        ("Yetkazib berish", {"fields": ["delivery_enabled", "delivery_price", "delivery_days",
                                        "delivery_note", "delivery_note_ru"]}),
        ("Olib ketish", {"fields": ["pickup_enabled"]}),
        ("Asosiy aloqa", {"fields": ["phone", "address", "address_ru", "working_hours", "working_hours_ru", "map_url"]}),
        ("Ommaviy oferta", {"fields": ["offer_text", "offer_text_ru"], "classes": ["collapse"],
                            "description": "Bo'limlar \"# \" bilan boshlanadi. [Kvadrat qavs] ichidagilarni to'ldiring."}),
        (None, {"fields": ["updated_at"]}),
    ]

    def changelist_view(self, request, extra_context=None):
        # Ro'yxat o'rniga to'g'ridan-to'g'ri yagona yozuvni ochamiz
        obj = StoreSettings.load()
        return redirect(reverse("admin:orders_storesettings_change", args=[obj.pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ---------- Mijoz profillari ----------

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "full_name", "phone", "address"]
    list_select_related = ["user"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "user__email", "phone", "address"]
    autocomplete_fields = ["user"]

    @admin.display(description="F.I.Sh.")
    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or "—"


# ---------- SMS kodlar (faqat ko'rish) ----------
# Kodning o'zi saqlanmaydi (faqat xeshi). O'chirish mumkin — masalan, mijoz kunlik limitga
# yetib qolsa, uning yozuvlarini o'chirib limitni bo'shatish uchun.

@admin.register(PhoneCode)
class PhoneCodeAdmin(admin.ModelAdmin):
    list_display = ["phone", "created_at", "attempts", "used", "ip"]
    list_filter = ["used", "created_at"]
    search_fields = ["phone", "ip"]
    date_hierarchy = "created_at"
    exclude = ["code_hash"]
    readonly_fields = ["phone", "created_at", "attempts", "used", "ip"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ---------- Integratsiyalar (SMS, Google) — yagona yozuv ----------

@admin.register(IntegrationSettings)
class IntegrationSettingsAdmin(admin.ModelAdmin):
    readonly_fields = ["updated_at"]
    fieldsets = [
        ("SMS (Eskiz.uz)", {"fields": ["sms_enabled", "eskiz_email", "eskiz_password", "eskiz_from",
                                       "sms_low_balance", "sms_otp_domain"],
                            "description": "Bo'sh maydon o'rniga .env dagi qiymat ishlatiladi. "
                                           "Yo'riqnoma: admin panel → Sozlamalar → Integratsiyalar."}),
        ("Google orqali kirish", {"fields": ["google_client_id", "google_ios_client_id", "google_android_client_id"]}),
        (None, {"fields": ["updated_at"]}),
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "eskiz_password":
            # Parol sahifaga chiqmaydi; bo'sh qoldirilsa eskisi saqlanadi
            kwargs["widget"] = forms.PasswordInput(render_value=False, attrs={"placeholder": "o'zgartirmaslik uchun bo'sh qoldiring"})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if change and not form.cleaned_data.get("eskiz_password"):
            obj.eskiz_password = IntegrationSettings.objects.get(pk=obj.pk).eskiz_password
        super().save_model(request, obj, form, change)
        from .sms import forget_token
        forget_token()

    def changelist_view(self, request, extra_context=None):
        return redirect(reverse("admin:orders_integrationsettings_change", args=[IntegrationSettings.load().pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ---------- SMS tarixi (faqat ko'rish) ----------

@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "phone", "status", "short_error", "provider_id"]
    list_filter = ["status", "created_at"]
    search_fields = ["phone", "error", "provider_id"]
    date_hierarchy = "created_at"

    @admin.display(description="Xato sababi")
    def short_error(self, obj):
        return obj.error[:80] or "—"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
