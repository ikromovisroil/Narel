from django.contrib import admin
from django.utils.html import format_html

from .models import AuditLog

COLORS = {
    "login": "#17a34a", "logout": "#6b7280", "login_failed": "#dc2626",
    "create": "#1f5eff", "update": "#ca8a04", "delete": "#dc2626", "action": "#7c3aed",
}


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Faqat superuser ko'radi. Qo'shib ham, o'zgartirib ham bo'lmaydi — jurnal ishonchli bo'lishi uchun."""

    list_display = ["created_at", "who_col", "action_col", "section", "object_id", "status_code", "ip"]
    list_filter = ["action", "is_staff", "section", "created_at"]
    search_fields = ["who", "ip", "path", "details", "object_id", "user__username", "user__email"]
    date_hierarchy = "created_at"
    list_per_page = 100
    list_select_related = ["user"]
    fields = ["created_at", "who", "user", "is_staff", "action", "section", "object_id", "method", "path",
              "status_code", "details", "ip", "user_agent"]
    readonly_fields = fields

    @admin.display(description="Kim", ordering="who")
    def who_col(self, obj):
        mark = " 👤" if obj.is_staff else ""
        return f"{obj.who or '—'}{mark}"

    @admin.display(description="Harakat", ordering="action")
    def action_col(self, obj):
        failed = obj.status_code and obj.status_code >= 400 and obj.action != "login_failed"
        label = obj.get_action_display() + (" (rad etildi)" if failed else "")
        return format_html('<b style="color:{}">{}</b>', "#dc2626" if failed else COLORS.get(obj.action, "#111"), label)

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
