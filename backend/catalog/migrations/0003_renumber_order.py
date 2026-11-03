from django.db import migrations


def renumber(apps, schema_editor):
    """Mavjud tartib raqamlarini 1, 2, 3... qilib qayta yozish."""
    Category = apps.get_model("catalog", "Category")
    Banner = apps.get_model("catalog", "Banner")

    def apply(qs, name_field):
        for i, obj in enumerate(qs.order_by("order", name_field, "pk"), start=1):
            if obj.order != i:
                obj.order = i
                obj.save(update_fields=["order"])

    for parent_id in set(Category.objects.values_list("parent_id", flat=True)):
        apply(Category.objects.filter(parent_id=parent_id), "name")
    apply(Banner.objects.all(), "title")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0002_sku_label")]
    operations = [migrations.RunPython(renumber, migrations.RunPython.noop)]
