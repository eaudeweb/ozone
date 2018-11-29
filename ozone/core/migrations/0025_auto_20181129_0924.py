# Generated by Django 2.0.5 on 2018-11-29 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_auto_20181128_1715'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partyhistory',
            name='party_type',
            field=models.CharField(blank=True, choices=[('Article 5', 'A5'), ('Article 5 Group 1', 'A5G1'), ('Article 5 Group 2', 'A5G2'), ('Non Article 5', 'NA5'), ('Non Article 5 Group 1', 'NA5G1'), ('Non Article 5 Group 2', 'NA5G2')], max_length=40),
        ),
    ]
