from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, override_settings
from rest_framework.test import APIRequestFactory, APITestCase

from catalog.models import Category, Product
from orders.models import CustomerProfile
from orders.security import client_ip
from payments.models import PaymentMethod

from .models import AuditLog


class StaffLoginSecurityTests(APITestCase):
    URL = "/api/auth/login/"

    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user("boss", password="Juda-Kuchli-Parol-77", is_staff=True)

    def login(self, password, ip="10.0.0.1"):
        return self.client.post(self.URL, {"username": "boss", "password": password}, format="json", REMOTE_ADDR=ip)

    def test_lockout_after_five_failures_even_with_right_password(self):
        for _ in range(5):
            self.assertEqual(self.login("xato").status_code, 401)
        r = self.login("Juda-Kuchli-Parol-77")
        self.assertEqual(r.status_code, 429)
        self.assertEqual(AuditLog.objects.filter(action="login_failed").count(), 6)
        self.assertTrue(AuditLog.objects.filter(action="login_failed", details__contains="bloklangan").exists())

    def test_success_is_logged_with_ip_and_resets_counter(self):
        for _ in range(3):
            self.login("xato")
        r = self.login("Juda-Kuchli-Parol-77", ip="10.0.0.9")
        self.assertEqual(r.status_code, 200)
        entry = AuditLog.objects.get(action="login")
        self.assertEqual((entry.user, entry.ip, entry.is_staff), (self.staff, "10.0.0.9", True))
        for _ in range(4):
            self.login("xato")
        self.assertEqual(self.login("Juda-Kuchli-Parol-77").status_code, 200)  # hisoblagich qaytadan boshlangan

    def test_django_admin_login_is_also_locked(self):
        web = Client(HTTP_HOST="127.0.0.1")
        for _ in range(5):
            web.post("/admin/login/", {"username": "boss", "password": "xato"})
        web.post("/admin/login/", {"username": "boss", "password": "Juda-Kuchli-Parol-77"})
        self.assertNotIn("_auth_user_id", web.session)

    def test_refresh_rotation_and_logout_revokes(self):
        tokens = self.login("Juda-Kuchli-Parol-77").json()
        r = self.client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(r.status_code, 200)
        new_refresh = r.json()["refresh"]
        self.assertNotEqual(new_refresh, tokens["refresh"])
        # Eski refresh endi ishlamaydi
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json").status_code, 401)
        self.assertEqual(self.client.post("/api/auth/logout/", {"refresh": new_refresh}, format="json").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": new_refresh}, format="json").status_code, 401)
        self.assertTrue(AuditLog.objects.filter(action="logout", user=self.staff).exists())


class ClientIpTests(APITestCase):
    def req(self, xff):
        return APIRequestFactory().get("/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR=xff)

    @override_settings(NUM_PROXIES=0)
    def test_spoofed_header_ignored_without_proxy(self):
        self.assertEqual(client_ip(self.req("1.2.3.4")), "10.0.0.1")

    @override_settings(NUM_PROXIES=1)
    def test_behind_one_proxy_takes_last_hop(self):
        # Mijoz o'zi "1.2.3.4" deb yozib yuborsa ham, nginx qo'shgan haqiqiy manzil olinadi
        self.assertEqual(client_ip(self.req("1.2.3.4, 85.1.2.3")), "85.1.2.3")


@override_settings(GOOGLE_CLIENT_ID="web.apps.googleusercontent.com")
class GoogleEmailTakeoverTests(APITestCase):
    INFO = {"aud": "web.apps.googleusercontent.com", "iss": "https://accounts.google.com",
            "email": "victim@gmail.com", "email_verified": "true"}

    def google(self):
        with patch("orders.google.verify_google_token", return_value=self.INFO):
            return self.client.post("/api/auth/google/", {"credential": "x"}, format="json")

    def test_unverified_email_is_not_linked(self):
        attacker = User.objects.create_user("998901112233")
        CustomerProfile.objects.create(user=attacker, phone="+998 90 111 22 33")
        self.client.force_authenticate(attacker)
        self.client.patch("/api/auth/me/", {"email": "victim@gmail.com"}, format="json")
        self.client.force_authenticate(None)
        r = self.google()
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["created"])  # yangi hisob, hujumchinikiga emas
        attacker.refresh_from_db()
        self.assertEqual(attacker.email, "")
        self.assertTrue(User.objects.get(email="victim@gmail.com").profile.email_verified)

    def test_verified_email_is_linked(self):
        self.assertTrue(self.google().json()["created"])
        self.assertFalse(self.google().json()["created"])
        self.assertEqual(User.objects.filter(email="victim@gmail.com").count(), 1)

    def test_editing_email_drops_verification(self):
        self.google()
        user = User.objects.get(email="victim@gmail.com")
        self.client.force_authenticate(user)
        self.client.patch("/api/auth/me/", {"email": "new@gmail.com"}, format="json")
        user.profile.refresh_from_db()
        self.assertFalse(user.profile.email_verified)


class AuditTrailTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.root = User.objects.create_superuser("root", password="x")
        cat = Category.objects.create(name="C", slug="c")
        self.product = Product.objects.create(category=cat, name="P", slug="p", price=100, stock=5)

    def test_admin_changes_logged_secrets_masked_reads_not_logged(self):
        self.client.force_authenticate(self.root)
        self.client.get("/api/admin/products/")
        self.client.patch(f"/api/admin/products/{self.product.id}/", {"price": 150}, format="json",
                          REMOTE_ADDR="10.1.1.1")
        self.client.post("/api/admin/staff/", {"username": "yangi", "password": "Maxfiy-Parol-12345"}, format="json")
        self.client.post("/api/cart/add/", {"product": self.product.id, "quantity": 1}, format="json")
        update = AuditLog.objects.get(action="update")
        self.assertEqual((update.section, update.object_id, update.ip, update.status_code),
                         ("admin/products", str(self.product.id), "10.1.1.1", 200))
        self.assertIn('"price": 150', update.details)
        staff = AuditLog.objects.get(section="admin/staff")
        self.assertEqual(staff.action, "create")
        self.assertNotIn("Maxfiy-Parol", staff.details)
        self.assertIn('"password": "***"', staff.details)
        self.assertEqual(AuditLog.objects.count(), 2)  # GET va savat yozilmaydi

    def test_customer_sms_login_and_order_logged(self):
        with self.settings(DEBUG=True, ESKIZ_EMAIL="", ESKIZ_PASSWORD=""):
            code = self.client.post("/api/auth/code/send/", {"phone": "+998 90 555 44 33", "agree": True},
                                    format="json").json()["debug_code"]
            self.client.post("/api/auth/code/verify/", {"phone": "+998 90 555 44 33", "code": "000000" if code != "000000" else "111111"}, format="json")
            r = self.client.post("/api/auth/code/verify/", {"phone": "+998 90 555 44 33", "code": code}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(AuditLog.objects.filter(action="login_failed", details__contains="+998 90 555 44 33").exists())
        login = AuditLog.objects.get(action="login")
        self.assertIn("+998 90 555 44 33", login.who)
        self.assertNotIn(code, login.details)

    def test_only_superuser_sees_journal_in_django_admin(self):
        AuditLog.objects.create(action="login", who="x")
        web = Client(HTTP_HOST="127.0.0.1")
        staff = User.objects.create_user("op", password="x", is_staff=True)
        from django.contrib.auth.models import Permission
        staff.user_permissions.set(Permission.objects.filter(codename__in=["view_auditlog", "delete_auditlog"]))
        web.force_login(staff)
        self.assertEqual(web.get("/admin/audit/auditlog/").status_code, 403)
        web.force_login(self.root)
        r = web.get("/admin/audit/auditlog/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(web.get("/admin/audit/auditlog/1/delete/").status_code, 403)
        # API orqali umuman yo'q
        self.client.force_authenticate(self.root)
        self.assertEqual(self.client.get("/api/admin/audit/").status_code, 404)


class DjangoAdminSecretsTests(APITestCase):
    def setUp(self):
        self.root = User.objects.create_superuser("root", password="x")
        self.web = Client(HTTP_HOST="127.0.0.1")
        self.web.force_login(self.root)

    def test_payment_secret_masked_and_kept(self):
        m = PaymentMethod.objects.get(code="click")  # to'lov usullari migratsiyada yaratilgan
        m.config = {"service_id": "1", "merchant_id": "2", "merchant_user_id": "3", "secret_key": "SUPER-SECRET"}
        m.save()
        page = self.web.get(f"/admin/payments/paymentmethod/{m.pk}/change/").content.decode()
        self.assertNotIn("SUPER-SECRET", page)
        self.assertIn("********", page)
        r = self.web.post(f"/admin/payments/paymentmethod/{m.pk}/change/", {
            "code": "click", "title": "Click 2", "title_ru": "", "description": "", "description_ru": "",
            "test_mode": "on", "order": 0,
            "config": '{"service_id": "1", "merchant_id": "2", "merchant_user_id": "3", "secret_key": "********"}',
        })
        self.assertEqual(r.status_code, 302)
        m.refresh_from_db()
        self.assertEqual((m.title, m.config["secret_key"]), ("Click 2", "SUPER-SECRET"))

    def test_eskiz_password_not_rendered_and_kept(self):
        from orders.models import IntegrationSettings
        s = IntegrationSettings.load()
        s.eskiz_password = "ESKIZ-PAROL"
        s.save()
        page = self.web.get("/admin/orders/integrationsettings/1/change/").content.decode()
        self.assertNotIn("ESKIZ-PAROL", page)
        r = self.web.post("/admin/orders/integrationsettings/1/change/", {
            "sms_enabled": "on", "eskiz_email": "a@b.uz", "eskiz_password": "", "eskiz_from": "",
            "sms_low_balance": "", "sms_otp_domain": "", "google_client_id": "", "google_ios_client_id": "",
            "google_android_client_id": "",
        })
        self.assertEqual(r.status_code, 302)
        s.refresh_from_db()
        self.assertEqual((s.eskiz_email, s.eskiz_password), ("a@b.uz", "ESKIZ-PAROL"))
