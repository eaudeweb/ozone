from decimal import Decimal

from django.utils.translation import gettext_lazy as _
from reportlab.platypus import PageBreak
from reportlab.platypus import Paragraph

from ozone.core.models import Obligation
from ozone.core.models import ObligationTypes
from ozone.core.models import Submission

from .section_labuses import join_labuse_data
from .. import util


def number_cell(value):
    if value:
        return f"{value.normalize():.10f}"

    return ""


def export_labuse_report(periods, parties):
    table_styles = list(util.SINGLE_HEADER_TABLE_STYLES)
    column_widths = util.col_widths([8, 2, 2, 3, 3])

    art7 = Obligation.objects.get(_obligation_type=ObligationTypes.ART7.value)

    for period in periods:
        title = f"Laboratory and Analytical Uses of ODSs in {period.name} (Tonnes)"
        yield util.Paragraph(title, util.h1_style)

        latest_submissions = Submission.latest_submitted_for_parties(
            art7,
            period,
            parties,
        )

        table = util.TableBuilder(table_styles, column_widths)
        table.add_row([
            "Substance Name",
            "Annex / Group",
            "Production",
            "Imports",
        ])

        for party in parties:
            submission = latest_submissions.get(party)
            if submission is None:
                continue

            imports = list(util.filter_lab_uses(
                util.exclude_blend_items(submission.article7imports)
            ))
            production = list(util.filter_lab_uses(submission.article7productions))
            data = join_labuse_data(imports, production)
            if not data:
                continue

            table.add_heading(party.name)

            prod_total = Decimal('0.0')
            cons_total = Decimal('0.0')
            for item in data.values():
                prod_total += item['production']
                cons_total += item['consumption']
                table.add_row([
                    util.sm_l(item['substance']),
                    util.sm_c(item['group']),
                    util.sm_r(number_cell(item['production'])),
                    util.sm_r(number_cell(item['consumption'])),
                ])

            table.add_row([
                util.smb_l(f"Sub-total for {party.name}"),
                "",
                util.smb_r(number_cell(prod_total)),
                util.smb_r(number_cell(cons_total)),
            ])
            table.add_heading("")

        yield table.done()
        yield PageBreak()


class LabUseReport(util.Report):

    name = 'labuse'
    has_period_param = True
    has_party_param = True
    display_name = "Laboratory and analytical uses"
    description = _(
        "Select one or more parties and one or more reporting periods"
    )

    def get_flowables(self):
        return (
            list(export_labuse_report(self.periods, self.parties)) or
            [Paragraph('No data', util.left_paragraph_style)]
        )
