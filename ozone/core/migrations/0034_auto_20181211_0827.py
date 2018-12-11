# Generated by Django 2.0.5 on 2018-12-11 08:27

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_substance_is_contained_in_polyols'),
    ]

    operations = [
        migrations.AddField(
            model_name='article7emission',
            name='quantity_captured_all_uses',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AddField(
            model_name='article7emission',
            name='quantity_captured_feedstock',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AddField(
            model_name='article7emission',
            name='quantity_captured_for_destruction',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
    ]