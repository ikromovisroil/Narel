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
    payment_method = models.CharField(
        "To'lov usuli", max_length=20, choices=Payment.choices, default=Payment.CASH
    )
    delivery_method = models.CharField(
        "Yetkazish usuli", max_length=20, choices=Delivery.choices, default=Delivery.COURIER
    )
    status = models.CharField(
        "Holati", max_length=20, choices=Status.choices, default=Status.NEW
    )
    total = models.DecimalField("Jami", max_digits=16, decimal_places=0, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Buyurtma #{self.pk}"


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
