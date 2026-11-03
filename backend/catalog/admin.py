from django.contrib import admin

from .models import Banner, Brand, Category, Product, ProductImage, ProductSpec


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "order"]
    list_filter = ["parent"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductSpecInline(admin.TabularInline):
    model = ProductSpec
    extra = 3


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "brand", "price", "old_price", "stock", "is_active", "is_hit"]
    list_filter = ["is_active", "is_hit", "is_new", "category", "brand"]
    list_editable = ["price", "old_price", "stock", "is_active", "is_hit"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name", "sku", "description"]
    autocomplete_fields = ["category", "brand"]
    inlines = [ProductImageInline, ProductSpecInline]


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["title", "order", "is_active"]
    list_editable = ["order", "is_active"]
