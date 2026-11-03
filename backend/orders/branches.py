"""Filiallar: sayt uchun serializer (boshqa modullarga bog'liq emas — aylana import bo'lmasin)."""
from rest_framework import serializers

from catalog.i18n import get_lang, localized

from .models import Branch


def active_branches():
    return Branch.objects.filter(is_active=True)


class PublicBranchSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    working_hours = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = ["id", "name", "address", "phone", "working_hours", "map_url"]

    def _lang(self):
        return get_lang(self.context.get("request"))

    def get_name(self, obj):
        return localized(obj, "name", self._lang())

    def get_address(self, obj):
        return localized(obj, "address", self._lang())

    def get_working_hours(self, obj):
        return localized(obj, "working_hours", self._lang())
