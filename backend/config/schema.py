"""Swagger / ReDoc uchun izohlar (drf-spectacular).

View va serializer kodiga tegmasdan, hammasi shu yerda: APIView'lar uchun so'rov/javob shakli,
SerializerMethodField turlari, sayt va admin serializer'larining nomlari (to'qnashmasligi uchun),
va endpoint'larni bo'limlarga (tag) ajratish. config/urls.py import qiladi.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_field, extend_schema_serializer,
    extend_schema_view, inline_serializer,
)
from django.conf import settings
from rest_framework import serializers
from rest_framework.permissions import BasePermission

import catalog.serializers as cat_s
import comments.serializers as com_s
import dashboard.serializers as adm_s
import orders.serializers as ord_s
import payments.serializers as pay_s
import staff.serializers as staff_s
from catalog.views import ProductViewSet
from comments.views import AdminCommentViewSet, MyCommentView, ProductCommentsView
from dashboard.views import ImageRulesView, ProductImageViewSet, StatsView
from dashboard.views import ProductViewSet as AdminProductViewSet
from orders import integrations_views as integ, store
from orders.google import GoogleLoginSerializer, GoogleLoginView
from orders.login import (
    ChangePhoneView, OfferView, SendCodeSerializer, SendCodeView, VerifyCodeSerializer, VerifyCodeView,
)

STR, INT, BOOL, OBJ = OpenApiTypes.STR, OpenApiTypes.INT, OpenApiTypes.BOOL, OpenApiTypes.OBJECT

# ---------- Umumiy javoblar ----------

Tokens = inline_serializer("Tokens", {
    "access": serializers.CharField(help_text="1 soat amal qiladi: Authorization: Bearer <access>"),
    "refresh": serializers.CharField(help_text="7 kun. /api/auth/refresh/ bilan yangi access olinadi"),
    "created": serializers.BooleanField(help_text="true — yangi hisob ochildi"),
})
Detail = inline_serializer("Detail", {"detail": serializers.CharField()})
ERRORS = {400: OpenApiResponse(Detail, description="Noto'g'ri ma'lumot"),
          429: OpenApiResponse(Detail, description="Juda ko'p urinish")}

# ---------- Kirish ----------

extend_schema_view(post=extend_schema(
    tags=["auth"], summary="SMS kod yuborish",
    description="Mijoz kirishi, 1-qadam. `agree` — ofertaga rozilik (true bo'lishi shart). "
                "Kod 120 soniya amal qiladi, qayta yuborish 60 soniyadan keyin. "
                "Sinov rejimida javobda `debug_code` ham bo'ladi.",
    request=SendCodeSerializer,
    responses={200: inline_serializer("CodeSent", {
        "phone": serializers.CharField(), "expires_in": serializers.IntegerField(),
        "resend_in": serializers.IntegerField(), "is_new": serializers.BooleanField(),
        "debug_code": serializers.CharField(required=False),
    }), **ERRORS, 503: OpenApiResponse(Detail, description="SMS xizmati ishlamayapti")},
))(SendCodeView)

extend_schema_view(post=extend_schema(
    tags=["auth"], summary="Kodni tasdiqlash va kirish",
    description="Mijoz kirishi, 2-qadam. Hisob bo'lmasa yaratiladi (`created: true`). 5 marta xatodan keyin kod bekor bo'ladi.",
    request=VerifyCodeSerializer, responses={200: Tokens, **ERRORS},
))(VerifyCodeView)

extend_schema_view(post=extend_schema(
    tags=["auth"], summary="Telefonni almashtirish",
    description="Avval yangi raqamga /api/auth/code/send/ bilan kod yuboriladi.",
    request=VerifyCodeSerializer,
    responses={200: inline_serializer("PhoneChanged", {"phone": serializers.CharField()}), **ERRORS},
))(ChangePhoneView)

extend_schema_view(post=extend_schema(
    tags=["auth"], summary="Google orqali kirish",
    description="`credential` — Google Identity Services bergan ID token. Email bo'yicha hisobga bog'lanadi yoki yangisi ochiladi.",
    request=GoogleLoginSerializer, responses={200: Tokens, **ERRORS},
))(GoogleLoginView)

# ---------- Sayt ----------

extend_schema_view(get=extend_schema(
    tags=["store"], summary="Ommaviy oferta",
    responses=inline_serializer("Offer", {"text": serializers.CharField(), "updated_at": serializers.DateTimeField()}),
))(OfferView)

extend_schema_view(get=extend_schema(
    tags=["store"], summary="Do'kon ma'lumotlari va filiallar", responses=store.PublicStoreSettingsSerializer,
))(store.PublicStoreSettingsView)

CommentsPage = inline_serializer("CommentsPage", {
    "count": serializers.IntegerField(), "next": serializers.URLField(allow_null=True),
    "previous": serializers.URLField(allow_null=True),
    "results": com_s.CommentSerializer(many=True),
    "summary": inline_serializer("RatingSummary", {
        "rating": serializers.FloatField(allow_null=True), "ratings_count": serializers.IntegerField(),
    }),
})
extend_schema_view(
    get=extend_schema(tags=["comments"], summary="Mahsulot izohlari (10 tadan)",
                      parameters=[OpenApiParameter("page", INT)], responses=CommentsPage),
    post=extend_schema(tags=["comments"], summary="Izoh yoki javob yozish",
                       description="Javob uchun `parent` — izoh id. Baho (`rating`) 1–5, ixtiyoriy.",
                       request=com_s.CommentSerializer, responses={201: com_s.CommentSerializer}),
)(ProductCommentsView)

extend_schema_view(delete=extend_schema(
    tags=["comments"], summary="O'z izohini o'chirish", responses={204: None},
))(MyCommentView)

extend_schema_view(
    list=extend_schema(summary="Mahsulotlar ro'yxati", parameters=[
        OpenApiParameter("category", STR, description="Kategoriya slug'i (ichidagilari bilan)"),
        OpenApiParameter("brand", STR, description="Brend slug'lari, vergul bilan: samsung,lg"),
        OpenApiParameter("price_min", INT), OpenApiParameter("price_max", INT),
        OpenApiParameter("discount", BOOL, description="Faqat chegirmadagilar"),
        OpenApiParameter("lang", STR, enum=["uz", "ru"]),
    ]),
    similar=extend_schema(summary="O'xshash mahsulotlar (10 ta)", responses=cat_s.ProductListSerializer(many=True)),
)(ProductViewSet)

# ---------- Admin ----------

extend_schema_view(
    get=extend_schema(tags=["admin"], summary="Do'kon sozlamalari", responses=store.AdminStoreSettingsSerializer),
    patch=extend_schema(tags=["admin"], summary="Do'kon sozlamalarini saqlash",
                        request=store.AdminStoreSettingsSerializer, responses=store.AdminStoreSettingsSerializer),
)(store.AdminStoreSettingsView)

extend_schema_view(get=extend_schema(
    tags=["admin"], summary="Statistika (bosh sahifa)",
    description="Bugun/oy/jami tushum, holatlar soni, kam qolgan mahsulotlar, top-5, 30 kunlik grafik, oxirgi buyurtmalar.",
    responses=OBJ,
))(StatsView)

extend_schema_view(get=extend_schema(tags=["admin"], summary="Rasm talablari", responses=OBJ))(ImageRulesView)

extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("kind", STR, enum=["reviews", "replies", "low", "unanswered"]),
]))(AdminCommentViewSet)

extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("low_stock", BOOL, description="Faqat kam qolganlar"),
]))(__import__("dashboard.views", fromlist=["ProductViewSet"]).ProductViewSet)

ProductImageViewSet.serializer_class = adm_s.ProductImageSerializer  # faqat DELETE, sxema uchun

# ---------- SerializerMethodField turlari ----------

for cls, names in [
    (cat_s.CategorySerializer, ["get_name"]),
    (cat_s.ProductSpecSerializer, ["get_name", "get_value"]),
    (cat_s.ProductListSerializer, ["get_name"]),
    (cat_s.ProductDetailSerializer, ["get_description"]),
    (cat_s.BannerSerializer, ["get_title", "get_subtitle"]),
    (ord_s.OrderItemSerializer, ["get_product_name"]),
    (pay_s.PublicPaymentMethodSerializer, ["get_title", "get_description"]),
    (pay_s.AdminPaymentMethodSerializer, ["get_about"]),
    (com_s.CommentSerializer, ["get_author"]),
    (com_s.AdminCommentSerializer, ["get_author"]),
    (store.PublicStoreSettingsSerializer, ["get_google_client_id", "get_delivery_note", "get_address", "get_working_hours"]),
]:
    for name in names:
        extend_schema_field(STR)(getattr(cls, name))

for cls, name in [(com_s.CommentSerializer, "get_is_staff"), (com_s.CommentSerializer, "get_is_mine"),
                  (staff_s.StaffSerializer, "get_is_self"), (store.PublicStoreSettingsSerializer, "get_sms_test_mode"),
                  (store.PublicStoreSettingsSerializer, "get_pickup_enabled")]:
    extend_schema_field(BOOL)(getattr(cls, name))

extend_schema_field(OpenApiTypes.INT)(pay_s.PublicPaymentMethodSerializer.get_months)
extend_schema_field(OBJ)(ord_s.UserSerializer.get_permissions)
extend_schema_field(OBJ)(ord_s.OrderSerializer.get_pickup_branch_info)
extend_schema_field(serializers.ListField(child=serializers.DictField()))(cat_s.CategorySerializer.get_children)
extend_schema_field(serializers.ListField(child=serializers.DictField()))(com_s.CommentSerializer.get_replies)
extend_schema_field(serializers.ListField(child=serializers.DictField()))(store.PublicStoreSettingsSerializer.get_branches)
for name in ["get_where", "get_contacts", "get_fields_schema"]:
    extend_schema_field(serializers.ListField(child=serializers.JSONField()))(getattr(pay_s.AdminPaymentMethodSerializer, name))

# ---------- Admin serializer'lari boshqa nom bilan (saytdagilari bilan to'qnashmasin) ----------

for cls in [adm_s.CategorySerializer, adm_s.BrandSerializer, adm_s.BannerSerializer, adm_s.ProductSerializer,
            adm_s.ProductImageSerializer, adm_s.ProductSpecSerializer, adm_s.OrderSerializer,
            adm_s.CustomerSerializer]:
    extend_schema_serializer(component_name="Admin" + cls.__name__.removesuffix("Serializer"))(cls)

# ---------- Bo'limlar (tag) yo'l bo'yicha ----------

def tag_by_path(result, generator, request, public):
    rules = [
        ("/api/admin/", "admin"),
        ("/api/auth/", "auth"),
        ("/api/orders/", "orders"),
        ("/api/comments/", "comments"),
        ("/comments/", "comments"),
        ("/api/products/", "catalog"), ("/api/categories/", "catalog"),
        ("/api/brands/", "catalog"), ("/api/banners/", "catalog"),
    ]
    for path, ops in result.get("paths", {}).items():
        tag = next((t for prefix, t in rules if prefix in path), "store")
        for op in ops.values():
            if isinstance(op, dict):
                op["tags"] = [tag]
    return result


class DocsAccess(BasePermission):
    """Swagger/ReDoc: DEBUG'da hamma uchun, serverda — faqat faol xodim (avval /admin/ ga kiriladi)."""

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        u = request.user
        return bool(u and u.is_authenticated and u.is_staff and u.is_active)


extend_schema_view(
    get=extend_schema(tags=["admin"], summary="Integratsiyalar: SMS va Google sozlamalari", responses=OBJ),
    patch=extend_schema(tags=["admin"], summary="Integratsiyalarni saqlash",
                        description="eskiz_password bo'sh yuborilsa eskisi saqlanadi; o'qishda hech qachon qaytmaydi.",
                        request=integ.IntegrationSettingsSerializer, responses=OBJ),
)(integ.AdminIntegrationsView)
extend_schema_view(post=extend_schema(
    tags=["admin"], summary="Eskiz ulanishini tekshirish (balans)", request=None, responses=OBJ,
))(integ.SmsCheckView)
extend_schema_view(post=extend_schema(
    tags=["admin"], summary="Sinov SMS yuborish",
    request=inline_serializer("SmsTest", {"phone": serializers.CharField()}), responses=OBJ,
))(integ.SmsTestView)
