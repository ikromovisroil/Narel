from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import CartItem, Order
from .serializers import OrderSerializer, UserSerializer


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class OrderPagination(PageNumberPagination):
    """Mijozning buyurtmalari 5 tadan: "Ko'proq ko'rish" har safar keyingi 5 tasini oladi."""

    page_size = 5


class OrderViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OrderPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # Swagger sxemasini yaratishda foydalanuvchi yo'q
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product")

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        CartItem.objects.filter(user=self.request.user, product_id__in=order.items.values("product_id")).delete()