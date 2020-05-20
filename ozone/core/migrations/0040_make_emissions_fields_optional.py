# Generated by Django 2.1.4 on 2020-05-14 10:31

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_party_groups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article7emission',
            name='facility_name',
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AlterField(
            model_name='article7emission',
            name='quantity_emitted',
            field=models.DecimalField(blank=True, decimal_places=15, max_digits=25, null=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
    ]
