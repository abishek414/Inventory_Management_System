from django.db import migrations


def rename_owner_role_to_admin(apps, schema_editor):
    Role = apps.get_model('organizations', 'Role')
    Role.objects.filter(is_owner_role=True, name='Owner').update(name='Admin')


def rename_admin_role_to_owner(apps, schema_editor):
    Role = apps.get_model('organizations', 'Role')
    Role.objects.filter(is_owner_role=True, name='Admin').update(name='Owner')


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0004_backfill_owner_permissions'),
    ]

    operations = [
        migrations.RunPython(rename_owner_role_to_admin, rename_admin_role_to_owner),
    ]
