# Generated by Django 2.0.5 on 2018-11-09 09:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20181102_1011'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='cloned_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clones', to='core.Submission'),
        ),
    ]