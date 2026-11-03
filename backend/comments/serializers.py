from rest_framework import serializers

from .models import Comment


def author_name(user):
    return f"{user.first_name} {user.last_name}".strip() or user.username


class CommentSerializer(serializers.ModelSerializer):
    """Saytdagi izoh: muallif nomi, do'kon xodimimi, javoblar."""

    author = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "parent", "author", "is_staff", "is_mine", "text", "rating", "created_at", "replies"]
        read_only_fields = ["created_at"]
        extra_kwargs = {"parent": {"required": False, "allow_null": True}}

    def get_author(self, obj):
        return author_name(obj.user)

    def get_is_staff(self, obj):
        return obj.user.is_staff

    def get_is_mine(self, obj):
        user = self.context["request"].user
        return user.is_authenticated and obj.user_id == user.pk

    def get_replies(self, obj):
        if obj.parent_id:
            return []
        # oldindan yuklangan ko'rinadigan javoblar (views.py da prefetch)
        replies = getattr(obj, "visible_replies", None)
        if replies is None:
            replies = obj.replies.filter(is_hidden=False).select_related("user").order_by("created_at", "id")
        return CommentSerializer(replies, many=True, context=self.context).data

    def validate_text(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Izoh juda qisqa.")
        return value

    def validate(self, attrs):
        product = self.context["product"]
        parent = attrs.get("parent")
        if parent:
            if parent.product_id != product.pk or parent.is_hidden:
                raise serializers.ValidationError({"parent": "Bunday izoh topilmadi."})
            if parent.parent_id:
                attrs["parent"] = parent.parent  # javobga javob — o'sha suhbatga qo'shiladi
            attrs["rating"] = None  # baho faqat asosiy izohda
        return attrs


class AdminCommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    parent_text = serializers.CharField(source="parent.text", read_only=True, default=None)
    replies_count = serializers.IntegerField(read_only=True, default=0)
    staff_replied = serializers.BooleanField(read_only=True, default=False)
    is_staff = serializers.BooleanField(source="user.is_staff", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id", "product", "product_name", "product_slug", "author", "username", "is_staff", "parent",
            "parent_text", "text", "rating", "is_hidden", "replies_count", "staff_replied", "created_at",
        ]
        read_only_fields = [f for f in fields if f != "is_hidden"]

    def get_author(self, obj):
        return author_name(obj.user)
