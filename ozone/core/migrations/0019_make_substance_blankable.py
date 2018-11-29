# Generated by Django 2.0.5 on 2018-11-27 08:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20181126_1123'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blendcomponent',
            name='substance',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='blends', to='core.Substance'),
        ),
    ]