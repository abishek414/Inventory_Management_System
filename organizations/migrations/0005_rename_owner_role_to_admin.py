from django.db import migrations


def rename_owner_role_to_admin(apps, schema_editor):
    """
    Renames every existing organization's built-in role from "Owner" to
    "Admin" — matching what a brand-new organization's built-in role is
    now called (see organizations.views.create_organization). Only
    touches rows that are actually the built-in role (is_owner_role=True)
    and still have their original name — that role could never be renamed
    through the app itself (editing it is blocked entirely), so every one
    of these is guaranteed to still say exactly "Owner" going into this.
    """
    Role = apps.get_model('organizations', 'Role')
    Role.objects.filter(is_owner_role=True, name='Owner').update(name='Admin')


def rename_admin_role_to_owner(apps, schema_editor):
    # Reverse of the above, for completeness — only touches rows this
    # migration itself would have renamed.
    Role = apps.get_model('organizations', 'Role')
    Role.objects.filter(is_owner_role=True, name='Admin').update(name='Owner')


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0004_backfill_owner_permissions'),
    ]

    operations = [
        migrations.RunPython(rename_owner_role_to_admin, rename_admin_role_to_owner),
    ]
