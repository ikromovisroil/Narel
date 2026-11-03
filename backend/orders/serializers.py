from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from catalog.i18n import get_lang, localized
from catalog.models import Product
from payments.models import PaymentMethod
from staff.models import effective_permissions

from .models import Order, OrderItem

User = get_user_model()

MESSAGES = {
    "payment": {
        "uz": "Bu to'lov usuli hozir mavjud emas. Boshqasini tanlang.",
        "ru": "Этот способ оплаты сейчас недоступен. Выберите другой.",
    },
    "empty": {"uz": "Savat bo'sh.", "ru": "Корзина пуста."},
    "address": {"uz": "Yetkazish manzilini kiriting.", "ru": "Укажите адрес доставки."},
    "stock": {
        "uz": "\"{0}\" omborda yetarli emas (bor: {1}).",
        "ru": "Товара «{0}» недостаточно на складе (в наличии: {1}).",
    },
}


def message(request, key, *args):
    return MESSAGES[key][get_lang(request)].format(*args)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_staff", "is_superuser", "permissions"]
        read_only_fields = ["username", "is_staff", "is_superuser"]

    def get_permissions(self, obj):
        # Admin panel menyusi va tugmalari shunga qarab ko'rsatiladi
        return effective_permissions(obj)


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    product_slug = serializers.CharField(source="product.slug", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["product", "product_name", "product_slug", "price", "quantity", "subtotal"]
        read_only_fields = ["price", "subtotal"]

    def get_product_name(self, obj):
        return localized(obj.product, "name", get_lang(self.context.get("request")))


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    cart = OrderItemInputSerializer(many=True, write_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "full_name", "phone", "address", "note", "payment_method",
            "delivery_method", "status", "status_display", "total",
            "created_at", "items", "cart",
        ]
        read_only_fields = ["status", "total", "created_at"]

    def validate(self, attrs):
        # Faqat admin Sozlamalarda yoqqan to'lov usuli qabul qilinadi
        method = attrs.get("payment_method", Order.Payment.CASH)
        if method not in PaymentMethod.active_codes():
            raise serializers.ValidationError({"payment_method": message(self.context.get("request"), "payment")})
        if not attrs.get("cart"):
            raise serializers.ValidationError({"cart": message(self.context.get("request"), "empty")})
        if attrs.get("delivery_method") != Order.Delivery.PICKUP and not attrs.get("address"):
            raise serializers.ValidationError({"address": message(self.context.get("request"), "address")})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        cart = validated_data.pop("cart")
        ids = [row["product"].pk for row in cart]
        # Bir vaqtda ikki kishi oxirgi mahsulotni olmasligi uchun qatorlarni qulflaymiz
        products = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=ids)}

        order = Order.objects.create(**validated_data)
        total = 0
        for row in cart:
            product = products[row["product"].pk]
            qty = row["quantity"]
            if product.stock < qty:
                lang = get_lang(self.context.get("request"))
                raise serializers.ValidationError({"cart": message(
                    self.context.get("request"), "stock",
                    localized(product, "name", lang), product.stock,
                )})
            product.stock -= qty
            product.save(update_fields=["stock"])
            OrderItem.objects.create(order=order, product=product, price=product.price, quantity=qty)
            total += product.price * qty

        order.total = total
        order.save(update_fields=["total"])
        return order
