from collections import defaultdict

from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.db.models import Sum

from ozone.core.models import Baseline
from ozone.core.models import Group
from ozone.core.models import Limit
from ozone.core.models import LimitTypes
from ozone.core.models import ObligationTypes
from ozone.core.models import Party
from ozone.core.models import PartyHistory
from ozone.core.models import ProdCons
from ozone.core.models import Region
from ozone.core.models import Submission
from ozone.core.models.utils import round_decimal_half_up
from ozone.core.api.export_pdf.util import (
    b_l,
    DOUBLE_HEADER_TABLE_STYLES,
    col_widths,
    TableBuilder,
    get_submission_dates,
    format_date,
    format_decimal,
)
from . import render


SUBMISSION_TABLE_CUSTOM_STYLES = (
    ('SPAN', (0, 0), (0, 1)),  # annex/group
    ('SPAN', (1, 0), (4, 0)),  # production
    ('SPAN', (5, 0), (9, 0)),  # consumption
    ('ALIGN', (1, 2), (-1, -1), 'RIGHT'),
)

PRODCONS_SUMMARY_CUSTOM_STYLES = (
    ('SPAN', (0, 0), (0, 1)),  # blank
    ('SPAN', (1, 0), (3, 0)),  # production
    ('SPAN', (4, 0), (7, 0)),  # consumption
    ('ALIGN', (1, 2), (-1, -1), 'RIGHT'),
)


def get_all_groups():
    return Group.objects.all()


def check_skip_group(values):
    return all(
        val is None or val == '-' or val == ""
        for val in values
    )


value_missing = object()
value_not_required = object()


class ValueNormalizer:

    def __init__(self, to_report_groups=[], controlled_groups=[]):
        self.to_report_groups = to_report_groups
        self.controlled_groups = controlled_groups

    def baseline(self, value, group, limit):
        if value is not None:
            return value

        if (
            group not in self.controlled_groups or  # noqa: W504
            group.group_id in ['CII', 'CIII'] or  # noqa: W504
            limit is None
        ):
            return value_not_required

        return value_missing

    def prodcons(self, value, group):
        if value is not None:
            return value

        if group in self.to_report_groups:
            return value_missing

        return value_not_required


class ValueFormatter:

    def __init__(self, round_prodcons=None, round_baseline=None):
        self.round_prodcons = round_prodcons
        self.round_baseline = round_baseline

    def prodcons(self, value):
        if value is value_not_required:
            return '-'

        if value is value_missing:
            return 'N.R.'

        if self.round_baseline is not None:
            value = round_decimal_half_up(value, self.round_prodcons)

        return format_decimal(value)

    def baseline(self, baseline, actual):
        # actual is format.value(production/consumption)
        if baseline is value_missing:
            return 'N.R.'

        if baseline is value_not_required:
            return '-'

        if actual is value_not_required:
            return '-'

        if self.round_baseline is not None:
            baseline = round_decimal_half_up(baseline, self.round_baseline)
        return format_decimal(baseline)

    def limit(self, limit):
        if limit is None:
            return '-'

        return format_decimal(limit)

    def change(self, actual_value, baseline):
        if actual_value in [value_not_required, value_missing]:
            return '-'

        if baseline in [value_not_required, value_missing]:
            return '-'

        if baseline is None:
            return '-'

        if actual_value <= 0:
            # even when baseline was not reported
            return -100

        if baseline == 0:
            return 100

        the_value = actual_value / baseline * 100 - 100
        return format_decimal(round_decimal_half_up(the_value, 2))

    def per_capita(self, cons, population):
        if cons in [None, value_missing, value_not_required]:
            return '-'

        if not population:
            return '-'

        return format_decimal(round_decimal_half_up(cons / population, 4))


def get_date_reported(prodcons_qs):
    # Get the date reported from the Article 7 submission related to ProdCons
    submission_id = None
    for subs in prodcons_qs.values_list('submissions', flat=True):
        id_list = subs.get(ObligationTypes.ART7.value, [])
        if id_list:
            submission_id = id_list[0]
    sub = Submission.objects.filter(id=submission_id).first()
    if sub:
        # There should only be one current submission.
        date_reported, date_revised = get_submission_dates(sub)
        return format_date(date_reported), format_date(date_revised)
    else:
        return "-", None


