from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "price", "quantity"]
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "full_name", "phone", "payment_method", "status", "total", "created_at"]
    list_filter = ["status", "payment_method", "delivery_method", "created_at"]
    list_editable = ["status"]
    search_fields = ["id", "full_name", "phone"]
    readonly_fields = ["user", "total", "created_at"]
    inlines = [OrderItemInline]
