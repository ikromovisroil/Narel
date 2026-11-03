from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Banner, Brand, Category, Product, ProductImage
from catalog.ordering import renumber
from orders.models import Order, OrderItem
from staff.permissions import AnyStaff, SectionPermission

from . import serializers as s
from .images import public_rules, validate_image

User = get_user_model()
LOW_STOCK = 5
MONEY_ZERO = Value(0, output_field=DecimalField(max_digits=16, decimal_places=0))


class AdminPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200


class AdminMixin:
    # Har bir view o'z bo'limini `section` bilan belgilaydi (staff.models.SECTIONS)
    permission_classes = [SectionPermission]
    pagination_class = AdminPagination

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "O'chirib bo'lmaydi: unga bog'liq yozuvlar bor (mahsulot yoki buyurtma)."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UploadMixin:
    """POST /<id>/upload/ — rasm yuklash, DELETE — rasmni olib tashlash.
    upload_rule — images.RULES dagi talablar kaliti."""

    upload_field = "image"
    upload_rule = "product"

    @action(detail=True, methods=["post", "delete"], parser_classes=[MultiPartParser])
    def upload(self, request, pk=None):
        obj = self.get_object()
        field = getattr(obj, self.upload_field)
        if request.method == "DELETE":
            if field:
                field.delete(save=False)
            setattr(obj, self.upload_field, None)
        else:
            setattr(obj, self.upload_field, validate_image(request.FILES.get("file"), self.upload_rule))
        obj.save()
        return Response(self.get_serializer(obj).data)


class CategoryViewSet(AdminMixin, UploadMixin, viewsets.ModelViewSet):
    section = "categories"
    serializer_class = s.CategorySerializer
    pagination_class = None
    upload_field = "icon"
    upload_rule = "category"

    def perform_destroy(self, instance):
        scope = Category.objects.filter(parent_id=instance.parent_id)
        instance.delete()
        renumber(scope)
    queryset = Category.objects.annotate(products_count=Count("products")).order_by("order", "name")


class BrandViewSet(AdminMixin, UploadMixin, viewsets.ModelViewSet):
    section = "brands"
    serializer_class = s.BrandSerializer
    pagination_class = None
    upload_field = "logo"
    upload_rule = "brand"
    queryset = Brand.objects.annotate(products_count=Count("products"))
    search_fields = ["name"]


class BannerViewSet(AdminMixin, UploadMixin, viewsets.ModelViewSet):
    section = "banners"
    serializer_class = s.BannerSerializer
    pagination_class = None
    upload_rule = "banner"

    def perform_destroy(self, instance):
        instance.delete()
        renumber(Banner.objects.all())
    queryset = Banner.objects.all()


class ProductViewSet(AdminMixin, UploadMixin, viewsets.ModelViewSet):
    section = "products"
    serializer_class = s.ProductSerializer
    search_fields = ["name", "sku", "brand__name"]
    ordering_fields = ["name", "price", "stock", "created_at", "sold"]
    filterset_fields = ["category", "brand", "is_active", "is_hit", "is_new"]

    def get_queryset(self):
        qs = (
            Product.objects.select_related("category", "brand")
            .prefetch_related("images", "specs")
            .annotate(sold=Coalesce(
                Sum("orderitem__quantity", filter=~Q(orderitem__order__status=Order.Status.CANCELLED)), 0
            ))
            .order_by("-created_at")
        )
        if self.request.query_params.get("low_stock") == "true":
            qs = qs.filter(stock__lte=LOW_STOCK)
        return qs

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser])
    def images(self, request, pk=None):
        product = self.get_object()
        ProductImage.objects.create(
            product=product, image=validate_image(request.FILES.get("file"), "product"), order=product.images.count()
        )
        return Response(self.get_serializer(self.get_object()).data, status=status.HTTP_201_CREATED)


class ProductImageViewSet(AdminMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    section = "products"
    delete_action = "change"  # galereyadan rasm o'chirish — mahsulotni tahrirlash
    queryset = ProductImage.objects.all()

    def perform_destroy(self, instance):
        instance.image.delete(save=False)
        instance.delete()


class OrderViewSet(
    AdminMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin, viewsets.GenericViewSet,
):
    section = "orders"
    serializer_class = s.OrderSerializer
    search_fields = ["id", "full_name", "phone", "user__username"]
    ordering_fields = ["created_at", "total"]
    filterset_fields = {
        "status": ["exact"], "payment_method": ["exact"], "delivery_method": ["exact"],
        "user": ["exact"], "created_at": ["date__gte", "date__lte"],
    }

    def get_queryset(self):
        return (
            Order.objects.select_related("user")
            .prefetch_related("items__product")
            .annotate(items_count=Sum("items__quantity"))
            .order_by("-created_at")
        )


class CustomerViewSet(AdminMixin, viewsets.ReadOnlyModelViewSet):
    section = "customers"
    serializer_class = s.CustomerSerializer
    search_fields = ["username", "first_name", "last_name", "email", "profile__phone"]
    ordering_fields = ["date_joined", "orders_count", "total_spent"]
    filterset_fields = ["is_staff"]

    def get_queryset(self):
        paid = ~Q(orders__status=Order.Status.CANCELLED)
        return User.objects.annotate(
            orders_count=Count("orders", distinct=True),
            total_spent=Coalesce(Sum("orders__total", filter=paid), MONEY_ZERO),
        ).order_by("-date_joined")


class StatsView(APIView):
    permission_classes = [SectionPermission]
    section = "dashboard"

    def get(self, request):
        now = timezone.localtime()
        today = now.date()
        month_start = today.replace(day=1)
        days = 30
        since = today - timedelta(days=days - 1)

        valid = Order.objects.exclude(status=Order.Status.CANCELLED)

        def summary(qs):
            r = qs.aggregate(revenue=Coalesce(Sum("total"), MONEY_ZERO), orders=Count("id"))
            return {"revenue": int(r["revenue"]), "orders": r["orders"]}

        daily = {
            row["day"]: row
            for row in valid.filter(created_at__date__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(revenue=Sum("total"), orders=Count("id"))
        }
        chart = []
        for i in range(days):
            d = since + timedelta(days=i)
            row = daily.get(d, {})
            chart.append({
                "date": d.isoformat(),
                "revenue": int(row.get("revenue") or 0),
                "orders": row.get("orders", 0),
            })

        top = (
            OrderItem.objects.exclude(order__status=Order.Status.CANCELLED)
            .values("product_id", "product__name")
            .annotate(qty=Sum("quantity"))
        )
        top = [
            {"id": r["product_id"], "name": r["product__name"], "qty": r["qty"]}
            for r in top.order_by("-qty")[:5]
        ]

        status_counts = dict(Order.objects.values_list("status").annotate(c=Count("id")))

        return Response({
            "today": summary(valid.filter(created_at__date=today)),
            "month": summary(valid.filter(created_at__date__gte=month_start)),
            "total": summary(valid),
            "new_orders": status_counts.get(Order.Status.NEW, 0),
            "status_counts": status_counts,
            "products": Product.objects.count(),
            "customers": User.objects.filter(is_staff=False).count(),
            "low_stock": list(
                Product.objects.filter(is_active=True, stock__lte=LOW_STOCK)
                .order_by("stock").values("id", "name", "stock")[:10]
            ),
            "top_products": top,
            "chart": chart,
            "recent_orders": s.OrderSerializer(
                Order.objects.select_related("user").prefetch_related("items__product")
                .order_by("-created_at")[:6], many=True
            ).data,
        })


class ImageRulesView(APIView):
    permission_classes = [AnyStaff]

    def get(self, request):
        return Response(public_rules())
