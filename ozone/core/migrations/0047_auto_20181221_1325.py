# Generated by Django 2.0.5 on 2018-12-21 10:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_auto_20181221_1212'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportingChannel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True)),
                ('description', models.CharField(blank=True, max_length=256)),
            ],
        ),
        migrations.RemoveField(
            model_name='historicalsubmission',
            name='submitted_via',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='submitted_via',
        ),
        migrations.AddField(
            model_name='submissioninfo',
            name='reporting_channel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='info', to='core.ReportingChannel'),
        ),
    ]