# Generated by Django 2.0.5 on 2018-12-04 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_remove_reportingperiod_is_year'),
    ]

    operations = [
        migrations.RenameField(
            model_name='partyratification',
            old_name='date',
            new_name='ratification_date',
        ),
        migrations.AddField(
            model_name='partyratification',
            name='entry_into_force_date',
            field=models.DateField(),
        ),
    ]
