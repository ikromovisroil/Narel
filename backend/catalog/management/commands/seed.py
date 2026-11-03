"""Demo ma'lumotlar: python manage.py seed [--orders 40]"""
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from orders.models import Order, OrderItem

from catalog.models import Banner, Brand, Category, Product, ProductSpec
from catalog.utils import make_slug as uslug

CATEGORIES = {
    "Smartfonlar va gadjetlar": ["Smartfonlar", "Planshetlar", "Aqlli soatlar", "Quloqchinlar"],
    "Noutbuklar va kompyuterlar": ["Noutbuklar", "Monitorlar", "Printerlar"],
    "Televizorlar va audio": ["Televizorlar", "Kolonkalar"],
    "Maishiy texnika": ["Muzlatgichlar", "Kir yuvish mashinalari", "Changyutgichlar", "Konditsionerlar"],
    "Oshxona texnikasi": ["Mikroto'lqinli pechlar", "Choynaklar", "Blenderlar"],
}

BRANDS = ["Samsung", "Apple", "Xiaomi", "Artel", "LG", "Lenovo", "HP", "Philips", "Sony", "Huawei"]

# (nomi, kategoriya, brend, narx, eski narx, xit, yangi, xususiyatlar)
PRODUCTS = [
    ("Samsung Galaxy S25 Ultra 12/256GB", "Smartfonlar", "Samsung", 15_990_000, 17_490_000, True, True,
     {"Ekran": "6.9\" Dynamic AMOLED 2X", "Protsessor": "Snapdragon 8 Elite", "Xotira": "12/256 GB", "Kamera": "200 MP", "Batareya": "5000 mAh"}),
    ("Apple iPhone 17 Pro 256GB", "Smartfonlar", "Apple", 18_490_000, None, True, True,
     {"Ekran": "6.3\" Super Retina XDR", "Protsessor": "A19 Pro", "Xotira": "256 GB", "Kamera": "48 MP"}),
    ("Xiaomi Redmi Note 14 Pro 8/256GB", "Smartfonlar", "Xiaomi", 3_990_000, 4_590_000, True, False,
     {"Ekran": "6.67\" AMOLED", "Xotira": "8/256 GB", "Kamera": "200 MP", "Batareya": "5110 mAh"}),
    ("Samsung Galaxy A56 8/256GB", "Smartfonlar", "Samsung", 5_290_000, None, False, True,
     {"Ekran": "6.7\" Super AMOLED", "Xotira": "8/256 GB", "Batareya": "5000 mAh"}),
    ("Apple iPad Air 11\" M3 128GB", "Planshetlar", "Apple", 8_990_000, 9_690_000, False, True,
     {"Ekran": "11\" Liquid Retina", "Protsessor": "Apple M3", "Xotira": "128 GB"}),
    ("Xiaomi Pad 7 8/256GB", "Planshetlar", "Xiaomi", 4_490_000, None, False, False,
     {"Ekran": "11.2\" 144 Hz", "Xotira": "8/256 GB"}),
    ("Apple Watch Series 11 45mm", "Aqlli soatlar", "Apple", 5_490_000, None, False, True,
     {"Korpus": "45 mm alyuminiy", "Suv o'tkazmasligi": "WR50"}),
    ("Samsung Galaxy Watch 8 44mm", "Aqlli soatlar", "Samsung", 3_690_000, 4_190_000, False, False,
     {"Korpus": "44 mm", "Ekran": "Super AMOLED"}),
    ("Apple AirPods Pro 3", "Quloqchinlar", "Apple", 3_290_000, None, True, False,
     {"Turi": "TWS", "Shovqinni bostirish": "Bor (ANC)"}),
    ("Sony WH-1000XM6", "Quloqchinlar", "Sony", 4_990_000, 5_490_000, False, True,
     {"Turi": "Quloq ustki", "Ishlash vaqti": "30 soat"}),
    ("Lenovo IdeaPad Slim 5 i5/16/512", "Noutbuklar", "Lenovo", 8_490_000, 9_290_000, True, False,
     {"Protsessor": "Intel Core i5-13420H", "Operativ xotira": "16 GB", "SSD": "512 GB", "Ekran": "15.3\" IPS"}),
    ("Apple MacBook Air 13\" M4 16/256", "Noutbuklar", "Apple", 14_990_000, None, True, True,
     {"Protsessor": "Apple M4", "Operativ xotira": "16 GB", "SSD": "256 GB", "Ekran": "13.6\" Liquid Retina"}),
    ("HP Victus 15 Ryzen 5/16/512 RTX 4050", "Noutbuklar", "HP", 10_990_000, 11_990_000, False, False,
     {"Protsessor": "AMD Ryzen 5 8645HS", "Videokarta": "RTX 4050 6GB", "Ekran": "15.6\" 144 Hz"}),
    ("Samsung Odyssey G5 27\" QHD", "Monitorlar", "Samsung", 3_590_000, None, False, False,
     {"Diagonal": "27\"", "Ruxsat": "2560x1440", "Chastota": "165 Hz"}),
    ("HP LaserJet M111w", "Printerlar", "HP", 1_790_000, None, False, False,
     {"Turi": "Lazer, oq-qora", "Wi-Fi": "Bor"}),
    ("Samsung 55\" Crystal UHD 4K Smart TV", "Televizorlar", "Samsung", 6_490_000, 7_290_000, True, False,
     {"Diagonal": "55\"", "Ruxsat": "4K UHD", "Smart TV": "Tizen"}),
    ("LG 65\" OLED evo C5", "Televizorlar", "LG", 22_990_000, 25_990_000, False, True,
     {"Diagonal": "65\"", "Matritsa": "OLED", "Chastota": "120 Hz"}),
    ("Artel 43\" Smart TV UA43H3502", "Televizorlar", "Artel", 2_890_000, None, True, False,
     {"Diagonal": "43\"", "Ruxsat": "Full HD", "Smart TV": "Android TV"}),
    ("Sony SRS-XB100 portativ kolonka", "Kolonkalar", "Sony", 790_000, None, False, False,
     {"Ulanish": "Bluetooth 5.3", "Suv o'tkazmasligi": "IP67"}),
    ("Samsung RB38 No Frost muzlatgichi", "Muzlatgichlar", "Samsung", 8_290_000, 8_990_000, True, False,
     {"Hajmi": "385 L", "Tizim": "No Frost", "Energiya sinfi": "A+"}),
    ("Artel HD 455 muzlatgichi", "Muzlatgichlar", "Artel", 4_590_000, None, False, False,
     {"Hajmi": "350 L", "Rangi": "Oq"}),
    ("LG F2V5 8 kg kir yuvish mashinasi", "Kir yuvish mashinalari", "LG", 5_990_000, 6_590_000, True, False,
     {"Yuklash": "8 kg", "Aylanish": "1200 ayl/min", "Inverter motor": "Bor"}),
    ("Artel WF60 6 kg kir yuvish mashinasi", "Kir yuvish mashinalari", "Artel", 2_990_000, None, False, False,
     {"Yuklash": "6 kg", "Aylanish": "1000 ayl/min"}),
    ("Xiaomi Robot Vacuum S20", "Changyutgichlar", "Xiaomi", 2_690_000, 3_190_000, False, True,
     {"Turi": "Robot", "Nam tozalash": "Bor"}),
    ("Philips 3000 Series changyutgichi", "Changyutgichlar", "Philips", 1_290_000, None, False, False,
     {"Quvvati": "900 W", "Turi": "Konteynerli"}),
    ("Artel Inverter 12 konditsioner", "Konditsionerlar", "Artel", 4_290_000, 4_790_000, True, False,
     {"Maydon": "35 m²", "Inverter": "Bor"}),
    ("Samsung MS23 mikroto'lqinli pech", "Mikroto'lqinli pechlar", "Samsung", 1_390_000, None, False, False,
     {"Hajmi": "23 L", "Quvvati": "800 W"}),
    ("Philips HD9350 elektr choynak", "Choynaklar", "Philips", 490_000, 590_000, False, False,
     {"Hajmi": "1.7 L", "Korpus": "Zanglamas po'lat"}),
    ("Philips HR3573 blender", "Blenderlar", "Philips", 1_090_000, None, False, True,
     {"Quvvati": "1000 W", "Idish": "2 L"}),
]

