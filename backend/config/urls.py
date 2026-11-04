from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from catalog.views import BannerViewSet, BrandViewSet, CategoryViewSet, ProductViewSet
from orders.views import MeView, OrderViewSet
from payments.views import PublicPaymentMethodViewSet
from comments.views import MyCommentView, ProductCommentsView
from orders.google import GoogleLoginView
from orders.login import ChangePhoneView, OfferView, SendCodeView, VerifyCodeView
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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/admin/", include("dashboard.urls")),
    path("api/products/<slug:slug>/comments/", ProductCommentsView.as_view()),
    path("api/comments/<int:pk>/", MyCommentView.as_view()),
    path("api/store-settings/", PublicStoreSettingsView.as_view()),
    path("api/", include(router.urls)),
    path("api/auth/login/", TokenObtainPairView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/auth/me/", MeView.as_view()),
    path("api/auth/phone/", ChangePhoneView.as_view()),
    path("api/auth/google/", GoogleLoginView.as_view()),
    path("api/auth/code/send/", SendCodeView.as_view()),
    path("api/auth/code/verify/", VerifyCodeView.as_view()),
    path("api/offer/", OfferView.as_view()),
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
