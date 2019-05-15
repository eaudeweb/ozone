# Generated by Django 2.1.4 on 2019-05-14 13:46

from django.db import migrations, models
import ozone.core.models.file


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0125_mt_aggregations'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='description_alt',
            field=models.CharField(blank=True, max_length=1024, null=True, verbose_name='Alternate description'),
        ),
        migrations.AddField(
            model_name='group',
            name='name_alt',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Alternate name'),
        ),
        migrations.RemoveField(
            model_name='group',
            name='exemption',
        ),
    ]
