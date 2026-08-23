from django.db import migrations


def grant_full_permissions_to_owner_roles(apps, schema_editor):
    """
    Backfills every existing organization's Owner role so "Borrow" and
    "Delete items" are switched on, matching what a brand-new
    organization's Owner already gets automatically (see
    organizations.views.create_organization).

    Those two permissions didn't exist until migration 0003 added them,
    and a migration that adds a field sets it to that field's default
    (False) on every row that already existed — including Owner roles
    created before this point. Normally you'd just go re-check a box on
    the "Edit role" screen to fix that, but the Owner role is deliberately
    blocked from being edited at all (it's meant to always have full
    access, by design), so there was no way to fix this from inside the
    app itself. This migration is that fix, one time, for every
    organization that already existed.
    """
    Role = apps.get_model('organizations', 'Role')
    Role.objects.filter(is_owner_role=True).update(
        can_borrow_items=True, can_delete_items=True,
    )


def noop_reverse(apps, schema_editor):
    # Nothing to undo — leaving an Owner role with full permissions is the
    # correct, safe state, not something a rollback should break.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0003_role_can_borrow_items_role_can_delete_items_and_more'),
    ]

    operations = [
        migrations.RunPython(grant_full_permissions_to_owner_roles, noop_reverse),
    ]
