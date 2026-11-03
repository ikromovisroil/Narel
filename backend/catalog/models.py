from decimal import Decimal

from django.db import models


class Category(models.Model):
    name = models.CharField("Nomi", max_length=120)
    name_ru = models.CharField("Nomi (ruscha)", max_length=120, blank=True)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    icon = models.ImageField("Ikonka", upload_to="categories/", blank=True)
    order = models.PositiveIntegerField("Tartib", default=0)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField("Nomi", max_length=100)
    slug = models.SlugField(unique=True)
    logo = models.ImageField("Logo", upload_to="brands/", blank=True)

    class Meta:
        verbose_name = "Brend"
        verbose_name_plural = "Brendlar"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products", verbose_name="Kategoriya"
    )
    brand = models.ForeignKey(
        Brand, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="products", verbose_name="Brend",
    )
    name = models.CharField("Nomi", max_length=200)
    name_ru = models.CharField("Nomi (ruscha)", max_length=200, blank=True)
    slug = models.SlugField(unique=True, max_length=220)
    sku = models.CharField("Mahsulot kodi", max_length=50, blank=True)
    description = models.TextField("Tavsif", blank=True)
    description_ru = models.TextField("Tavsif (ruscha)", blank=True)
    price = models.DecimalField("Narxi", max_digits=14, decimal_places=0)
    old_price = models.DecimalField(
        "Eski narxi", max_digits=14, decimal_places=0, null=True, blank=True
    )
    stock = models.PositiveIntegerField("Ombordagi soni", default=0)
    image = models.ImageField("Asosiy rasm", upload_to="products/", blank=True)
    is_active = models.BooleanField("Faol", default=True)
    is_hit = models.BooleanField("Xit savdo", default=False)
    is_new = models.BooleanField("Yangi", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    INSTALLMENT_MONTHS = 12

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int((self.old_price - self.price) * 100 / self.old_price)
        return 0

    @property
    def monthly_price(self):
        """12 oylik muddatli to'lovda oylik summa (ustamasiz, taxminiy)."""
        return int((self.price / Decimal(self.INSTALLMENT_MONTHS)).quantize(Decimal("1")))


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("Rasm", upload_to="products/")
    order = models.PositiveIntegerField("Tartib", default=0)

    class Meta:
        verbose_name = "Mahsulot rasmi"
        verbose_name_plural = "Mahsulot rasmlari"
        ordering = ["order"]


class ProductSpec(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specs")
    name = models.CharField("Xususiyat", max_length=120)
    value = models.CharField("Qiymati", max_length=255)
    name_ru = models.CharField("Xususiyat (ruscha)", max_length=120, blank=True)
    value_ru = models.CharField("Qiymati (ruscha)", max_length=255, blank=True)
    order = models.PositiveIntegerField("Tartib", default=0)

    class Meta:
        verbose_name = "Xususiyat"
        verbose_name_plural = "Xususiyatlar"
        ordering = ["order"]


class Banner(models.Model):
    title = models.CharField("Sarlavha", max_length=200)
    title_ru = models.CharField("Sarlavha (ruscha)", max_length=200, blank=True)
    subtitle = models.CharField("Qo'shimcha matn", max_length=255, blank=True)
    subtitle_ru = models.CharField("Qo'shimcha matn (ruscha)", max_length=255, blank=True)
    image = models.ImageField("Rasm", upload_to="banners/", blank=True)
    link = models.CharField("Havola", max_length=255, blank=True)
    order = models.PositiveIntegerField("Tartib", default=0)
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Bannerlar"
        ordering = ["order"]

    def __str__(self):
        return self.title