BANNERS = [
    ("Smartfonlarga 20% gacha chegirma", "Faqat shu hafta: eng yangi modellar arzon narxda"),
    ("0% ustama bilan muddatli to'lov", "12 oygacha bo'lib to'lang"),
    ("Maishiy texnika haftaligi", "Muzlatgich va kir yuvish mashinalariga maxsus narxlar"),
]

# ---- Ruscha tarjimalar (bo'sh ruscha maydonlar to'ldiriladi) ----

CATEGORIES_RU = {
    "Smartfonlar va gadjetlar": "Смартфоны и гаджеты", "Smartfonlar": "Смартфоны",
    "Planshetlar": "Планшеты", "Aqlli soatlar": "Умные часы", "Quloqchinlar": "Наушники",
    "Noutbuklar va kompyuterlar": "Ноутбуки и компьютеры", "Noutbuklar": "Ноутбуки",
    "Monitorlar": "Мониторы", "Printerlar": "Принтеры",
    "Televizorlar va audio": "Телевизоры и аудио", "Televizorlar": "Телевизоры", "Kolonkalar": "Колонки",
    "Maishiy texnika": "Бытовая техника", "Muzlatgichlar": "Холодильники",
    "Kir yuvish mashinalari": "Стиральные машины", "Changyutgichlar": "Пылесосы",
    "Konditsionerlar": "Кондиционеры", "Oshxona texnikasi": "Техника для кухни",
    "Mikroto'lqinli pechlar": "Микроволновые печи", "Choynaklar": "Чайники", "Blenderlar": "Блендеры",
}

