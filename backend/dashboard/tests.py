import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from catalog.models import Category, Product
from orders.models import Order, OrderItem

MEDIA = tempfile.mkdtemp()


def png(name="a.png"):
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA)
class AdminApiTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.staff = User.objects.create_user("boss", password="x", is_staff=True)
        self.user = User.objects.create_user("client", password="x")
        self.cat = Category.objects.create(name="Telefonlar", slug="telefonlar")
        self.client.force_authenticate(self.staff)

    def test_non_staff_forbidden(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/admin/stats/").status_code, 403)
        self.assertEqual(self.client.get("/api/admin/products/").status_code, 403)

    def test_product_crud_with_specs_and_auto_slug(self):
        r = self.client.post("/api/admin/products/", {
            "name": "Galaxy A56 qora", "category": self.cat.id, "price": 5000000, "stock": 3,
            "specs": [{"name": "Xotira", "value": "256 GB"}, {"name": "Rang", "value": "Qora"}],
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["slug"], "galaxy-a56-qora")
        self.assertEqual(len(r.data["specs"]), 2)
        pid = r.data["id"]

        # Bir xil nom — slug takrorlanmaydi
        r2 = self.client.post("/api/admin/products/", {
            "name": "Galaxy A56 qora", "category": self.cat.id, "price": 1, "stock": 1,
        }, format="json")
        self.assertEqual(r2.data["slug"], "galaxy-a56-qora-2")

        r = self.client.patch(f"/api/admin/products/{pid}/", {
            "price": 4500000, "old_price": 5000000, "specs": [{"name": "Xotira", "value": "512 GB"}],
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["specs"], [{"name": "Xotira", "value": "512 GB"}])
        self.assertEqual(r.data["slug"], "galaxy-a56-qora")

        r = self.client.patch(f"/api/admin/products/{pid}/", {"old_price": 100}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_image_upload_and_gallery(self):
        p = Product.objects.create(name="X", slug="x", category=self.cat, price=10)
        r = self.client.post(f"/api/admin/products/{p.id}/upload/", {"file": png()}, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(r.data["image"])
        r = self.client.post(f"/api/admin/products/{p.id}/images/", {"file": png("b.png")}, format="multipart")
        self.assertEqual(r.status_code, 201)
        img_id = r.data["images"][0]["id"]
        self.assertEqual(self.client.delete(f"/api/admin/product-images/{img_id}/").status_code, 204)
        bad = SimpleUploadedFile("x.png", b"not an image", content_type="image/png")
        r = self.client.post(f"/api/admin/products/{p.id}/upload/", {"file": bad}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_delete_protected_category(self):
        Product.objects.create(name="X", slug="x", category=self.cat, price=10)
        r = self.client.delete(f"/api/admin/categories/{self.cat.id}/")
        self.assertEqual(r.status_code, 400)

    def test_category_cannot_be_own_parent(self):
        child = Category.objects.create(name="Ichki", slug="ichki", parent=self.cat)
        r = self.client.patch(f"/api/admin/categories/{self.cat.id}/", {"parent": child.id}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_cancel_order_restores_stock_and_stats(self):
        p = Product.objects.create(name="X", slug="x", category=self.cat, price=100, stock=5)
        order = Order.objects.create(user=self.user, full_name="A", phone="1", address="B", total=300)
        OrderItem.objects.create(order=order, product=p, price=100, quantity=3)

        stats = self.client.get("/api/admin/stats/").data
        self.assertEqual(stats["today"], {"revenue": 300, "orders": 1})
        self.assertEqual(stats["new_orders"], 1)
        self.assertEqual(stats["top_products"][0]["qty"], 3)
        self.assertEqual(len(stats["chart"]), 30)

        r = self.client.patch(f"/api/admin/orders/{order.id}/", {"status": "cancelled", "total": 1}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["total"], "300")  # total o'zgarmaydi
        p.refresh_from_db()
        self.assertEqual(p.stock, 8)

        r = self.client.patch(f"/api/admin/orders/{order.id}/", {"status": "new"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.client.get("/api/admin/stats/").data["today"]["revenue"], 0)

    def test_customers_totals(self):
        Order.objects.create(user=self.user, full_name="A", phone="1", total=500)
        Order.objects.create(user=self.user, full_name="A", phone="1", total=200, status="cancelled")
        r = self.client.get("/api/admin/customers/?search=client")
        row = r.data["results"][0]
        self.assertEqual(row["orders_count"], 2)
        self.assertEqual(int(row["total_spent"]), 500)

    def test_me_cannot_make_self_staff(self):
        self.client.force_authenticate(self.user)
        self.client.patch("/api/auth/me/", {"is_staff": True}, format="json")
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)
