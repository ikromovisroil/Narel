from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from catalog.i18n import get_lang, localized
from catalog.models import Product
from payments.models import PaymentMethod
from staff.models import effective_permissions

from .models import Branch, CustomerProfile, Order, OrderItem, StoreSettings, user_address, user_phone
from .branches import PublicBranchSerializer

User = get_user_model()

MESSAGES = {
    "payment": {
        "uz": "Bu to'lov usuli hozir mavjud emas. Boshqasini tanlang.",
        "ru": "Этот способ оплаты сейчас недоступен. Выберите другой.",
    },
    "empty": {"uz": "Savat bo'sh.", "ru": "Корзина пуста."},
    "no_delivery": {
        "uz": "Hozircha yetkazib berish yo'q. Buyurtmani do'kondan olib keting.",
        "ru": "Доставка сейчас недоступна. Заберите заказ в магазине.",
    },
    "no_branch": {
        "uz": "Buyurtmani olib ketadigan filialni tanlang.",
        "ru": "Выберите филиал, откуда заберёте заказ.",
    },
    "no_pickup": {
        "uz": "Do'kondan olib ketish hozir mavjud emas.",
        "ru": "Самовывоз сейчас недоступен.",
    },
    "address": {"uz": "Manzilni to'liq kiriting.", "ru": "Укажите адрес полностью."},
    "full_name": {
        "uz": "Profilingizda ism va familiya yo'q. Profilni to'ldiring.",
        "ru": "В профиле нет имени и фамилии. Заполните профиль.",
    },
    "phone_taken": {
        "uz": "Bu telefon raqami bilan boshqa hisob ro'yxatdan o'tgan.",
        "ru": "Этот номер телефона уже используется другим аккаунтом.",
    },
    "email_taken": {
        "uz": "Bu email bilan boshqa hisob ro'yxatdan o'tgan.",
        "ru": "Этот email уже используется другим аккаунтом.",
    },
    "username_taken": {"uz": "Bu login band. Boshqasini tanlang.", "ru": "Этот логин занят. Выберите другой."},
    "username_or_email": {
        "uz": "Login yoki emaildan birini kiriting.",
        "ru": "Укажите логин или email.",
    },
    "required": {"uz": "Bu maydonni to'ldiring.", "ru": "Заполните это поле."},
    "old_password": {"uz": "Joriy parol noto'g'ri.", "ru": "Текущий пароль неверный."},
    "same_password": {
        "uz": "Yangi parol joriy paroldan farq qilishi kerak.",
        "ru": "Новый пароль должен отличаться от текущего.",
    },
    "phone": {
        "uz": "Telefon raqamini to'liq kiriting: +998 XX XXX XX XX.",
        "ru": "Укажите номер телефона полностью: +998 XX XXX XX XX.",
    },
    "stock": {
        "uz": "\"{0}\" omborda yetarli emas (bor: {1}).",
        "ru": "Товара «{0}» недостаточно на складе (в наличии: {1}).",
    },
}


def normalize_phone(raw):
    """O'zbekiston raqami: 9 ta raqam yoki 998 bilan 12 ta. Natija: "+998 90 123 45 67", noto'g'ri bo'lsa ""."""
    digits = "".join(c for c in str(raw or "") if c.isdigit())
    if len(digits) == 9:
        digits = "998" + digits
    if len(digits) != 12 or not digits.startswith("998"):
        return ""
    d = digits[3:]
    return f"+998 {d[:2]} {d[2:5]} {d[5:7]} {d[7:]}"


def message(request, key, *args):
    return MESSAGES[key][get_lang(request)].format(*args)


class AccountFieldsMixin:
    """Registratsiya va profil uchun umumiy tekshiruvlar: login, email va telefon takrorlanmasin."""

    def _others(self):
        qs = User.objects.all()
        return qs.exclude(pk=self.instance.pk) if getattr(self, "instance", None) else qs

    def _err(self, key):
        return serializers.ValidationError(message(self.context.get("request"), key))

    def validate_username(self, value):
        value = (value or "").strip()
        if value and self._others().filter(username__iexact=value).exists():
            raise self._err("username_taken")
        return value

    def validate_email(self, value):
        value = (value or "").strip().lower()
        if value and self._others().filter(email__iexact=value).exists():
            raise self._err("email_taken")
        return value

    def validate_phone(self, value):
        phone = normalize_phone(value)
        if not phone:
            raise self._err("phone")
        others = CustomerProfile.objects.filter(phone=phone)
        if getattr(self, "instance", None):
            others = others.exclude(user=self.instance)
        if others.exists():
            raise self._err("phone_taken")
        return phone

    def validate_first_name(self, value):
        if not (value or "").strip():
            raise self._err("required")
        return value.strip()

    validate_last_name = validate_first_name


