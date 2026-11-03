from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from catalog.models import Category, Product, ProductImage

from .models import StaffProfile, clean_permissions

ALL = ["view", "add", "change", "delete"]


def make_staff(username, perms=None, superuser=False):
    u = User.objects.create_user(username, password="Kuchli-Parol-77", is_staff=True, is_superuser=superuser)
    StaffProfile.objects.create(user=u, permissions=perms or {})
    return u


class CleanPermissionsTests(APITestCase):
    def test_rules(self):
        self.assertEqual(
            clean_permissions({
                "products": ["delete"],            # har qanday amal ko'rishni ham beradi
                "customers": ALL,                  # mijozlar faqat ko'riladi
                "orders": ["add", "change"],       # buyurtmaga "qo'shish" yo'q
                "brands": "edit",                  # eski format
                "banners": "view",                 # eski format
                "nonsense": ALL, "staff": "x",
            }),
            {
                "orders": ["view", "change"], "products": ["view", "delete"], "brands": ALL,
                "banners": ["view"], "customers": ["view"],
            },
        )


class SectionPermissionTests(APITestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="C", slug="c")

    def test_each_action_separately(self):
        viewer = make_staff("viewer", {"categories": ["view"]})
        self.client.force_authenticate(viewer)
        self.assertEqual(self.client.get("/api/admin/categories/").status_code, 200)
        self.assertEqual(self.client.post("/api/admin/categories/", {"name": "X"}, format="json").status_code, 403)
        self.assertEqual(self.client.get("/api/admin/products/").status_code, 403)
        self.assertEqual(self.client.get("/api/admin/stats/").status_code, 403)

        adder = make_staff("adder", {"categories": ["add"]})
        self.client.force_authenticate(adder)
        r = self.client.post("/api/admin/categories/", {"name": "Yangi"}, format="json")
        self.assertEqual(r.status_code, 201)
        new_id = r.data["id"]
        self.assertEqual(self.client.patch(f"/api/admin/categories/{new_id}/", {"name": "Z"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/admin/categories/{new_id}/").status_code, 403)

        changer = make_staff("changer", {"categories": ["change"]})
        self.client.force_authenticate(changer)
        self.assertEqual(self.client.patch(f"/api/admin/categories/{new_id}/", {"name": "Z"}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/admin/categories/{new_id}/").status_code, 403)

        deleter = make_staff("deleter", {"categories": ["delete"]})
        self.client.force_authenticate(deleter)
        self.assertEqual(self.client.delete(f"/api/admin/categories/{new_id}/").status_code, 204)

    def test_image_upload_and_gallery_delete_need_change(self):
        product = Product.objects.create(name="P", slug="p", category=self.cat, price=10)
        img = ProductImage.objects.create(product=product, image="products/x.png")
        adder = make_staff("adder", {"products": ["add", "delete"]})
        self.client.force_authenticate(adder)
        self.assertEqual(self.client.post(f"/api/admin/products/{product.id}/upload/", {}, format="multipart").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/admin/product-images/{img.id}/").status_code, 403)
        changer = make_staff("changer", {"products": ["change"]})
        self.client.force_authenticate(changer)
        self.assertEqual(self.client.delete(f"/api/admin/product-images/{img.id}/").status_code, 204)

    def test_me_returns_actions(self):
        u = make_staff("op", {"orders": ["change"]})
        self.client.force_authenticate(u)
        self.assertEqual(self.client.get("/api/auth/me/").json()["permissions"], {"orders": ["view", "change"]})
        boss = make_staff("boss", superuser=True)
        self.client.force_authenticate(boss)
        perms = self.client.get("/api/auth/me/").json()["permissions"]
        self.assertEqual(perms["staff"], ALL)
        self.assertEqual(perms["customers"], ["view"])


class StaffManagementTests(APITestCase):
    def setUp(self):
        self.boss = make_staff("boss", superuser=True)
        self.manager = make_staff("manager", {
            "staff": ALL, "orders": ["view", "change"], "products": ["view", "add"],
        })

    def test_superuser_creates_staff_who_can_login(self):
        self.client.force_authenticate(self.boss)
        r = self.client.post("/api/admin/staff/", {
            "username": "kassir", "first_name": "Ali", "position": "Operator",
            "password": "Kuchli-Parol-77", "permissions": {"orders": ["view", "change"], "customers": ALL},
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["position"], "Operator")
        self.assertEqual(r.data["permissions"], {"orders": ["view", "change"], "customers": ["view"]})
        self.assertNotIn("password", r.data)
        self.client.force_authenticate(None)
        login = self.client.post("/api/auth/login/", {"username": "kassir", "password": "Kuchli-Parol-77"}, format="json")
        self.assertEqual(login.status_code, 200)
        self.assertIsNotNone(User.objects.get(username="kassir").last_login)

    def test_weak_password_rejected(self):
        self.client.force_authenticate(self.boss)
        r = self.client.post("/api/admin/staff/", {"username": "x", "password": "123"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("password", r.data)
        self.assertEqual(self.client.post("/api/admin/staff/", {"username": "y"}, format="json").status_code, 400)

    def test_cannot_grant_more_than_own(self):
        self.client.force_authenticate(self.manager)
        ok = self.client.post("/api/admin/staff/", {
            "username": "op", "password": "Kuchli-Parol-77", "permissions": {"products": ["view", "add"]},
        }, format="json")
        self.assertEqual(ok.status_code, 201, ok.data)
        for perms in ({"products": ["delete"]}, {"products": ["change"]}, {"settings": ["view"]}):
            r = self.client.post("/api/admin/staff/", {
                "username": "op2", "password": "Kuchli-Parol-77", "permissions": perms,
            }, format="json")
            self.assertEqual(r.status_code, 400, perms)

    def test_non_superuser_cannot_touch_superuser(self):
        self.client.force_authenticate(self.manager)
        r = self.client.post("/api/admin/staff/", {
            "username": "hacker", "password": "Kuchli-Parol-77", "is_superuser": True,
        }, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.client.patch(f"/api/admin/staff/{self.boss.id}/", {"is_active": False}, format="json").status_code, 400)
        self.assertEqual(self.client.delete(f"/api/admin/staff/{self.boss.id}/").status_code, 403)
        self.boss.refresh_from_db()
        self.assertTrue(self.boss.is_active)

    def test_cannot_lock_yourself(self):
        self.client.force_authenticate(self.manager)
        url = f"/api/admin/staff/{self.manager.id}/"
        self.assertEqual(self.client.patch(url, {"is_active": False}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(url, {"permissions": {"orders": ["view"]}}, format="json").status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 400)
        self.client.force_authenticate(self.boss)
        url = f"/api/admin/staff/{self.boss.id}/"
        self.assertEqual(self.client.patch(url, {"is_superuser": False}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(url, {"first_name": "Bosh"}, format="json").status_code, 200)

    def test_blocked_staff_has_no_access(self):
        self.client.force_authenticate(self.boss)
        self.client.patch(f"/api/admin/staff/{self.manager.id}/", {"is_active": False}, format="json")
        self.manager.refresh_from_db()
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.get("/api/admin/orders/").status_code, 403)

    def test_password_change_and_sections(self):
        self.client.force_authenticate(self.boss)
        url = f"/api/admin/staff/{self.manager.id}/"
        self.client.patch(url, {"password": "Yangi-Parol-2026", "position": "Menejer"}, format="json")
        self.manager.refresh_from_db()
        self.assertTrue(self.manager.check_password("Yangi-Parol-2026"))
        self.client.patch(url, {"password": ""}, format="json")
        self.manager.refresh_from_db()
        self.assertTrue(self.manager.check_password("Yangi-Parol-2026"))
        self.assertEqual([s["username"] for s in self.client.get("/api/admin/staff/").json()], ["boss", "manager"])
        sections = {s["code"]: s["actions"] for s in self.client.get("/api/admin/staff/sections/").json()}
        self.assertEqual(sections["products"], ALL)
        self.assertEqual(sections["customers"], ["view"])
