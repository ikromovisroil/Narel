"""Do'kon va yetkazib berish sozlamalari: sayt uchun (o'qish) va admin uchun (tahrirlash)."""
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.i18n import get_lang, localized
from staff.permissions import SectionPermission

from rest_framework import viewsets

from dashboard.views import AdminMixin

from .branches import PublicBranchSerializer, active_branches
from .models import Branch, StoreSettings


class PublicStoreSettingsSerializer(serializers.ModelSerializer):
    delivery_note = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    working_hours = serializers.SerializerMethodField()

    class Meta:
        model = StoreSettings
        fields = [
            "delivery_enabled", "delivery_price", "delivery_days", "delivery_note", "pickup_enabled",
            "phone", "address", "working_hours", "map_url", "branches", "google_client_id",
        ]

    google_client_id = serializers.SerializerMethodField()

    def get_google_client_id(self, obj):
        from django.conf import settings
        return settings.GOOGLE_CLIENT_ID

    branches = serializers.SerializerMethodField()
    pickup_enabled = serializers.SerializerMethodField()

    def get_branches(self, obj):
        return PublicBranchSerializer(active_branches(), many=True, context=self.context).data

    def get_pickup_enabled(self, obj):
        # Faol filial bo'lmasa olib ketish ham yo'q
        return obj.pickup_enabled and active_branches().exists()

    def _lang(self):
        return get_lang(self.context.get("request"))

    def get_delivery_note(self, obj):
        return localized(obj, "delivery_note", self._lang())

    def get_address(self, obj):
        return localized(obj, "address", self._lang())

    def get_working_hours(self, obj):
        return localized(obj, "working_hours", self._lang())


class AdminStoreSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreSettings
        exclude = ["id"]
        read_only_fields = ["updated_at"]

    def validate(self, attrs):
        delivery = attrs.get("delivery_enabled", self.instance.delivery_enabled)
        pickup = attrs.get("pickup_enabled", self.instance.pickup_enabled)
        if pickup and not active_branches().exists():
            raise serializers.ValidationError("Olib ketishni yoqish uchun kamida bitta faol filial qo'shing.")
        if not delivery and not pickup:
            raise serializers.ValidationError(
                "Yetkazib berish va olib ketishni birdan o'chirib bo'lmaydi — mijozlar buyurtma bera olmay qoladi."
            )
        return attrs


class PublicStoreSettingsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(PublicStoreSettingsSerializer(StoreSettings.load(), context={"request": request}).data)


class AdminStoreSettingsView(APIView):
    permission_classes = [SectionPermission]
    section = "settings"

    def get(self, request):
        return Response(AdminStoreSettingsSerializer(StoreSettings.load()).data)

    def patch(self, request):
        serializer = AdminStoreSettingsSerializer(StoreSettings.load(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AdminBranchSerializer(serializers.ModelSerializer):
    orders_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Branch
        fields = [
            "id", "name", "name_ru", "address", "address_ru", "phone", "working_hours", "working_hours_ru",
            "map_url", "is_active", "order", "orders_count",
        ]

    def validate(self, attrs):
        # Oxirgi faol filialni o'chirib, mijozlarni buyurtmasiz qoldirmaslik
        deactivating = self.instance and self.instance.is_active and attrs.get("is_active") is False
        if deactivating:
            check_last_branch(self.instance)
        return attrs


def check_last_branch(branch):
    store = StoreSettings.load()
    others = active_branches().exclude(pk=branch.pk).exists()
    if not others and store.pickup_enabled and not store.delivery_enabled:
        raise serializers.ValidationError(
            "Bu oxirgi faol filial, yetkazib berish esa o'chiq — mijozlar buyurtma bera olmay qoladi."
        )


class AdminBranchViewSet(AdminMixin, viewsets.ModelViewSet):
    section = "settings"
    write_action = "change"  # filial qo'shish/o'zgartirish/o'chirish — "Sozlamalar: tahrirlash"
    serializer_class = AdminBranchSerializer
    pagination_class = None

    def get_queryset(self):
        from django.db.models import Count
        return Branch.objects.annotate(orders_count=Count("orders")).order_by("order", "id")

    def perform_destroy(self, instance):
        if instance.is_active:
            check_last_branch(instance)
        instance.delete()