class ProdConsTable:

    def __init__(self, party, period, history, all_groups):
        self.all_groups = all_groups
        self.party = party
        self.period = period
        self.show_prod = not party.is_eu
        self.show_cons = not history.is_eu_member
        self.is_article5 = history.is_article5
        self.population = history.population

        self.normalize = ValueNormalizer(
            to_report_groups=Group.get_report_groups(party, period),
            controlled_groups=Group.get_controlled_groups(party, period),
        )
        self.format = ValueFormatter()

        prodcons_qs = ProdCons.objects.filter(party=party, reporting_period=period)
        self.date_reported, self.date_revised = get_date_reported(prodcons_qs)
        self.prodcons_data = {row.group: row for row in prodcons_qs}

    def get_limit(self, group, limit_type):
        limit = Limit.objects.filter(
            party=self.party,
            reporting_period=self.period,
            group=group,
            limit_type=limit_type,
        ).first()
        return limit.limit if limit else None

    def get_baseline(self, group, baseline_type):
        row = Baseline.objects.filter(
            party=self.party,
            group=group,
            baseline_type__name=baseline_type,
        ).first()
        return row.baseline if row else None

    def get_table_row(self, group):
        main_prodcons = self.prodcons_data.get(group)

        if main_prodcons:
            # Get some pre-calculated values
            limit_prod = main_prodcons.limit_prod
            limit_cons = main_prodcons.limit_cons
            baseline_prod = main_prodcons.baseline_prod
            baseline_cons = main_prodcons.baseline_cons
            calculated_production = main_prodcons.calculated_production
            calculated_consumption = main_prodcons.calculated_consumption

        else:
            limit_prod = self.get_limit(group, LimitTypes.PRODUCTION.value)
            limit_cons = self.get_limit(group, LimitTypes.CONSUMPTION.value)
            baseline_prod = self.get_baseline(group, 'A5Prod' if self.is_article5 else 'NA5Prod')
            baseline_cons = self.get_baseline(group, 'A5Cons' if self.is_article5 else 'NA5Cons')
            calculated_production = None
            calculated_consumption = None

        if self.show_prod:
            prod_value = self.normalize.prodcons(calculated_production, group)
            baseline_prod_value = self.normalize.baseline(baseline_prod, group, limit_prod)
            main_prod = self.format.prodcons(prod_value)
            chng_prod = self.format.change(prod_value, baseline_prod_value)
            baseline_prod = self.format.baseline(baseline_prod_value, prod_value)
            limit_prod = self.format.limit(limit_prod)
        else:
            main_prod = None
            chng_prod = None
            baseline_prod = None
            limit_prod = None

        if self.show_cons:
            cons_value = self.normalize.prodcons(calculated_consumption, group)
            baseline_cons_value = self.normalize.baseline(baseline_cons, group, limit_cons)
            main_cons = self.format.prodcons(cons_value)
            per_capita_cons = self.format.per_capita(cons_value, self.population)
            chng_cons = self.format.change(cons_value, baseline_cons_value)
            baseline_cons = self.format.baseline(baseline_cons_value, cons_value)
            limit_cons = self.format.limit(limit_cons)
        else:
            main_cons = None
            per_capita_cons = None
            chng_cons = None
            baseline_cons = None
            limit_cons = None

        skip_group = check_skip_group([main_prod, baseline_prod, main_cons, baseline_cons])

        row = (
            f'{group.group_id}  - {group.description}',
            main_prod, baseline_prod, chng_prod, limit_prod,
            main_cons, baseline_cons, chng_cons, limit_cons,
            per_capita_cons,
        )

        return (row, skip_group)

    def get_data_rows(self):
        rv = {}

        for group in self.all_groups:
            (row, skip_group) = self.get_table_row(group)

            if not skip_group:
                rv[group.group_id] = row

        return rv


class SubmissionTable(ProdConsTable):

    def __init__(self, submission, history, all_groups):
        self.submission = submission
        party = submission.party
        period = submission.reporting_period
        super().__init__(party, period, history, all_groups)

        # We need to get the actual data from *this* submission
        self.prodcons_data = submission.get_aggregated_data()
        date_reported, date_revised = get_submission_dates(self.submission)
        self.date_reported = format_date(date_reported)
        self.date_revised = format_date(date_revised)


def render_party_history(party, history, date_reported, date_revised):
    vars = {
        'party_name': party.name,
        'date_reported': date_reported,
        'date_revised': date_revised,
        'party_type': history.party_type.abbr,
        'party_region': party.subregion.region.abbr,
        'population': '{:,}'.format(history.population) if history.population else '',
    }
    paragraph = b_l(
        _(
            "{party_name} - Date Received: {date_reported} " +
            ("Date Revised: {date_revised} " if date_revised else "") +
            "{party_type} {party_region} - Population*: {population}"
        ).format(**vars))
    paragraph.keepWithNext = True
    return paragraph


