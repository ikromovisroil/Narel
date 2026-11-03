"""Admin jadvallarini (sahifalash, qidiruv, filtr) sinash uchun ko'p test ma'lumot.

    python manage.py seed_test_data          # yaratish
    python manage.py seed_test_data --clear  # faqat test ma'lumotlarini o'chirish

Belgilar: mahsulot slug "test-product-", brend "test-brand-", kategoriya "test-cat-",
banner "Test banner", mijoz va xodim login "tst_", buyurtma izohi "Test buyurtma".
Test mahsulotlar va bannerlar nofaol — do'kon saytida ko'rinmaydi.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalog.models import Banner, Brand, Category, Product, ProductSpec
from comments.models import Comment
from orders.models import Branch, CustomerProfile, Order, OrderItem, StoreSettings
from staff.models import StaffProfile

FIRST = ["Aziz", "Bobur", "Dilnoza", "Gulnora", "Jasur", "Kamola", "Laziz", "Madina", "Nodir", "Ozoda",
         "Rustam", "Sardor", "Shahzod", "Umida", "Xurshid", "Zarina", "Otabek", "Malika", "Sherzod", "Nilufar"]
LAST = ["Karimov", "Rahimova", "Tursunov", "Yusupova", "Aliyev", "Qodirova", "Ergashev", "Saidova",
        "Nazarov", "Xolmatova", "Ismoilov", "Abdullayeva", "Mirzayev", "Hasanova"]
STREETS = ["Chilonzor", "Yunusobod", "Mirzo Ulug'bek", "Sergeli", "Yakkasaroy", "Olmazor", "Shayxontohur", "Mirobod"]
BRANDS = ["Hofmann", "Vitek", "Redmond", "Polaris", "Scarlett", "Tefal", "Bosch", "Midea", "Haier", "Hisense",
          "TCL", "Gorenje", "Candy", "Beko", "Indesit", "Zanussi", "Kenwood", "Braun", "Rowenta", "Dyson",
          "JBL", "Marshall", "Logitech", "Asus", "Acer"]
KINDS = ["Elektr choynak", "Blender", "Mikroto'lqinli pech", "Changyutgich", "Dazmol", "Fen", "Kolonka",
         "Monitor", "Sichqoncha", "Klaviatura", "Smart soat", "Quloqchin", "Planshet", "Televizor", "Muzlatgich"]
GOOD = ["Juda yaxshi mahsulot, tavsiya qilaman!", "Tez yetkazib berishdi, rahmat.", "Narxiga arziydi.",
        "Sifati zo'r, ishlatishga qulay.", "Hammasi tavsifdagidek."]
BAD = ["Kutganimdek emas.", "Qadog'i biroz ezilgan holda keldi.", "Yetkazish kechikdi.", "Ovozi past ekan."]


class Command(BaseCommand):
    help = "Admin sahifalarini sinash uchun test ma'lumot yaratadi (--clear — o'chiradi)"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Faqat test ma'lumotlarini o'chirish")

    def handle(self, *args, **opts):
        if opts["clear"]:
            self.clear()
            return
        random.seed(2026)
        with transaction.atomic():
            self.clear(quiet=True)
            self.now = timezone.now()
            brands = self.brands()
            cats = self.categories()
            products = self.products(brands, cats)
            self.banners()
            customers = self.customers()
            self.orders(customers)
            self.comments(customers, products)
            self.staff()
        self.stdout.write(self.style.SUCCESS("Tayyor. O'chirish: python manage.py seed_test_data --clear"))

    def log(self, what, n):
        self.stdout.write(f"  {what}: {n} ta")

    def ago(self, days_max):
        return self.now - timedelta(days=random.uniform(0, days_max), minutes=random.randint(0, 600))

    # ---------- yaratish ----------
    def brands(self):
        items = [Brand.objects.create(name=n, slug=f"test-brand-{i + 1}") for i, n in enumerate(BRANDS)]
        self.log("Brendlar", len(items))
        return items

    def categories(self):
        tops = list(Category.objects.filter(parent__isnull=True).exclude(slug__startswith="test-cat-"))
        items = []
        for i in range(12):
            name = f"Test bo'lim {i + 1}"
            items.append(Category.objects.create(
                name=name, name_ru=f"Тестовый раздел {i + 1}", slug=f"test-cat-{i + 1}",
                parent=random.choice(tops) if tops else None, order=100 + i,
            ))
        self.log("Kategoriyalar", len(items))
        return items

    def products(self, brands, cats):
        items = []
        for i in range(60):
            kind = random.choice(KINDS)
            brand = random.choice(brands)
            price = Decimal(random.randrange(150_000, 15_000_000, 10_000))
            discount = random.choice([0, 0, 100_000, 300_000])
            p = Product.objects.create(
                name=f"{brand.name} {kind} T{i + 1:02d}", slug=f"test-product-{i + 1}",
                sku=f"TST-{1000 + i}", category=random.choice(cats), brand=brand, price=price,
                old_price=price + discount if discount else None,
                stock=random.choice([0, 1, 3, 5, 12, 40]), description="Test mahsulot (admin sinovi uchun).",
                is_active=False, is_hit=i % 7 == 0, is_new=i % 5 == 0,
            )
            ProductSpec.objects.create(product=p, name="Kafolat", value=f"{random.choice([6, 12, 24])} oy")
            items.append(p)
        self.log("Mahsulotlar (nofaol)", len(items))
        return items

    def banners(self):
        for i in range(6):
            Banner.objects.create(title=f"Test banner {i + 1}", subtitle="Admin sinovi uchun",
                                  link="/catalog", order=100 + i, is_active=False)
        self.log("Bannerlar (nofaol)", 6)

    def customers(self):
        users = []
        for i in range(50):
            first, last = random.choice(FIRST), random.choice(LAST)
            u = User.objects.create_user(
                username=f"tst_mijoz_{i + 1:02d}", first_name=first, last_name=last,
                email=f"tst{i + 1}@example.com" if i % 3 else "",
            )
            u.set_unusable_password()
            u.date_joined = self.ago(180)
            u.save(update_fields=["password", "date_joined"])
            CustomerProfile.objects.create(
                user=u, phone=f"+998 99 0{i // 10}{i % 10} {10 + i:02d} {20 + i % 70:02d}",
                address=f"Toshkent, {random.choice(STREETS)} {random.randint(1, 30)}-uy",
            )
            users.append(u)
        self.log("Mijozlar", len(users))
        return users

    def orders(self, customers):
        real = list(Product.objects.filter(is_active=True))
        branch = Branch.objects.filter(is_active=True).first()
        store = StoreSettings.load()
        statuses = ["delivered"] * 40 + ["cancelled"] * 10 + ["shipped"] * 10 + ["confirmed"] * 10 + ["new"] * 10
        for status in statuses:
            u = random.choice(customers)
            when = self.ago(2 if status == "new" else 90)
            pickup = branch is not None and random.random() < 0.25
            o = Order.objects.create(
                user=u, full_name=f"{u.first_name} {u.last_name}", phone=u.profile.phone, address=u.profile.address,
                note="Test buyurtma", payment_method=random.choice(["cash", "card", "click", "payme"]),
                delivery_method="pickup" if pickup else "courier", status=status,
                pickup_branch=branch if pickup else None,
                pickup_point=f"{branch.name} · {branch.address}" if pickup else "",
            )
            total = Decimal(0)
            for p in random.sample(real, min(len(real), random.randint(1, 3))):
                qty = random.randint(1, 2)
                OrderItem.objects.create(order=o, product=p, price=p.price, quantity=qty)
                total += p.price * qty
            fields = {"created_at": when, "total": total}
            if not pickup:
                fields["delivery_price"] = store.delivery_price
                fields["total"] = total + store.delivery_price
                if status != "new":
                    d = (when + timedelta(days=store.delivery_days)).date()
                    fields["expected_date"] = fields["original_expected_date"] = d
            Order.objects.filter(pk=o.pk).update(**fields)
        self.log("Buyurtmalar", len(statuses))

    def comments(self, customers, products):
        n = 0
        for _ in range(60):
            rating = random.choice([5, 5, 5, 4, 4, 3, 2, 1])
            c = Comment.objects.create(
                product=random.choice(products), user=random.choice(customers), rating=rating,
                text=random.choice(GOOD if rating >= 4 else BAD), is_hidden=random.random() < 0.1,
            )
            Comment.objects.filter(pk=c.pk).update(created_at=self.ago(60))
            n += 1
        self.log("Izohlar (test mahsulotlarda)", n)

    def staff(self):
        roles = [
            ("Operator", {"orders": ["view", "change"], "customers": ["view"]}),
            ("Kontent menejer", {"products": ["view", "add", "change"], "categories": ["view", "add", "change"]}),
            ("Moderator", {"comments": ["view", "add", "change", "delete"]}),
            ("Omborchi", {"products": ["view", "change"]}),
            ("Kuryerlar boshlig'i", {"orders": ["view", "change"]}),
            ("Hisobchi", {"dashboard": ["view"], "orders": ["view"]}),
        ]
        for i, (position, perms) in enumerate(roles):
            u = User.objects.create_user(
                username=f"tst_xodim_{i + 1}", first_name=random.choice(FIRST), last_name=random.choice(LAST),
                is_staff=True,
            )
            u.set_unusable_password()  # kira olmaydi — faqat ro'yxatni ko'rish uchun
            u.save(update_fields=["password"])
            StaffProfile.objects.create(user=u, position=position, permissions=perms)
        self.log("Xodimlar (kira olmaydi)", len(roles))

    # ---------- o'chirish ----------
    def clear(self, quiet=False):
        test_users = User.objects.filter(username__startswith="tst_")
        counts = {
            "Buyurtmalar": Order.objects.filter(note="Test buyurtma").delete()[1].get("orders.Order", 0),
            "Mijoz va xodimlar": test_users.delete()[1].get("auth.User", 0),
            "Mahsulotlar": Product.objects.filter(slug__startswith="test-product-").delete()[1].get("catalog.Product", 0),
            "Kategoriyalar": Category.objects.filter(slug__startswith="test-cat-").delete()[1].get("catalog.Category", 0),
            "Brendlar": Brand.objects.filter(slug__startswith="test-brand-").delete()[1].get("catalog.Brand", 0),
            "Bannerlar": Banner.objects.filter(title__startswith="Test banner").delete()[1].get("catalog.Banner", 0),
        }
        if not quiet:
            for k, v in counts.items():
                self.log(f"O'chirildi — {k}", v)
