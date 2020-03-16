from collections import defaultdict
from decimal import Decimal

from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from reportlab.platypus import PageBreak
from reportlab.platypus import Paragraph

from ozone.core.models import Article7Import
from ozone.core.models import Article7Export
from ozone.core.models import Group
from ozone.core.models import Obligation
from ozone.core.models import ObligationTypes
from ozone.core.models import Party
from ozone.core.models import PartyHistory
from ozone.core.models import ProdCons
from ozone.core.models import Submission
from ozone.core.models import Substance

from ozone.core.models.utils import round_decimal_half_up
from ..util import h1_style
from ..util import left_paragraph_style
from ..util import centered_paragraph_style
from ..util import sm_r
from ..util import smb_r
from ..util import smb_l
from ..util import nbsp
from ..util import SINGLE_HEADER_TABLE_STYLES
from ..util import DOUBLE_HEADER_TABLE_STYLES
from ..util import col_widths
from ..util import TableBuilder
from ..util import format_decimal
from ..util import bold_centered_paragraph_style
from ..util import Report


class Sums(defaultdict):

    def __init__(self):
        super().__init__(Decimal)

    def add(self, other):
        for key, value in other.items():
            if value is not None:
                self[key] += value


class RecoveredImportExportTable:

    def __init__(self, period):
        self.period = period
        self.get_data()

    def get_data(self):
        main_parties = Party.get_main_parties()
        art7 = Obligation.objects.get(_obligation_type=ObligationTypes.ART7.value)
        self.submissions = Submission.latest_submitted_for_parties(
            art7,
            self.period,
            main_parties,
        )

        self.group_map = {g.pk: g for g in Group.objects.all()}

        import_data = self.aggregates_by_submission_and_substance(Article7Import)
        export_data = self.aggregates_by_submission_and_substance(Article7Export)

        self.impexp_rows = defaultdict(dict)
        for party in main_parties:
            party_imports = import_data.get(party, {})
            party_exports = export_data.get(party, {})
            for substance in set(party_imports) | set(party_exports):
                self.impexp_rows[party][substance] = {
                    'import': party_imports.get(substance),
                    'export': party_exports.get(substance),
                }

    def aggregates_by_submission_and_substance(self, model):
        rv = defaultdict(lambda: defaultdict(Decimal))
        imports_queryset = (
            model.objects
            .filter(submission__in=self.submissions.values())
            .filter(blend_item_id__isnull=True)
            .prefetch_related('substance', 'blend', 'submission', 'submission__party')
        )

        for i in imports_queryset:
            value = i.quantity_total_recovered
            if value:
                substance = i.substance or i.blend
                rv[i.submission.party][substance] += value

        return rv

    def get_parties(self, is_article5):
        histories = (
            PartyHistory.objects
            .filter(reporting_period=self.period)
            .filter(is_article5=is_article5)
        )
        return Party.objects.filter(history__in=histories)

    def begin_table(self):
        styles = list(SINGLE_HEADER_TABLE_STYLES)
        column_widths = col_widths([10, 2, 3, 3])
        builder = TableBuilder(styles, column_widths, repeat_rows=1)

        builder.add_row([
            "Substance Name",
            "Annex / Group",
            "Recovered Import",
            "Recovered Export",
        ])

        return builder

    def format_value(self, value):
        if value is None:
            return ""
        return format_decimal(value)

    def render_sums(self, heading, sums):
        self.builder.add_row([
            smb_l(heading),
            "",
            smb_r(self.format_value(sums.get('import'))),
            smb_r(self.format_value(sums.get('export'))),
        ])
        current_row = self.builder.current_row
        self.builder.styles += [('SPAN', (0, current_row), (1, current_row))]

    def render_party(self, party):
        party_impexp_rows = self.impexp_rows.get(party)
        if not party_impexp_rows:
            return

        self.builder.add_heading(party.name)

        sums = Sums()

        for substance in sorted(party_impexp_rows, key=lambda s: s.sort_order):
            impexp = party_impexp_rows[substance]

            if isinstance(substance, Substance):
                substance_txt = str(substance)
                if substance.group_id:
                    group_txt = self.group_map[substance.group_id].name
                else:
                    group_txt = ""
            else:
                substance_txt = f"{substance} ({substance.composition})"
                group_txt = ""

            self.builder.add_row([
                substance_txt,
                group_txt,
                sm_r(self.format_value(impexp.get('import'))),
                sm_r(self.format_value(impexp.get('export'))),
            ])

            sums.add(impexp)

        self.render_sums(f"{nbsp*4}Sub-total {party.name}", sums)
        self.builder.add_heading("")

        return sums

    def render_parties(self, heading, parties):
        self.builder.add_heading(heading, style=bold_centered_paragraph_style)

        group_sums = Sums()
        for party in parties:
            sums = self.render_party(party)
            if sums:
                group_sums.add(sums)

        self.render_sums(f"Sub-total {heading}", group_sums)
        self.builder.add_heading("")

        return group_sums

    def render(self):
        self.builder = self.begin_table()

        sums = Sums()
        sums.add(self.render_parties("Article 5 parties", self.get_parties(is_article5=True)))
        sums.add(self.render_parties("Non-Article 5 parties", self.get_parties(is_article5=False)))

        self.render_sums(f"Total for {self.period.name}", sums)

        return self.builder.done()


