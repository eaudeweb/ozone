# Generated by Django 2.1.4 on 2020-02-04 08:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20200203_1718'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='licensingsystem',
            name='kigali_licensing_system_reported',
        ),
        migrations.RemoveField(
            model_name='licensingsystem',
            name='kigali_licensing_system_status',
        ),
        migrations.RemoveField(
            model_name='licensingsystem',
            name='kigali_ratification_date',
        ),
    ]
