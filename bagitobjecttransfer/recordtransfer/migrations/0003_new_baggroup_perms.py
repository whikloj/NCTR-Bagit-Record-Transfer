
from django.db import migrations, models
from django.contrib.auth.models import Group, Permission


def add_bag_group_permissions(apps, schema_editor):
    group = Group.objects.get(name='archivist_user')
    existing_permissions = group.permissions.all()

    for codename in (
        'add_baggroup',
        'change_baggroup',
        'delete_baggroup',
        'view_baggroup',
    ):
        permission = Permission.objects.get(codename=codename)
        if permission not in existing_permissions:
            group.permissions.add(permission)

    group = Group.objects.get(name='transfer_user')
    existing_permissions = group.permissions.all()
    for codename in (
            'add_baggroup',
            'change_baggroup',
            'view_baggroup'
    ):
        permission = Permission.objects.get(codename=codename)
        if permission not in existing_permissions:
            group.permissions.add(permission)


class Migration(migrations.Migration):
    dependencies = [
        ('recordtransfer', '0002_submission_extent_statement'),
    ]

    operations = [
        migrations.RunPython(add_bag_group_permissions),
    ]
