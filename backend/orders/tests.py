from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase

from catalog.models import Category, Product

from .models import Branch, Order, StoreSettings


class DeliverySettingsTests(APITestCase):
    def setUp(self):
        cat = Category.objects.create(name="C", slug="c")
        self.product = Product.objects.create(name="P", slug="p", category=cat, price=100_000, stock=10)
        self.client_user = User.objects.create_user("client", password="x")
        self.boss = User.objects.create_user("boss", password="x", is_staff=True, is_superuser=True)

    def order(self, delivery, **extra):
        self.client.force_authenticate(self.client_user)
        data = {
            "full_name": "A", "phone": "+998 90 123 45 67", "address": "Toshkent, Chilonzor 1",
            "delivery_method": delivery, "payment_method": "cash",
            "cart": [{"product": self.product.id, "quantity": 2}],
        }
        if delivery == "pickup":
            data["pickup_branch"] = Branch.objects.filter(is_active=True).first().id
        data.update(extra)
        return self.client.post("/api/orders/", data, format="json")

    def test_courier_adds_price_and_expected_date(self):
        StoreSettings.objects.update_or_create(pk=1, defaults={"delivery_price": 25_000, "delivery_days": 2})
        r = self.order("courier", address="Chilonzor")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(int(r.data["total"]), 225_000)
        self.assertEqual(int(r.data["delivery_price"]), 25_000)
        self.assertEqual(r.data["expected_date"], str(timezone.localdate() + timedelta(days=2)))

    def test_pickup_is_free(self):
        StoreSettings.objects.update_or_create(pk=1, defaults={"delivery_price": 25_000})
        r = self.order("pickup")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(int(r.data["total"]), 200_000)
        self.assertEqual(r.data["address"], "Toshkent, Chilonzor 1")
        self.assertIsNone(r.data["expected_date"])

    def test_disabled_delivery_rejected(self):
        StoreSettings.objects.update_or_create(pk=1, defaults={"delivery_enabled": False})
        r = self.order("courier", address="Chilonzor")
        self.assertEqual(r.status_code, 400)
        self.assertIn("delivery_method", r.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertEqual(self.order("pickup").status_code, 201)

    def test_public_settings_localized(self):
        data = self.client.get("/api/store-settings/", HTTP_ACCEPT_LANGUAGE="ru").json()
        self.assertEqual(data["address"], "г. Ташкент")
        self.assertTrue(data["delivery_enabled"])
        self.assertNotIn("address_ru", data)

    def test_admin_cannot_disable_both(self):
        self.client.force_authenticate(self.boss)
        r = self.client.patch("/api/admin/store-settings/", {"delivery_enabled": False, "pickup_enabled": False}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.patch("/api/admin/store-settings/", {"delivery_enabled": False, "phone": "+998 90 123 45 67"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(StoreSettings.load().delivery_enabled)
        self.client.force_authenticate(self.client_user)
        self.assertEqual(self.client.get("/api/admin/store-settings/").status_code, 403)

    def test_admin_changes_expected_date_customer_sees_it(self):
        order = self.order("courier").data
        self.client.force_authenticate(self.boss)
        r = self.client.patch(f"/api/admin/orders/{order['id']}/", {"expected_date": "2026-12-01", "status": "shipped"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.client.force_authenticate(self.client_user)
        mine = self.client.get("/api/orders/").json()["results"][0]
        self.assertEqual((mine["status"], mine["expected_date"]), ("shipped", "2026-12-01"))
        self.assertEqual(Order.objects.get(pk=order["id"]).total, 200_000)


class PhoneAndAddressTests(APITestCase):
    def setUp(self):
        cat = Category.objects.create(name="C", slug="c")
        self.product = Product.objects.create(name="P", slug="p", category=cat, price=100, stock=10)
        self.client.force_authenticate(User.objects.create_user("client", password="x"))

    def post(self, phone, address, delivery="courier"):
        return self.client.post("/api/orders/", {
            "full_name": "A", "phone": phone, "address": address, "delivery_method": delivery,
            "payment_method": "cash", "cart": [{"product": self.product.id, "quantity": 1}],
            "pickup_branch": Branch.objects.first().id if delivery == "pickup" else None,
        }, format="json")

    def test_phone_required_and_normalized(self):
        for bad in ("+998", "", "123", "+998 90 123 45", "+7 900 123 45 67"):
            r = self.post(bad, "Toshkent, Chilonzor 1")
            self.assertEqual(r.status_code, 400, bad)
            self.assertIn("phone", r.data)
        for good in ("+998901234567", "90 123-45-67", "998 (90) 123 45 67"):
            r = self.post(good, "Toshkent, Chilonzor 1")
            self.assertEqual(r.status_code, 201, (good, r.data))
            self.assertEqual(r.data["phone"], "+998 90 123 45 67")

    def test_address_required_for_both_delivery_types(self):
        for delivery in ("courier", "pickup"):
            for bad in ("", "   ", "Tosh"):
                r = self.post("+998901234567", bad, delivery)
                self.assertEqual(r.status_code, 400, (delivery, bad))
                self.assertIn("address", r.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)  # rad etilganlar omborga tegmaydi


class AcceptAndDelayTests(APITestCase):
    def setUp(self):
        cat = Category.objects.create(name="C", slug="c")
        product = Product.objects.create(name="P", slug="p", category=cat, price=100, stock=10)
        self.customer = User.objects.create_user("client", password="x")
        self.boss = User.objects.create_user("boss", password="x", is_staff=True, is_superuser=True)
        self.client.force_authenticate(self.customer)
        self.order = self.client.post("/api/orders/", {
            "full_name": "A", "phone": "+998901234567", "address": "Toshkent, Chilonzor 1",
            "delivery_method": "courier", "payment_method": "cash", "cart": [{"product": product.id, "quantity": 1}],
        }, format="json").data
        self.url = f"/api/admin/orders/{self.order['id']}/"
        self.client.force_authenticate(self.boss)
        self.today = timezone.localdate()

    def patch(self, **data):
        return self.client.patch(self.url, data, format="json")

    def mine(self):
        self.client.force_authenticate(self.customer)
        data = self.client.get("/api/orders/").json()["results"][0]
        self.client.force_authenticate(self.boss)
        return data

    def test_accept_requires_date(self):
        r = self.patch(status="confirmed")
        self.assertEqual(r.status_code, 400)
        self.assertIn("expected_date", r.data)
        r = self.patch(status="confirmed", expected_date=str(self.today - timedelta(days=1)))
        self.assertEqual(r.status_code, 400)  # o'tgan sana
        promised = self.today + timedelta(days=2)
        r = self.patch(status="confirmed", expected_date=str(promised))
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["original_expected_date"], str(promised))
        self.assertFalse(r.data["is_delayed"])

    def test_delay_shown_to_customer_with_apology_note(self):
        promised = self.today + timedelta(days=1)
        self.patch(status="confirmed", expected_date=str(promised))
        # Yuborilganda sana surildi
        later = promised + timedelta(days=2)
        r = self.patch(status="shipped", expected_date=str(later), delay_note="Ombordan kech chiqdi")
        self.assertEqual(r.status_code, 200, r.data)
        mine = self.mine()
        self.assertTrue(mine["is_delayed"])
        self.assertEqual(mine["expected_date"], str(later))
        self.assertEqual(mine["original_expected_date"], str(promised))  # va'da o'zgarmaydi
        self.assertEqual(mine["delay_note"], "Ombordan kech chiqdi")
        # Sana va'daga qaytsa — kechikish va izoh yo'qoladi
        self.patch(expected_date=str(promised))
        mine = self.mine()
        self.assertFalse(mine["is_delayed"])
        self.assertEqual(mine["delay_note"], "")

    def test_overdue_counts_as_delayed_until_delivered(self):
        self.patch(status="confirmed", expected_date=str(self.today))
        Order.objects.filter(pk=self.order["id"]).update(expected_date=self.today - timedelta(days=1))
        self.assertTrue(self.mine()["is_delayed"])
        self.patch(status="delivered")
        self.assertFalse(self.mine()["is_delayed"])
        r = self.patch(expected_date=str(self.today + timedelta(days=5)))
        self.assertEqual(r.status_code, 400)  # yakunlanganini o'zgartirib bo'lmaydi

    def test_pickup_does_not_require_date(self):
        self.client.force_authenticate(self.customer)
        cat = Category.objects.get(slug="c")
        product = Product.objects.create(name="Q", slug="q", category=cat, price=50, stock=5)
        order = self.client.post("/api/orders/", {
            "full_name": "A", "phone": "+998901234567", "address": "Toshkent, Chilonzor 1",
            "delivery_method": "pickup", "payment_method": "cash", "cart": [{"product": product.id, "quantity": 1}],
            "pickup_branch": Branch.objects.first().id,
        }, format="json").data
        self.client.force_authenticate(self.boss)
        r = self.client.patch(f"/api/admin/orders/{order['id']}/", {"status": "confirmed"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)


class BranchTests(APITestCase):
    def setUp(self):
        Branch.objects.all().delete()
        cat = Category.objects.create(name="C", slug="c")
        self.product = Product.objects.create(name="P", slug="p", category=cat, price=100, stock=10)
        self.chilonzor = Branch.objects.create(name="Chilonzor", name_ru="Чиланзар", address="Chilonzor 1", phone="+998 71 111 11 11", order=1)
        self.yunusobod = Branch.objects.create(name="Yunusobod", address="Yunusobod 5", phone="+998 71 222 22 22", order=2)
        self.closed = Branch.objects.create(name="Yopiq", address="X ko'chasi", phone="1", is_active=False, order=3)
        self.customer = User.objects.create_user("client", password="x")
        self.boss = User.objects.create_user("boss", password="x", is_staff=True, is_superuser=True)

    def pickup(self, branch_id):
        self.client.force_authenticate(self.customer)
        return self.client.post("/api/orders/", {
            "full_name": "A", "phone": "+998901234567", "address": "Toshkent, Chilonzor 1",
            "delivery_method": "pickup", "payment_method": "cash", "pickup_branch": branch_id,
            "cart": [{"product": self.product.id, "quantity": 1}],
        }, format="json")

    def test_public_settings_list_active_branches(self):
        data = self.client.get("/api/store-settings/", HTTP_ACCEPT_LANGUAGE="ru").json()
        self.assertEqual([b["name"] for b in data["branches"]], ["Чиланзар", "Yunusobod"])
        self.assertTrue(data["pickup_enabled"])

    def test_branch_required_and_must_be_active(self):
        self.assertEqual(self.pickup(None).status_code, 400)
        self.assertEqual(self.pickup(self.closed.id).status_code, 400)
        r = self.pickup(self.yunusobod.id)
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["pickup_branch_info"]["name"], "Yunusobod")
        order = Order.objects.get(pk=r.data["id"])
        self.assertIn("Yunusobod 5", order.pickup_point)
        # Filial o'chirilsa ham buyurtmada joy saqlanadi
        self.yunusobod.delete()
        mine = self.client.get("/api/orders/").json()["results"][0]
        self.assertIn("Yunusobod 5", mine["pickup_branch_info"]["name"])

    def test_courier_ignores_branch(self):
        self.client.force_authenticate(self.customer)
        r = self.client.post("/api/orders/", {
            "full_name": "A", "phone": "+998901234567", "address": "Toshkent, Chilonzor 1",
            "delivery_method": "courier", "payment_method": "cash", "pickup_branch": self.chilonzor.id,
            "cart": [{"product": self.product.id, "quantity": 1}],
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertIsNone(r.data["pickup_branch"])

    def test_admin_crud_and_last_branch_protection(self):
        self.client.force_authenticate(self.boss)
        r = self.client.post("/api/admin/branches/", {"name": "Sergeli", "address": "Sergeli 3", "phone": "+998 71 333 33 33"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(len(self.client.get("/api/admin/branches/").json()), 4)
        # Yetkazib berish o'chiq — oxirgi faol filialni o'chirib bo'lmaydi
        StoreSettings.objects.update_or_create(pk=1, defaults={"delivery_enabled": False})
        Branch.objects.exclude(pk=self.chilonzor.pk).update(is_active=False)
        self.assertEqual(self.client.patch(f"/api/admin/branches/{self.chilonzor.id}/", {"is_active": False}, format="json").status_code, 400)
        self.assertEqual(self.client.delete(f"/api/admin/branches/{self.chilonzor.id}/").status_code, 400)

    def test_cannot_enable_pickup_without_branches(self):
        Branch.objects.update(is_active=False)
        StoreSettings.objects.update_or_create(pk=1, defaults={"pickup_enabled": False})
        self.client.force_authenticate(self.boss)
        r = self.client.patch("/api/admin/store-settings/", {"pickup_enabled": True}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertFalse(self.client.get("/api/store-settings/").json()["pickup_enabled"])

    def test_settings_change_permission_for_branches(self):
        from staff.models import StaffProfile
        viewer = User.objects.create_user("v", password="x", is_staff=True)
        StaffProfile.objects.create(user=viewer, permissions={"settings": ["view"]})
        self.client.force_authenticate(viewer)
        self.assertEqual(self.client.get("/api/admin/branches/").status_code, 200)
        self.assertEqual(self.client.post("/api/admin/branches/", {"name": "Z", "address": "Z ko'chasi", "phone": "1"}, format="json").status_code, 403)


class AccountTests(APITestCase):
    def register(self, **data):
        body = {"first_name": "Ali", "last_name": "Valiyev", "phone": "90 123 45 67", "password": "Kuchli-parol-77"}
        body.update(data)
        return self.client.post("/api/auth/register/", body, format="json")

    def login(self, username, password="Kuchli-parol-77"):
        return self.client.post("/api/auth/login/", {"username": username, "password": password}, format="json")

    def test_register_requires_name_and_phone(self):
        r = self.register(first_name="", phone="123", username="ali")
        self.assertEqual(r.status_code, 400)
        self.assertIn("first_name", r.data)
        self.assertIn("phone", r.data)

    def test_register_with_email_only_and_login_by_email_or_phone(self):
        r = self.register(email="Ali@Mail.uz")
        self.assertEqual(r.status_code, 201, r.data)
        user = User.objects.get(pk=r.data["id"])
        self.assertEqual(user.username, "ali@mail.uz")
        self.assertEqual(user.profile.phone, "+998 90 123 45 67")
        self.assertEqual(self.login("ALI@mail.uz").status_code, 200)
        self.assertEqual(self.login("+998901234567").status_code, 200)
        self.assertEqual(self.login("ali@mail.uz", "xato").status_code, 401)

    def test_register_needs_login_or_email_and_unique_values(self):
        self.assertEqual(self.register().status_code, 400)
        self.assertEqual(self.register(username="ali", email="a@b.uz").status_code, 201)
        r = self.register(username="ALI", email="A@b.uz", phone="+998 90 123 45 67")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.data), {"username", "email", "phone"})

    def test_profile_update(self):
        self.register(username="ali")
        self.register(username="vali", phone="91 000 00 00", email="v@b.uz")
        user = User.objects.get(username="ali")
        self.client.force_authenticate(user)
        me = self.client.get("/api/auth/me/").json()
        self.assertEqual(me["phone"], "+998 90 123 45 67")
        # Band telefon/login/email — xato
        r = self.client.patch("/api/auth/me/", {"phone": "+998910000000", "username": "Vali", "email": "V@b.uz"}, format="json")
        self.assertEqual(set(r.data), {"phone", "username", "email"})
        r = self.client.patch("/api/auth/me/", {"first_name": " "}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.patch("/api/auth/me/", {
            "first_name": "Alisher", "last_name": "Navoiy", "phone": "93-555-44-33", "username": "alisher",
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["phone"], "+998 93 555 44 33")
        self.assertEqual(r.data["username"], "alisher")
        self.assertFalse(r.data["is_staff"])
        # Xodim bo'lib qolishning iloji yo'q
        self.client.patch("/api/auth/me/", {"is_staff": True, "is_superuser": True}, format="json")
        user.refresh_from_db()
        self.assertFalse(user.is_staff or user.is_superuser)
        self.client.force_authenticate(None)
        self.assertEqual(self.login("alisher").status_code, 200)

    def test_order_takes_name_and_phone_from_profile(self):
        StoreSettings.objects.update_or_create(pk=1, defaults={"delivery_enabled": True})
        cat = Category.objects.create(name="C", slug="c")
        product = Product.objects.create(name="P", slug="p", category=cat, price=100, stock=5)
        self.register(username="ali")
        user = User.objects.get(username="ali")
        self.client.force_authenticate(user)
        body = {
            "address": "Toshkent, Chilonzor 1", "delivery_method": "courier", "payment_method": "cash",
            "cart": [{"product": product.id, "quantity": 1}],
        }
        r = self.client.post("/api/orders/", body, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual((r.data["full_name"], r.data["phone"]), ("Ali Valiyev", "+998 90 123 45 67"))
        # Profilida telefon yo'q eski hisob — xato bilan
        old = User.objects.create_user("old", password="x")
        self.client.force_authenticate(old)
        r = self.client.post("/api/orders/", body, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("full_name", r.data)
