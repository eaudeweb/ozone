# Generated by Django 2.1.4 on 2019-03-11 10:45

from django.db import migrations, models
from django.core.management import call_command


def refresh_obligations(apps, schema_editor):
    call_command('loaddata', 'obligations')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0094_auto_20190304_1742'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='obligation',
            name='form_type',
        ),
        migrations.AddField(
            model_name='obligation',
            name='_form_type',
            field=models.CharField(choices=[('art7', 'ART7'), ('essencrit', 'ESSENCRIT'), ('hat', 'HAT'), ('other', 'OTHER'), ('exemption', 'EXEMPTION')], help_text='Used to generate the correct form, based on this obligation.', max_length=64, null=True),
        ),
        migrations.RunPython(refresh_obligations),
    ]