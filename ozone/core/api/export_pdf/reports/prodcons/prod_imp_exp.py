from decimal import Decimal
from collections import defaultdict

from reportlab.platypus import PageBreak
from reportlab.platypus import Paragraph
from django.utils.translation import gettext_lazy as _

from ozone.core.models import Group
from ozone.core.models import Obligation
from ozone.core.models import ObligationTypes
from ozone.core.models import PartyHistory
from ozone.core.models import ProdCons
from ozone.core.models import Submission

from ozone.core.api.export_pdf.util import h2_style
from ozone.core.api.export_pdf.util import DOUBLE_HEADER_TABLE_STYLES
from ozone.core.api.export_pdf.util import col_widths
from ozone.core.api.export_pdf.util import TableBuilder
from ozone.core.api.export_pdf.util import get_submission_dates
from ozone.core.api.export_pdf.util import format_date
from ozone.core.api.export_pdf.util import format_decimal
from ozone.core.api.export_pdf.util import Report

from . import data
from . import render


TABLE_CUSTOM_STYLES = (
    ('SPAN', (0, 0), (1, 1)),  # blank
    ('SPAN', (2, 0), (4, 0)),  # production
    ('SPAN', (5, 0), (7, 0)),  # imports
    ('SPAN', (8, 0), (10, 0)),  # exports
    ('ALIGN', (2, 2), (-1, -1), 'RIGHT'),
)


