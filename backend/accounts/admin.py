from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import User

ROLE_COLOURS = {
    "student": ("#e8f0fd", "#1b4fa0"),
    "parent": ("#f3e8fd", "#6b2fa0"),
    "school_admin": ("#fff6e5", "#8a5a00"),
    "ministry_admin": ("#e8f5ee", "#1d6f42"),
}


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Placement system role", {"fields": ("role", "phone_number")}),
    )
    # Let the role (and email, which must be unique) be set when creating a user.
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("username", "email", "first_name", "last_name", "role",
                                                 "password1", "password2")}),
    )
    list_display = ["username", "full_name", "email", "role_badge", "is_active", "last_login"]
    list_filter = ["role", "is_active", "is_staff", "is_superuser"]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering = ["username"]
    list_per_page = 50

    @admin.display(description="Name", ordering="last_name")
    def full_name(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description="Role", ordering="role")
    def role_badge(self, obj):
        bg, fg = ROLE_COLOURS.get(obj.role, ("#eef2f0", "#374151"))
        return format_html(
            '<span style="background:{};color:{};padding:2px 9px;border-radius:999px;font-weight:600;font-size:11px">{}</span>',
            bg, fg, obj.get_role_display() if obj.role else "—",
        )
