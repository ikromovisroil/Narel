# Do'kon nomi Narel -> Rendershop: ommaviy oferta matnidagi nomni almashtiradi (0011 yozgan boshlang'ich matn ham).
from django.db import migrations

FIELDS = ("offer_text", "offer_text_ru")


def rename(apps, old, new):
    StoreSettings = apps.get_model("orders", "StoreSettings")
    for s in StoreSettings.objects.all():
        changed = [f for f in FIELDS if old in (getattr(s, f) or "")]
        for f in changed:
            setattr(s, f, getattr(s, f).replace(old, new))
        if changed:
            s.save(update_fields=changed)


def forwards(apps, schema_editor):
    rename(apps, "Narel", "Rendershop")


def backwards(apps, schema_editor):
    rename(apps, "Rendershop", "Narel")


class Migration(migrations.Migration):
    dependencies = [("orders", "0018_order_item_name")]
    operations = [migrations.RunPython(forwards, backwards)]
