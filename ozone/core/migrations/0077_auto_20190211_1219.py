# Generated by Django 2.1.4 on 2019-02-11 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0076_submission_file_delete_cascade'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalsubmission',
            name='exemption_remarks_secretariat',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='exemption_remarks_secretariat',
        ),
        migrations.AddField(
            model_name='historicalsubmission',
            name='exemption_approved_remarks_os',
            field=models.CharField(blank=True, help_text='Exemption approved remarks added by the ozone secretariat', max_length=9999),
        ),
        migrations.AddField(
            model_name='historicalsubmission',
            name='exemptions_nomination_remarks_os',
            field=models.CharField(blank=True, help_text='Exemption nomination remarks added by the ozone secretariat', max_length=9999),
        ),
        migrations.AddField(
            model_name='submission',
            name='exemption_approved_remarks_os',
            field=models.CharField(blank=True, help_text='Exemption approved remarks added by the ozone secretariat', max_length=9999),
        ),
        migrations.AddField(
            model_name='submission',
            name='exemptions_nomination_remarks_os',
            field=models.CharField(blank=True, help_text='Exemption nomination remarks added by the ozone secretariat', max_length=9999),
        ),
    ]
