# Generated by Django 2.1.4 on 2020-03-19 14:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0034_country_profile_upload_tos_and_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='othercountryprofiledata',
            unique_together=set(),
        ),
    ]
