from django.contrib import admin

from .models import Comment


class ReplyInline(admin.TabularInline):
    model = Comment
    fk_name = "parent"
    extra = 0
    fields = ["user", "text", "is_hidden", "created_at"]
    readonly_fields = ["created_at"]
    autocomplete_fields = ["user"]
    verbose_name = "Javob"
    verbose_name_plural = "Javoblar"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["short_text", "product", "user", "rating", "is_reply", "is_hidden", "created_at"]
    list_filter = ["is_hidden", "rating", "created_at"]
    list_editable = ["is_hidden"]
    list_select_related = ["product", "user"]
    list_per_page = 50
    search_fields = ["text", "product__name", "user__first_name", "user__last_name", "user__profile__phone"]
    autocomplete_fields = ["product", "user"]
    raw_id_fields = ["parent"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
    inlines = [ReplyInline]
    actions = ["hide", "show"]

    @admin.display(description="Matn")
    def short_text(self, obj):
        return obj.text[:80] + ("…" if len(obj.text) > 80 else "")

    @admin.display(description="Javob", boolean=True)
    def is_reply(self, obj):
        return obj.parent_id is not None

    def save_formset(self, request, form, formset, change):
        # Javob ham o'sha mahsulotga tegishli bo'lsin
        for item in formset.save(commit=False):
            item.product = form.instance.product
            item.save()
        for item in formset.deleted_objects:
            item.delete()

    @admin.action(description="Yashirish")
    def hide(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_hidden=True)} ta izoh yashirildi")

    @admin.action(description="Ko'rsatish")
    def show(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_hidden=False)} ta izoh ko'rsatildi")