def render_submission_table(period, table):
    ods_caption = _("Production and Consumption of ODSs for {period} (ODP tonnes)")
    hfc_caption = _("Production and Consumption of HFCs for {period} (CO2-equivalent tonnes)")

    styles = list(DOUBLE_HEADER_TABLE_STYLES + SUBMISSION_TABLE_CUSTOM_STYLES)
    column_widths = col_widths([5.5, 1.5, 1.5, 1.2, 1.5, 1.5, 1.5, 1.2, 1.5, 2])
    table_builder = TableBuilder(styles, column_widths)

    table_builder.add_row([
        _('Annex/Group'),
        "{label}**".format(label=_('PRODUCTION')), '', '', '',
        "{label}**".format(label=_('CONSUMPTION')), '', '', '', '',
    ])
    table_builder.add_row([
        '',
        period.name, _('Base'), _('% Chng'), _('Limit'),
        period.name, _('Base'), _('% Chng'), _('Limit'), _('Per Cap. Cons.'),
    ])

    table_builder.add_heading(ods_caption.format(period=period.name))

    table_rows = table.get_data_rows()

    for k, row in table_rows.items():
        if k == 'F':
            continue
        table_builder.add_row(row)

    if 'F' in table_rows:
        row = table_rows['F']
        table_builder.add_heading(hfc_caption.format(period=period.name))
        table_builder.add_row(row)

    return table_builder.done()


def submission_table(party, period, submission, all_groups):
    try:
        history = PartyHistory.objects.get(
            party=party,
            reporting_period=period
        )
    except PartyHistory.DoesNotExist:
        return

    if submission:
        table = SubmissionTable(submission, history, all_groups)
    else:
        table = ProdConsTable(party, period, history, all_groups)

    yield render_party_history(party, history, table.date_reported, table.date_revised)
    yield render_submission_table(period, table)
    yield render.Paragraph('', style=render.h1_style)


class ProdConsSummary:

    def __init__(self, period):
        self.period = period
        self.groups = list(Group.objects.all())
        self.groups_by_pk = {g.pk: g for g in self.groups}
        self.format = ValueFormatter()

    def is_phased_out(self, group):
        return self.period.start_date >= group.phase_out_year_article_5

    def render_groups(self, table_builder, prodcons_groups, population,
                      show_prod=True, show_cons=True):
        for group in self.groups:
            prodcons = prodcons_groups.get(group)
            if not prodcons:
                continue

            (prod, cons, baseline_prod, baseline_cons) = prodcons
            if not (prod or cons) and self.is_phased_out(group):
                continue

            row = [
                f'{group.group_id}  - {group.description}',
            ]

            if show_prod:
                row += [
                    self.format.prodcons(prod),
                    self.format.baseline(baseline_prod, prod),
                    self.format.change(prod, baseline_prod),
                ]
            else:
                row += [None, None, None]

            if show_cons:
                row += [
                    self.format.prodcons(cons),
                    self.format.baseline(baseline_cons, prod),
                    self.format.change(cons, baseline_cons),
                    self.format.per_capita(cons, population),
                ]
            else:
                row += [None, None, None, None]

            table_builder.add_row(row)

    def get_prodcons_groups(self, queryset):
        rv = defaultdict(dict)

        queryset = (
            queryset
            .values('group')
            .annotate(
                Sum('calculated_production'),
                Sum('calculated_consumption'),
                Sum('baseline_prod'),
                Sum('baseline_cons'),
            )
        )

        for row in queryset:
            group = self.groups_by_pk[row['group']]
            rv[group] = (
                row['calculated_production__sum'],
                row['calculated_consumption__sum'],
                row['baseline_prod__sum'],
                row['baseline_cons__sum'],
            )

        return rv

    def get_stats(self, parties):
        stats = (
            PartyHistory.objects
            .filter(reporting_period=self.period)
            .filter(party__in=parties)
            .order_by()
            .aggregate(population=Sum('population'), count=Count('pk'))
        )

        eu = parties.filter(abbr='EU').first()
        if eu:
            eu_history = eu.history.filter(reporting_period=self.period).first()
            stats['population'] -= eu_history.population

        return stats

    def render_heading(self, name, count, population):
        return f"{name} - {count}    (Population: {format_decimal(population)})"

    def render_table(self):
        styles = list(DOUBLE_HEADER_TABLE_STYLES + PRODCONS_SUMMARY_CUSTOM_STYLES)
        column_widths = col_widths([5.5, 2, 2, 2, 2, 2, 2, 2])
        table_builder = TableBuilder(styles, column_widths)

        table_builder.add_row([
            "",
            "{label}**".format(label=_('PRODUCTION')), '', '',
            "{label}**".format(label=_('CONSUMPTION')), '', '', '',
        ])
        table_builder.add_row([
            '',
            self.period.name, _('Base'), _('% Chng'),
            self.period.name, _('Base'), _('% Chng'), _('Per Cap. Cons.'),
        ])

        self.render_data(table_builder)

        return table_builder.done()


