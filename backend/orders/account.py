"""Mijozning sevimlilari va savati — serverda (sayt va mobil ilova o'rtasida bir xil).

Sayt kirmagan holda brauzerda saqlaydi; kirganda /sync/ bilan serverga qo'shadi.
Mobil ilova to'g'ridan-to'g'ri shu API bilan ishlaydi.
"""
from django.db import transaction
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product
from catalog.serializers import ProductListSerializer

from .models import CartItem, Favorite

MAX_ITEMS = 200  # bir so'rovda ko'pi bilan


def active_products(ids):
    return {p.pk: p for p in Product.objects.filter(pk__in=ids, is_active=True).select_related("brand", "category")}


class ProductIdsSerializer(serializers.Serializer):
    products = serializers.ListField(child=serializers.IntegerField(min_value=1), max_length=MAX_ITEMS)


class FavoriteAddSerializer(serializers.Serializer):
    product = serializers.IntegerField(min_value=1)


def favorites_response(request):
    qs = (Favorite.objects.filter(user=request.user, product__is_active=True)
          .select_related("product__brand", "product__category"))
    products = [f.product for f in qs]
    return Response(ProductListSerializer(products, many=True, context={"request": request}).data)


class FavoritesView(APIView):
    """GET — sevimlilar (yangisi birinchi), POST {"product": id} — qo'shish."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return favorites_response(request)

    def post(self, request):
        s = FavoriteAddSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        if not active_products([s.validated_data["product"]]):
            return Response({"product": ["Mahsulot topilmadi."]}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.get_or_create(user=request.user, product_id=s.validated_data["product"])
        return favorites_response(request)


class FavoriteDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, product_id):
        Favorite.objects.filter(user=request.user, product_id=product_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoritesSyncView(APIView):
    """Kirgandan keyin: qurilmadagi sevimlilarni serverdagilarga qo'shadi va to'liq ro'yxatni qaytaradi."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = ProductIdsSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        found = active_products(s.validated_data["products"])
        have = set(Favorite.objects.filter(user=request.user).values_list("product_id", flat=True))
        Favorite.objects.bulk_create(
            [Favorite(user=request.user, product_id=pk) for pk in reversed(s.validated_data["products"])
             if pk in found and pk not in have],
            ignore_conflicts=True,
        )
        return favorites_response(request)


# ---------- Savat ----------

class CartItemInput(serializers.Serializer):
    product = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=999)


class CartInput(serializers.Serializer):
    items = CartItemInput(many=True, max_length=MAX_ITEMS)


def cart_response(request):
    items = (CartItem.objects.filter(user=request.user, product__is_active=True)
             .select_related("product__brand", "product__category"))
    data, total = [], 0
    for item in items:
        qty = min(item.quantity, item.product.stock) if item.product.stock else item.quantity
        data.append({
            "product": ProductListSerializer(item.product, context={"request": request}).data,
            "quantity": qty,
            "available": item.product.stock >= item.quantity,
        })
        total += item.product.price * qty
    return Response({"items": data, "total": int(total), "count": len(data)})


def save_cart(user, wanted):
    """wanted: {product_id: quantity}. Nofaol mahsulotlar tashlanadi, son ombordagidan oshmaydi."""
    found = active_products(list(wanted))
    with transaction.atomic():
        CartItem.objects.filter(user=user).exclude(product_id__in=found).delete()
        for pk, qty in wanted.items():
            if pk not in found:
                continue
            stock = found[pk].stock
            CartItem.objects.update_or_create(
                user=user, product_id=pk, defaults={"quantity": max(1, min(qty, stock)) if stock else qty},
            )


class CartView(APIView):
    """GET — savat. PUT {"items": [{"product", "quantity"}]} — savatni to'liq almashtirish (bo'sh ro'yxat — tozalash)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return cart_response(request)

    def put(self, request):
        s = CartInput(data=request.data)
        s.is_valid(raise_exception=True)
        save_cart(request.user, {i["product"]: i["quantity"] for i in s.validated_data["items"]})
        return cart_response(request)


class CartAddView(APIView):
    """POST {"product", "quantity"} — savatga qo'shish (bor bo'lsa soni oshadi)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = CartItemInput(data=request.data)
        s.is_valid(raise_exception=True)
        pk, qty = s.validated_data["product"], s.validated_data["quantity"]
        if not active_products([pk]):
            return Response({"product": ["Mahsulot topilmadi."]}, status=status.HTTP_400_BAD_REQUEST)
        current = dict(CartItem.objects.filter(user=request.user).values_list("product_id", "quantity"))
        current[pk] = current.get(pk, 0) + qty
        save_cart(request.user, current)
        return cart_response(request)


class CartItemDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, product_id):
        CartItem.objects.filter(user=request.user, product_id=product_id).delete()
        return cart_response(request)


class CartSyncView(APIView):
    """Kirgandan keyin: qurilmadagi savatni serverdagisi bilan birlashtiradi (bir xil mahsulotda kattaroq son)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = CartInput(data=request.data)
        s.is_valid(raise_exception=True)
        merged = dict(CartItem.objects.filter(user=request.user).values_list("product_id", "quantity"))
        for i in s.validated_data["items"]:
            merged[i["product"]] = max(merged.get(i["product"], 0), i["quantity"])
        save_cart(request.user, merged)
        return cart_response(request)
