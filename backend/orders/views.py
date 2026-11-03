from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import Order
from .serializers import OrderSerializer, UserSerializer


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class OrderViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)