class SummaryByRegion(ProdConsSummary):

    def __init__(self, period):
        super().__init__(period)
        self.regions = list(Region.get_real_regions())
        self.regions_by_pk = {r.pk: r for r in self.regions}

    def render_data(self, table_builder):
        # global
        prodcons_groups = self.get_prodcons_groups(
            ProdCons.objects
            .filter(reporting_period=self.period)
        )
        parties = (
            Party.get_main_parties()
            .filter(submissions__reporting_period=self.period)
        )
        stats = self.get_stats(parties)

        heading = self.render_heading("All parties", **stats)
        table_builder.add_heading(heading)

        self.render_groups(table_builder, prodcons_groups, stats['population'])

        # regions
        for region in self.regions:
            prodcons_groups = self.get_prodcons_groups(
                ProdCons.objects
                .filter(reporting_period=self.period)
                .filter(party__subregion__region=region)
            )
            parties = (
                Party.get_main_parties()
                .filter(subregion__region=region)
                .filter(submissions__reporting_period=self.period)
            )
            stats = self.get_stats(parties)

            heading = self.render_heading(region.name, **stats)
            table_builder.add_heading(heading)

            self.render_groups(table_builder, prodcons_groups, stats['population'])


class SummaryByArt5(ProdConsSummary):

    def render_data(self, table_builder):
        # global
        prodcons_groups = self.get_prodcons_groups(
            ProdCons.objects
            .filter(reporting_period=self.period)
        )
        parties = (
            Party.get_main_parties()
            .filter(submissions__reporting_period=self.period)
        )
        stats = self.get_stats(parties)

        heading = self.render_heading("All parties", **stats)
        table_builder.add_heading(heading)

        self.render_groups(table_builder, prodcons_groups, stats['population'])

        # by is_article5
        for is_article5 in [True, False]:
            histories = (
                PartyHistory.objects
                .filter(reporting_period=self.period)
                .filter(is_article5=is_article5)
            )
            parties = (
                Party.get_main_parties()
                .filter(submissions__reporting_period=self.period)
                .filter(history__in=histories)
            )
            prodcons_groups = self.get_prodcons_groups(
                ProdCons.objects
                .filter(reporting_period=self.period)
                .filter(party__in=parties)
            )
            stats = self.get_stats(parties)

            if is_article5:
                heading = self.render_heading("Article 5 parties", **stats)
            else:
                heading = self.render_heading("Non-Article 5 parties", **stats)

            table_builder.add_heading(heading)

            self.render_groups(table_builder, prodcons_groups, stats['population'])


class SummaryParties(ProdConsSummary):

    def __init__(self, period, is_article5):
        super().__init__(period)
        self.is_article5 = is_article5

    def is_phased_out(self, group):
        if self.is_article5:
            phase_out = group.phase_out_year_article_5
        else:
            phase_out = group.phase_out_year_non_article_5

        if not phase_out:
            return False

        return self.period.start_date >= phase_out

    def render_heading(self, party, history, date_reported, date_revised):
        if history.is_article5:
            is_art5_txt = "A5"
        else:
            is_art5_txt = "Non-A5"

        return (
            f"{party.name}  Date Received: {date_reported}" +
            (f" Date Revised: {date_revised}" if date_revised else "") +
            f" - {is_art5_txt}  "
            f"{party.subregion.region.abbr}  "
            f"(Population: {format_decimal(history.population)})"
        )

    def render_data(self, table_builder):
        histories = (
            PartyHistory.objects
            .filter(reporting_period=self.period)
            .filter(is_article5=self.is_article5)
        )
        parties = (
            Party.get_main_parties()
            .filter(submissions__reporting_period=self.period)
            .filter(history__in=histories)
            .distinct()
        )

        history_map = {h.party: h for h in histories}

        for party in parties:
            history = history_map[party]

            prodcons_qs = (
                ProdCons.objects
                .filter(reporting_period=self.period)
                .filter(party=party)
            )

            prodcons_groups = self.get_prodcons_groups(prodcons_qs)
            date_reported, date_revised = get_date_reported(prodcons_qs)

            heading = self.render_heading(party, history, date_reported, date_revised)
            table_builder.add_heading(heading)

            self.render_groups(
                table_builder, prodcons_groups, history.population,
                show_prod=not party.is_eu,
                show_cons=not history.is_eu_member,
            )
