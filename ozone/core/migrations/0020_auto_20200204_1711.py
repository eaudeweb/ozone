# Generated by Django 2.1.4 on 2020-02-04 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_auto_20200204_1514'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImpComBody',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(default=20)),
                ('name', models.CharField(max_length=256)),
            ],
            options={
                'verbose_name': 'IMPCOM Body',
                'verbose_name_plural': 'IMPCOM Bodies',
                'db_table': 'impcom_bodies',
                'ordering': ('sort_order',),
            },
        ),
        migrations.CreateModel(
            name='ImpComTopic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=512)),
            ],
            options={
                'verbose_name': 'IMPCOM Topic',
                'verbose_name_plural': 'IMPCOM Topics',
                'db_table': 'impcom_topics',
                'ordering': ('name',),
            },
        ),
        migrations.AlterModelOptions(
            name='impcomrecommendation',
            options={'ordering': ('-reporting_period',), 'verbose_name': 'IMPCOM Recommendation', 'verbose_name_plural': 'IMPCOM Recommendations'},
        ),
        migrations.AlterModelOptions(
            name='teapindicativenumberofreports',
            options={'ordering': ('-reporting_period',), 'verbose_name_plural': 'TEAP indicative numbers of reports'},
        ),
        migrations.RemoveField(
            model_name='impcomrecommendation',
            name='body',
        ),
        migrations.RemoveField(
            model_name='impcomrecommendation',
            name='topic',
        ),
        migrations.AddField(
            model_name='impcomrecommendation',
            name='bodies',
            field=models.ManyToManyField(to='core.ImpComBody'),
        ),
        migrations.AddField(
            model_name='impcomrecommendation',
            name='topics',
            field=models.ManyToManyField(to='core.ImpComTopic'),
        ),
    ]
