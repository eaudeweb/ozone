# Generated by Django 2.1.4 on 2019-09-24 14:55

from django.db import migrations, models
import django.db.models.deletion
import ozone.core.models.file


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0201_aggregation_qps_lab_calculations'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplateAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='email-template-attachments/')),
                ('filename', models.CharField(max_length=255)),
                ('email_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.EmailTemplate')),
            ],
        ),
        migrations.AlterField(
            model_name='submissionfile',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=ozone.core.models.file.SubmissionFile.get_storage_directory),
        ),
    ]
