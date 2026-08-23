from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organizations_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or 'org'
            slug = base_slug
            suffix = 1
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix += 1
                slug = f'{base_slug}-{suffix}'
            self.slug = slug
        super().save(*args, **kwargs)


class Role(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)

    can_view_inventory = models.BooleanField(default=True, help_text='See items and stock levels.')
    can_add_stock = models.BooleanField(default=False, help_text='Increase stock quantities.')
    can_remove_stock = models.BooleanField(
        default=False, help_text='Decrease stock quantity — the "Take" action.',
    )
    can_borrow_items = models.BooleanField(
        default=False, help_text='Borrow items marked as borrowable, and mark them returned.',
    )
    can_delete_items = models.BooleanField(
        default=False, help_text='Permanently delete an item from inventory.',
    )
    can_edit_items = models.BooleanField(default=False, help_text='Edit item details and storage location.')
    can_upload_excel = models.BooleanField(default=False, help_text='Bulk-upload inventory via an Excel file.')
    can_manage_users = models.BooleanField(default=False, help_text='Create roles and add/manage members.')

    is_owner_role = models.BooleanField(
        default=False,
        help_text=(
            "The organization's built-in Admin role (shown to users as \"Admin\" — this "
            "field name is historical). Always has every permission and can't be edited "
            "or deleted — this is what guarantees an organization can never end up with "
            "nobody able to manage it. Only set automatically when an organization is "
            "created; there is no way to grant this to a role through the app."
        ),
    )

    PERMISSION_FIELDS = [
        'can_view_inventory', 'can_add_stock', 'can_remove_stock', 'can_borrow_items',
        'can_delete_items', 'can_edit_items', 'can_upload_excel', 'can_manage_users',
    ]

    class Meta:
        unique_together = ('organization', 'name')
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.organization})'

    def save(self, *args, **kwargs):
        if self.is_owner_role:
            for field_name in self.PERMISSION_FIELDS:
                setattr(self, field_name, True)
        super().save(*args, **kwargs)


class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='memberships')
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'organization')
        ordering = ['organization__name']

    def __str__(self):
        return f'{self.user} @ {self.organization} ({self.role.name})'
