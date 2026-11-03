from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from catalog.models import Banner, Brand, Category, Product, ProductImage, ProductSpec
from catalog.utils import unique_slug
from orders.models import Order
from orders.serializers import OrderItemSerializer

User = get_user_model()


class AutoSlugMixin:
    """slug bo'sh qolsa nomdan avtomatik yasaladi."""

    slug_source = "name"

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get("slug"):
            text = attrs.get(self.slug_source) or getattr(self.instance, self.slug_source, "")
            if self.instance and "slug" not in attrs:
                return attrs
            attrs["slug"] = unique_slug(
                self.Meta.model, text, self.instance.pk if self.instance else None
            )
        return attrs


class CategorySerializer(AutoSlugMixin, serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "icon", "order", "products_count"]
        read_only_fields = ["icon"]

    def validate_slug(self, value):
        if value and Category.objects.exclude(pk=getattr(self.instance, "pk", None)).filter(slug=value).exists():
            raise serializers.ValidationError("Bu slug band.")
        return value

    def validate_parent(self, parent):
        node = parent
        while node is not None and self.instance:
            if node.pk == self.instance.pk:
                raise serializers.ValidationError("Kategoriya o'zining ichiga joylasha olmaydi.")
            node = node.parent
        return parent


class BrandSerializer(AutoSlugMixin, serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "logo", "products_count"]
        read_only_fields = ["logo"]

    def validate_slug(self, value):
        if value and Brand.objects.exclude(pk=getattr(self.instance, "pk", None)).filter(slug=value).exists():
            raise serializers.ValidationError("Bu slug band.")
        return value


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "title", "subtitle", "image", "link", "order", "is_active"]
        read_only_fields = ["image"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "order"]


class ProductSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpec
        fields = ["name", "value"]


class ProductSerializer(AutoSlugMixin, serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True, max_length=220)
    specs = ProductSpecSerializer(many=True, required=False)
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True, default=None)
    sold = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "sku", "description", "category", "category_name",
            "brand", "brand_name", "price", "old_price", "stock", "is_active", "is_hit",
            "is_new", "image", "images", "specs", "sold", "created_at", "updated_at",
        ]
        read_only_fields = ["image", "created_at", "updated_at"]

    def validate_slug(self, value):
        if value and Product.objects.exclude(pk=getattr(self.instance, "pk", None)).filter(slug=value).exists():
            raise serializers.ValidationError("Bu slug band.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        price = attrs.get("price", getattr(self.instance, "price", None))
        old = attrs.get("old_price", getattr(self.instance, "old_price", None))
        if old is not None and price is not None and old <= price:
            raise serializers.ValidationError({"old_price": "Eski narx joriy narxdan katta bo'lishi kerak."})
        return attrs

    def _save_specs(self, product, specs):
        if specs is None:
            return
        product.specs.all().delete()
        ProductSpec.objects.bulk_create(
            ProductSpec(product=product, name=s["name"], value=s["value"], order=i)
            for i, s in enumerate(specs)
        )

    @transaction.atomic
    def create(self, validated_data):
        specs = validated_data.pop("specs", None)
        product = super().create(validated_data)
        self._save_specs(product, specs)
        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        specs = validated_data.pop("specs", None)
        product = super().update(instance, validated_data)
        self._save_specs(product, specs)
        return product


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    items_count = serializers.IntegerField(read_only=True, default=None)

    class Meta:
        model = Order
        fields = [
            "id", "user", "username", "full_name", "phone", "address", "note",
            "payment_method", "delivery_method", "status", "total", "items_count",
            "created_at", "items",
        ]
        read_only_fields = [f for f in fields if f != "status"]

    def validate_status(self, value):
        if self.instance and self.instance.status == Order.Status.CANCELLED and value != Order.Status.CANCELLED:
            raise serializers.ValidationError("Bekor qilingan buyurtmani qayta tiklab bo'lmaydi.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        new_status = validated_data.get("status")
        if new_status == Order.Status.CANCELLED and instance.status != Order.Status.CANCELLED:
            # Bekor qilinganda mahsulotlar omborga qaytadi
            for item in instance.items.all():
                Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
        return super().update(instance, validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    orders_count = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(max_digits=16, decimal_places=0, read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email", "is_staff",
            "is_active", "date_joined", "last_login", "orders_count", "total_spent",
        ]
        read_only_fields = fields
