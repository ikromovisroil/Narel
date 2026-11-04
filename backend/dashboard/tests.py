import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from catalog.models import Brand, Category, Product
from orders.models import Order, OrderItem

MEDIA = tempfile.mkdtemp()


def png(name="a.png", size=(800, 800), fmt="PNG"):
    buf = io.BytesIO()
    Image.new("RGB", size, "red").save(buf, fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=f"image/{fmt.lower()}")


@override_settings(MEDIA_ROOT=MEDIA)
class AdminApiTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.staff = User.objects.create_user("boss", password="x", is_staff=True, is_superuser=True)
        self.user = User.objects.create_user("client", password="x")
        self.cat = Category.objects.create(name="Telefonlar", slug="telefonlar")
        self.client.force_authenticate(self.staff)

    def test_non_staff_forbidden(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/admin/stats/").status_code, 403)
        self.assertEqual(self.client.get("/api/admin/products/").status_code, 403)

    def test_product_crud_with_specs_and_auto_slug(self):
        r = self.client.post("/api/admin/products/", {
            "name": "Galaxy A56 qora", "slug": "qolda-yozilgan", "category": self.cat.id, "price": 5000000, "stock": 3,
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
            "name": "Galaxy A56 qora (yangi)", "slug": "boshqa", "price": 4500000, "old_price": 5000000,
            "specs": [{"name": "Xotira", "value": "512 GB", "name_ru": "Память"}],
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["specs"], [{"name": "Xotira", "value": "512 GB", "name_ru": "Память", "value_ru": ""}])
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

    def test_image_rules(self):
        p = Product.objects.create(name="X", slug="x", category=self.cat, price=10)
        url = f"/api/admin/products/{p.id}/upload/"

        r = self.client.post(url, {"file": png(size=(300, 300))}, format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("kichik", r.data["file"][0])

        r = self.client.post(url, {"file": png(size=(1200, 600))}, format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("nisbati 1:1", r.data["file"][0])

        r = self.client.post(url, {"file": png("a.gif", fmt="GIF")}, format="multipart")
        self.assertEqual(r.status_code, 400)

        # 10% gacha farq mumkin
        r = self.client.post(url, {"file": png("a.jpg", size=(1000, 950), fmt="JPEG")}, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)

        # Banner: 16:5, kamida 1200x375
        b = self.client.post("/api/admin/banners/", {"title": "B"}, format="json").data
        r = self.client.post(f"/api/admin/banners/{b['id']}/upload/", {"file": png(size=(1000, 1000))}, format="multipart")
        self.assertEqual(r.status_code, 400)
        r = self.client.post(f"/api/admin/banners/{b['id']}/upload/", {"file": png(size=(1280, 400))}, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)

        # Brend logosi 5:2
        br = self.client.post("/api/admin/brands/", {"name": "Sony"}, format="json").data
        r = self.client.post(f"/api/admin/brands/{br['id']}/upload/", {"file": png(size=(400, 160))}, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)

        rules = self.client.get("/api/admin/image-rules/").data
        self.assertEqual(rules["product"]["recommended"], [1000, 1000])

    def test_image_too_heavy(self):
        p = Product.objects.create(name="X", slug="x", category=self.cat, price=10)
        heavy = SimpleUploadedFile("big.png", b"0" * (5 * 1024 * 1024 + 1), content_type="image/png")
        r = self.client.post(f"/api/admin/products/{p.id}/upload/", {"file": heavy}, format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("5 MB", r.data["file"][0])

    def _orders(self, model, **flt):
        return list(model.objects.filter(**flt).order_by("order").values_list("name" if model is Category else "title", "order"))

    def test_order_insert_shifts_others(self):
        from catalog.models import Banner
        for t in ["A", "B", "C"]:
            self.client.post("/api/admin/banners/", {"title": t}, format="json")  # oxiriga qo'shiladi
        self.assertEqual(self._orders(Banner), [("A", 1), ("B", 2), ("C", 3)])

        # C ni 1-o'ringa: qolganlari suriladi
        c = Banner.objects.get(title="C")
        r = self.client.patch(f"/api/admin/banners/{c.id}/", {"order": 1}, format="json")
        self.assertEqual(r.data["order"], 1)
        self.assertEqual(self._orders(Banner), [("C", 1), ("A", 2), ("B", 3)])

        # Yangi banner 2-o'ringa
        self.client.post("/api/admin/banners/", {"title": "D", "order": 2}, format="json")
        self.assertEqual(self._orders(Banner), [("C", 1), ("D", 2), ("A", 3), ("B", 4)])

        # Juda katta raqam — oxiriga
        self.client.patch(f"/api/admin/banners/{c.id}/", {"order": 99}, format="json")
        self.assertEqual(self._orders(Banner), [("D", 1), ("A", 2), ("B", 3), ("C", 4)])

        # Faqat boshqa maydon o'zgarsa tartib joyida qoladi
        self.client.patch(f"/api/admin/banners/{c.id}/", {"is_active": False}, format="json")
        self.assertEqual(self._orders(Banner)[-1], ("C", 4))

        # O'chirilganda bo'shliq qolmaydi
        self.client.delete(f"/api/admin/banners/{Banner.objects.get(title='A').id}/")
        self.assertEqual(self._orders(Banner), [("D", 1), ("B", 2), ("C", 3)])

        self.assertEqual(self.client.patch(f"/api/admin/banners/{c.id}/", {"order": 0}, format="json").status_code, 400)

    def test_category_order_per_parent(self):
        ids = {}
        for name in ["X", "Y"]:
            ids[name] = self.client.post("/api/admin/categories/", {"name": name, "parent": self.cat.id}, format="json").data["id"]
        other = self.client.post("/api/admin/categories/", {"name": "Boshqa"}, format="json").data
        self.assertEqual(self._orders(Category, parent=self.cat), [("X", 1), ("Y", 2)])
        self.assertEqual(other["order"], 2)  # asosiy darajada "Telefonlar"dan keyin

        # Y ni boshqa ota kategoriyaning 1-o'rniga ko'chirish: eski guruh zichlanadi
        self.client.patch(f"/api/admin/categories/{ids['Y']}/", {"parent": other["id"], "order": 1}, format="json")
        self.assertEqual(self._orders(Category, parent=self.cat), [("X", 1)])
        self.assertEqual(self._orders(Category, parent_id=other["id"]), [("Y", 1)])

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
        self.user.first_name = "Klient"
        self.user.save(update_fields=["first_name"])
        r = self.client.get("/api/admin/customers/?search=Klient")
        row = r.data["results"][0]
        self.assertEqual(row["orders_count"], 2)
        self.assertEqual(int(row["total_spent"]), 500)

    def test_customers_list_excludes_staff(self):
        User.objects.create_user("xodim", password="x", is_staff=True)
        r = self.client.get("/api/admin/customers/?page_size=200")
        names = [c["username"] for c in r.data["results"]]
        self.assertIn("client", names)
        self.assertNotIn("xodim", names)
        self.assertTrue(all(not c["is_staff"] for c in r.data["results"]))
        self.assertEqual(r.data["count"], User.objects.filter(is_staff=False).count())

    def test_me_cannot_make_self_staff(self):
        self.client.force_authenticate(self.user)
        self.client.patch("/api/auth/me/", {"is_staff": True}, format="json")
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)


class SoftDeleteTests(APITestCase):
    """Admin panelda o'chirish = yashirish: tarix, buyurtmalar va izohlar saqlanadi, Django admin'dan qaytariladi."""

    def setUp(self):
        from orders.models import CustomerProfile, Order, OrderItem
        self.root = User.objects.create_superuser("root", password="x")
        self.client.force_authenticate(self.root)
        self.top = Category.objects.create(name="Texnika", slug="texnika")
        self.cat = Category.objects.create(name="Choynaklar", slug="choynaklar", parent=self.top)
        self.brand = Brand.objects.create(name="Tefal", slug="tefal")
        self.p = Product.objects.create(category=self.cat, brand=self.brand, name="Tefal choynak", slug="tefal-choynak",
                                        price=100, stock=5)
        self.customer = User.objects.create_user("998901234567")
        CustomerProfile.objects.create(user=self.customer, phone="+998 90 123 45 67")
        self.order = Order.objects.create(user=self.customer, full_name="A", phone="1", total=100)
        OrderItem.objects.create(order=self.order, product=self.p, price=100, quantity=1)

    def test_delete_ordered_product_hides_it_but_keeps_history(self):
        r = self.client.delete(f"/api/admin/products/{self.p.id}/")
        self.assertEqual(r.status_code, 204)
        self.p.refresh_from_db()
        self.assertIsNotNone(self.p.deleted_at)
        # Admin panelda va saytda yo'q
        self.assertNotIn(self.p.id, [x["id"] for x in self.client.get("/api/admin/products/").data["results"]])
        self.assertEqual(self.client.get(f"/api/admin/products/{self.p.id}/").status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/products/").data["count"], 0)
        self.assertEqual(self.client.get("/api/products/tefal-choynak/").status_code, 404)
        # Mijozning buyurtma tarixida nom qoladi, havola yo'q
        self.client.force_authenticate(self.customer)
        item = self.client.get("/api/orders/").data["results"][0]["items"][0]
        self.assertEqual((item["product_name"], item["product_slug"]), ("Tefal choynak", None))
        # Buyurtma qilib bo'lmaydi
        r = self.client.post("/api/orders/", {"cart": [{"product": self.p.id, "quantity": 1}]}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_order_keeps_name_after_rename(self):
        self.p.name = "Yangi nom"
        self.p.save()
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get("/api/orders/").data["results"][0]["items"][0]["product_name"], "Tefal choynak")

    def test_django_admin_shows_and_restores(self):
        from django.test import Client
        self.client.delete(f"/api/admin/products/{self.p.id}/")
        web = Client(HTTP_HOST="127.0.0.1")
        web.force_login(self.root)
        page = web.get("/admin/catalog/product/?deleted=yes").content.decode()
        self.assertIn("Tefal choynak", page)
        web.post("/admin/catalog/product/", {"action": "restore", "_selected_action": [self.p.id]})
        self.p.refresh_from_db()
        self.assertIsNone(self.p.deleted_at)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/products/tefal-choynak/").status_code, 200)

    def test_category_and_brand_with_products_cannot_be_deleted(self):
        self.assertEqual(self.client.delete(f"/api/admin/categories/{self.top.id}/").status_code, 400)
        self.assertEqual(self.client.delete(f"/api/admin/brands/{self.brand.id}/").status_code, 400)
        # Mahsulot o'chirilgach — mumkin; ichki kategoriya ham birga yashiriladi
        self.client.delete(f"/api/admin/products/{self.p.id}/")
        self.assertEqual(self.client.delete(f"/api/admin/categories/{self.top.id}/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/admin/brands/{self.brand.id}/").status_code, 204)
        self.cat.refresh_from_db()
        self.assertIsNotNone(self.cat.deleted_at)
        self.assertEqual(self.client.get("/api/admin/categories/").data, [])
        self.assertEqual(self.client.get("/api/admin/brands/").data, [])
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/categories/").data, [])
        # Hech narsa bazadan o'chmagan
        self.assertEqual((Category.objects.count(), Brand.objects.count(), Product.objects.count()), (2, 1, 1))

    def test_deleted_category_cannot_be_chosen(self):
        empty = Category.objects.create(name="Bo'sh", slug="bosh")
        self.client.delete(f"/api/admin/categories/{empty.id}/")
        r = self.client.patch(f"/api/admin/products/{self.p.id}/", {"category": empty.id}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("category", r.data)

    def test_counts_and_favorites_skip_deleted(self):
        from orders.models import Favorite
        Favorite.objects.create(user=self.customer, product=self.p)
        self.client.delete(f"/api/admin/products/{self.p.id}/")
        self.assertEqual(self.client.get("/api/admin/stats/").data["products"], 0)
        cats = {c["name"]: c["products_count"] for c in self.client.get("/api/admin/categories/").data}
        self.assertEqual(cats["Choynaklar"], 0)
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get("/api/favorites/").data, [])
