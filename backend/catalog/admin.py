from django.contrib import admin
from django.utils.html import format_html

from .models import Banner, Brand, Category, Product, ProductImage, ProductSpec


def thumb(image, size=48):
    if not image:
        return "—"
    return format_html('<img src="{}" style="height:{}px;max-width:{}px;object-fit:contain;border-radius:4px">',
                       image.url, size, size * 2)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "name_ru", "slug", "parent", "order", "products_count"]
    list_filter = ["parent"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name", "name_ru", "slug"]
    autocomplete_fields = ["parent"]
    list_select_related = ["parent"]

    @admin.display(description="Mahsulotlar")
    def products_count(self, obj):
        return obj.products.count()


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["logo_preview", "name", "slug"]
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
class ProductAdmin(admin.ModelAdmin):
    list_display = ["preview", "name", "sku", "category", "brand", "price", "old_price", "stock",
                    "is_active", "is_hit", "is_new"]
    list_display_links = ["preview", "name"]
    list_filter = ["is_active", "is_hit", "is_new", "category", "brand", "created_at"]
    list_editable = ["price", "old_price", "stock", "is_active", "is_hit", "is_new"]
    list_select_related = ["category", "brand"]
    list_per_page = 50
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name", "name_ru", "sku", "slug", "description"]
    autocomplete_fields = ["category", "brand"]
    readonly_fields = ["preview_big", "created_at", "updated_at"]
    date_hierarchy = "created_at"
    inlines = [ProductImageInline, ProductSpecInline]
    actions = ["make_active", "make_inactive"]
    fieldsets = [
        (None, {"fields": ["name", "name_ru", "slug", "sku", "category", "brand"]}),
        ("Narx va ombor", {"fields": ["price", "old_price", "stock"]}),
        ("Rasm", {"fields": ["preview_big", "image"]}),
        ("Tavsif", {"fields": ["description", "description_ru"]}),
        ("Belgilar", {"fields": ["is_active", "is_hit", "is_new"]}),
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
