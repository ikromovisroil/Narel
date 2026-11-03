"""Demo ma'lumotlar: python manage.py seed"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Banner, Brand, Category, Product, ProductSpec

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


def uslug(text):
    return slugify(text.replace("'", "").replace('"', "")) or "item"


class Command(BaseCommand):
    help = "Demo kategoriyalar, brendlar, mahsulotlar va bannerlarni qo'shadi"

    def handle(self, *args, **opts):
        cats = {}
        for i, (parent_name, children) in enumerate(CATEGORIES.items()):
            parent, _ = Category.objects.get_or_create(
                slug=uslug(parent_name), defaults={"name": parent_name, "order": i}
            )
            for j, child in enumerate(children):
                cats[child], _ = Category.objects.get_or_create(
                    slug=uslug(child), defaults={"name": child, "parent": parent, "order": j}
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
            Banner.objects.get_or_create(title=title, defaults={"subtitle": subtitle, "order": i})

        self.stdout.write(self.style.SUCCESS(f"Tayyor: {created} ta yangi mahsulot qo'shildi."))
