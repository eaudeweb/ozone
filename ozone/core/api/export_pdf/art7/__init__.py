from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from reportlab.platypus import PageBreak
from reportlab.platypus import Paragraph

from ozone.core.models import Blend
from ozone.core.models import Group
from ozone.core.models import Obligation
from ozone.core.models import ObligationTypes
from ozone.core.models import ReportingPeriod
from ozone.core.models import Submission
from ozone.core.models import Substance

from .section_info import export_info, export_info_diff
from .section_impexp import export_imports, export_imports_diff
from .section_impexp import export_exports, export_exports_diff
from .section_production import export_production, export_production_diff
from .section_destruction import export_destruction, export_destruction_diff
from .section_nonparty import export_nonparty, export_nonparty_diff
from .section_emission import export_emission
from .section_labuses import export_labuses
from .labuse_report import export_labuse_report

from ..util import exclude_blend_items
from ..util import filter_lab_uses
from ..util import Report
from ..util import ReportForSubmission
from ..util import get_submissions
from ..util import left_paragraph_style

__all__ = [
    'export_labuse_report',
]


def export_submissions(submissions):
    for submission in submissions:

        yield from export_info(submission)

        yield from export_imports(
            submission,
            exclude_blend_items(submission.article7imports),
        )

        yield from export_exports(
            submission,
            exclude_blend_items(submission.article7exports),
        )

        yield from export_production(
            submission,
            submission.article7productions.all(),
        )

        yield from export_destruction(
            submission,
            exclude_blend_items(submission.article7destructions),
        )

        yield from export_nonparty(
            submission,
            exclude_blend_items(submission.article7nonpartytrades),
        )

        yield from export_emission(
            submission,
            submission.article7emissions.all(),
        )

        # For lab uses, consumption is actually data from imports
        # Apparently there aren't any lab uses in exports (?)
        yield from export_labuses(
            filter_lab_uses(exclude_blend_items(submission.article7imports)),
            filter_lab_uses(submission.article7productions),
        )

        yield PageBreak()


class Art7RawdataReport(ReportForSubmission):

    name = "art7_raw"
    has_party_param = True
    has_period_param = True
    display_name = "Raw data reported - Article 7"
    description = _("Select one or more parties and one or more reporting periods")
    landscape = True

    def get_flowables(self):
        if self.submission:
            submissions = [self.submission]
        else:
            art7 = Obligation.objects.get(
                _obligation_type=ObligationTypes.ART7.value
            )
            submissions = get_submissions(art7, self.periods, self.parties)

        if not submissions:
            yield Paragraph('No data', left_paragraph_style)
        else:
            yield from export_submissions(submissions)


def export_submission_diff(submission):
    previous_submission = submission.get_previous_version()
    if previous_submission is None:
        yield Paragraph(
            'No previous submission to compare to', left_paragraph_style
        )
    else:
        yield from export_info_diff(submission, previous_submission)

        yield from export_imports_diff(
            submission,
            previous_submission,
            exclude_blend_items(submission.article7imports),
            exclude_blend_items(previous_submission.article7imports),
        )

        yield from export_exports_diff(
            submission,
            previous_submission,
            exclude_blend_items(submission.article7exports),
            exclude_blend_items(previous_submission.article7exports),
        )

        yield from export_production_diff(
            submission,
            previous_submission,
            submission.article7productions.all(),
            previous_submission.article7productions.all()
        )

        yield from export_destruction_diff(
            submission,
            previous_submission,
            exclude_blend_items(submission.article7destructions),
            exclude_blend_items(previous_submission.article7destructions)
        )

        yield from export_nonparty_diff(
            submission,
            previous_submission,
            exclude_blend_items(submission.article7nonpartytrades),
            exclude_blend_items(previous_submission.article7nonpartytrades),
        )

        """
        yield from export_emission_diff(
            submission,
            submission.article7emissions.all(),
        )

        # For lab uses, consumption is actually data from imports
        # Apparently there aren't any lab uses in exports (?)
        yield from export_labuses_diff(
            filter_lab_uses(exclude_blend_items(submission.article7imports)),
            filter_lab_uses(submission.article7productions),
        )
        """

        yield PageBreak()


class Art7RawdataDiffReport(ReportForSubmission):
    name = "art7_raw"
    has_party_param = True
    has_period_param = True
    display_name = "Raw data reported - diff from previous version - Article 7"
    landscape = True

    def get_flowables(self):
        if not self.submission:
            yield Paragraph('No data', left_paragraph_style)
        else:
            yield from export_submission_diff(self.submission)


class SubstanceFilter:

    def __init__(self, groups):
        self.groups = groups
        self.substances = Substance.objects.filter(group__in=groups)
        self.blends = Blend.objects.filter(components__substance__in=self.substances)

    def filter_substances(self, queryset):
        return queryset.filter(substance__in=self.substances)

    def filter_substances_blends(self, queryset):
        return queryset.filter(Q(blend__in=self.blends) | Q(substance__in=self.substances))


def baseline_hfc_raw_page(submission, substance_filter):
    yield from export_info(submission)

    yield from export_imports(
        submission,
        substance_filter.filter_substances_blends(
            exclude_blend_items(
                submission.article7imports
            )
        ),
    )

    yield from export_exports(
        submission,
        substance_filter.filter_substances_blends(
            exclude_blend_items(
                submission.article7exports
            )
        ),
    )

    yield from export_production(
        submission,
        substance_filter.filter_substances(
            submission.article7productions
        ),
    )

    yield from export_destruction(
        submission,
        substance_filter.filter_substances_blends(
            exclude_blend_items(
                submission.article7destructions
            )
        ),
    )

    yield PageBreak()


def export_baseline_hfc_raw(parties):
    reporting_periods = {
        _period.name: _period
        for _period in ReportingPeriod.objects.all()
    }
    current_period = ReportingPeriod.get_current_period()
    art7 = Obligation.objects.get(_obligation_type=ObligationTypes.ART7.value)

    group_f_filter = SubstanceFilter(Group.objects.filter(group_id='F'))
    group_ai_ci_filter = SubstanceFilter(Group.objects.filter(group_id__in=['AI', 'CI']))

    for party in parties:
        current_history = party.history.get(reporting_period=current_period)

        if current_history.is_article5:
            if current_history.is_group2():
                years = [
                    ('2026', group_f_filter),
                    ('2025', group_f_filter),
                    ('2024', group_f_filter),
                    ('2010', group_ai_ci_filter),
                    ('2009', group_ai_ci_filter),
                ]
            else:
                years = [
                    ('2022', group_f_filter),
                    ('2021', group_f_filter),
                    ('2020', group_f_filter),
                    ('2010', group_ai_ci_filter),
                    ('2009', group_ai_ci_filter),
                ]

        else:
            years = [
                ('2013', group_f_filter),
                ('2012', group_f_filter),
                ('2011', group_f_filter),
                ('1989', group_ai_ci_filter),
            ]

        for year, substance_filter in years:
            period = reporting_periods[year]
            submission = Submission.latest_submitted(art7, party, period)

            if submission is not None:
                yield from baseline_hfc_raw_page(submission, substance_filter)


class BaselineHfcRawReport(Report):

    name = "baseline_hfc_raw"
    has_party_param = True
    display_name = "HFC baseline - raw data reported"
    description = _("Select one or more parties")

    def get_flowables(self):
        yield from export_baseline_hfc_raw(self.parties)
