from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from catalog.models import Banner, Brand, Category, Product, ProductImage, ProductSpec
from catalog.ordering import place, renumber
from catalog.utils import unique_slug
from orders.models import Order
from orders.serializers import OrderItemSerializer

User = get_user_model()


class AutoSlugMixin:
    """slug foydalanuvchidan so'ralmaydi: yaratilganda nomdan avtomatik yasaladi
    va keyin o'zgarmaydi (saytdagi havolalar buzilmasligi uchun)."""

    def create(self, validated_data):
        validated_data["slug"] = unique_slug(self.Meta.model, validated_data["name"])
        return super().create(validated_data)


class OrderedMixin:
    """`order` maydoni: yozuv shu o'ringa qo'yiladi, qolganlar suriladi.
    Bo'sh qoldirilsa yangi yozuv guruh oxiriga qo'shiladi."""

    def scope(self, instance):
        return self.Meta.model.objects.all()

    @transaction.atomic
    def create(self, validated_data):
        position = validated_data.pop("order", None)
        instance = super().create(validated_data)
        place(instance, position, self.scope(instance))
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        position = validated_data.pop("order", None)
        old_scope = self.scope(instance)
        old_key = self.scope_key(instance)
        instance = super().update(instance, validated_data)
        moved = self.scope_key(instance) != old_key
        if moved:
            renumber(old_scope, exclude_pk=instance.pk)  # eski guruhda bo'shliq qolmasin
        if moved or position is not None:
            place(instance, position, self.scope(instance))
        return instance

    def scope_key(self, instance):
        return None


class CategorySerializer(OrderedMixin, AutoSlugMixin, serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)
    order = serializers.IntegerField(min_value=1, required=False, allow_null=True)

    def scope(self, instance):
        return Category.objects.filter(parent_id=instance.parent_id)

    def scope_key(self, instance):
        return instance.parent_id

    class Meta:
        model = Category
        fields = ["id", "name", "name_ru", "slug", "parent", "icon", "order", "products_count"]
        read_only_fields = ["slug", "icon"]

    def validate_parent(self, parent):
        node = parent
        while node is not None and self.instance:
            if node.pk == self.instance.pk:
                raise serializers.ValidationError("Kategoriya o'zining ichiga joylasha olmaydi.")
            node = node.parent
        return parent


class BrandSerializer(AutoSlugMixin, serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "logo", "products_count"]
        read_only_fields = ["slug", "logo"]


class BannerSerializer(OrderedMixin, serializers.ModelSerializer):
    order = serializers.IntegerField(min_value=1, required=False, allow_null=True)

    class Meta:
        model = Banner
        fields = ["id", "title", "title_ru", "subtitle", "subtitle_ru", "image", "link", "order", "is_active"]
        read_only_fields = ["image"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "order"]


class ProductSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpec
        fields = ["name", "value", "name_ru", "value_ru"]


class ProductSerializer(AutoSlugMixin, serializers.ModelSerializer):
    specs = ProductSpecSerializer(many=True, required=False)
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True, default=None)
    sold = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Product
        fields = [
            "id", "name", "name_ru", "slug", "sku", "description", "description_ru", "category", "category_name",
            "brand", "brand_name", "price", "old_price", "stock", "is_active", "is_hit",
            "is_new", "image", "images", "specs", "sold", "created_at", "updated_at",
        ]
        read_only_fields = ["slug", "image", "created_at", "updated_at"]

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
            ProductSpec(
                product=product, name=s["name"], value=s["value"],
                name_ru=s.get("name_ru", ""), value_ru=s.get("value_ru", ""), order=i,
            )
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