PRODUCTS_RU = {
    "Sony SRS-XB100 portativ kolonka": "Портативная колонка Sony SRS-XB100",
    "Samsung RB38 No Frost muzlatgichi": "Холодильник Samsung RB38 No Frost",
    "Artel HD 455 muzlatgichi": "Холодильник Artel HD 455",
    "LG F2V5 8 kg kir yuvish mashinasi": "Стиральная машина LG F2V5 8 кг",
    "Artel WF60 6 kg kir yuvish mashinasi": "Стиральная машина Artel WF60 6 кг",
    "Philips 3000 Series changyutgichi": "Пылесос Philips 3000 Series",
    "Artel Inverter 12 konditsioner": "Кондиционер Artel Inverter 12",
    "Samsung MS23 mikroto'lqinli pech": "Микроволновая печь Samsung MS23",
    "Philips HD9350 elektr choynak": "Электрический чайник Philips HD9350",
    "Philips HR3573 blender": "Блендер Philips HR3573",
}

SPEC_NAMES_RU = {
    "Ekran": "Экран", "Protsessor": "Процессор", "Xotira": "Память", "Kamera": "Камера",
    "Batareya": "Аккумулятор", "Korpus": "Корпус", "Suv o'tkazmasligi": "Влагозащита",
    "Turi": "Тип", "Shovqinni bostirish": "Шумоподавление", "Ishlash vaqti": "Время работы",
    "Operativ xotira": "Оперативная память", "Videokarta": "Видеокарта", "Diagonal": "Диагональ",
    "Ruxsat": "Разрешение", "Chastota": "Частота", "Matritsa": "Матрица", "Ulanish": "Подключение",
    "Hajmi": "Объём", "Tizim": "Система", "Energiya sinfi": "Класс энергопотребления",
    "Rangi": "Цвет", "Yuklash": "Загрузка", "Aylanish": "Отжим", "Inverter motor": "Инверторный мотор",
    "Nam tozalash": "Влажная уборка", "Quvvati": "Мощность", "Maydon": "Площадь",
    "Inverter": "Инвертор", "Idish": "Чаша",
}

SPEC_VALUES_RU = {
    "45 mm alyuminiy": "45 мм, алюминий", "44 mm": "44 мм", "Bor (ANC)": "Есть (ANC)",
    "Quloq ustki": "Накладные", "30 soat": "30 часов", "Lazer, oq-qora": "Лазерный, чёрно-белый",
    "Bor": "Есть", "Oq": "Белый", "Robot": "Робот", "Konteynerli": "С контейнером",
    "Zanglamas po'lat": "Нержавеющая сталь", "8 kg": "8 кг", "6 kg": "6 кг",
    "1200 ayl/min": "1200 об/мин", "1000 ayl/min": "1000 об/мин", "35 m²": "35 м²",
    "385 L": "385 л", "350 L": "350 л", "23 L": "23 л", "1.7 L": "1,7 л", "2 L": "2 л",
}

BANNERS_RU = {
    "Smartfonlarga 20% gacha chegirma": ("Скидки до 20% на смартфоны", "Только на этой неделе: новейшие модели по выгодной цене"),
    "0% ustama bilan muddatli to'lov": ("Рассрочка без переплаты", "Оплачивайте частями до 12 месяцев"),
    "Maishiy texnika haftaligi": ("Неделя бытовой техники", "Специальные цены на холодильники и стиральные машины"),
}


def fill_russian():
    """Bo'sh ruscha maydonlarni demo tarjimalar bilan to'ldiradi (qo'lda kiritilganiga tegmaydi)."""
    for cat in Category.objects.filter(name_ru=""):
        if cat.name in CATEGORIES_RU:
            cat.name_ru = CATEGORIES_RU[cat.name]
            cat.save(update_fields=["name_ru"])
    for p in Product.objects.all():
        changed = []
        if not p.name_ru and p.name in PRODUCTS_RU:
            p.name_ru = PRODUCTS_RU[p.name]
            changed.append("name_ru")
        if not p.description_ru and p.description.endswith("bo'ylab."):
            p.description_ru = f"{p.name_ru or p.name} — с официальной гарантией. Доставка по всему Узбекистану."
            changed.append("description_ru")
        if changed:
            p.save(update_fields=changed)
    for spec in ProductSpec.objects.filter(name_ru=""):
        spec.name_ru = SPEC_NAMES_RU.get(spec.name, "")
        spec.value_ru = spec.value_ru or SPEC_VALUES_RU.get(spec.value, "")
        spec.save(update_fields=["name_ru", "value_ru"])
    for b in Banner.objects.filter(title_ru=""):
        if b.title in BANNERS_RU:
            b.title_ru, b.subtitle_ru = BANNERS_RU[b.title]
            b.save(update_fields=["title_ru", "subtitle_ru"])


