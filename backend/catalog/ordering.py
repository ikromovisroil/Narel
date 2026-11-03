"""Tartib raqamlari: 1, 2, 3... ketma-ket va takrorlanmaydi.

Yozuv N-o'ringa qo'yilsa, shu guruhdagi N va undan keyingilar bittadan suriladi.
Guruh (scope) — bir-biri bilan solishtiriladigan yozuvlar, masalan bitta ota
kategoriyaning bolalari.
"""
from django.db import transaction


def category_scope(model, parent_id):
    return model.objects.filter(parent_id=parent_id)


def renumber(scope_qs, exclude_pk=None):
    """Guruhdagi raqamlarni 1..n qilib zichlaydi (tartibni saqlagan holda)."""
    qs = scope_qs.exclude(pk=exclude_pk) if exclude_pk else scope_qs
    rows = list(qs.select_for_update().order_by("order", "pk").values_list("pk", "order"))
    for i, (pk, order) in enumerate(rows, start=1):
        if order != i:
            scope_qs.model.objects.filter(pk=pk).update(order=i)
    return [pk for pk, _ in rows]


@transaction.atomic
def place(instance, position, scope_qs):
    """instance'ni guruhda `position`-o'ringa qo'yadi (None — oxiriga)."""
    others = renumber(scope_qs, exclude_pk=instance.pk)
    if position is None:
        position = len(others) + 1
    position = max(1, min(int(position), len(others) + 1))
    others.insert(position - 1, instance.pk)
    model = scope_qs.model
    for i, pk in enumerate(others, start=1):
        model.objects.filter(pk=pk).update(order=i)
    instance.order = position
