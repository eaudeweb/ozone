# Generated by Django 2.1.4 on 2020-02-26 15:24

from django.db import migrations


def populate_decisions(apps, schema_editor):
    ProcessAgentUsesReported = apps.get_model(
        'core', 'ProcessAgentUsesReported'
    )

    for p in ProcessAgentUsesReported.objects.all():
        if p.contain_technologies.all().count() == 0:
            continue
        p.contain_technologies_text = '\n'.join(
            [tech.description for tech in p.contain_technologies.all()]
        )
        p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_processagentusesreported_contain_technologies_text'),
    ]

    operations = [
        migrations.RunPython(populate_decisions),
    ]