class Command(BaseCommand):
    help = "Demo kategoriyalar, brendlar, mahsulotlar va bannerlarni qo'shadi"

    def add_arguments(self, parser):
        parser.add_argument(
            "--orders", type=int, default=0,
            help="Oxirgi 30 kun uchun shuncha demo buyurtma qo'shish (dashboard uchun)",
        )

    def handle(self, *args, **opts):
        cats = {}
        for i, (parent_name, children) in enumerate(CATEGORIES.items()):
            parent, _ = Category.objects.get_or_create(
                slug=uslug(parent_name), defaults={"name": parent_name, "order": i + 1}
            )
            for j, child in enumerate(children):
                cats[child], _ = Category.objects.get_or_create(
                    slug=uslug(child), defaults={"name": child, "parent": parent, "order": j + 1}
                )

        brands = {
            name: Brand.objects.get_or_create(slug=uslug(name), defaults={"name": name})[0]
            for name in BRANDS
        }

        created = 0
        for n, (name, cat, brand, price, old, hit, new, specs) in enumerate(PRODUCTS):
            product, is_new = Product.objects.get_or_create(
                slug=uslug(name),
                defaults=dict(
                    name=name, category=cats[cat], brand=brands[brand], price=price,
                    old_price=old, is_hit=hit, is_new=new, stock=10 + n % 7 * 5,
                    sku=f"SKU-{100000 + n}",
                    description=f"{name} — rasmiy kafolat bilan. Yetkazib berish butun O'zbekiston bo'ylab.",
                ),
            )
            if is_new:
                created += 1
                ProductSpec.objects.bulk_create(
                    ProductSpec(product=product, name=k, value=v, order=i)
                    for i, (k, v) in enumerate(specs.items())
                )

        for i, (title, subtitle) in enumerate(BANNERS):
            Banner.objects.get_or_create(title=title, defaults={"subtitle": subtitle, "order": i + 1})

        fill_russian()
        self.stdout.write(self.style.SUCCESS(f"Tayyor: {created} ta yangi mahsulot qo'shildi, ruscha tarjimalar to'ldirildi."))

        if opts["orders"]:
            self.demo_orders(opts["orders"])

    @transaction.atomic
    def demo_orders(self, count):
        names = ["Aziz Karimov", "Dilnoza Rahimova", "Sardor Aliyev", "Malika Yusupova", "Jasur Toshmatov"]
        customers = []
        for i, full in enumerate(names):
            first, last = full.split()
            user, made = User.objects.get_or_create(
                username=f"demo_mijoz{i + 1}", defaults={"first_name": first, "last_name": last}
            )
            if made:
                user.set_unusable_password()  # demo hisoblar bilan kirib bo'lmaydi
                user.save()
            customers.append(user)

        products = list(Product.objects.filter(is_active=True))
        statuses = ["delivered"] * 5 + ["shipped", "confirmed", "new", "new", "cancelled"]
        now = timezone.now()
        for _ in range(count):
            user = random.choice(customers)
            status = random.choice(statuses)
            order = Order.objects.create(
                user=user, full_name=user.get_full_name(), phone=f"+99890{random.randint(1000000, 9999999)}",
                address="Toshkent sh., demo manzil", status=status,
                payment_method=random.choice(["cash", "card", "installment"]),
            )
            # Sanani oxirgi 30 kunga tarqatamiz (auto_now_add'ni chetlab o'tish uchun update)
            created_at = now - timedelta(days=random.randint(0, 29), hours=random.randint(0, 12))
            if status == "new":
                created_at = now - timedelta(hours=random.randint(0, 20))
            total = 0
            for product in random.sample(products, k=random.randint(1, 3)):
                qty = random.randint(1, 2)
                OrderItem.objects.create(order=order, product=product, price=product.price, quantity=qty)
                total += product.price * qty
            Order.objects.filter(pk=order.pk).update(total=total, created_at=created_at)
        self.stdout.write(self.style.SUCCESS(f"{count} ta demo buyurtma qo'shildi."))
