from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Banner, Brand, Category, Product, ProductImage, ProductSpec


class DeletedFilter(admin.SimpleListFilter):
    title = "o'chirilganmi"
    parameter_name = "deleted"

    def lookups(self, request, model_admin):
        return [("no", "Yo'q (ishlatilmoqda)"), ("yes", "Ha (admin panelda o'chirilgan)")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(deleted_at__isnull=False)
        if self.value() == "no":
            return queryset.filter(deleted_at__isnull=True)
        return queryset


class SoftDeleteAdmin(admin.ModelAdmin):
    """Admin panelda o'chirilganlar shu yerda ko'rinadi va "Qaytarish" bilan tiklanadi."""

    actions = ["restore", "hide"]

    @admin.display(description="Holati", ordering="deleted_at")
    def state(self, obj):
        if obj.deleted_at:
            return format_html('<b style="color:#dc2626">O\'chirilgan</b><br><small>{}</small>',
                               timezone.localtime(obj.deleted_at).strftime("%d.%m.%Y %H:%M"))
        return format_html('<span style="color:#17a34a">{}</span>', "Ishlatilmoqda")

    @admin.action(description="Qaytarish (admin panel va saytga)")
    def restore(self, request, queryset):
        self.message_user(request, f"{queryset.update(deleted_at=None)} ta qaytarildi")

    @admin.action(description="O'chirish (yashirish, tarix saqlanadi)")
    def hide(self, request, queryset):
        self.message_user(request, f"{queryset.filter(deleted_at__isnull=True).update(deleted_at=timezone.now())} ta o'chirildi")


def thumb(image, size=48):
    if not image:
        return "—"
    return format_html('<img src="{}" style="height:{}px;max-width:{}px;object-fit:contain;border-radius:4px">',
                       image.url, size, size * 2)


@admin.register(Category)
class CategoryAdmin(SoftDeleteAdmin):
    list_display = ["name", "name_ru", "slug", "parent", "order", "products_count", "state"]
    list_filter = [DeletedFilter, "parent"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name", "name_ru", "slug"]
    autocomplete_fields = ["parent"]
    list_select_related = ["parent"]

    @admin.display(description="Mahsulotlar")
    def products_count(self, obj):
        return obj.products.count()


@admin.register(Brand)
class BrandAdmin(SoftDeleteAdmin):
    list_display = ["logo_preview", "name", "slug", "state"]
    list_filter = [DeletedFilter]
    list_display_links = ["logo_preview", "name"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name", "slug"]

    @admin.display(description="Logo")
    def logo_preview(self, obj):
        return thumb(obj.logo, 32)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["preview", "image", "order"]
    readonly_fields = ["preview"]

    @admin.display(description="Ko'rinishi")
    def preview(self, obj):
        return thumb(obj.image)


class ProductSpecInline(admin.TabularInline):
    model = ProductSpec
    extra = 1
    fields = ["name", "value", "name_ru", "value_ru", "order"]


@admin.register(Product)
class ProductAdmin(SoftDeleteAdmin):
    list_display = ["preview", "name", "sku", "category", "brand", "price", "old_price", "stock",
                    "is_active", "is_hit", "is_new", "state"]
    list_display_links = ["preview", "name"]
    list_filter = [DeletedFilter, "is_active", "is_hit", "is_new", "category", "brand", "created_at"]
    list_editable = ["price", "old_price", "stock", "is_active", "is_hit", "is_new"]
    list_select_related = ["category", "brand"]
    list_per_page = 50
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name", "name_ru", "sku", "slug", "description"]
    autocomplete_fields = ["category", "brand"]
    readonly_fields = ["preview_big", "created_at", "updated_at"]
    date_hierarchy = "created_at"
    inlines = [ProductImageInline, ProductSpecInline]
    actions = ["make_active", "make_inactive", "restore", "hide"]
    fieldsets = [
        (None, {"fields": ["name", "name_ru", "slug", "sku", "category", "brand"]}),
        ("Narx va ombor", {"fields": ["price", "old_price", "stock"]}),
        ("Rasm", {"fields": ["preview_big", "image"]}),
        ("Tavsif", {"fields": ["description", "description_ru"]}),
        ("Belgilar", {"fields": ["is_active", "is_hit", "is_new", "deleted_at"],
                      "description": "\"O'chirilgan vaqti\" to'ldirilgan bo'lsa — admin panelda va saytda ko'rinmaydi. "
                                     "Qaytarish uchun bo'shating."}),
        ("Vaqt", {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    @admin.display(description="Rasm")
    def preview(self, obj):
        return thumb(obj.image, 40)

    @admin.display(description="Ko'rinishi")
    def preview_big(self, obj):
        return thumb(obj.image, 160)

    @admin.action(description="Faol qilish (saytda ko'rinsin)")
    def make_active(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_active=True)} ta mahsulot faol qilindi")

    @admin.action(description="Nofaol qilish (saytdan yashirish)")
    def make_inactive(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_active=False)} ta mahsulot yashirildi")


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["preview", "title", "link", "order", "is_active"]
    list_display_links = ["preview", "title"]
    list_editable = ["order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["title", "title_ru", "subtitle"]
    readonly_fields = ["preview_big"]
    fields = ["title", "title_ru", "subtitle", "subtitle_ru", "preview_big", "image", "link", "order", "is_active"]

    @admin.display(description="Rasm")
    def preview(self, obj):
        return thumb(obj.image, 40)

    @admin.display(description="Ko'rinishi")
    def preview_big(self, obj):
        return thumb(obj.image, 160)
