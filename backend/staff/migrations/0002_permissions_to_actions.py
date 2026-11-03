from django.db import migrations

# Migratsiya paytidagi holat (keyin modeldagi ro'yxat o'zgarsa ham shu qoladi)
SECTION_ACTIONS = {
    "dashboard": ["view"], "orders": ["view", "change"], "products": ["view", "add", "change", "delete"],
    "categories": ["view", "add", "change", "delete"], "brands": ["view", "add", "change", "delete"],
    "banners": ["view", "add", "change", "delete"], "customers": ["view"],
    "staff": ["view", "add", "change", "delete"], "settings": ["view", "change"],
}


def forwards(apps, schema_editor):
    """Eski format {"products": "edit"} -> yangi {"products": ["view", "add", "change", "delete"]}."""
    StaffProfile = apps.get_model("staff", "StaffProfile")
    for profile in StaffProfile.objects.all():
        new = {}
        for code, value in (profile.permissions or {}).items():
            if code not in SECTION_ACTIONS:
                continue
            if value == "view":
                new[code] = ["view"]
            elif value == "edit":
                new[code] = list(SECTION_ACTIONS[code])
            elif isinstance(value, list):
                new[code] = value
        profile.permissions = new
        profile.save(update_fields=["permissions"])


class Migration(migrations.Migration):
    dependencies = [("staff", "0001_initial")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
