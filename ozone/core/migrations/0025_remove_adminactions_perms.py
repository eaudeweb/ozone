# Generated by Django 2.1.4 on 2020-02-25 09:30

from django.db import migrations


def remove_admin_actions_perms(apps, schema_editor):
    """
    Removes all permissions auto-magically added by django-adminactions to the
    BaselineLimitPermissions model.
    """
    Permission = apps.get_model('auth', 'Permission')
    Permission.objects.filter(
        content_type__model='baselinelimitpermissions',
        codename__startswith='adminactions'
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_baselinelimitpermissions'),
    ]

    operations = [
        migrations.RunPython(remove_admin_actions_perms),
    ]
