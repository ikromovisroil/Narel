from django.db import migrations


def create_first_branch(apps, schema_editor):
    """Hozirgi do'kon manzili birinchi filial bo'ladi."""
    Branch = apps.get_model("orders", "Branch")
    StoreSettings = apps.get_model("orders", "StoreSettings")
    if Branch.objects.exists():
        return
    s = StoreSettings.objects.filter(pk=1).first()
    Branch.objects.create(
        name="Asosiy do'kon", name_ru="Главный магазин",
        address=getattr(s, "address", "") or "Toshkent sh.",
        address_ru=getattr(s, "address_ru", "") or "",
        phone=getattr(s, "phone", "") or "+998 71 000 00 00",
        working_hours=getattr(s, "working_hours", "") or "",
        working_hours_ru=getattr(s, "working_hours_ru", "") or "",
        map_url=getattr(s, "map_url", "") or "",
        order=1,
    )


class Migration(migrations.Migration):
    dependencies = [("orders", "0006_branches")]
    operations = [migrations.RunPython(create_first_branch, migrations.RunPython.noop)]
