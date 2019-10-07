# Generated by Django 2.1.4 on 2019-10-01 14:19

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import ozone.core.models.file


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_squashed_0204_auto_20190924_1740'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplateAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='email-template-attachments/')),
                ('filename', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('email_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='core.EmailTemplate')),
            ],
        ),
        migrations.AddField(
            model_name='email',
            name='attachments',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='submissionfile',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=ozone.core.models.file.SubmissionFile.get_storage_directory),
        ),
    ]
