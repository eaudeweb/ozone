# Generated by Django 2.0.5 on 2018-09-26 12:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20180926_0827'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article7questionnaire',
            name='submission',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='article7questionnaire', to='core.Submission'),
        ),
    ]
