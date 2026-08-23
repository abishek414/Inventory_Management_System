from django.contrib import admin

from .models import Membership, Organization, Role


class RoleInline(admin.TabularInline):
    model = Role
    extra = 0


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_by', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [RoleInline]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'organization', 'can_view_inventory', 'can_add_stock',
        'can_remove_stock', 'can_borrow_items', 'can_delete_items',
        'can_edit_items', 'can_upload_excel', 'can_manage_users',
    )
    list_filter = ('organization',)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'is_active', 'date_joined')
    list_filter = ('organization', 'is_active')
