# Generated by Django 2.1.4 on 2019-05-10 08:31

from django.db import migrations, models
import django.db.models.deletion
import ozone.core.models.file


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0119_auto_20190507_1516'),
    ]

    operations = [
        migrations.CreateModel(
            name='MDGRegion',
            fields=[
                ('code', models.CharField(max_length=32, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256, unique=True)),
                ('income_type', models.CharField(blank=True, choices=[('High', 'ZEOTROPE'), ('Low', 'AZEOTROPE'), ('Lower-middle', 'MeBr'), ('Upper-middle', 'OTHER')], help_text='High, Low, Lower-middle, Upper-middle', max_length=128, null=True)),
                ('remark', models.CharField(blank=True, max_length=256)),
                ('parent_regions', models.ManyToManyField(related_name='child_regions', to='core.MDGRegion')),
            ],
            options={
                'db_table': 'mdg_region',
                'ordering': ('name',),
            },
        ),
        migrations.AddField(
            model_name='party',
            name='abbr_alt',
            field=models.CharField(blank=True, max_length=6),
        ),
        migrations.AddField(
            model_name='party',
            name='iso_alpha3_code',
            field=models.CharField(blank=True, max_length=3),
        ),
        migrations.AddField(
            model_name='party',
            name='name_alt',
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name='party',
            name='mdg_region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='party', to='core.MDGRegion'),
        ),
    ]
