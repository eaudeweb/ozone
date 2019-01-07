# Generated by Django 2.1.4 on 2019-01-07 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0050_submissionfile_uploadtoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalsubmission',
            name='hat_production_remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AddField(
            model_name='historicalsubmission',
            name='hat_production_remarks_secretariat',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AddField(
            model_name='submission',
            name='hat_production_remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AddField(
            model_name='submission',
            name='hat_production_remarks_secretariat',
            field=models.CharField(blank=True, max_length=9999),
        ),
    ]
