# Generated by Django 2.1.4 on 2019-05-28 11:05

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0138_auto_20190527_1621'),
    ]

    operations = [
        migrations.AddField(
            model_name='prodcons',
            name='submissions',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='prodconsmt',
            name='submissions',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
    ]
