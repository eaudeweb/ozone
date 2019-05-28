# Generated by Django 2.1.4 on 2019-05-27 13:03

from django.db import migrations, models
import django.db.models.deletion


def link_parties(apps, schema_editor):
    SubmissionInfo = apps.get_model('core', 'SubmissionInfo')
    Party = apps.get_model('core', 'Party')
    for info in SubmissionInfo.objects.all():
        country = Party.objects.filter(name=info.country).first()
        info.country_fk = country
        info.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0136_nomination_is_emergency'),
    ]

    operations = [
        migrations.AddField(
            model_name='submissioninfo',
            name='country_fk',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='infos', to='core.Party'),
        ),
        migrations.RunPython(link_parties),
    ]
