from django.db import migrations


def grant_full_permissions_to_owner_roles(apps, schema_editor):
    Role = apps.get_model('organizations', 'Role')
    Role.objects.filter(is_owner_role=True).update(
        can_borrow_items=True, can_delete_items=True,
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0003_role_can_borrow_items_role_can_delete_items_and_more'),
    ]

    operations = [
        migrations.RunPython(grant_full_permissions_to_owner_roles, noop_reverse),
    ]
