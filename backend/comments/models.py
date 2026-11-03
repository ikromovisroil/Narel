from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from catalog.models import Product


class Comment(models.Model):
    """Mahsulotga izoh. parent bo'lsa — boshqa izohga javob (faqat bir daraja)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="comments", verbose_name="Mahsulot")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments", verbose_name="Muallif")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies", verbose_name="Javob qaysi izohga"
    )
    text = models.TextField("Matn", max_length=1000)
    rating = models.PositiveSmallIntegerField(
        "Baho", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    is_hidden = models.BooleanField("Yashirilgan", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Izoh"
        verbose_name_plural = "Izohlar"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["product", "parent", "is_hidden"])]

    def __str__(self):
        return f"{self.user} — {self.text[:40]}"