class RegisterSerializer(AccountFieldsMixin, serializers.ModelSerializer):
    """Ro'yxatdan o'tish: ism, familiya, telefon majburiy; login yoki email (ikkalasi ham bo'lishi mumkin)."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    phone = serializers.CharField(write_only=True)
    username = serializers.CharField(required=False, allow_blank=True, max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "phone", "password"]

    def validate(self, attrs):
        if not attrs.get("username") and not attrs.get("email"):
            raise serializers.ValidationError({"username": message(self.context.get("request"), "username_or_email")})
        if not attrs.get("username"):
            # Email bilan ro'yxatdan o'tganda login sifatida email ishlatiladi
            attrs["username"] = attrs["email"]
            if User.objects.filter(username__iexact=attrs["username"]).exists():
                raise serializers.ValidationError({"email": message(self.context.get("request"), "email_taken")})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        phone = validated_data.pop("phone")
        user = User.objects.create_user(**validated_data)
        CustomerProfile.objects.create(user=user, phone=phone)
        return user


class UserSerializer(AccountFieldsMixin, serializers.ModelSerializer):
    """Joriy foydalanuvchi: mijoz profilida FISH, telefon, login va emailni o'zgartiradi."""

    permissions = serializers.SerializerMethodField()
    phone = serializers.CharField(required=False, allow_blank=False)
    username = serializers.CharField(required=False, max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    # Buyurtma berishda avtomatik qo'yiladi (ixtiyoriy)
    address = serializers.CharField(required=False, allow_blank=True, max_length=255)
    has_password = serializers.BooleanField(source="has_usable_password", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email", "phone", "address",
            "is_staff", "is_superuser", "permissions", "date_joined", "has_password",
        ]
        read_only_fields = ["is_staff", "is_superuser", "date_joined"]

    def validate_username(self, value):
        value = super().validate_username(value)
        if not value:
            raise self._err("required")
        # Djangoning login qoidasi (harf, raqam va @ . + - _)
        User.username_validator(value)
        return value

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data["phone"] = user_phone(obj)
        data["address"] = user_address(obj)
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        extra = {k: validated_data.pop(k) for k in ("phone", "address") if k in validated_data}
        if "address" in extra:
            extra["address"] = extra["address"].strip()
        user = super().update(instance, validated_data)
        if extra:
            user.profile, _ = CustomerProfile.objects.update_or_create(user=user, defaults=extra)
        return user

    def get_permissions(self, obj):
        # Admin panel menyusi va tugmalari shunga qarab ko'rsatiladi
        return effective_permissions(obj)


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    product_slug = serializers.CharField(source="product.slug", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["product", "product_name", "product_slug", "price", "quantity", "subtotal"]
        read_only_fields = ["price", "subtotal"]

    def get_product_name(self, obj):
        return localized(obj.product, "name", get_lang(self.context.get("request")))


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    cart = OrderItemInputSerializer(many=True, write_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_delayed = serializers.BooleanField(read_only=True)
    pickup_branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), required=False, allow_null=True
    )
    pickup_branch_info = serializers.SerializerMethodField()

    def get_pickup_branch_info(self, obj):
        """Olib ketish joyi (joriy tilda). Filial o'chirilgan bo'lsa — buyurtma paytidagi yozuv."""
        if obj.delivery_method != Order.Delivery.PICKUP:
            return None
        if obj.pickup_branch:
            return PublicBranchSerializer(obj.pickup_branch, context=self.context).data
        return {"name": obj.pickup_point, "address": "", "phone": "", "working_hours": "", "map_url": ""}

    class Meta:
        model = Order
        fields = [
            "id", "full_name", "phone", "address", "note", "payment_method",
            "delivery_method", "status", "status_display", "delivery_price", "expected_date",
            "original_expected_date", "delay_note", "is_delayed", "pickup_branch", "pickup_branch_info", "total",
            "created_at", "items", "cart",
        ]
        read_only_fields = [
            "status", "delivery_price", "expected_date", "original_expected_date", "delay_note", "total", "created_at",
        ]
        # Yuborilmasa — mijoz profilidan olinadi
        extra_kwargs = {"full_name": {"required": False, "allow_blank": True}, "phone": {"required": False, "allow_blank": True}}

    def validate(self, attrs):
        # Faqat admin Sozlamalarda yoqqan to'lov usuli qabul qilinadi
        method = attrs.get("payment_method", Order.Payment.CASH)
        if method not in PaymentMethod.active_codes():
            raise serializers.ValidationError({"payment_method": message(self.context.get("request"), "payment")})
        if not attrs.get("cart"):
            raise serializers.ValidationError({"cart": message(self.context.get("request"), "empty")})
        # Admin Sozlamalarda o'chirilgan yetkazish usulini qabul qilmaymiz
        store = StoreSettings.load()
        delivery = attrs.get("delivery_method", Order.Delivery.COURIER)
        if delivery == Order.Delivery.COURIER and not store.delivery_enabled:
            raise serializers.ValidationError({"delivery_method": message(self.context.get("request"), "no_delivery")})
        if delivery == Order.Delivery.PICKUP and not store.pickup_enabled:
            raise serializers.ValidationError({"delivery_method": message(self.context.get("request"), "no_pickup")})
        if delivery == Order.Delivery.PICKUP:
            branch = attrs.get("pickup_branch")
            if not branch or not branch.is_active:
                raise serializers.ValidationError({"pickup_branch": message(self.context.get("request"), "no_branch")})
        else:
            attrs["pickup_branch"] = None
        # FISH va telefon registratsiyada olingan — buyurtmada qayta so'ralmaydi
        request = self.context.get("request")
        user = getattr(request, "user", None)
        full_name = (attrs.get("full_name") or "").strip() or (user.get_full_name().strip() if user else "")
        if not full_name:
            raise serializers.ValidationError({"full_name": message(request, "full_name")})
        attrs["full_name"] = full_name
        phone = normalize_phone(attrs.get("phone") or user_phone(user))
        if not phone:
            raise serializers.ValidationError({"phone": message(request, "phone")})
        attrs["phone"] = phone
        attrs["address"] = (attrs.get("address") or "").strip() or user_address(user)
        if len(attrs["address"]) < 5:
            raise serializers.ValidationError({"address": message(request, "address")})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        cart = validated_data.pop("cart")
        ids = [row["product"].pk for row in cart]
        # Bir vaqtda ikki kishi oxirgi mahsulotni olmasligi uchun qatorlarni qulflaymiz
        products = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=ids)}

        order = Order.objects.create(**validated_data)
        total = 0
        for row in cart:
            product = products[row["product"].pk]
            qty = row["quantity"]
            if product.stock < qty:
                lang = get_lang(self.context.get("request"))
                raise serializers.ValidationError({"cart": message(
                    self.context.get("request"), "stock",
                    localized(product, "name", lang), product.stock,
                )})
            product.stock -= qty
            product.save(update_fields=["stock"])
            OrderItem.objects.create(order=order, product=product, price=product.price, quantity=qty)
            total += product.price * qty

        # Olib ketish — filial ma'lumotlarini buyurtmaga yozib qo'yamiz (filial keyin o'zgarsa ham saqlansin)
        if order.pickup_branch:
            b = order.pickup_branch
            order.pickup_point = " · ".join(x for x in [b.name, b.address, b.phone, b.working_hours] if x)
            order.save(update_fields=["pickup_point"])
        # Kuryer bilan — yetkazish narxi va taxminiy yetib kelish sanasi
        if order.delivery_method == Order.Delivery.COURIER:
            store = StoreSettings.load()
            order.delivery_price = store.delivery_price
            order.expected_date = timezone.localdate() + timedelta(days=store.delivery_days)
            total += store.delivery_price
        order.total = total
        order.save(update_fields=["total", "delivery_price", "expected_date"])
        return order


class PasswordChangeSerializer(serializers.Serializer):
    # Google orqali ochilgan hisobda parol yo'q — birinchi marta joriy parolsiz o'rnatiladi
    old_password = serializers.CharField(required=False, allow_blank=True)
    new_password = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        if user.has_usable_password() and not user.check_password(attrs.get("old_password") or ""):
            raise serializers.ValidationError({"old_password": message(request, "old_password")})
        if attrs.get("old_password") == attrs["new_password"]:
            raise serializers.ValidationError({"new_password": message(request, "same_password")})
        try:
            validate_password(attrs["new_password"], request.user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        return attrs
