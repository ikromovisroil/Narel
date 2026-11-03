from django.conf import settings
from django.db import models

from catalog.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Yangi"
        CONFIRMED = "confirmed", "Tasdiqlangan"
        SHIPPED = "shipped", "Yuborilgan"
        DELIVERED = "delivered", "Yetkazilgan"
        CANCELLED = "cancelled", "Bekor qilingan"

    class Payment(models.TextChoices):
        CASH = "cash", "Naqd pul"
        CARD = "card", "Karta orqali"
        INSTALLMENT = "installment", "Muddatli to'lov"

    class Delivery(models.TextChoices):
        COURIER = "courier", "Kuryer orqali"
        PICKUP = "pickup", "Do'kondan olib ketish"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    full_name = models.CharField("F.I.Sh.", max_length=150)
    phone = models.CharField("Telefon", max_length=20)
    address = models.TextField("Manzil", blank=True)
    note = models.TextField("Izoh", blank=True)
    # Kod payments.PaymentMethod.code ga mos (cash, card, click, payme, ...).
    # Qaysilari mavjudligi admin paneldagi Sozlamalarda boshqariladi.
    payment_method = models.CharField(
        "To'lov usuli", max_length=20, default=Payment.CASH
    )
    delivery_method = models.CharField(
        "Yetkazish usuli", max_length=20, choices=Delivery.choices, default=Delivery.COURIER
    )
    status = models.CharField(
        "Holati", max_length=20, choices=Status.choices, default=Status.NEW
    )
    delivery_price = models.DecimalField("Yetkazish narxi", max_digits=12, decimal_places=0, default=0)
    expected_date = models.DateField("Taxminiy yetkazish sanasi", null=True, blank=True)
    # Qabul qilinganda mijozga va'da qilingan sana — keyin surilsa kechikish hisoblanadi
    original_expected_date = models.DateField("Dastlab va'da qilingan sana", null=True, blank=True)
    delay_note = models.CharField("Kechikish sababi (mijozga ko'rinadi)", max_length=255, blank=True)
    # Olib ketishda tanlangan filial va o'sha paytdagi ma'lumotlari (filial keyin o'zgarsa ham tarix saqlanadi)
    pickup_branch = models.ForeignKey(
        "Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="orders", verbose_name="Filial"
    )
    pickup_point = models.CharField("Olib ketish joyi", max_length=400, blank=True)
    total = models.DecimalField("Jami", max_digits=16, decimal_places=0, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Buyurtma #{self.pk}"

    ACTIVE = ("new", "confirmed", "shipped")

    @property
    def is_delayed(self):
        """Sana va'da qilingandan keyinga surilgan yoki o'tib ketgan (hali yetkazilmagan)."""
        if self.status not in self.ACTIVE or not self.expected_date:
            return False
        from django.utils import timezone
        moved = bool(self.original_expected_date and self.expected_date > self.original_expected_date)
        overdue = self.expected_date < timezone.localdate()
        return moved or overdue


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField("Narxi", max_digits=14, decimal_places=0)
    quantity = models.PositiveIntegerField("Soni")

    class Meta:
        verbose_name = "Buyurtma qatori"
        verbose_name_plural = "Buyurtma qatorlari"

    @property
    def subtotal(self):
        return self.price * self.quantity


class StoreSettings(models.Model):
    """Do'kon va yetkazib berish sozlamalari (yagona yozuv, pk=1)."""

    delivery_enabled = models.BooleanField("Yetkazib berish bor", default=True)
    delivery_price = models.DecimalField("Yetkazish narxi", max_digits=12, decimal_places=0, default=0)
    delivery_days = models.PositiveSmallIntegerField("Yetkazish muddati (kun)", default=1)
    delivery_note = models.CharField("Yetkazish izohi", max_length=150, blank=True, default="Toshkent bo'ylab 1 kunda")
    delivery_note_ru = models.CharField("Yetkazish izohi (ruscha)", max_length=150, blank=True, default="По Ташкенту за 1 день")
    pickup_enabled = models.BooleanField("Do'kondan olib ketish bor", default=True)
    phone = models.CharField("Telefon", max_length=30, default="+998 71 000 00 00")
    address = models.CharField("Do'kon manzili", max_length=255, default="Toshkent sh.")
    address_ru = models.CharField("Do'kon manzili (ruscha)", max_length=255, blank=True, default="г. Ташкент")
    working_hours = models.CharField("Ish vaqti", max_length=100, blank=True, default="Har kuni 9:00 – 21:00")
    working_hours_ru = models.CharField("Ish vaqti (ruscha)", max_length=100, blank=True, default="Ежедневно 9:00 – 21:00")
    map_url = models.URLField("Xaritadagi havola", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Do'kon sozlamalari"
        verbose_name_plural = "Do'kon sozlamalari"

    def __str__(self):
        return "Do'kon sozlamalari"

    def save(self, *args, **kwargs):
        self.pk = 1  # har doim bitta yozuv
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Branch(models.Model):
    """Filial — mijoz buyurtmani shu yerdan olib ketadi."""

    name = models.CharField("Nomi", max_length=100)
    name_ru = models.CharField("Nomi (ruscha)", max_length=100, blank=True)
    address = models.CharField("Manzil", max_length=255)
    address_ru = models.CharField("Manzil (ruscha)", max_length=255, blank=True)
    phone = models.CharField("Telefon", max_length=30)
    working_hours = models.CharField("Ish vaqti", max_length=100, blank=True)
    working_hours_ru = models.CharField("Ish vaqti (ruscha)", max_length=100, blank=True)
    map_url = models.URLField("Xaritadagi havola", blank=True)
    is_active = models.BooleanField("Faol", default=True)
    order = models.PositiveIntegerField("Tartib", default=0)

    class Meta:
        verbose_name = "Filial"
        verbose_name_plural = "Filiallar"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class CustomerProfile(models.Model):
    """Mijozning qo'shimcha ma'lumoti: telefon (buyurtmada qayta so'ralmaydi)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField("Telefon", max_length=20, blank=True)
    address = models.CharField("Yetkazish manzili", max_length=255, blank=True)

    class Meta:
        verbose_name = "Mijoz profili"
        verbose_name_plural = "Mijoz profillari"
        constraints = [
            models.UniqueConstraint(fields=["phone"], condition=~models.Q(phone=""), name="unique_customer_phone"),
        ]

    def __str__(self):
        return f"{self.user} · {self.phone}"


def user_profile(user):
    return getattr(user, "profile", None) if user and user.pk else None


def user_phone(user):
    profile = user_profile(user)
    return profile.phone if profile else ""


def user_address(user):
    profile = user_profile(user)
    return profile.address if profile else ""
