# Generated by Django 2.1.4 on 2019-09-17 09:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0193_auto_20190917_1219'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='licensingsystemfile',
            table='licensing_system_file',
        ),
        migrations.AlterModelTable(
            name='licensingsystemurl',
            table='licensing_system_url',
        ),
    ]
