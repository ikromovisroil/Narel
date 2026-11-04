"""Django admin ko'rinishi (Jazzmin). settings.py import qiladi."""
import os

SITE_URL = os.getenv("SITE_URL", "http://localhost:5173").rstrip("/")
ADMIN_PANEL_URL = os.getenv("ADMIN_PANEL_URL", "http://localhost:5174").rstrip("/")

JAZZMIN_SETTINGS = {
    "site_title": "Narel admin",
    "site_header": "Narel",
    "site_brand": "Narel",
    "site_logo": "narel/logo.svg",
    "login_logo": "narel/logo-dark.svg",
    "login_logo_dark": "narel/logo.svg",
    "site_logo_classes": "img-fluid",
    "site_icon": "narel/logo-dark.svg",
    "welcome_sign": "Narel — texnik boshqaruv paneli",
    "copyright": "Narel · Dasturchi: Ikromov.I",
    # Yuqoridagi qidiruv
    "search_model": ["catalog.Product", "orders.Order", "auth.User"],
    "user_avatar": None,

    # Yuqori menyu
    "topmenu_links": [
        {"name": "Bosh sahifa", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Sayt", "url": SITE_URL, "new_window": True},
        {"name": "Admin panel", "url": ADMIN_PANEL_URL, "new_window": True},
        {"name": "API hujjati", "url": "/api/docs/", "new_window": True},
        {"model": "audit.AuditLog"},
    ],
    "usermenu_links": [
        {"name": "Dasturchi: Ikromov.I", "url": "https://t.me/Isroil_0309", "new_window": True, "icon": "fab fa-telegram"},
    ],

    # Yon menyu
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_models": [],
    "order_with_respect_to": [
        "orders", "orders.Order", "orders.Branch", "orders.StoreSettings", "orders.IntegrationSettings",
        "orders.CustomerProfile", "orders.SmsLog", "orders.PhoneCode",
        "catalog", "catalog.Product", "catalog.Category", "catalog.Brand", "catalog.Banner",
        "comments", "payments", "auth", "staff", "audit", "token_blacklist",
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "orders.Order": "fas fa-shopping-cart",
        "orders.Branch": "fas fa-store",
        "orders.StoreSettings": "fas fa-cogs",
        "orders.IntegrationSettings": "fas fa-plug",
        "orders.CustomerProfile": "fas fa-id-card",
        "orders.SmsLog": "fas fa-sms",
        "orders.PhoneCode": "fas fa-key",
        "catalog.Product": "fas fa-box",
        "catalog.Category": "fas fa-sitemap",
        "catalog.Brand": "fas fa-tags",
        "catalog.Banner": "fas fa-image",
        "comments.Comment": "fas fa-comments",
        "payments.PaymentMethod": "fas fa-credit-card",
        "staff.StaffProfile": "fas fa-user-tie",
        "audit.AuditLog": "fas fa-shield-alt",
        "token_blacklist.OutstandingToken": "fas fa-ticket-alt",
        "token_blacklist.BlacklistedToken": "fas fa-ban",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",

    "related_modal_active": True,
    "show_ui_builder": False,
    # Tahrirlash sahifasi: bo'limlar (fieldsets) va bog'liq jadvallar alohida tablarda
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
        "audit.auditlog": "single",
    },
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": True,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "default_theme_mode": "light",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
