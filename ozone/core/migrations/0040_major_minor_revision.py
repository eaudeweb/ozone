# Generated by Django 2.1.4 on 2020-05-19 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_party_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalsubmission',
            name='revision_major',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='historicalsubmission',
            name='revision_minor',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='revision_major',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='revision_minor',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
    ]
