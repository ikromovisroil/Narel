from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from catalog.models import Category, Product

from .models import PaymentMethod


class PaymentSettingsTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("boss", password="x", is_staff=True, is_superuser=True)
        self.client_user = User.objects.create_user("client", password="x")
        cat = Category.objects.create(name="C", slug="c")
        self.product = Product.objects.create(name="P", slug="p", category=cat, price=1000, stock=10)
        self.payme = PaymentMethod.objects.get(code="payme")

    def order(self, method):
        self.client.force_authenticate(self.client_user)
        return self.client.post("/api/orders/", {
            "full_name": "A", "phone": "1", "address": "B", "payment_method": method,
            "cart": [{"product": self.product.id, "quantity": 1}],
        }, format="json")

    def test_defaults(self):
        codes = [m["code"] for m in self.client.get("/api/payment-methods/").json()]
        self.assertEqual(codes, ["cash", "card"])  # qolganlari kalitsiz o'chiq

    def test_cannot_activate_without_keys(self):
        self.client.force_authenticate(self.admin)
        r = self.client.patch(f"/api/admin/payment-methods/{self.payme.id}/", {"is_active": True}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Merchant ID", str(r.data))

    def test_configure_activate_and_secret_hidden(self):
        self.client.force_authenticate(self.admin)
        url = f"/api/admin/payment-methods/{self.payme.id}/"
        r = self.client.patch(url, {
            "config": {"merchant_id": "abc123", "secret_key": "TOP-SECRET", "hack": "x"}, "is_active": True,
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["config"]["secret_key"], "")  # maxfiy qiymat qaytmaydi
        self.assertNotIn("hack", r.data["config"])
        self.assertTrue(next(f for f in r.data["fields_schema"] if f["key"] == "secret_key")["is_set"])

        # Bo'sh maxfiy maydon yuborilsa eski qiymat saqlanadi
        self.client.patch(url, {"config": {"merchant_id": "new", "secret_key": ""}}, format="json")
        self.payme.refresh_from_db()
        self.assertEqual(self.payme.config["secret_key"], "TOP-SECRET")
        self.assertEqual(self.payme.config["merchant_id"], "new")

        # Saytda paydo bo'ladi, lekin kalitlarsiz
        public = self.client.get("/api/payment-methods/").json()
        self.assertIn("payme", [m["code"] for m in public])
        self.assertNotIn("TOP-SECRET", str(public))
        self.assertNotIn("config", public[0])

    def test_order_only_with_active_method(self):
        self.assertEqual(self.order("payme").status_code, 400)
        self.assertEqual(self.order("unknown").status_code, 400)
        self.assertEqual(self.order("cash").status_code, 201)

        PaymentMethod.objects.filter(code="cash").update(is_active=False)
        r = self.order("cash")
        self.assertEqual(r.status_code, 400)
        self.assertIn("payment_method", r.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 9)  # rad etilgan buyurtma omborga tegmaydi

    def test_admin_only(self):
        self.client.force_authenticate(self.client_user)
        self.assertEqual(self.client.get("/api/admin/payment-methods/").status_code, 403)

    def test_logo_upload(self):
        import io as _io
        import shutil
        import tempfile

        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from PIL import Image

        def png(size):
            buf = _io.BytesIO()
            Image.new("RGB", size, "blue").save(buf, "PNG")
            return SimpleUploadedFile("l.png", buf.getvalue(), content_type="image/png")

        media = tempfile.mkdtemp()
        try:
            with override_settings(MEDIA_ROOT=media):
                self.client.force_authenticate(self.admin)
                url = f"/api/admin/payment-methods/{self.payme.id}/upload/"
                self.assertEqual(self.client.post(url, {"file": png((300, 100))}, format="multipart").status_code, 400)
                r = self.client.post(url, {"file": png((256, 256))}, format="multipart")
                self.assertEqual(r.status_code, 200, r.data)
                self.assertTrue(r.data["logo"])
        finally:
            shutil.rmtree(media, ignore_errors=True)

    def test_installment_months_public(self):
        m = PaymentMethod.objects.get(code="installment")
        m.config = {"provider": "Uzum Nasiya", "merchant_id": "1", "api_key": "k", "months": "6"}
        m.is_active = True
        m.save()
        data = {x["code"]: x for x in self.client.get("/api/payment-methods/", HTTP_ACCEPT_LANGUAGE="ru").json()}
        self.assertEqual(data["installment"]["months"], 6)
        self.assertEqual(data["installment"]["title"], "Рассрочка")
