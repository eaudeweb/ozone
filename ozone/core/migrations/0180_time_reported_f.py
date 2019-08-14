# Generated by Django 2.1.4 on 2019-08-13 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0179_auto_20190812_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalsubmission',
            name='time_reported_f',
            field=models.DateTimeField(help_text='Date at which substances under Annex F were reported.', null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='time_reported_f',
            field=models.DateTimeField(help_text='Date at which substances under Annex F were reported.', null=True),
        ),
    ]
