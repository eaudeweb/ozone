from collections import defaultdict
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from reportlab.platypus import Paragraph, Table, PageBreak

from ozone.core.models import (
    Group,
    ProdCons,
    PartyHistory,
)

from ozone.core.models.utils import round_decimal_half_up

from ..util import (
    TABLE_STYLES_NOBORDER,
    col_widths,
    format_decimal,
    h1_style,
    sm_no_spacing_style,
    left_paragraph_style,
    b_c,
    b_r,
    b_l,
    smb_c,
    smb_r,
    smb_l,
    smi_l,
    sm_r,
    Report,
)


TABLE_CUSTOM_STYLES = (
    ('ALIGN', (1, 3), (-1, -1), 'RIGHT'),
    ('SPAN', (0, 0), (4, 0)),  # Title: Annex III
    ('SPAN', (0, 1), (4, 1)),  # Subtitle
    ('SPAN', (0, 2), (4, 2)),  # Sub-subtitle
    ('SPAN', (1, 4), (2, 4)),  # imports
    ('SPAN', (3, 4), (4, 4)),  # exports
)


TABLE_CUSTOM_KEEPTOGETHER_STYLES = (
    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
    ('KEEPTOGETHER', (0, 0), (-1, -1)),
)


class ImpExpNewRecReport(Report):

    name = "impexp_new_rec"
    has_party_param = True
    has_period_param = True
    display_name = "Import and export of new and recovered substances - by party and annex group"
    description = _("Select one or more parties and one reporting period")

    def get_flowables(self):
        data = get_data(self.periods, self.parties)

        flowables = []
        for period_data in data:
            period = period_data['period']
            parties = period_data['parties']
            flowables.append(get_table(period, parties))
            flowables.append(*get_footer())
            flowables.append(Paragraph('', style=h1_style))
            flowables += [PageBreak()]
        if not data:
            flowables += [Paragraph('No data', left_paragraph_style)]
        return flowables


def get_data(periods, parties):
    data = []
    for period in periods:
        period_data = {
            'period': period.name,
            'parties': []
        }
        for party in parties:
            prodcons_qs = ProdCons.objects.filter(
                party=party,
                reporting_period=period
            )
            period_data['parties'].append(get_party_data(period, party, prodcons_qs))
        data.append(period_data)
    return data


def get_party_data(period, party, prodcons_qs):
    population = party_type = None
    try:
        history = PartyHistory.objects.get(
            party=party,
            reporting_period=period
        )
        population = history.population
        party_type = history.party_type.abbr
    except PartyHistory.DoesNotExist:
        pass

    ods_data = []
    hfc_data = []
    all_groups = Group.objects.all()
    for group in all_groups:
        try:
            prodcons = prodcons_qs.get(group=group)
            # Don't round yet, because very small figures might exist
            # and we want them displayed as 0.000 in the report
            import_new = prodcons.import_new
            import_recovered = prodcons.import_recovered
            export_new = prodcons.export_new
            export_recovered = prodcons.export_recovered
            if any((import_new, import_recovered, export_new, export_recovered)):
                data = ods_data if group.is_odp else hfc_data
                data.append(
                    (
                        group.group_id + ' - ' + group.description,
                        import_new,
                        import_recovered,
                        export_new,
                        export_recovered,
                    )
                )
        except ProdCons.DoesNotExist:
            pass

    return {
        'name': party.name,
        'population': population,
        'party_type': party_type,
        'ods_data': ods_data,
        'hfc_data': hfc_data,
        'ods_subtotal': get_subtotal(ods_data),
    }


def get_subtotal(rows):
    import_new = import_recovered = export_new = export_recovered = Decimal('0.0')
    for row in rows:
        import_new += row[1]
        import_recovered += row[2]
        export_new += row[3]
        export_recovered += row[4]
    return (
        smi_l(_('Subtotal ODS in ODP tonnes')),
        import_new,
        import_recovered,
        export_new,
        export_recovered,
    ) if any((import_new, import_recovered, export_new, export_recovered)) else None


