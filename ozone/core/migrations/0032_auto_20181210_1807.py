# Generated by Django 2.0.5 on 2018-12-10 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_blend_sort_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blend',
            name='sort_order',
            field=models.IntegerField(default=0, null=True),
        ),
    ]
