from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from catalog.views import BannerViewSet, BrandViewSet, CategoryViewSet, ProductViewSet
from orders.views import MeView, OrderViewSet, RegisterView
from payments.views import PublicPaymentMethodViewSet
from comments.views import MyCommentView, ProductCommentsView

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("brands", BrandViewSet)
router.register("banners", BannerViewSet)
router.register("products", ProductViewSet)
router.register("orders", OrderViewSet, basename="order")
router.register("payment-methods", PublicPaymentMethodViewSet, basename="payment-method")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/admin/", include("dashboard.urls")),
    path("api/products/<slug:slug>/comments/", ProductCommentsView.as_view()),
    path("api/comments/<int:pk>/", MyCommentView.as_view()),
    path("api/", include(router.urls)),
    path("api/auth/register/", RegisterView.as_view()),
    path("api/auth/login/", TokenObtainPairView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/auth/me/", MeView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