def get_row(data, precision):
    return (
        data[0],
        sm_r(format_decimal(round_decimal_half_up(data[1], precision))),
        sm_r(format_decimal(round_decimal_half_up(data[2], precision))),
        sm_r(format_decimal(round_decimal_half_up(data[3], precision))),
        sm_r(format_decimal(round_decimal_half_up(data[4], precision))),
    )


def get_table(period, parties):
    rows = list()
    rows += get_table_header(period)
    styles = list(TABLE_STYLES_NOBORDER + TABLE_CUSTOM_STYLES)

    for party in parties:
        party_rows = list()
        if party['ods_data'] or party['hfc_data']:
            party_rows.append((
                smb_l(get_party_history(party)),
            ))
        for data in party['ods_data']:
            party_rows.append(get_row(data, 5))
        # append subtotals
        if party['ods_subtotal']:
            party_rows.append(get_row(party['ods_subtotal'], 5))
        for data in party['hfc_data']:
            # We append annex F data after the sub-total
            party_rows.append(get_row(data, 0))

        # Append party data as table to use "keeptogether" feature
        styles_keeptogether = list(TABLE_STYLES_NOBORDER + TABLE_CUSTOM_KEEPTOGETHER_STYLES)
        if party_rows:
            rows.append(
                (
                    Table(
                        party_rows,
                        colWidths=col_widths([8, 2, 3, 2, 3]),
                        style=styles_keeptogether,
                        hAlign='RIGHT'
                    ),
                    '',
                    '',
                    '',
                    ''
                )
            )
            rows.append(('', '', '', '', ''))

    rows += get_totals(parties)

    return Table(
        rows,
        repeatRows=6,
        colWidths=col_widths([8, 2, 3, 2, 3]),
        style=styles,
        hAlign='LEFT'
    )


def get_table_header(period):
    return [
        (
            Paragraph(_('Annex III'), style=h1_style),
            '',
            '',
            '',
            '',
        ),
        (
            b_c(
                _(
                    "{period} import and export of new and recovered substances".format(
                        period=period
                    )
                )
            ),
            '',
            '',
            '',
            '',
        ),
        (
            b_c(
                _("(in ODP tonnes for annexes A,B,C,E and CO2-equivalent tonnes for annex F)")
            ),
            '',
            '',
            '',
            '',
        ),
        (
            '',
            '',
            '',
            '',
            '',
        ),
        (
            '',
            smb_c(_('IMPORTS')),
            '',
            smb_c(_('EXPORTS')),
            '',
        ),
        (
            '',
            smb_r(_('New')),
            smb_r(_('Recovered')),
            smb_r(_('New')),
            smb_r(_('Recovered')),
        ),
    ]


def get_party_history(party):
    return _(
        """{party_name} {party_type} - Population*: {population}""".format(
            party_name=party['name'],
            party_type=party['party_type'],
            population=party['population'],
        )
    )


def get_totals(parties):
    totals = {
        'ods_data': defaultdict(Decimal),
        'hfc_data': defaultdict(Decimal),
    }
    for key in totals:
        for party in parties:
            for row in party[key]:
                totals[key]['import_new'] += row[1]
                totals[key]['import_recovered'] += row[2]
                totals[key]['export_new'] += row[3]
                totals[key]['export_recovered'] += row[4]
                totals[key]['sum'] += sum(row[1:4])

    totals['ods_data']['label'] = 'TOTAL ODS in ODP tonnes'
    totals['hfc_data']['label'] = 'TOTAL HFC in CO2-equivalent tonnes'
    totals['ods_data']['precision'] = 5
    totals['hfc_data']['precision'] = 0

    def to_cell(x, precision):
        return b_r(format_decimal(round_decimal_half_up(x, precision)))

    return [(
        b_l(_(totals[key]['label'])),
        *(
            to_cell(totals[key][x], totals[key]['precision'])
            for x in ('import_new', 'import_recovered', 'export_new', 'export_recovered')
        )
    ) for key in totals if totals[key]['sum']]


def get_footer():
    notes = [
        "* Population in thousands",
    ]

    return [
        Paragraph(_(note), sm_no_spacing_style) for note in notes
    ]