class ProdImpExpTable:

    def __init__(self, period, parties):
        self.period = period

        self.all_groups = list(Group.objects.all())
        self.group_map = {g.group_id: g for g in self.all_groups}
        histories = PartyHistory.objects.filter(reporting_period=period)
        self.history_map = {h.party: h for h in histories}
        self.prodcons_map = self.get_prodcons_map()
        self.parties = parties
        art7 = Obligation.objects.get(_obligation_type=ObligationTypes.ART7.value)
        self.submission_map = Submission.latest_submitted_for_parties(art7, self.period, self.parties)

        self.normalize = data.ValueNormalizer()
        self.builder = self.begin_table()
        self.fields = ['prod', 'imp', 'exp']

    def get_prodcons_map(self):
        rv = defaultdict(defaultdict)

        for row in ProdCons.objects.filter(reporting_period=self.period).iterator():
            if row.group in rv[row.party]:
                raise RuntimeError(f"duplicate wtf: {row.pk} {row}")
            rv[row.party][row.group] = row

        return dict(rv)

    def get_baselines(self, party):
        def averages(group, years):
            rows = list(
                ProdCons.objects
                .filter(party=party)
                .filter(reporting_period__name__in=years)
                .filter(group=group)
            )

            if not rows:
                return {f: None for f in self.fields}

            return {
                'prod': sum(r.calculated_production or d0 for r in rows) / len(rows),
                'imp': sum(r.import_new or d0 for r in rows) / len(rows),
                'exp': sum(r.export_new or d0 for r in rows) / len(rows),
            }

        d0 = Decimal(0)
        g = self.group_map

        history = self.history_map[party]
        if history.is_article5:
            yield g['AI'], averages(g['AI'], ['1995', '1996', '1997'])
            yield g['AII'], averages(g['AII'], ['1995', '1996', '1997'])

            yield g['BI'], averages(g['BI'], ['1998', '1999', '2000'])
            yield g['BII'], averages(g['BII'], ['1998', '1999', '2000'])
            yield g['BIII'], averages(g['BIII'], ['1998', '1999', '2000'])

            ci_baseline = averages(g['CI'], ['2009', '2010'])
            yield g['CI'], ci_baseline

            yield g['EI'], averages(g['EI'], ['1995', '1996', '1997', '1998'])

            if history.is_group2:
                f_years = ['2024', '2025', '2026']
            else:
                f_years = ['2020', '2021', '2022']
            avg_f = averages(g['F'], f_years)
            f_baseline = {
                field: (avg_f[field] or d0) + Decimal('.15') * (ci_baseline[field] or d0)
                for field in self.fields
            }
            yield g['F'], f_baseline

        else:
            yield g['AI'], averages(g['AI'], ['1986'])
            yield g['AII'], averages(g['AI'], ['1986'])

            yield g['BI'], averages(g['BI'], ['1989'])
            yield g['BII'], averages(g['BII'], ['1989'])
            yield g['BIII'], averages(g['BIII'], ['1989'])

            avg_ci = averages(g['CI'], ['1989'])
            avg_ai = averages(g['AI'], ['1989'])
            ci_baseline = {
                field: (avg_ci[field] or d0) + Decimal('.028') * (avg_ai[field] or d0)
                for field in self.fields
            }
            yield g['CI'], ci_baseline

            yield g['EI'], averages(g['EI'], ['1991'])

            avg_f = averages(g['F'], ['2011', '2012', '2013'])
            f_baseline = {
                field: (avg_f[field] or d0) + Decimal('.15') * (ci_baseline[field] or d0)
                for field in self.fields
            }
            yield g['F'], f_baseline

    def begin_table(self):
        styles = list(DOUBLE_HEADER_TABLE_STYLES + TABLE_CUSTOM_STYLES)
        column_widths = col_widths([0.7, 4.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
        builder = TableBuilder(styles, column_widths, repeat_rows=2)
        builder.add_row([
            "", "",
            "PRODUCTION", "", "",
            "IMPORTS", "", "",
            "EXPORTS", "", "",
        ])
        builder.add_row([
            "", "",
            self.period.name, "Base", "% Chng",
            self.period.name, "Base", "% Chng",
            self.period.name, "Base", "% Chng",
        ])
        return builder

    def party_heading(self, party, history, date_reported, date_revised):
        badges = []

        if history.is_article5:
            badges.append("A5")
        else:
            badges.append("Non-A5")

        if history.is_ceit:
            badges.append("CEIT")

        if history.is_eu_member:
            badges.append("EU")

        return (f"{party.name}  (Date received: {date_reported})" +
                (f" Date revised: {date_revised}" if date_revised else "") +
                f" - {' '.join(badges)}  "
                f"(Population: {format_decimal(history.population)})")

    def format_comparison(self, group, party, value, baseline):
        decimals = ProdCons.get_decimals(self.period, group, party)
        format = data.ValueFormatter(
            round_prodcons=decimals,
            round_baseline=decimals,
        )
        return [
            format.prodcons(value),
            format.baseline(baseline, value),
            format.change(value, baseline),
        ]

    def render_party(self, party):
        submission = self.submission_map.get(party)
        if not submission:
            return

        history = self.history_map[party]
        date_reported, date_revised = get_submission_dates(submission)
        heading = self.party_heading(
            party,
            history,
            format_date(date_reported),
            format_date(date_revised),
        )
        self.builder.add_heading(heading)
        baselines_map = dict(self.get_baselines(party))
        _blank_baseline = {f: None for f in self.fields}

        for group in self.all_groups:
            prodcons = self.prodcons_map[party].get(group)
            if not prodcons:
                continue

            values = {
                'prod': prodcons.calculated_production,
                'imp': prodcons.import_new,
                'exp': prodcons.export_new,
            }

            baselines = baselines_map.get(group, _blank_baseline)

            row = [group.name, group.description]
            for name in self.fields:
                row += self.format_comparison(
                    group,
                    party,
                    self.normalize.prodcons(values[name], group),
                    self.normalize.baseline(baselines[name], group, None),
                )

            self.builder.add_row(row)

    def render_parties(self):
        for party in self.parties:
            self.render_party(party)

    def done(self):
        return self.builder.done()


def render_header(period):
    title = (
        f"Production, Import and Export of ODSs - "
        f"Comparison of {period.name} with Base (ODP Tons)"
    )
    return Paragraph(title, style=h2_style)


class ProdImpExpReport(Report):

    name = "prod_imp_exp"
    has_party_param = True
    has_period_param = True

    display_name = "Production, import and export - comparison with base year"
    description = _("Select one or more reporting periods")

    def get_flowables(self):
        all_groups = data.get_all_groups()
        groups_description = list(render.get_groups_description(all_groups))

        for period in self.periods:
            yield render_header(period)
            yield from groups_description

            table = ProdImpExpTable(period, self.parties)
            table.render_parties()
            yield table.done()

            yield PageBreak()
