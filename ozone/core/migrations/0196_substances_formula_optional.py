# Generated by Django 2.1.4 on 2019-09-19 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0195_auto_20190917_1651'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='article7export',
            options={'ordering': ['substance__sort_order', 'substance__substance_id', 'blend__sort_order', 'destination_party__name']},
        ),
        migrations.AlterModelOptions(
            name='article7import',
            options={'ordering': ['substance__sort_order', 'substance__substance_id', 'blend__sort_order', 'source_party__name']},
        ),
        migrations.AlterField(
            model_name='substance',
            name='formula',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
