# Generated by Django 2.1.4 on 2019-08-08 16:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0175_auto_20190808_1447'),
    ]

    operations = [
        migrations.CreateModel(
            name='IllegalTrade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submission_id', models.IntegerField(blank=True, null=True)),
                ('seizure_date_year', models.CharField(blank=True, max_length=256)),
                ('substances_traded', models.CharField(blank=True, max_length=256)),
                ('volume', models.CharField(blank=True, max_length=256)),
                ('importing_exporting_country', models.CharField(blank=True, max_length=256)),
                ('illegal_trade_details', models.CharField(blank=True, max_length=9999)),
                ('action_taken', models.CharField(blank=True, max_length=9999)),
                ('remarks', models.CharField(blank=True, max_length=9999)),
                ('ordering_id', models.IntegerField(default=0)),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='illegal_trades', to='core.Party')),
            ],
            options={
                'db_table': 'illegal_trade',
            },
        ),
        migrations.CreateModel(
            name='MultilateralFund',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('funds_approved', models.IntegerField()),
                ('funds_disbursed', models.IntegerField()),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='multilateral_funds', to='core.Party')),
            ],
            options={
                'db_table': 'multilateral_fund',
            },
        ),
        migrations.CreateModel(
            name='ORMReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meeting', models.CharField(blank=True, max_length=64)),
                ('description', models.CharField(blank=True, max_length=9999)),
                ('url', models.URLField(blank=True, max_length=1024, null=True, verbose_name='URL')),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orm_reports', to='core.Party')),
                ('reporting_period', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orm_reports', to='core.ReportingPeriod')),
            ],
            options={
                'verbose_name': 'ORM reports',
                'db_table': 'orm_report',
            },
        ),
    ]
