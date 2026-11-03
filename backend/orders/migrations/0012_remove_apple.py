from django.db import migrations

REPLACE = [
    ("offer_text", " Saytga Google yoki Apple hisobi orqali ham kirish mumkin.", " Saytga Google hisobi orqali ham kirish mumkin."),
    ("offer_text_ru", " Войти также можно через аккаунт Google или Apple.", " Войти также можно через аккаунт Google."),
]


def drop_apple_from_offer(apps, schema_editor):
    StoreSettings = apps.get_model("orders", "StoreSettings")
    for store in StoreSettings.objects.all():
        changed = []
        for field, old, new in REPLACE:
            value = getattr(store, field)
            if old in value:
                setattr(store, field, value.replace(old, new))
                changed.append(field)
        if changed:
            store.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [("orders", "0011_default_offer")]
    operations = [
        migrations.RemoveField(model_name="customerprofile", name="apple_id"),
        migrations.RunPython(drop_apple_from_offer, migrations.RunPython.noop),
    ]
