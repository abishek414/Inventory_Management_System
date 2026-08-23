from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Reuses Django's battle-tested UserAdmin, just pointed at our model."""

    fieldsets = DjangoUserAdmin.fieldsets
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
