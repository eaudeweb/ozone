# Generated by Django 2.1.4 on 2018-12-21 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0045_add_submitted_at_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article7destruction',
            name='remarks_os',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7destruction',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7emission',
            name='remarks_os',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7emission',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7export',
            name='remarks_os',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7export',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7import',
            name='remarks_os',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7import',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7nonpartytrade',
            name='remarks_os',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7nonpartytrade',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7production',
            name='remarks_os',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7production',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7questionnaire',
            name='remarks_os',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='article7questionnaire',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='highambienttemperatureimport',
            name='remarks_os',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='highambienttemperatureimport',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='highambienttemperatureproduction',
            name='remarks_os',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='highambienttemperatureproduction',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='historicalsubmission',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='historicalsubmission',
            name='remarks_secretariat',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='party',
            name='remark',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='processagentapplication',
            name='remark',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='processagentcontaintechnology',
            name='contain_technology',
            field=models.CharField(max_length=9999),
        ),
        migrations.AlterField(
            model_name='processagentemissionlimit',
            name='remark',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='submission',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='submission',
            name='remarks_secretariat',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='transfer',
            name='remarks_os',
            field=models.CharField(blank=True, max_length=9999),
        ),
        migrations.AlterField(
            model_name='transfer',
            name='remarks_party',
            field=models.CharField(blank=True, max_length=9999),
        ),
    ]
