# Generated by Django 3.0.3 on 2020-02-24 21:00

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('mockup', '0002_auto_20200224_1445'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='User',
            new_name='AppUser',
        ),
    ]
