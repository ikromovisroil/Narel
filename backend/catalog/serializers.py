from rest_framework import serializers

from .i18n import get_lang, localized
from .models import Banner, Brand, Category, Product, ProductImage, ProductSpec


class LangMixin:
    """So'rov tilini (uz / ru) aniqlaydi."""

    @property
    def lang(self):
        if not hasattr(self, "_lang"):
            self._lang = get_lang(self.context.get("request"))
        return self._lang


class CategorySerializer(LangMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "parent", "children"]

    def get_name(self, obj):
        return localized(obj, "name", self.lang)

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


class ProductSpecSerializer(LangMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = ProductSpec
        fields = ["name", "value"]

    def get_name(self, obj):
        return localized(obj, "name", self.lang)

    def get_value(self, obj):
        return localized(obj, "value", self.lang)


class ProductListSerializer(LangMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    brand = BrandSerializer(read_only=True)
    category = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "price", "old_price", "discount_percent",
            "monthly_price", "stock", "image", "brand", "category", "is_hit", "is_new",
        ]

    def get_name(self, obj):
        return localized(obj, "name", self.lang)


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    specs = ProductSpecSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    description = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ["sku", "description", "images", "specs"]

    def get_description(self, obj):
        return localized(obj, "description", self.lang)


class BannerSerializer(LangMixin, serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = ["id", "title", "subtitle", "image", "link"]

    def get_title(self, obj):
        return localized(obj, "title", self.lang)

    def get_subtitle(self, obj):
        return localized(obj, "subtitle", self.lang)
