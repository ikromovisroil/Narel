"""Ombor qoldig'i buyurtma holatiga qarab o'zgaradi.

- Mijoz buyurtma berganda — qoldiq faqat tekshiriladi, kamaymaydi.
- Buyurtma qabul qilinganda (Tasdiqlangan / Yuborilgan / Yetkazilgan) — qoldiqdan ayriladi.
- Bekor qilinganda — ayrilgan bo'lsa, omborga qaytadi.

Order.stock_deducted — bu buyurtma uchun qoldiqdan ayrilganmi. Shu belgi tufayli ikki marta
ayirish yoki qaytarish bo'lmaydi. Hammasi transaction.atomic ichida chaqiriladi.
"""
from collections import defaultdict

from django.db.models import F

from catalog.models import Product

from .models import Order

ACCEPTED = (Order.Status.CONFIRMED, Order.Status.SHIPPED, Order.Status.DELIVERED)


class NotEnoughStock(Exception):
    pass


def _needs(order):
    need = defaultdict(int)
    for item in order.items.all():
        need[item.product_id] += item.quantity
    return need


def deduct(order):
    """Buyurtmadagi mahsulotlarni qoldiqdan ayiradi. Yetmasa — NotEnoughStock (hech narsa o'zgarmaydi)."""
    if order.stock_deducted:
        return
    need = _needs(order)
    products = Product.objects.select_for_update().filter(pk__in=need).order_by("pk")
    short = [f"«{p.name}» — omborda {p.stock} ta, buyurtmada {need[p.pk]} ta" for p in products if p.stock < need[p.pk]]
    if short:
        raise NotEnoughStock("Omborda yetarli emas: " + "; ".join(short) + ". Avval qoldiqni to'ldiring.")
    for pk, qty in need.items():
        Product.objects.filter(pk=pk).update(stock=F("stock") - qty)
    Order.objects.filter(pk=order.pk).update(stock_deducted=True)
    order.stock_deducted = True


def restore(order):
    """Ayrilgan qoldiqni omborga qaytaradi (ayrilmagan bo'lsa — hech narsa qilmaydi)."""
    if not order.stock_deducted:
        return
    for pk, qty in _needs(order).items():
        Product.objects.filter(pk=pk).update(stock=F("stock") + qty)
    Order.objects.filter(pk=order.pk).update(stock_deducted=False)
    order.stock_deducted = False


def apply_status(order, new_status):
    """Holat o'zgarishidan oldin chaqiriladi: qabul qilinsa — ayiradi, bekor qilinsa — qaytaradi."""
    if new_status == Order.Status.CANCELLED:
        restore(order)
    elif new_status in ACCEPTED:
        deduct(order)
