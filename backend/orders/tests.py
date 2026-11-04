from datetime import timedelta
from unittest.mock import patch

from django.test import override_settings

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase

from catalog.models import Category, Product

from .models import Branch, CustomerProfile, Order, PhoneCode, StoreSettings


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

    def test_postpone_without_reason(self):
        promised = self.today + timedelta(days=1)
        self.patch(status="confirmed", expected_date=str(promised))
        r = self.patch(expected_date=str(promised + timedelta(days=3)))
        self.assertEqual(r.status_code, 200, r.data)
        mine = self.mine()
        self.assertTrue(mine["is_delayed"])
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


class ProfileAddressTests(APITestCase):
    def setUp(self):
        StoreSettings.objects.update_or_create(pk=1, defaults={"delivery_enabled": True})
        cat = Category.objects.create(name="C", slug="c")
        self.product = Product.objects.create(name="P", slug="p", category=cat, price=100, stock=5)
        self.user = User.objects.create_user("ali", password="x", first_name="Ali", last_name="Valiyev")
        self.client.force_authenticate(self.user)

    def order(self, **data):
        body = {"delivery_method": "courier", "payment_method": "cash", "cart": [{"product": self.product.id, "quantity": 1}]}
        body.update(data)
        return self.client.post("/api/orders/", body, format="json")

    def test_saved_address_used_and_can_be_overridden(self):
        CustomerProfile.objects.create(user=self.user, phone="+998 90 123 45 67")
        r = self.client.patch("/api/auth/me/", {"address": "  Toshkent, Chilonzor 5  "}, format="json")
        self.assertEqual(r.data["address"], "Toshkent, Chilonzor 5")
        r = self.order()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["address"], "Toshkent, Chilonzor 5")
        r = self.order(full_name="Vali Aliyev", phone="+998 93 111 22 33", address="Samarqand, Registon 1")
        self.assertEqual((r.data["full_name"], r.data["phone"], r.data["address"]),
                         ("Vali Aliyev", "+998 93 111 22 33", "Samarqand, Registon 1"))
        # Profil o'zgarmaydi
        self.assertEqual(self.client.get("/api/auth/me/").json()["address"], "Toshkent, Chilonzor 5")

    def test_empty_fields_rejected(self):
        r = self.order(phone="+998 90 123 45 67")
        self.assertEqual(r.status_code, 400)
        self.assertIn("address", r.data)


@override_settings(GOOGLE_CLIENT_ID="test-client.apps.googleusercontent.com")
class GoogleLoginTests(APITestCase):
    INFO = {
        "aud": "test-client.apps.googleusercontent.com", "iss": "https://accounts.google.com", "sub": "123",
        "email": "Ali@Gmail.com", "email_verified": "true", "given_name": "Ali", "family_name": "Valiyev",
    }

    def google(self, info):
        with patch("orders.google.verify_google_token", return_value=info):
            return self.client.post("/api/auth/google/", {"credential": "x"}, format="json")

    def test_creates_account_then_logs_in(self):
        r = self.google(self.INFO)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(r.data["created"])
        user = User.objects.get(email="ali@gmail.com")
        self.assertEqual((user.first_name, user.last_name), ("Ali", "Valiyev"))
        self.assertFalse(user.has_usable_password())
        r = self.google(self.INFO)
        self.assertFalse(r.data["created"])
        self.assertEqual(User.objects.filter(email="ali@gmail.com").count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        self.assertEqual(self.client.get("/api/auth/me/").json()["email"], "ali@gmail.com")

    def test_links_existing_customer_and_blocks_staff(self):
        User.objects.create_user("ali", email="ali@gmail.com", password="x")
        r = self.google(self.INFO)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["created"])
        User.objects.create_user("boss", email="boss@gmail.com", password="x", is_staff=True)
        r = self.google({**self.INFO, "email": "boss@gmail.com"})
        self.assertEqual(r.status_code, 400)

    def test_invalid_token(self):
        self.assertEqual(self.google(None).status_code, 400)

    def test_public_client_id(self):
        self.assertEqual(self.client.get("/api/store-settings/").json()["google_client_id"], self.INFO["aud"])

    @override_settings(GOOGLE_CLIENT_ID="")
    def test_disabled(self):
        self.assertEqual(self.google(self.INFO).status_code, 400)


