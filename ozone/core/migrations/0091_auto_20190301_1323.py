# Generated by Django 2.1.4 on 2019-03-01 10:23

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0090_auto_20190301_1252'),
    ]

    operations = [
        migrations.AddField(
            model_name='exemptionapproved',
            name='approved_teap_amount',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AddField(
            model_name='exemptionapproved',
            name='essen_crit_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='core.EssentialCriticalType'),
        ),
    ]
