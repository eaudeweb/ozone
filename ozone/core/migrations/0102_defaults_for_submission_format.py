# Generated by Django 2.1.4 on 2019-03-26 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0101_set_language_existing_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='submissionformat',
            name='is_default_party',
            field=models.BooleanField(default=False),
        ),
    ]
