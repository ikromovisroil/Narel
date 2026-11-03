from django.db import migrations

DEFAULTS = [
    # code, nomi, ruscha, izoh, ruscha izoh, faol
    ("cash", "Naqd pul", "Наличные", "Qabul qilganda", "При получении", True),
    ("card", "Karta orqali", "Картой", "Kuryerga Uzcard / Humo", "Курьеру Uzcard / Humo", True),
    ("click", "Click", "Click", "Click ilovasi yoki karta orqali", "Через приложение Click или картой", False),
    ("payme", "Payme", "Payme", "Payme ilovasi yoki karta orqali", "Через приложение Payme или картой", False),
    ("paynet", "Paynet", "Paynet", "Paynet ilovasi yoki shoxobchalarida", "В приложении или пунктах Paynet", False),
    ("uzum", "Uzum Bank", "Uzum Bank", "Uzum Bank ilovasi orqali", "Через приложение Uzum Bank", False),
    ("installment", "Muddatli to'lov", "Рассрочка", "Nasiya orqali bo'lib to'lash", "Оплата частями", False),
]


def create(apps, schema_editor):
    PaymentMethod = apps.get_model("payments", "PaymentMethod")
    for i, (code, title, title_ru, desc, desc_ru, active) in enumerate(DEFAULTS, start=1):
        PaymentMethod.objects.get_or_create(code=code, defaults=dict(
            title=title, title_ru=title_ru, description=desc, description_ru=desc_ru,
            is_active=active, order=i, config={"months": "12"} if code == "installment" else {},
        ))


class Migration(migrations.Migration):
    dependencies = [("payments", "0001_initial")]
    operations = [migrations.RunPython(create, migrations.RunPython.noop)]
