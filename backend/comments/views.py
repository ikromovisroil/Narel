from django.db.models import Avg, Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from catalog.models import Product
from dashboard.views import AdminMixin

from .models import Comment
from .serializers import AdminCommentSerializer, CommentSerializer


class CommentPagination(PageNumberPagination):
    page_size = 10


def visible_threads(product):
    replies = Comment.objects.filter(is_hidden=False).select_related("user").order_by("created_at")
    return (
        Comment.objects.filter(product=product, parent__isnull=True, is_hidden=False)
        .select_related("user")
        .prefetch_related(Prefetch("replies", queryset=replies, to_attr="visible_replies"))
        .order_by("-created_at")
    )


def summary(product):
    visible = Comment.objects.filter(product=product, is_hidden=False)
    rated = visible.filter(parent__isnull=True, rating__isnull=False).aggregate(avg=Avg("rating"), n=Count("id"))
    return {
        "count": visible.count(),
        "rating": round(rated["avg"], 1) if rated["avg"] else None,
        "ratings_count": rated["n"],
    }


class ProductCommentsView(APIView):
    """GET — izohlar (hamma uchun), POST — yangi izoh yoki javob (kirgan foydalanuvchi)."""

    throttle_scope = "comments"

    def get_permissions(self):
        return [permissions.AllowAny()] if self.request.method == "GET" else [permissions.IsAuthenticated()]

    def get_throttles(self):
        return [ScopedRateThrottle()] if self.request.method == "POST" else []

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        paginator = CommentPagination()
        page = paginator.paginate_queryset(visible_threads(product), request, view=self)
        data = CommentSerializer(page, many=True, context={"request": request, "product": product}).data
        response = paginator.get_paginated_response(data)
        response.data["summary"] = summary(product)
        return response

    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        serializer = CommentSerializer(data=request.data, context={"request": request, "product": product})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(product=product, user=request.user)
        return Response(CommentSerializer(comment, context={"request": request, "product": product}).data,
                        status=status.HTTP_201_CREATED)


class MyCommentView(APIView):
    """O'z izohini o'chirish."""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk, user=request.user)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminCommentViewSet(
    AdminMixin, mixins.ListModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """Moderatsiya: ro'yxat, yashirish/ko'rsatish, o'chirish."""

    section = "comments"
    serializer_class = AdminCommentSerializer
    search_fields = ["text", "user__username", "user__first_name", "product__name"]
    filterset_fields = ["is_hidden", "product", "rating"]

    def get_queryset(self):
        qs = (
            Comment.objects.select_related("user", "product", "parent")
            .annotate(replies_count=Count("replies"))
            .order_by("-created_at")
        )
        kind = self.request.query_params.get("kind")
        if kind == "reviews":
            qs = qs.filter(parent__isnull=True)
        elif kind == "replies":
            qs = qs.filter(parent__isnull=False)
        elif kind == "low":
            qs = qs.filter(Q(rating__lte=2))
        return qs
