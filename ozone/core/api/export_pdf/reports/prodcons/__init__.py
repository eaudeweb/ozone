from django.utils.translation import gettext_lazy as _

from reportlab.platypus import Paragraph

from . import render
from . import data
from ...util import Report
from ...util import ReportForSubmission
from ...util import left_paragraph_style


class ProdConsReport(ReportForSubmission):

    name = "prodcons"
    has_party_param = True
    has_period_param = True
    display_name = "Production and consumption - comparison with base year"
    description = _("Select one or more parties and one or more reporting periods")

    def get_flowables(self):
        all_groups = data.get_all_groups()
        groups_description = list(render.get_groups_description(all_groups))

        for party in self.parties:
            yield from render.get_header(party.name)
            yield from groups_description

            for period in self.periods:
                yield from data.submission_table(party, period, self.submission, all_groups)

            yield from render.get_footer()


class ProdConsByRegionReport(Report):

    name = "prodcons_by_region"
    has_period_param = True
    display_name = "Production and consumption - summary by region"
    description = _("Select one or more reporting periods")

    def get_flowables(self):
        groups_description = list(render.get_groups_description(data.get_all_groups()))

        for period in self.periods:
            yield from render.get_summary_report_header(period, _("Summary by region"))
            yield from groups_description
            yield data.SummaryByRegion(period).render_table()
            yield render.PageBreak()


class ProdConsArt5SummaryReport(Report):

    name = "prodcons_a5_summary"
    has_period_param = True
    display_name = "Production and consumption - summary by Art5 status"
    description = _("Select one or more reporting periods")

    def get_flowables(self):
        groups_description = list(render.get_groups_description(data.get_all_groups()))

        for period in self.periods:
            yield from render.get_summary_report_header(period, _("Summary for All Parties"))
            yield from groups_description
            yield data.SummaryByArt5(period).render_table()
            yield render.PageBreak()


class BaseProdConsPartiesReport(Report):

    has_period_param = True

    def get_flowables(self):
        groups_description = list(render.get_groups_description(data.get_all_groups()))

        for period in self.periods:
            if self.is_article5:
                title = _("Article 5 parties")
            else:
                title = _("Non-Article 5 parties")
            yield from render.get_summary_report_header(period, title)
            yield from groups_description
            yield data.SummaryParties(period, self.is_article5).render_table()
            yield render.PageBreak()
        if not self.periods:
            # This can happen if a future reporting period is selected
            yield Paragraph('No data', left_paragraph_style)


class ProdConsArt5PartiesReport(BaseProdConsPartiesReport):

    name = "prodcons_a5_parties"
    display_name = "Production and consumption - comparison with base year for all Art5 parties"
    description = _("Select one or more reporting periods")
    is_article5 = True


class ProdConsNonArt5PartiesReport(BaseProdConsPartiesReport):

    name = "prodcons_na5_parties"
    display_name = "Production and consumption - comparison with base year for all non-Art5 parties"
    description = _("Select one or more reporting periods")
    is_article5 = False
