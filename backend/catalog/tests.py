from rest_framework.test import APITestCase

from .i18n import to_latin
from .models import Banner, Brand, Category, Product, ProductSpec


class CyrillicSearchHelperTests(APITestCase):
    def test_cyrillic_to_latin(self):
        self.assertEqual(to_latin("Музлатгич"), "Muzlatgich")
        self.assertEqual(to_latin("ўзбек"), "o'zbek")


class PublicApiLanguageTests(APITestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Muzlatgichlar", name_ru="Холодильники", slug="muz", order=1)
        brand = Brand.objects.create(name="Artel", slug="artel")
        self.product = Product.objects.create(
            name="Artel HD 455 muzlatgichi", name_ru="Холодильник Artel HD 455", slug="artel-hd",
            category=self.cat, brand=brand, price=100, stock=5,
            description="Artel muzlatgichi rasmiy kafolat bilan.", description_ru="С официальной гарантией.",
        )
        ProductSpec.objects.create(product=self.product, name="Rangi", value="Oq", name_ru="Цвет", value_ru="Белый")
        ProductSpec.objects.create(product=self.product, name="Sinf", value="A+", order=1)
        Banner.objects.create(title="Yangi chegirmalar", title_ru="Новые скидки", order=1)

    def get(self, url, lang):
        return self.client.get(url, HTTP_ACCEPT_LANGUAGE=lang).json()

    def test_uzbek_and_russian(self):
        uz, ru = (self.get("/api/products/artel-hd/", lang) for lang in ("uz", "ru"))
        self.assertEqual(uz["name"], "Artel HD 455 muzlatgichi")
        self.assertEqual(ru["name"], "Холодильник Artel HD 455")
        self.assertEqual(uz["specs"][0], {"name": "Rangi", "value": "Oq"})
        self.assertEqual(ru["specs"][0], {"name": "Цвет", "value": "Белый"})
        self.assertEqual(ru["category"]["name"], "Холодильники")
        self.assertEqual(ru["description"], "С официальной гарантией.")
        self.assertEqual(self.get("/api/banners/", "ru")[0]["title"], "Новые скидки")

    def test_russian_falls_back_to_uzbek(self):
        ru = self.get("/api/products/artel-hd/", "ru")
        self.assertEqual(ru["specs"][1], {"name": "Sinf", "value": "A+"})  # ruschasi kiritilmagan

    def test_unknown_language_is_uzbek(self):
        self.assertEqual(self.get("/api/products/artel-hd/", "uz-cyrl")["name"], "Artel HD 455 muzlatgichi")
        self.assertEqual(self.get("/api/products/artel-hd/", "en")["name"], "Artel HD 455 muzlatgichi")

    def test_search_in_latin_cyrillic_and_russian(self):
        for q in ("muzlatgich", "музлатгич", "холодильник"):
            r = self.client.get("/api/products/", {"search": q}).json()
            self.assertEqual(r["count"], 1, q)


class SimilarProductsTests(APITestCase):
    def test_same_category_first_then_parent(self):
        parent = Category.objects.create(name="Gadjetlar", slug="g")
        phones = Category.objects.create(name="Telefonlar", slug="tel", parent=parent)
        watches = Category.objects.create(name="Soatlar", slug="soat", parent=parent)
        tv = Category.objects.create(name="TV", slug="tv")
        sam, apple = Brand.objects.create(name="Samsung", slug="s"), Brand.objects.create(name="Apple", slug="a")

        def make(slug, cat, brand, price, **kw):
            return Product.objects.create(name=slug, slug=slug, category=cat, brand=brand, price=price,
                                          stock=kw.pop("stock", 5), **kw)

        current = make("s25", phones, sam, 1000)
        make("iphone", phones, apple, 1100)
        make("a56", phones, sam, 500)
        make("old", phones, sam, 1000, stock=0)          # tugagan — ko'rsatilmaydi
        make("hidden", phones, sam, 1000, is_active=False)
        make("watch", watches, sam, 300)
        make("tv", tv, sam, 1000)                         # boshqa bo'lim — ko'rsatilmaydi

        names = [p["name"] for p in self.client.get("/api/products/s25/similar/").json()]
        # Avval shu kategoriya (shu brend oldin), keyin ota kategoriya
        self.assertEqual(names, ["a56", "iphone", "watch"])
        self.assertNotIn(current.slug, names)
