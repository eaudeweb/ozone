# Generated by Django 2.1.4 on 2019-02-12 07:48

from django.db import migrations, models
import ozone.core.models.file


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0079_auto_20190211_1639'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalsubmission',
            name='questionnaire_remarks_party',
            field=models.CharField(blank=True, help_text='General Article7 obligation remarks added by the reporting party for questionnaire', max_length=9999),
        ),
        migrations.AddField(
            model_name='historicalsubmission',
            name='questionnaire_remarks_secretariat',
            field=models.CharField(blank=True, help_text='General Article7 obligation remarks added by the ozone secretariat for questionnaire', max_length=9999),
        ),
        migrations.AddField(
            model_name='submission',
            name='questionnaire_remarks_party',
            field=models.CharField(blank=True, help_text='General Article7 obligation remarks added by the reporting party for questionnaire', max_length=9999),
        ),
        migrations.AddField(
            model_name='submission',
            name='questionnaire_remarks_secretariat',
            field=models.CharField(blank=True, help_text='General Article7 obligation remarks added by the ozone secretariat for questionnaire', max_length=9999),
        ),
    ]
