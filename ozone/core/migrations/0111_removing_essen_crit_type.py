# Generated by Django 2.1.4 on 2019-04-11 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0110_aggregations_20190411_1205'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='exemptionapproved',
            name='essen_crit_type',
        ),
        migrations.RemoveField(
            model_name='rafreport',
            name='essen_crit_type',
        ),
        migrations.AddField(
            model_name='exemptionapproved',
            name='is_emergency',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='rafreport',
            name='is_emergency',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='substance',
            name='has_critical_uses',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='group',
            name='exemption',
            field=models.CharField(blank=True, choices=[('Critical use', 'CRITICAL'), ('Essential use', 'ESSENTIAL'), ('High ambient', 'HIGH_AMBIENT'), ('Process agent', 'PROCESS_AGENT'), ('Laboratory', 'LABORATORY'), ('Pre 96 Stock', 'PRE_96_STOCK'), ('Other', 'OTHER')], max_length=64),
        ),
        migrations.DeleteModel(
            name='EssentialCriticalType',
        ),
    ]
