# Generated by Django 2.0.5 on 2018-12-20 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_remove_flags_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalsubmission',
            name='submitted_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='submitted_at',
            field=models.DateTimeField(null=True),
        ),
    ]