@override_settings(DEBUG=True, ESKIZ_EMAIL="", ESKIZ_PASSWORD="")
class PhoneCodeLoginTests(APITestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()  # so'rovlar cheklovi testlar orasida saqlanmasin

    def send(self, phone="90 123 45 67", agree=True):
        return self.client.post("/api/auth/code/send/", {"phone": phone, "agree": agree}, format="json")

    def verify(self, code, phone="+998901234567"):
        return self.client.post("/api/auth/code/verify/", {"phone": phone, "code": code}, format="json")

    def test_new_phone_creates_account(self):
        self.assertIn("agree", self.send(agree=False).data)
        self.assertIn("phone", self.send(phone="123").data)
        r = self.send()
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(r.data["is_new"])
        code = r.data["debug_code"]
        self.assertEqual(len(code), 6)
        r = self.verify(code)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(r.data["created"])
        user = User.objects.get(profile__phone="+998 90 123 45 67")
        self.assertFalse(user.has_usable_password())
        # Kod ikkinchi marta ishlamaydi
        self.assertEqual(self.verify(code).status_code, 400)

    def test_existing_customer_logs_in_and_resend_limit(self):
        user = User.objects.create_user("ali", password="x")
        CustomerProfile.objects.create(user=user, phone="+998 90 123 45 67")
        r = self.send()
        self.assertFalse(r.data["is_new"])
        self.assertEqual(self.send().status_code, 429)  # 60 soniya o'tmagan
        r = self.verify(r.data["debug_code"])
        self.assertFalse(r.data["created"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        self.assertEqual(self.client.get("/api/auth/me/").json()["username"], "ali")

    def test_wrong_code_attempts_and_expiry(self):
        code = self.send().data["debug_code"]
        wrong = "000000" if code != "000000" else "111111"
        for i in range(4):
            r = self.verify(wrong)
            self.assertEqual(r.data["attempts_left"], 4 - i)
        self.verify(wrong)  # 5-urinish — kod yonadi
        self.assertEqual(self.verify(code).status_code, 400)
        # Muddati o'tgan kod
        PhoneCode.objects.all().delete()
        code = self.send(phone="91 000 00 00").data["debug_code"]
        PhoneCode.objects.update(created_at=timezone.now() - timedelta(minutes=5))
        self.assertEqual(self.verify(code, "+998910000000").status_code, 400)

    def test_staff_cannot_use_phone_login(self):
        boss = User.objects.create_user("boss", password="x", is_staff=True)
        CustomerProfile.objects.create(user=boss, phone="+998 90 123 45 67")
        r = self.verify(self.send().data["debug_code"])
        self.assertEqual(r.status_code, 400)

    @override_settings(DEBUG=False)
    def test_no_sms_service_in_production(self):
        r = self.send()
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("debug_code", r.data)

    def test_offer_text(self):
        StoreSettings.objects.update_or_create(pk=1, defaults={"offer_text": "Shartlar", "offer_text_ru": "Условия"})
        self.assertEqual(self.client.get("/api/offer/", HTTP_ACCEPT_LANGUAGE="ru").json()["text"], "Условия")


class CustomerAccountTests(APITestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_password_login_only_for_staff(self):
        User.objects.create_user("ali", password="Parol-123456")
        User.objects.create_user("boss", password="Parol-123456", is_staff=True)
        login = lambda u: self.client.post("/api/auth/login/", {"username": u, "password": "Parol-123456"}, format="json")
        self.assertEqual(login("ali").status_code, 401)
        self.assertEqual(login("boss").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/register/", {}, format="json").status_code, 404)

    def test_profile_update_cannot_touch_phone_or_login(self):
        user = User.objects.create_user("ali", first_name="Ali", last_name="V")
        CustomerProfile.objects.create(user=user, phone="+998 90 123 45 67")
        User.objects.create_user("vali", email="v@b.uz")
        self.client.force_authenticate(user)
        r = self.client.patch("/api/auth/me/", {"email": "V@b.uz"}, format="json")
        self.assertIn("email", r.data)
        self.assertEqual(self.client.patch("/api/auth/me/", {"first_name": " "}, format="json").status_code, 400)
        r = self.client.patch("/api/auth/me/", {
            "first_name": "Alisher", "phone": "+998 93 555 44 33", "username": "boshqa", "is_staff": True,
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual((r.data["first_name"], r.data["phone"], r.data["username"]), ("Alisher", "+998 90 123 45 67", "ali"))
        user.refresh_from_db()
        self.assertFalse(user.is_staff)

    @override_settings(DEBUG=True, ESKIZ_EMAIL="", ESKIZ_PASSWORD="")
    def test_change_phone_with_code(self):
        user = User.objects.create_user("ali")
        CustomerProfile.objects.create(user=user, phone="+998 90 123 45 67")
        other = User.objects.create_user("vali")
        CustomerProfile.objects.create(user=other, phone="+998 91 000 00 00")
        self.client.force_authenticate(user)
        send = lambda p: self.client.post("/api/auth/code/send/", {"phone": p, "agree": True}, format="json").data
        change = lambda p, c: self.client.post("/api/auth/phone/", {"phone": p, "code": c}, format="json")
        code = send("93 555 44 33")["debug_code"]
        self.assertEqual(change("+998935554433", "000000" if code != "000000" else "111111").status_code, 400)
        r = change("+998935554433", code)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(self.client.get("/api/auth/me/").json()["phone"], "+998 93 555 44 33")
        # Boshqa mijozning raqami
        self.assertIn("phone", change("+998910000000", "123456").data)


class MyOrdersPaginationTests(APITestCase):
    def test_orders_come_five_per_page_newest_first(self):
        user = User.objects.create_user("ali")
        other = User.objects.create_user("vali")
        for i in range(12):
            Order.objects.create(user=user, full_name="A", phone="+998 90 123 45 67", address="Toshkent 1", total=i)
        Order.objects.create(user=other, full_name="V", phone="+998 91 000 00 00", address="Toshkent 2")
        self.client.force_authenticate(user)
        r = self.client.get("/api/orders/").json()
        self.assertEqual((r["count"], len(r["results"])), (12, 5))
        self.assertIsNotNone(r["next"])
        ids = [o["id"] for o in r["results"]]
        self.assertEqual(ids, sorted(ids, reverse=True))
        last = self.client.get("/api/orders/?page=3").json()
        self.assertEqual(len(last["results"]), 2)
        self.assertIsNone(last["next"])


class DjangoAdminOrderTests(APITestCase):
    """Django admin (texnik panel) orqali buyurtmani o'zgartirish React admin qoidalariga mos ishlaydi."""

    def setUp(self):
        from django.test import Client
        from .models import OrderItem
        self.root = User.objects.create_superuser("root", password="x")
        self.web = Client(HTTP_HOST="127.0.0.1")
        self.web.force_login(self.root)
        cat = Category.objects.create(name="C", slug="c")
        self.p = Product.objects.create(category=cat, name="P", slug="p", price=100, stock=10)
        self.order = Order.objects.create(user=self.root, full_name="A", phone="1", delivery_price=20, total=220)
        self.item = OrderItem.objects.create(order=self.order, product=self.p, price=100, quantity=2)
        self.url = f"/admin/orders/order/{self.order.pk}/change/"

    def post(self, status="new", qty=2, delete=False, extra=None):
        data = {
            "user": self.root.pk, "full_name": "A", "phone": "1", "address": "", "note": "",
            "status": status, "payment_method": "cash", "delivery_method": "courier", "delivery_price": 20,
            "expected_date": "", "original_expected_date": "", "delay_note": "", "pickup_branch": "", "pickup_point": "",
            "items-TOTAL_FORMS": 1, "items-INITIAL_FORMS": 1, "items-MIN_NUM_FORMS": 0, "items-MAX_NUM_FORMS": 1000,
            "items-0-id": self.item.pk, "items-0-order": self.order.pk, "items-0-product": self.p.pk,
            "items-0-price": 100, "items-0-quantity": qty,
        }
        if delete:
            data["items-0-DELETE"] = "on"
        data.update(extra or {})
        return self.web.post(self.url, data)

    def test_all_admin_pages_open(self):
        from django.contrib import admin
        from django.urls import reverse
        for model in admin.site._registry:
            m = model._meta
            r = self.web.get(reverse(f"admin:{m.app_label}_{m.model_name}_changelist"), follow=True)
            self.assertEqual(r.status_code, 200, m.label)

    def test_quantity_change_updates_stock_and_total(self):
        r = self.post(qty=5)
        self.assertEqual(r.status_code, 302)
        self.p.refresh_from_db(); self.order.refresh_from_db()
        self.assertEqual(self.p.stock, 7)
        self.assertEqual(self.order.total, 520)

    def test_not_enough_stock(self):
        r = self.post(qty=20)
        self.assertEqual(r.status_code, 200)  # forma xato bilan qaytadi
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 10)

    def test_delete_item_returns_stock(self):
        self.post(delete=True)
        self.p.refresh_from_db(); self.order.refresh_from_db()
        self.assertEqual(self.p.stock, 12)
        self.assertEqual(self.order.total, 20)

    def test_cancel_returns_stock_and_cannot_restore(self):
        self.assertEqual(self.post(status="cancelled").status_code, 302)
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 12)
        r = self.post(status="new")
        self.assertEqual(r.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cancelled")

    def test_cancel_action(self):
        r = self.web.post("/admin/orders/order/", {"action": "mark_cancelled", "_selected_action": [self.order.pk]})
        self.assertEqual(r.status_code, 302)
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 12)
        # Ikkinchi marta bekor qilish omborni yana oshirmaydi
        self.web.post("/admin/orders/order/", {"action": "mark_cancelled", "_selected_action": [self.order.pk]})
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 12)


class ApiDocsTests(APITestCase):
    """Swagger/ReDoc: DEBUG'da ochiq, serverda faqat xodim ko'radi."""

    PAGES = ["/api/schema/", "/api/docs/", "/api/redoc/"]

    @override_settings(DEBUG=True)
    def test_open_in_debug(self):
        for url in self.PAGES:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    @override_settings(DEBUG=False)
    def test_closed_in_production(self):
        for url in self.PAGES:
            self.assertIn(self.client.get(url).status_code, (401, 403), url)
        customer = User.objects.create_user("mijoz", password="x")
        self.client.force_login(customer)
        self.assertEqual(self.client.get("/api/docs/").status_code, 403)
        staff = User.objects.create_user("xodim", password="x", is_staff=True)
        self.client.force_login(staff)
        for url in self.PAGES:
            self.assertEqual(self.client.get(url).status_code, 200, url)
