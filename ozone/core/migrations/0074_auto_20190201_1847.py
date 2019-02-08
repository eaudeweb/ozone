# Generated by Django 2.1.4 on 2019-02-01 15:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0073_auto_20190129_1553'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='nomination',
            options={},
        ),
        migrations.RenameField(
            model_name='exemptionapproved',
            old_name='approved_amount',
            new_name='quantity',
        ),
        migrations.RenameField(
            model_name='nomination',
            old_name='submit_amount',
            new_name='quantity',
        ),
        migrations.RemoveField(
            model_name='exemptionapproved',
            name='approved_teap_amount',
        ),
        migrations.RemoveField(
            model_name='exemptionapproved',
            name='critical_uses_category',
        ),
        migrations.RemoveField(
            model_name='exemptionapproved',
            name='laboratory_analytical_uses_category',
        ),
        migrations.RemoveField(
            model_name='exemptionapproved',
            name='party',
        ),
        migrations.RemoveField(
            model_name='exemptionapproved',
            name='remark',
        ),
        migrations.RemoveField(
            model_name='exemptionapproved',
            name='reporting_period',
        ),
        migrations.RemoveField(
            model_name='exemptionapproved',
            name='uses_type',
        ),
        migrations.RemoveField(
            model_name='exemptionreported',
            name='critical_uses_category',
        ),
        migrations.RemoveField(
            model_name='exemptionreported',
            name='party',
        ),
        migrations.RemoveField(
            model_name='exemptionreported',
            name='reporting_period',
        ),
        migrations.RemoveField(
            model_name='exemptionreported',
            name='uses_type',
        ),
        migrations.RemoveField(
            model_name='nomination',
            name='nomination_id',
        ),
        migrations.RemoveField(
            model_name='nomination',
            name='party',
        ),
        migrations.RemoveField(
            model_name='nomination',
            name='remark',
        ),
        migrations.RemoveField(
            model_name='nomination',
            name='reporting_period',
        ),
        migrations.RemoveField(
            model_name='nomination',
            name='submit_date',
        ),
        migrations.RemoveField(
            model_name='nomination',
            name='uses_type',
        ),
        migrations.AddField(
            model_name='exemptionapproved',
            name='ordering_id',
            field=models.IntegerField(default=0, help_text='This allows the interface to keep the data entries in theiroriginal order, as given by the user.'),
        ),
        migrations.AddField(
            model_name='exemptionapproved',
            name='remarks_os',
            field=models.CharField(blank=True, help_text='Remarks added by the ozone secretariat', max_length=9999),
        ),
        migrations.AddField(
            model_name='exemptionapproved',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='exemptionapproveds', to='core.Submission'),
        ),
        migrations.AddField(
            model_name='historicalsubmission',
            name='exemption_remarks_secretariat',
            field=models.CharField(blank=True, help_text='General Exemption remarks added by the ozone secretariat', max_length=9999),
        ),
        migrations.AddField(
            model_name='nomination',
            name='ordering_id',
            field=models.IntegerField(default=0, help_text='This allows the interface to keep the data entries in theiroriginal order, as given by the user.'),
        ),
        migrations.AddField(
            model_name='nomination',
            name='remarks_os',
            field=models.CharField(blank=True, help_text='Remarks added by the ozone secretariat', max_length=9999),
        ),
        migrations.AddField(
            model_name='nomination',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='nominations', to='core.Submission'),
        ),
        migrations.AddField(
            model_name='submission',
            name='exemption_remarks_secretariat',
            field=models.CharField(blank=True, help_text='General Exemption remarks added by the ozone secretariat', max_length=9999),
        ),
    ]