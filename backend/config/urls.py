from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView

from catalog.views import BannerViewSet, BrandViewSet, CategoryViewSet, ProductViewSet
from orders.views import MeView, OrderViewSet
from orders.account import (
    CartAddView, CartItemDeleteView, CartSyncView, CartView, FavoriteDeleteView, FavoritesSyncView, FavoritesView,
)
from payments.views import PublicPaymentMethodViewSet
from comments.views import MyCommentView, ProductCommentsView
from orders.google import GoogleLoginView
from orders.login import ChangePhoneView, LogoutView, OfferView, SendCodeView, StaffLoginView, VerifyCodeView
from orders.store import PublicStoreSettingsView
from config.schema import DocsAccess  # Swagger izohlari ham shu modulda

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("brands", BrandViewSet)
router.register("banners", BannerViewSet)
router.register("products", ProductViewSet)
router.register("orders", OrderViewSet, basename="order")
router.register("payment-methods", PublicPaymentMethodViewSet, basename="payment-method")

admin.site.site_header = "Narel — texnik boshqaruv"
admin.site.site_title = "Narel admin"
admin.site.index_title = "Barcha ma'lumotlar"

# API yo'llari. Bir xil ro'yxat ikki joyda: /api/ (sayt va admin panel) va /api/v1/ (mobil ilovalar).
# Mobil ilova /api/v1/ ni ishlatadi: keyinchalik mos kelmaydigan o'zgarish bo'lsa /api/v2/ ochiladi,
# eski ilovalar esa v1 da ishlashda davom etadi.
api_patterns = [
    path("admin/", include("dashboard.urls")),
    path("products/<slug:slug>/comments/", ProductCommentsView.as_view()),
    path("comments/<int:pk>/", MyCommentView.as_view()),
    path("store-settings/", PublicStoreSettingsView.as_view()),
    path("favorites/", FavoritesView.as_view()),
    path("favorites/sync/", FavoritesSyncView.as_view()),
    path("favorites/<int:product_id>/", FavoriteDeleteView.as_view()),
    path("cart/", CartView.as_view()),
    path("cart/add/", CartAddView.as_view()),
    path("cart/sync/", CartSyncView.as_view()),
    path("cart/<int:product_id>/", CartItemDeleteView.as_view()),
    path("", include(router.urls)),
    path("auth/login/", StaffLoginView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("auth/phone/", ChangePhoneView.as_view()),
    path("auth/google/", GoogleLoginView.as_view()),
    path("auth/code/send/", SendCodeView.as_view()),
    path("auth/code/verify/", VerifyCodeView.as_view()),
    path("offer/", OfferView.as_view()),
]

urlpatterns = [
    path(settings.DJANGO_ADMIN_URL, admin.site.urls),
    path("api/v1/", include(api_patterns)),
    path("api/", include(api_patterns)),
]

# Swagger: DEBUG'da ochiq; serverda faqat xodim (avval /admin/ ga kiriladi)
docs_access = {
    "authentication_classes": [SessionAuthentication, JWTAuthentication],
    "permission_classes": [DocsAccess],
}
urlpatterns += [
    path("api/schema/", SpectacularAPIView.as_view(**docs_access), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", **docs_access), name="swagger"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema", **docs_access), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
