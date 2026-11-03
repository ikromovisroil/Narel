from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APITestCase

from catalog.models import Category, Product
from staff.models import StaffProfile

from .models import Comment


class CommentTests(APITestCase):
    def setUp(self):
        cache.clear()  # throttle hisoblagichi testlar orasida aralashmasin
        cat = Category.objects.create(name="C", slug="c")
        self.product = Product.objects.create(name="P", slug="p", category=cat, price=10)
        self.other = Product.objects.create(name="Q", slug="q", category=cat, price=10)
        self.ali = User.objects.create_user("ali", password="x", first_name="Ali")
        self.vali = User.objects.create_user("vali", password="x")
        self.seller = User.objects.create_user("sotuvchi", password="x", is_staff=True, first_name="Do'kon")
        self.url = "/api/products/p/comments/"

    def post(self, user, **data):
        self.client.force_authenticate(user)
        return self.client.post(self.url, data, format="json")

    def test_guest_reads_but_cannot_write(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.url, {"text": "Salom"}, format="json").status_code, 401)

    def test_thread_with_replies_and_summary(self):
        root = self.post(self.ali, text="Zo'r choynak!", rating=5).data
        self.assertEqual(root["author"], "Ali")
        self.post(self.vali, text="Rostdanmi? Tez qaynaydimi?", parent=root["id"], rating=1)
        reply = self.post(self.seller, text="Ha, 3 daqiqada qaynaydi", parent=root["id"]).data
        # Javobga javob — o'sha suhbatga tushadi
        self.post(self.ali, text="Rahmat!", parent=reply["id"])
        self.post(self.vali, text="Yomon emas", rating=3)

        self.client.force_authenticate(None)
        data = self.client.get(self.url).json()
        self.assertEqual(data["count"], 2)  # asosiy izohlar soni
        self.assertEqual(data["summary"], {"count": 5, "rating": 4.0, "ratings_count": 2})
        thread = next(c for c in data["results"] if c["id"] == root["id"])
        self.assertEqual([r["text"] for r in thread["replies"]], ["Rostdanmi? Tez qaynaydimi?", "Ha, 3 daqiqada qaynaydi", "Rahmat!"])
        self.assertIsNone(thread["replies"][0]["rating"])  # javobda baho yo'q
        self.assertTrue(thread["replies"][1]["is_staff"])

    def test_validation(self):
        self.assertEqual(self.post(self.ali, text=" ").status_code, 400)
        self.assertEqual(self.post(self.ali, text="Yaxshi", rating=6).status_code, 400)
        foreign = Comment.objects.create(product=self.other, user=self.vali, text="Boshqa mahsulot")
        self.assertEqual(self.post(self.ali, text="Javob", parent=foreign.id).status_code, 400)
        self.assertEqual(self.post(self.ali, text="x" * 1001).status_code, 400)

    def test_delete_only_own(self):
        mine = self.post(self.ali, text="Mening izohim").data
        self.client.force_authenticate(self.vali)
        self.assertEqual(self.client.delete(f"/api/comments/{mine['id']}/").status_code, 404)
        self.client.force_authenticate(self.ali)
        self.assertEqual(self.client.delete(f"/api/comments/{mine['id']}/").status_code, 204)

    def test_hidden_not_shown_and_moderation_permissions(self):
        c = self.post(self.ali, text="Spam spam").data
        moderator = User.objects.create_user("mod", password="x", is_staff=True)
        StaffProfile.objects.create(user=moderator, permissions={"comments": ["view", "change"]})
        self.client.force_authenticate(moderator)
        self.assertEqual(self.client.patch(f"/api/admin/comments/{c['id']}/", {"is_hidden": True}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/admin/comments/{c['id']}/").status_code, 403)  # o'chirish ruxsati yo'q
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).json()["count"], 0)

    def test_throttle(self):
        for i in range(10):
            self.assertEqual(self.post(self.ali, text=f"Izoh {i}").status_code, 201)
        self.assertEqual(self.post(self.ali, text="Yana bittasi").status_code, 429)


class AdminReplyTests(APITestCase):
    def setUp(self):
        cache.clear()
        cat = Category.objects.create(name="C", slug="c")
        self.product = Product.objects.create(name="P", slug="p", category=cat, price=10)
        self.client_user = User.objects.create_user("ali", password="x", first_name="Ali")
        self.question = Comment.objects.create(product=self.product, user=self.client_user, text="Kafolat bormi?")
        self.other = Comment.objects.create(product=self.product, user=self.client_user, text="Rangi qanday?")
        self.operator = User.objects.create_user("op", password="x", is_staff=True, first_name="Operator")
        StaffProfile.objects.create(user=self.operator, permissions={"comments": ["view", "add"]})

    def test_reply_shows_on_site_with_store_badge(self):
        self.client.force_authenticate(self.operator)
        r = self.client.post(f"/api/admin/comments/{self.question.id}/reply/", {"text": "Ha, 1 yil rasmiy kafolat."}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data["is_staff"])
        self.assertEqual(r.data["parent"], self.question.id)

        self.client.force_authenticate(None)
        thread = next(c for c in self.client.get("/api/products/p/comments/").json()["results"] if c["id"] == self.question.id)
        self.assertEqual(thread["replies"][0]["text"], "Ha, 1 yil rasmiy kafolat.")
        self.assertTrue(thread["replies"][0]["is_staff"])

    def test_reply_to_reply_goes_to_same_thread(self):
        answer = Comment.objects.create(product=self.product, user=self.client_user, parent=self.question, text="Yana savol")
        self.client.force_authenticate(self.operator)
        r = self.client.post(f"/api/admin/comments/{answer.id}/reply/", {"text": "Javob"}, format="json")
        self.assertEqual(r.data["parent"], self.question.id)

    def test_unanswered_filter_and_flag(self):
        self.client.force_authenticate(self.operator)
        self.client.post(f"/api/admin/comments/{self.question.id}/reply/", {"text": "Ha, bor."}, format="json")
        ids = [c["id"] for c in self.client.get("/api/admin/comments/?kind=unanswered").json()["results"]]
        self.assertEqual(ids, [self.other.id])
        rows = {c["id"]: c for c in self.client.get("/api/admin/comments/").json()["results"]}
        self.assertTrue(rows[self.question.id]["staff_replied"])
        self.assertFalse(rows[self.other.id]["staff_replied"])

    def test_permissions_and_validation(self):
        viewer = User.objects.create_user("v", password="x", is_staff=True)
        StaffProfile.objects.create(user=viewer, permissions={"comments": ["view"]})
        self.client.force_authenticate(viewer)
        self.assertEqual(self.client.post(f"/api/admin/comments/{self.question.id}/reply/", {"text": "Salom"}, format="json").status_code, 403)
        self.client.force_authenticate(self.operator)
        self.assertEqual(self.client.post(f"/api/admin/comments/{self.question.id}/reply/", {"text": " "}, format="json").status_code, 400)
        # Faqat "add" bor — yashira olmaydi
        self.assertEqual(self.client.patch(f"/api/admin/comments/{self.question.id}/", {"is_hidden": True}, format="json").status_code, 403)
