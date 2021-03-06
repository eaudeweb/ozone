# Generated by Django 2.1.4 on 2020-02-29 06:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_submission_not_mandatory'),
    ]

    operations = [
        migrations.AddField(
            model_name='processagentusesreported',
            name='party',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pa_uses_reported', to='core.Party'),
        ),
        migrations.AddField(
            model_name='processagentusesreported',
            name='reporting_period',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pa_uses_reported', to='core.ReportingPeriod'),
        ),
    ]
