import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from .i18n import has_cyrillic, to_latin

from .models import Banner, Brand, Category, Product
from .serializers import (
    BannerSerializer, BrandSerializer, CategorySerializer,
    ProductDetailSerializer, ProductListSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    pagination_class = None
    lookup_field = "slug"

    def get_queryset(self):
        qs = Category.objects.prefetch_related("children__children")
        # Ro'yxatda faqat yuqori darajadagilar (bolalari ichida keladi)
        if self.action == "list":
            qs = qs.filter(parent__isnull=True)
        return qs


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    pagination_class = None
    lookup_field = "slug"


class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Banner.objects.filter(is_active=True)
    serializer_class = BannerSerializer
    pagination_class = None


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method="filter_category")
    brand = django_filters.BaseInFilter(field_name="brand__slug")
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    discount = django_filters.BooleanFilter(method="filter_discount")

    class Meta:
        model = Product
        fields = ["is_hit", "is_new"]

    def filter_category(self, qs, name, value):
        # Kategoriya va uning ichki kategoriyalari bo'yicha
        return qs.filter(
            Q(category__slug=value)
            | Q(category__parent__slug=value)
            | Q(category__parent__parent__slug=value)
        )

    def filter_discount(self, qs, name, value):
        return qs.filter(old_price__isnull=False) if value else qs


class MultiScriptSearchFilter(SearchFilter):
    """Kirillcha so'rov ("музлатгич") lotin matndan ham, ruscha matndan ham qidiradi."""

    _override = None

    def get_search_terms(self, request):
        return self._override if self._override is not None else super().get_search_terms(request)

    def filter_queryset(self, request, queryset, view):
        found = super().filter_queryset(request, queryset, view)
        terms = self.get_search_terms(request)
        if not any(has_cyrillic(t) for t in terms):
            return found
        self._override = [to_latin(t) for t in terms]
        try:
            latin = super().filter_queryset(request, queryset, view)
        finally:
            self._override = None
        return queryset.filter(Q(pk__in=found.values("pk")) | Q(pk__in=latin.values("pk")))


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Product.objects.filter(is_active=True)
        .select_related("category", "brand")
        .prefetch_related("images", "specs")
    )
    lookup_field = "slug"
    filterset_class = ProductFilter
    filter_backends = [DjangoFilterBackend, MultiScriptSearchFilter, OrderingFilter]
    search_fields = ["name", "name_ru", "description", "description_ru", "brand__name", "sku"]
    ordering_fields = ["price", "created_at", "name"]

    def get_serializer_class(self):
        return ProductDetailSerializer if self.action == "retrieve" else ProductListSerializer
