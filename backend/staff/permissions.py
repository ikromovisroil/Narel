from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import has_section

# Mavjud yozuvni o'zgartiradigan qo'shimcha amallar (rasm yuklash va h.k.)
CHANGE_ACTIONS = {"upload", "images"}


def required_action(request, view):
    """So'rovga qaysi amal kerakligini aniqlaydi: view / add / change / delete."""
    if request.method in SAFE_METHODS:
        return "view"
    if getattr(view, "write_action", None):
        return view.write_action
    if getattr(view, "action", None) in CHANGE_ACTIONS:
        return "change"  # rasm yuklash/o'chirish — yozuvni tahrirlash
    if request.method == "POST":
        return "add"
    if request.method == "DELETE":
        return getattr(view, "delete_action", "delete")
    return "change"  # PUT / PATCH


class SectionPermission(BasePermission):
    """View'dagi `section` bo'limi uchun kerakli amalga ruxsat borligini tekshiradi."""

    message = "Bu amal uchun ruxsatingiz yo'q."

    def has_permission(self, request, view):
        section = getattr(view, "section", None)
        return bool(section) and has_section(request.user, section, required_action(request, view))


class AnyStaff(BasePermission):
    """Faol xodim (ruxsatidan qat'i nazar) — masalan rasm talablarini o'qish uchun."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_staff and u.is_active)