class ImportExportRecoveredSubstancesReport(Report):

    name = "impexp_rec_subst"
    has_period_param = True
    display_name = "Import and export of recovered substances - by party and substance"
    description = _("Select one or more reporting periods")

    def get_flowables(self):
        for period in self.periods:
            yield Paragraph(
                f"Recovered imports and exports in {period.name} (Tonnes)",
                h1_style,
            )
            table = RecoveredImportExportTable(period)
            yield table.render()
            yield PageBreak()

        if not self.periods:
            # This can happen if a future reporting period is selected
            yield Paragraph('No data', left_paragraph_style)


class NewRecoveredImportExportAggregateTable:

    def __init__(self, period):
        self.period = period

    def begin_table(self):
        styles = list(DOUBLE_HEADER_TABLE_STYLES) + [
            ('SPAN', (0, 0), (1, 1)),  # group
            ('SPAN', (2, 0), (3, 0)),  # imports
            ('SPAN', (4, 0), (5, 0)),  # exports
            ('ALIGN', (2, 2), (-1, -1), 'RIGHT'),  # values
        ]
        column_widths = col_widths([1, 7, 2.5, 2.5, 2.5, 2.5])
        builder = TableBuilder(styles, column_widths)

        builder.add_row(["", "", "Imports", "", "Exports", ""])
        builder.add_row(["", "", "New", "Recovered", "New", "Recovered"])

        return builder

    def format_value(self, value):
        return format_decimal(round_decimal_half_up(value))

    def render_aggregation(self, label, histories):
        prodcons_queryset = (
            ProdCons.objects
            .filter(reporting_period=self.period)
            .filter(party__history__in=histories)
            .prefetch_related('party', 'group')
        )
        cols = ['import_new', 'import_recovered', 'export_new', 'export_recovered']
        parties = set()
        group_sum = defaultdict(lambda: defaultdict(Decimal))
        total_sum = defaultdict(Decimal)
        group_parties = defaultdict(set)
        for row in prodcons_queryset:
            data = {c: getattr(row, c) for c in cols}
            if not any(data.values()):
                continue

            parties.add(row.party)
            group_parties[row.group].add(row.party)
            for c in cols:
                group_sum[row.group][c] += data[c]
                total_sum[c] += data[c]

        def party_plural(n):
            if n == 1:
                return f"{n} Party"
            else:
                return f"{n} Parties"

        population = (
            histories
            .filter(party__in=parties)
            .aggregate(population=Sum('population'))
            ['population']
        )
        self.builder.add_heading(f"{label} (Population: {format_decimal(population)})")

        for group in sorted(group_sum.keys(), key=lambda g: g.group_id):
            parties_count = party_plural(len(group_parties[group]))
            row = [group.name, f"{group.description} ({parties_count})"]
            row += [self.format_value(group_sum[group][c]) for c in cols]
            self.builder.add_row(row)

        totals_row = ["Sub-Total", ""]
        totals_row += [smb_r(self.format_value(total_sum[c])) for c in cols]
        self.builder.add_row(totals_row)
        current_row = self.builder.current_row
        self.builder.styles.append(('SPAN', (0, current_row), (1, current_row)))

    def render(self):
        self.builder = self.begin_table()

        histories = PartyHistory.objects.filter(reporting_period=self.period)

        self.render_aggregation("All parties", histories)
        self.render_aggregation("Article 5 parties", histories.filter(is_article5=True))
        self.render_aggregation("Non-Article 5 parties", histories.filter(is_article5=False))

        return self.builder.done()


class ImportExportNewRecoveredAggregateReport(Report):

    name = "impexp_new_rec_agg"
    has_period_param = True
    display_name = "Import and export of new and recovered substances - summary by Art5 status"
    description = _("Select one or more reporting periods")

    def get_flowables(self):
        for period in self.periods:
            yield Paragraph(
                f"{period.name} import and export of new and recovered substances ",
                h1_style,
            )
            yield Paragraph(
                f"(in ODP tonnes for annexes A,B,C,E and CO2-equivalent tonnes for annex F)",
                centered_paragraph_style,
            )
            table = NewRecoveredImportExportAggregateTable(period)
            yield table.render()
            yield PageBreak()

        if not self.periods:
            # This can happen if a future reporting period is selected
            yield Paragraph('No data', left_paragraph_style)
