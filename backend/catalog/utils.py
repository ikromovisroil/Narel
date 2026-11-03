from django.utils.text import slugify


def make_slug(text):
    for ch in "'\"ʻʼ’‘`":
        text = text.replace(ch, "")
    return slugify(text) or "item"


def unique_slug(model, text, exclude_pk=None, max_length=200):
    base = make_slug(text)[:max_length]
    qs = model.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    slug, n = base, 2
    while qs.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug
