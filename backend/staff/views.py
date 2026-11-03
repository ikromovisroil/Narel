from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from dashboard.views import AdminMixin

from .models import SECTIONS
from .serializers import StaffSerializer

User = get_user_model()


class StaffViewSet(AdminMixin, viewsets.ModelViewSet):
    section = "staff"
    serializer_class = StaffSerializer
    pagination_class = None
    search_fields = ["username", "first_name", "last_name", "email", "staff_profile__position"]

    def get_queryset(self):
        return User.objects.filter(is_staff=True).select_related("staff_profile").order_by("-is_superuser", "username")

    def destroy(self, request, *args, **kwargs):
        target = self.get_object()
        if target.pk == request.user.pk:
            return Response({"detail": "O'zingizni o'chira olmaysiz."}, status=status.HTTP_400_BAD_REQUEST)
        if target.is_superuser and not request.user.is_superuser:
            return Response({"detail": "Super adminni faqat super admin o'chira oladi."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def sections(self, request):
        return Response([{"code": c, "title": t, "actions": a} for c, t, a in SECTIONS])
