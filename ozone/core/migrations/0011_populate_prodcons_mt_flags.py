# Generated by Django 2.1.4 on 2019-11-26 13:31

from django.db import migrations


def populate_prodcons_mt_flags(apps, schema_editor):
    """
    Populates is_eu_member and is_article5 flags for existing ProdCons entries.
    """
    ProdConsMT = apps.get_model('core', 'ProdConsMT')
    PartyHistory = apps.get_model('core', 'PartyHistory')

    for ph in PartyHistory.objects.all():
        ProdConsMT.objects.filter(
            party=ph.party, reporting_period=ph.reporting_period
        ).update(
            is_article5=ph.is_article5, is_eu_member=ph.is_eu_member
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_prodcons_updated_at_data_migration'),
    ]

    operations = [
        migrations.RunPython(populate_prodcons_mt_flags),
    ]
