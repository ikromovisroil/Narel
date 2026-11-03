from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import SECTION_CODES, StaffProfile, clean_permissions, effective_permissions

User = get_user_model()


class StaffSerializer(serializers.ModelSerializer):
    position = serializers.CharField(source="staff_profile.position", required=False, allow_blank=True, default="")
    permissions = serializers.JSONField(required=False)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, trim_whitespace=False)
    is_self = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email", "position", "is_active", "is_superuser",
            "permissions", "password", "is_self", "last_login", "date_joined",
        ]
        read_only_fields = ["last_login", "date_joined"]

    # ---- o'qish ----
    def get_is_self(self, obj):
        return obj.pk == self.context["request"].user.pk

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data["permissions"] = effective_permissions(obj) if obj.is_active else (
            clean_permissions(getattr(getattr(obj, "staff_profile", None), "permissions", {}))
        )
        profile = getattr(obj, "staff_profile", None)
        data["position"] = profile.position if profile else ""
        return data

    # ---- tekshiruvlar ----
    @property
    def actor(self):
        return self.context["request"].user

    def validate_permissions(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Noto'g'ri format.")
        perms = clean_permissions(value)
        if not self.actor.is_superuser:
            # O'zida yo'q amalni boshqaga bera olmaydi
            mine = effective_permissions(self.actor)
            too_high = [
                f"{code}: {action}" for code, actions in perms.items()
                for action in actions if action not in mine.get(code, [])
            ]
            if too_high:
                raise serializers.ValidationError(
                    "O'zingizda yo'q ruxsatni bera olmaysiz: " + ", ".join(too_high) + "."
                )
        return perms

    def validate(self, attrs):
        actor, target = self.actor, self.instance
        creating = target is None

        if creating and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Yangi xodim uchun parol kiriting."})
        if attrs.get("password"):
            user_for_check = target or User(username=attrs.get("username", ""), email=attrs.get("email", ""))
            try:
                validate_password(attrs["password"], user_for_check)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"password": exc.messages})

        wants_super = attrs.get("is_superuser", target.is_superuser if target else False)
        if not actor.is_superuser:
            if wants_super or (target and target.is_superuser):
                raise serializers.ValidationError("Super adminni faqat super admin yarata yoki o'zgartira oladi.")

        if target and target.pk == actor.pk:
            # O'zini bloklab yoki huquqini kamaytirib qo'ymasin
            if attrs.get("is_active") is False:
                raise serializers.ValidationError({"is_active": "O'zingizni bloklay olmaysiz."})
            if "is_superuser" in attrs and actor.is_superuser and not attrs["is_superuser"]:
                raise serializers.ValidationError({"is_superuser": "O'zingizdan super admin huquqini ola olmaysiz."})
            if "permissions" in attrs and not actor.is_superuser:
                raise serializers.ValidationError({"permissions": "O'z ruxsatlaringizni o'zgartira olmaysiz."})
        return attrs

    # ---- saqlash ----
    @transaction.atomic
    def create(self, validated):
        profile = validated.pop("staff_profile", {})
        perms = validated.pop("permissions", {})
        password = validated.pop("password")
        user = User(**validated, is_staff=True)
        user.set_password(password)
        user.save()
        StaffProfile.objects.create(user=user, position=profile.get("position", ""), permissions=perms)
        return user

    @transaction.atomic
    def update(self, user, validated):
        profile_data = validated.pop("staff_profile", None)
        perms = validated.pop("permissions", None)
        password = validated.pop("password", "")
        for key, value in validated.items():
            setattr(user, key, value)
        if password:
            user.set_password(password)
        user.is_staff = True
        user.save()
        profile, _ = StaffProfile.objects.get_or_create(user=user)
        if profile_data is not None:
            profile.position = profile_data.get("position", profile.position)
        if perms is not None:
            profile.permissions = perms
        profile.save()
        return user


class SectionSerializer(serializers.Serializer):
    code = serializers.CharField()
    title = serializers.CharField()
    editable = serializers.BooleanField()


__all__ = ["StaffSerializer", "SectionSerializer", "SECTION_CODES"]
