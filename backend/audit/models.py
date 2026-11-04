from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Harakatlar jurnali: kim, qachon, qaysi IP'dan kirdi/chiqdi va nima qildi. Faqat Django admin'da ko'rinadi."""

    class Action(models.TextChoices):
        LOGIN = "login", "Kirdi"
        LOGIN_FAILED = "login_failed", "Kirish xatosi"
        LOGOUT = "logout", "Chiqdi"
        CREATE = "create", "Qo'shdi"
        UPDATE = "update", "O'zgartirdi"
        DELETE = "delete", "O'chirdi"
        ACTION = "action", "Amal"

    created_at = models.DateTimeField("Vaqti", auto_now_add=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="+", verbose_name="Foydalanuvchi")
    # Foydalanuvchi keyin o'chirilsa ham kimligi qolsin
    who = models.CharField("Kim", max_length=200, blank=True)
    is_staff = models.BooleanField("Xodim", default=False)
    action = models.CharField("Harakat", max_length=20, choices=Action.choices, db_index=True)
    section = models.CharField("Bo'lim", max_length=60, blank=True, db_index=True)
    object_id = models.CharField("Yozuv ID", max_length=64, blank=True)
    details = models.TextField("Tafsilot", blank=True)
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField("Manzil", max_length=300, blank=True)
    status_code = models.PositiveSmallIntegerField("Javob kodi", null=True, blank=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True, db_index=True)
    user_agent = models.CharField("Brauzer / qurilma", max_length=300, blank=True)

    class Meta:
        verbose_name = "Harakat"
        verbose_name_plural = "Harakatlar jurnali"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.who or '—'} · {self.get_action_display()}"
