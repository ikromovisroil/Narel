"""Qidiruv tizimlari (Google, Yandex) uchun: /robots.txt va /sitemap.xml.

nginx bu ikki manzilni Django'ga uzatadi. Sitemap har so'rovda bazadan yig'iladi —
yangi mahsulot yoki kategoriya qo'shilsa, avtomatik ro'yxatga tushadi.
"""
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from .models import Category, Product

# Shaxsiy sahifalar qidiruvga kirmaydi. /api/ yopilmaydi: Google sahifani chizishda undan ma'lumot oladi.
ROBOTS_DISALLOW = ["/seller/", "/cart", "/checkout", "/login", "/orders", "/profile", "/favorites"]


def _base(request):
    return request.build_absolute_uri("/").rstrip("/")


@require_GET
@cache_control(public=True, max_age=3600)
def robots_txt(request):
    lines = ["User-agent: *", *(f"Disallow: {p}" for p in ROBOTS_DISALLOW), "",
             f"Sitemap: {_base(request)}/sitemap.xml", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@require_GET
@cache_control(public=True, max_age=3600)
def sitemap_xml(request):
    base = _base(request)
    urls = [(f"{base}/", None, "daily", "1.0"), (f"{base}/catalog", None, "daily", "0.8")]
    for slug in Category.objects.alive().values_list("slug", flat=True):
        urls.append((f"{base}/catalog/{slug}", None, "daily", "0.7"))
    products = (Product.objects.alive().filter(is_active=True, category__deleted_at__isnull=True)
                .order_by("-updated_at").values_list("slug", "updated_at")[:45000])
    for slug, updated in products:
        urls.append((f"{base}/product/{slug}", updated, "weekly", "0.6"))
    urls.append((f"{base}/oferta", None, "yearly", "0.1"))

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, freq, prio in urls:
        out.append("<url><loc>" + escape(loc) + "</loc>"
                   + (f"<lastmod>{lastmod.date().isoformat()}</lastmod>" if lastmod else "")
                   + f"<changefreq>{freq}</changefreq><priority>{prio}</priority></url>")
    out.append("</urlset>")
    return HttpResponse("\n".join(out), content_type="application/xml; charset=utf-8")
