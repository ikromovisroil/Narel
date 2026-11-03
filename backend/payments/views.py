from rest_framework import mixins, permissions, viewsets

from dashboard.views import UploadMixin
from staff.permissions import SectionPermission

from .models import PaymentMethod
from .serializers import AdminPaymentMethodSerializer, PublicPaymentMethodSerializer


class PublicPaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """Saytdagi buyurtma sahifasi uchun: faqat yoqilgan usullar."""

    serializer_class = PublicPaymentMethodSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = PaymentMethod.objects.filter(is_active=True)
    lookup_field = "code"


class AdminPaymentMethodViewSet(
    UploadMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    serializer_class = AdminPaymentMethodSerializer
    permission_classes = [SectionPermission]
    section = "settings"
    pagination_class = None
    queryset = PaymentMethod.objects.all()
    upload_field = "logo"
    upload_rule = "payment_logo"
