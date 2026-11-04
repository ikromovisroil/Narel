"""Eski jurnal yozuvlarini o'chirish (cron bilan kuniga bir marta ishga tushirish tavsiya etiladi).

    python manage.py prune_audit            # AUDIT_KEEP_DAYS (sukut: 365) kundan eskilarini
    python manage.py prune_audit --days 90
"""
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from audit.models import AuditLog


class Command(BaseCommand):
    help = "Harakatlar jurnalidan eski yozuvlarni o'chiradi"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=None)

    def handle(self, *args, **opts):
        days = opts["days"] or settings.AUDIT_KEEP_DAYS
        deleted, _ = AuditLog.objects.filter(created_at__lt=timezone.now() - timedelta(days=days)).delete()
        self.stdout.write(f"{days} kundan eski {deleted} ta yozuv o'chirildi")
