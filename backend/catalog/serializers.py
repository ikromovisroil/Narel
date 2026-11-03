from rest_framework import serializers

from .models import Banner, Brand, Category, Product, ProductImage, ProductSpec


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "parent", "children"]

    def get_children(self, obj):
        return CategorySerializer(obj.children.all(), many=True, context=self.context).data


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "logo"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


class ProductSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpec
        fields = ["name", "value"]


class ProductListSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "price", "old_price", "discount_percent",
            "monthly_price", "stock", "image", "brand", "category", "is_hit", "is_new",
        ]


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    specs = ProductSpecSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ["sku", "description", "images", "specs"]


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "title", "subtitle", "image", "link"]
