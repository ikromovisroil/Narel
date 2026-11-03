from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("categories", views.CategoryViewSet, basename="admin-category")
router.register("brands", views.BrandViewSet, basename="admin-brand")
router.register("banners", views.BannerViewSet, basename="admin-banner")
router.register("products", views.ProductViewSet, basename="admin-product")
router.register("product-images", views.ProductImageViewSet, basename="admin-product-image")
router.register("orders", views.OrderViewSet, basename="admin-order")
router.register("customers", views.CustomerViewSet, basename="admin-customer")

urlpatterns = [
    path("stats/", views.StatsView.as_view()),
] + router.urls
