from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .serializers import normalize_phone

User = get_user_model()


class LoginEmailPhoneBackend(ModelBackend):
    """Kirish: login, email yoki telefon raqami + parol."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or not password:
            return None
        user = self.find_user(username.strip())
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        User().set_password(password)  # vaqt bo'yicha farq bilinmasin
        return None

    @staticmethod
    def find_user(value):
        # Avval aniq login, keyin email, keyin telefon
        user = User.objects.filter(username__iexact=value).first()
        if not user and "@" in value:
            user = User.objects.filter(email__iexact=value).order_by("id").first()
        phone = normalize_phone(value)
        if not user and phone:
            user = User.objects.filter(profile__phone=phone).first()
        return user
