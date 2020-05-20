from django.db import migrations


def clear_party_groups(apps, schema_editor):
    User = apps.get_model('core', 'User')
    User.objects.exclude(
        party_group__isnull=True
    ).update(
        party_group=None
    )
    PartyGroup = apps.get_model('core', 'PartyGroup')
    PartyGroup.objects.all().delete()

def create_party_groups(apps, schema_editor):
    clear_party_groups(apps, schema_editor)
    # initial party groups are based on subregions
    groups = {
        'Africa - English Speaking': ['AFE'],
        'Africa - French Speaking': ['AFF'],
        'Africa - all': ['AFE', 'AFF'],
        'East/Central Europe Network': ['ECAN'],
        'Pacific Island Countries': ['PIC'],
        'South Asia': ['ASO'],
        'South-East Asia': ['ASE'],
        'West Asia': ['ASR'],
        'Caribbean': ['LCA'],
        'Latin America - Central': ['LCE'],
        'Latin America - South': ['LCS'],
        'Africa English Speaking | Pacific Islands | West Asia': ['AFE', 'PIC', 'ASR'],
        'South Asia | South-East Asia': ['ASO', 'ASE'],
        'South Asia | South-East Asia | Pacific Islands': ['ASO', 'ASE', 'PIC'],
    }
    PartyGroup = apps.get_model('core', 'PartyGroup')
    Subregion = apps.get_model('core', 'Subregion')
    Party = apps.get_model('core', 'Party')
    for name, subregions in groups.items():
        obj = PartyGroup.objects.create(
            name=name
        )
        for subregion_abbr in subregions:
            parties = Party.objects.filter(
                subregion__abbr=subregion_abbr
            )
            for party in parties:
                obj.parties.add(party)
        obj.save()



class Migration(migrations.Migration):

    dependencies = [
        ('core', '0038_change_users_manager'),
    ]

    operations = [
        migrations.RunPython(create_party_groups, clear_party_groups),
    ]
