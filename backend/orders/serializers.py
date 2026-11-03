from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from catalog.models import Product

from .models import Order, OrderItem

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["product", "product_name", "product_slug", "price", "quantity", "subtotal"]
        read_only_fields = ["price", "subtotal"]


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
        if not attrs.get("cart"):
            raise serializers.ValidationError({"cart": "Savat bo'sh."})
        if attrs.get("delivery_method") != Order.Delivery.PICKUP and not attrs.get("address"):
            raise serializers.ValidationError({"address": "Yetkazish manzilini kiriting."})
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
                raise serializers.ValidationError(
                    {"cart": f"\"{product.name}\" omborda yetarli emas (bor: {product.stock})."}
                )
            product.stock -= qty
            product.save(update_fields=["stock"])
            OrderItem.objects.create(order=order, product=product, price=product.price, quantity=qty)
            total += product.price * qty

        order.total = total
        order.save(update_fields=["total"])
        return order
