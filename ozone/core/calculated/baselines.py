import json
from decimal import Decimal
from functools import lru_cache
import logging

from django.db import transaction
from django.template.response import TemplateResponse
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.utils.translation import gettext_lazy as _

from ozone.core.models import Baseline
from ozone.core.models import BaselineType
from ozone.core.models import Group
from ozone.core.models import Party
from ozone.core.models import PartyHistory
from ozone.core.models import ProdCons
from ozone.core.models import ReportingPeriod
from ozone.core.models import Submission
from ozone.core.models import Transfer
from ozone.core.models.utils import round_decimal_half_up
from ozone.core.models.utils import sum_decimals
from ozone.core.models.utils import decimal_zero_if_none


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CalculationError(Exception):
    pass


class BaselineCalculator:

    def __init__(self):
        self.current_period = ReportingPeriod.get_current_period()
        self.groups = {
            _group.group_id: _group
            for _group in Group.objects.all()
        }
        self.reporting_periods = {
            _period.name: _period
            for _period in ReportingPeriod.objects.all()
        }
        self.parties = {
            _party.abbr: _party
            for _party in Party.get_main_parties()
        }
        self.party_types = {
            entry['party__abbr']: entry['party_type__abbr']
            for entry in PartyHistory.objects.filter(
                reporting_period=self.current_period,
            ).values('party__abbr', 'party_type__abbr')
        }
        self.eu_member_states = [
            _party.abbr
            for _party in Party.get_eu_members()
        ]
        self.eu_member_states_1989 = [
            _party.abbr
            for _party in Party.get_eu_members_at(
                self.reporting_periods['1989']
            )
        ]
        self.baseline_types = {
            _baseline_type.name: _baseline_type
            for _baseline_type in BaselineType.objects.all()
        }

        def _new_eu_member_states_since(period_name):
            eu_members_for_period = Party.get_eu_members_at(
                self.reporting_periods[period_name]
            ).values_list('abbr', flat=True)
            return [
                self.parties[_party]
                for _party in self.eu_member_states
                if _party not in eu_members_for_period
            ]
        self.new_eu_member_states_since = {
            _period: _new_eu_member_states_since(_period)
            for _period in ('1989', '2009', '2010')
        }

    @lru_cache(maxsize=1)
    def _get_prodcons_objects(self, group, party):
        prodcons_objects = {p: None for p in self.reporting_periods}
        for p in ProdCons.objects.filter(group=group, party=party):
            prodcons_objects[p.reporting_period.name] = p
        return prodcons_objects

    def get_baseline(self, baseline_type, group, party):
        func, periods = getattr(
            self, 'baseline_' + baseline_type
        )(group, party)
        return func(party, group, periods) if func else None

    @lru_cache(maxsize=1)
    def _get_prodcons(self, party, group, period_name):
        prodcons_objects = self._get_prodcons_objects(group, party)
        p = prodcons_objects.get(period_name, None)
        if p is None:
            logger.warning("{} has not reported {} for {}".format(
                party.name,
                group.group_id,
                period_name
            ))
        return p

    def _get_bdn_transfer(self, party, group, period_name):
        transfers = Transfer.objects.filter(
            is_basic_domestic_need=True,
            source_party=party,
            reporting_period__name=period_name,
            substance__group=group
        )
        transfer_odp = Decimal(0)
        for tx in transfers:
            transfer_odp += tx.transferred_amount * tx.substance.odp
        return transfer_odp

    def production(self, party, group, periods):
        if len(periods) != 1:
            raise CalculationError(
                f"Production func should have only one period parameter,"
                "got {periods}"
            )
        prodcons = self._get_prodcons(party, group, periods[0])
        if not prodcons:
            return None
        return prodcons.calculated_production \
            if prodcons.calculated_production > 0 else Decimal('0.0')

    def average_production(self, party, group, periods):
        total_prod = Decimal('0.0')
        rounding_digits = 0
        for period in periods:
            prodcons = self._get_prodcons(party, group, period)
            if not prodcons:
                return None
            total_prod += prodcons.calculated_production
            rounding_digits = max(rounding_digits, prodcons.decimals)

        average_prod = round_decimal_half_up(
            total_prod / len(periods),
            rounding_digits
        )
        return average_prod if average_prod > 0 else Decimal('0')

    def average_production_bdn(self, party, group, periods):
        total_prod = Decimal('0.0')
        for period in periods:
            prodcons = self._get_prodcons(party, group, period)
            if not prodcons:
                return None
            total_prod += prodcons.production_article_5
            if total_prod > 0:
                # Special case, e.g. France/AI (no production, only transfers)
                total_prod += self._get_bdn_transfer(party, group, period)

        average_prod = round_decimal_half_up(total_prod / len(periods), 5)
        return average_prod if average_prod > 0 else Decimal('0')

    def consumption(self, party, group, periods):
        if len(periods) != 1:
            raise CalculationError(
                f"Consumption func should have only one period parameter,"
                "got {periods}"
            )
        prodcons = self._get_prodcons(party, group, periods[0])
        if not prodcons:
            return None

        if prodcons.is_eu_member:
            # TODO: re-calculate real consumption
            consumption = round_decimal_half_up(
                prodcons.get_calc_consumption(),
                prodcons.decimals
            )
        else:
            consumption = prodcons.calculated_consumption
        return consumption if consumption > 0 else Decimal('0')

    def average_consumption(self, party, group, periods):
        total_cons = Decimal('0.0')
        rounding_digits = 0
        for period in periods:
            prodcons = self._get_prodcons(party, group, period)
            if not prodcons:
                return None
            if prodcons.is_eu_member:
                total_cons += round_decimal_half_up(
                    prodcons.get_calc_consumption(),
                    prodcons.decimals
                )
            else:
                total_cons += prodcons.calculated_consumption
            if group.group_id in ('AI', 'AII', 'BI', 'BII', 'BIII'):
                # Add ImpRecov and subtract ExpRecov
                total_cons += prodcons.import_recovered - prodcons.export_recovered
            rounding_digits = max(rounding_digits, prodcons.decimals)

        average_cons = round_decimal_half_up(
            total_cons / len(periods),
            rounding_digits
        )
        return average_cons if average_cons > 0 else Decimal('0')

    def production_ci_na5(self, party, _group, _periods):
        """ Average of
            1989 HCFC production + 2.8 per cent of 1989 CFC production
            and
            1989 HCFC consumption + 2.8 per cent of 1989 CFC consumption
        """

        hcfc_group = self.groups.get('CI')
        cfc_group = self.groups.get('AI')
        hcfc_1989 = self._get_prodcons(party, hcfc_group, '1989')
        cfc_1989 = self._get_prodcons(party, cfc_group, '1989')
        if hcfc_1989 and cfc_1989:
            # Note: For EU members, real consumption is included in the formula
            # even if they have NULL calculated_consumption

            average_prod = sum_decimals(
                hcfc_1989.calculated_production,
                decimal_zero_if_none(cfc_1989.calculated_production) * Decimal('0.028'),
                hcfc_1989.get_calc_consumption(),
                cfc_1989.get_calc_consumption() * Decimal('0.028'),
            )
            average_prod = round_decimal_half_up(
                average_prod / 2,
                1  # always 1 decimal for 1989
            )
            return average_prod if average_prod > 0 else Decimal('0')
        return None

    def consumption_ci_na5(self, party, _group, _periods):
        """
            1989 HCFC consumption + 2.8 per cent of 1989 CFC consumption
        """
        hcfc_group = self.groups.get('CI')
        cfc_group = self.groups.get('AI')
        hcfc_1989 = self._get_prodcons(party, hcfc_group, '1989')
        cfc_1989 = self._get_prodcons(party, cfc_group, '1989')
        if hcfc_1989 and cfc_1989:
            if hcfc_1989.is_eu_member:
                # hcfc_1989.calculated_consumption = round_decimal_half_up(
                #     hcfc_1989.get_calc_consumption(),
                #     1  # always 1 decimal for 1989
                # )
                # cfc_1989.calculated_consumption = round_decimal_half_up(
                #     cfc_1989.get_calc_consumption(),
                #     1  # always 1 decimal for 1989
                # )
                # TODO: but is it correct to use unrounded values for EU members
                # and rounded values for non-EU?
                hcfc_1989.calculated_consumption = hcfc_1989.get_calc_consumption()
                cfc_1989.calculated_consumption = cfc_1989.get_calc_consumption()

            # Use already rounded values for calculated consumption
            c1_baseline_cons = round_decimal_half_up(
                sum((
                    hcfc_1989.calculated_consumption,
                    cfc_1989.calculated_consumption * Decimal('0.028'),
                )),
                1,  # always 1 decimal for 1989
            )
            return c1_baseline_cons if c1_baseline_cons > 0 else Decimal('0')
        return None

    def _get_hcfc_percentage(self, party):
        """
            Returns the percentage of the HCFC baseline included in
            the formula for the HFC baseline
            15% for NA5G1
            25% for NA5G2
            65% for A5 (G1 and G2)
        """
        party_type = self.party_types[party.abbr]
        return {
            'NA5G1': Decimal('0.15'),
            'NA5G2': Decimal('0.25'),
            'A5G1': Decimal('0.65'),
            'A5G2': Decimal('0.65'),
        }.get(party_type)

    def production_f_na5(self, party, _group, _periods):
        return self._prod_cons_f(party, _group, _periods, 'PROD', 'NA5')

    def consumption_f_na5(self, party, _group, _periods):
        return self._prod_cons_f(party, _group, _periods, 'CONS', 'NA5')

    def production_f_a5(self, party, _group, _periods):
        return self._prod_cons_f(party, _group, _periods, 'PROD', 'A5')

    def consumption_f_a5(self, party, _group, _periods):
        return self._prod_cons_f(party, _group, _periods, 'CONS', 'A5')

    def _prod_cons_f(self, party, _group, _periods, prod_cons, base_party_type):  # noqa: C901
        """
            HFC baseline actually depends on the party group:

            NA5 Group 1: Average HFC for 2011-2013 + 15% of HCFC baseline
            NA5 Group 2: Average HFC for 2011-2013 + 25% of HCFC baseline
             A5 Group 1: Average HFC for 2020–2022 + 65% of HCFC baseline
             A5 Group 2: Average HFC for 2024–2026 + 65% of HCFC baseline
        """

        party_type = self.party_types.get(party.abbr, None)
        if party_type is None:
            # can happen for Palestine or new states
            logger.warning(f"No party history for {party.abbr}/{self.current_period.name}")
            return None

        if not party_type.startswith(base_party_type):
            return None

        base_periods = {
            'NA5G1': ('2011', '2012', '2013'),
            'NA5G2': ('2011', '2012', '2013'),
            'A5G1': ('2020', '2021', '2022'),
            'A5G2': ('2024', '2025', '2026'),
        }.get(party_type)

        hfc_group = self.groups.get('F')
        total_amount = Decimal('0.0')
        for period in base_periods:
            prodcons = self._get_prodcons(party, hfc_group, period)
            if not prodcons:
                # If data not reported, no baseline is computed
                return None
            if prod_cons == 'PROD':
                total_amount += prodcons.calculated_production
            elif prod_cons == 'CONS':
                # Check EU membership
                if party in Party.get_eu_members_at(
                    self.reporting_periods[period]
                ):
                    return None
                total_amount += (
                    prodcons.calculated_consumption
                    if prodcons.calculated_consumption
                    else Decimal('0')
                )
        if total_amount < 0:
            total_amount = Decimal('0')

        hcfc_group = self.groups.get('CI')
        hcfc_baseline_type = {
            ('PROD', 'NA5G1'): 'NA5ProdGWP',
            ('PROD', 'NA5G2'): 'NA5ProdGWP',
            ('PROD', 'A5G1'): 'A5ProdGWP',
            ('PROD', 'A5G2'): 'A5ProdGWP',
            ('CONS', 'NA5G1'): 'NA5ConsGWP',
            ('CONS', 'NA5G2'): 'NA5ConsGWP',
            ('CONS', 'A5G1'): 'A5ConsGWP',
            ('CONS', 'A5G2'): 'A5ConsGWP',
        }.get(
            (prod_cons, party_type)
        )
        hcfc_baseline = self.get_baseline(hcfc_baseline_type, hcfc_group, party)
        if hcfc_baseline is None:
            return None

        rounded_average = round_decimal_half_up(
            sum((
                total_amount / len(base_periods),
                self._get_hcfc_percentage(party) * hcfc_baseline,
            )),
            0
        )
        return rounded_average if rounded_average > 0 else Decimal('0')

    def baseline_NA5Prod(self, group, party):
        if party.abbr == 'EU':
            # EU doesn't have this baseline
            return None, None

        if group.group_id in ('AI', 'AII'):
            periods = ('1986',)
            func = self.production
        elif group.group_id in ('BI', 'BII', 'BIII'):
            periods = ('1989',)
            func = self.production
        elif group.group_id in ('CI'):
            periods = ('1989',)
            func = self.production_ci_na5
        elif group.group_id in ('CII', 'CIII'):
            periods = None
            func = None
        elif group.group_id in ('EI'):
            periods = ('1991',)
            func = self.production
        elif group.group_id in ('F'):
            periods = None
            func = self.production_f_na5

        return func, periods

    def baseline_NA5Cons(self, group, party):
        # We need this baseline also for EU member states
        #  which weren't EU members in 1986, 1989, etc.
        if group.group_id in ('AI', 'AII'):
            periods = ('1986',)
            func = self.consumption
        elif group.group_id in ('BI', 'BII', 'BIII'):
            periods = ('1989',)
            func = self.consumption
        elif group.group_id in ('CI'):
            periods = ('1989',)
            func = self.consumption_ci_na5
        elif group.group_id in ('CII', 'CIII'):
            periods = None
            func = None
        elif group.group_id in ('EI'):
            periods = ('1991',)
            func = self.consumption
        elif group.group_id in ('F'):
            periods = None
            func = self.consumption_f_na5

        return func, periods

    def baseline_A5Prod(self, group, party):
        if party.abbr == 'EU':
            # EU doesn't have this baseline
            return None, None

        if group.group_id in ('AI', 'AII'):
            periods = ('1995', '1996', '1997')
            func = self.average_production
        elif group.group_id in ('BI', 'BII', 'BIII'):
            periods = ('1998', '1999', '2000')
            func = self.average_production
        elif group.group_id in ('CI'):
            periods = ('2009', '2010')
            func = self.average_production
        elif group.group_id in ('CII', 'CIII'):
            periods = None
            func = None
        elif group.group_id in ('EI'):
            periods = ('1995', '1996', '1997', '1998')
            func = self.average_production
        elif group.group_id in ('F'):
            periods = None
            func = self.production_f_a5

        return func, periods

    def baseline_A5Cons(self, group, party):
        # We need this baseline for EU member states
        #  which weren't EU members in 1986, 1989, etc.
        if group.group_id in ('AI', 'AII'):
            periods = ('1995', '1996', '1997')
            func = self.average_consumption
        elif group.group_id in ('BI', 'BII', 'BIII'):
            periods = ('1998', '1999', '2000')
            func = self.average_consumption
        elif group.group_id in ('CI'):
            periods = ('2009', '2010')
            func = self.average_consumption
        elif group.group_id in ('CII', 'CIII'):
            periods = None
            func = None
        elif group.group_id in ('EI'):
            periods = ('1995', '1996', '1997', '1998')
            func = self.average_consumption
        elif group.group_id in ('F'):
            periods = None
            func = self.consumption_f_a5

        return func, periods

    def baseline_BDN_NA5(self, group, party):
        if party.abbr == 'EU':
            # EU doesn't have this baseline
            return None, None
        if group.group_id in ('AI', 'AII'):
            periods = ('1995', '1996', '1997')
            func = self.average_production_bdn
        elif group.group_id in ('BI'):
            periods = ('1998', '1999', '2000')
            func = self.average_production_bdn
        elif group.group_id in ('BII', 'BIII', 'CI', 'CII', 'CIII', 'F'):
            periods = None
            func = None
        elif group.group_id in ('EI'):
            periods = ('1995', '1996', '1997', '1998')
            func = self.average_production_bdn
        return func, periods

    @lru_cache(maxsize=1)
    def _get_aggregation_from_submission(self, submission_id):
        """
        Helps cache result of expensive call made in _prod_cons_gwp().
        """
        submission = Submission.objects.get(pk=submission_id)
        return submission.get_aggregated_data(
            baseline=True, populate_baselines=False
        )

    def _prod_cons_gwp(self, party, group, period_name, prod_or_cons):
        """
        Normally should be invoked only for groups A/I (CFC) and C/I (HCFC).
        prod_or_cons should be 'PROD' or 'CONS'.
        Note that the result is unrounded because that's necessary
        for consumption_ci_na5_gwp
        """
        prodcons = self._get_prodcons(party, group, period_name)
        if not prodcons:
            return None

        if len(prodcons.submissions.get('art7')) > 1:
            logger.error(
                'Multiple art7 submissions found for {}/{}/{}'.format(
                    party.abbr, group.group_id, period_name
                )
            )
        submission_id = prodcons.submissions.get('art7')[0]
        agg = self._get_aggregation_from_submission(submission_id).get(group)
        if prod_or_cons == 'PROD':
            return agg.calculated_production
        else:
            return agg.get_calc_consumption()

    def consumption_ci_na5_gwp(self, party, _group, _periods):
        """
            The HFC baseline includes a % of the HCFC baseline
            computed in CO2-equivalent tonnes
            The HCFC baseline formula contains in its turn a percentage of
            the CFC production/consumption
        """
        cfc_group = self.groups.get('AI')
        hcfc_group = self.groups.get('CI')
        hcfc_cons = self._prod_cons_gwp(party, hcfc_group, '1989', 'CONS')
        cfc_cons = self._prod_cons_gwp(party, cfc_group, '1989', 'CONS')
        if hcfc_cons is None or cfc_cons is None:
            return None

        if party.abbr == 'EU':
            # Must add consumption of EU member states
            # which were not member states in 1989
            for _ms in self.new_eu_member_states_since['1989']:
                hcfc_cons_ms = self._prod_cons_gwp(_ms, hcfc_group, '1989', 'CONS')
                if hcfc_cons_ms is not None and hcfc_cons_ms > 0:
                    hcfc_cons += hcfc_cons_ms
                cfc_cons_ms = self._prod_cons_gwp(_ms, cfc_group, '1989', 'CONS')
                if cfc_cons_ms is not None and cfc_cons_ms > 0:
                    cfc_cons += cfc_cons_ms
                logger.debug(f"{_ms.abbr} cfc={cfc_cons_ms} hcfc={hcfc_cons_ms}")

        rounded_average = round_decimal_half_up(
            sum((
                round_decimal_half_up(hcfc_cons, 0),
                round_decimal_half_up(cfc_cons, 0) * Decimal('0.028'),
            )),
            0,
        )
        return rounded_average if rounded_average > 0 else Decimal('0')

    def production_ci_na5_gwp(self, party, _group, _periods):
        """
            The HFC baseline includes a % of the HCFC baseline
            computed in CO2-equivalent tonnes
            The HCFC baseline formula contains in its turn a percentage of
            the CFC production/consumption
        """
        cfc_group = self.groups.get('AI')
        hcfc_group = self.groups.get('CI')

        # Note that the consumption of EU member states SHOULD BE included!
        # Also, these should be unrounded values!
        hcfc_prod = self._prod_cons_gwp(party, hcfc_group, '1989', 'PROD')
        cfc_prod = self._prod_cons_gwp(party, cfc_group, '1989', 'PROD')
        hcfc_cons = self._prod_cons_gwp(party, hcfc_group, '1989', 'CONS')
        cfc_cons = self._prod_cons_gwp(party, cfc_group, '1989', 'CONS')

        if any(x is None for x in (hcfc_prod, cfc_prod, hcfc_cons, cfc_cons)):
            return None

        rounded_average = round_decimal_half_up(
            sum((
                round_decimal_half_up(hcfc_prod, 0),
                round_decimal_half_up(cfc_prod, 0) * Decimal('0.028'),
                round_decimal_half_up(hcfc_cons, 0),
                round_decimal_half_up(cfc_cons, 0) * Decimal('0.028'),
            )) / 2,
            0,
        )
        return rounded_average if rounded_average > 0 else Decimal('0')

    def average_production_gwp(self, party, group, periods):
        total_prod = Decimal('0.0')
        for period in periods:
            prod = self._prod_cons_gwp(party, group, period, 'PROD')
            if prod is None:
                # Don't compute if party has not reported for a baseline period
                return None
            total_prod += round_decimal_half_up(prod, 0)

        rounded_average = round_decimal_half_up(
            total_prod / len(periods), 0
        )
        return rounded_average if rounded_average > 0 else Decimal('0')

    def average_consumption_gwp(self, party, group, periods):
        total_cons = Decimal('0.0')
        for period in periods:
            cons = self._prod_cons_gwp(party, group, period, 'CONS')
            if cons is None:
                # Don't compute if party has not reported for a baseline period
                return None
            total_cons += round_decimal_half_up(cons, 0)

            if party.abbr == 'EU':
                # Must add consumption of EU member states
                # which were not member states in 1989
                for _ms in self.new_eu_member_states_since[period]:
                    cons_ms = self._prod_cons_gwp(_ms, group, period, 'CONS')
                    if cons_ms is not None:
                        total_cons += round_decimal_half_up(cons_ms, 0)

        rounded_average = round_decimal_half_up(
            total_cons / len(periods), 0
        )
        return rounded_average if rounded_average > 0 else Decimal('0')

    def baseline_NA5ProdGWP(self, group, party):
        # only for group C/I, which is part of the HFC baseline formula
        if party.abbr == 'EU':
            # EU doesn't have this baseline
            return None, None

        if group.group_id in ('CI'):
            periods = ('1989',)
            func = self.production_ci_na5_gwp
        elif group.group_id in ('F'):
            periods = None
            func = self.production_f_na5
        else:
            periods = None
            func = None
        return func, periods

    def baseline_NA5ConsGWP(self, group, party):
        # only for group C/I, which is part of the HFC baseline formula
        if group.group_id in ('CI',):
            periods = ('1989',)
            func = self.consumption_ci_na5_gwp
        elif group.group_id in ('F'):
            periods = None
            func = self.consumption_f_na5
        else:
            periods = None
            func = None

        return func, periods

    def baseline_A5ProdGWP(self, group, party):
        # only for group C/I, which is part of the HFC baseline formula
        if party.abbr == 'EU':
            # EU doesn't have this baseline
            return None, None

        if group.group_id in ('CI'):
            periods = ('2009', '2010')
            func = self.average_production_gwp
        elif group.group_id in ('F'):
            periods = None
            func = self.production_f_a5
        else:
            periods = None
            func = None
        return func, periods

    def baseline_A5ConsGWP(self, group, party):
        # only for group C/I, which is part of the HFC baseline formula
        if group.group_id in ('CI',):
            periods = ('2009', '2010')
            func = self.average_consumption_gwp
        elif group.group_id in ('F'):
            periods = None
            func = self.consumption_f_a5
        else:
            periods = None
            func = None

        return func, periods


def expected_baselines(parties, groups):
    calculator = BaselineCalculator()
    baseline_types = list(BaselineType.objects.all())

    for party in parties:
        for group in groups:
            for baseline_type in baseline_types:
                baseline = calculator.get_baseline(baseline_type.name, group, party)
                if baseline is None:
                    continue

                yield {
                    'baseline_type': baseline_type,
                    'group': group,
                    'party': party,
                    'baseline': baseline,
                }


def baselines_diff(parties, groups):
    def record_key(record):
        return (
            record['party'].id,
            record['baseline_type'].id,
            record['group'].id,
        )

    def row_key(row):
        return (
            row.party_id,
            row.baseline_type_id,
            row.group_id,
        )

    expected = {
        record_key(record): record
        for record in expected_baselines(
            list(parties),
            list(groups),
        )
    }

    obsolete = []
    different = []

    existing_baselines = (
        Baseline.objects
        .filter(party__in=parties)
        .filter(group__in=groups)
    )
    for row in existing_baselines.iterator():
        key = row_key(row)
        try:
            expected_record = expected.pop(key)
        except KeyError:
            obsolete.append({'row': row})
        else:
            new_value = expected_record['baseline']
            if new_value != row.baseline:
                different.append({'row': row, 'new_value': new_value})

    return {
        'missing': [expected[k] for k in sorted(expected)],
        'different': sorted(different, key=lambda d: row_key(d['row'])),
        'obsolete': sorted(obsolete, key=lambda d: row_key(d['row'])),
    }


def admin_diff(request, context):
    parties = Party.get_main_parties()
    if request.POST['party'] != '*':
        parties = parties.filter(pk=request.POST['party'])

    groups = Group.objects.all()
    if request.POST['group'] != '*':
        groups = groups.filter(pk=request.POST['group'])

    diff = baselines_diff(parties, groups)

    for record in diff['missing']:
        record['checkbox_value'] = json.dumps({
            'party_id': record['party'].id,
            'baseline_type_id': record['baseline_type'].id,
            'group_id': record['group'].id,
            'baseline': str(record['baseline']),
        })

    for record in diff['different']:
        record['checkbox_value'] = json.dumps({
            'pk': record['row'].pk,
            'baseline': str(record['new_value']),
        })

    for record in diff['obsolete']:
        record['checkbox_value'] = json.dumps({
            'pk': record['row'].pk,
        })

    context['diff'] = diff


@transaction.atomic
def admin_apply(request, context):
    created = 0

    for payload in request.POST.getlist('missing'):
        data = json.loads(payload)
        Baseline.objects.create(**data)
        created += 1

    if created:
        messages.success(
            request,
            _("Created %d baselines") % created,
        )

    updated = 0

    for payload in request.POST.getlist('different'):
        data = json.loads(payload)
        row = Baseline.objects.get(pk=data['pk'])
        row.baseline = Decimal(data['baseline'])
        row.save()
        updated += 1

    if updated:
        messages.success(
            request,
            _("Updated %d baselines") % updated,
        )

    removed = 0

    for payload in request.POST.getlist('obsolete'):
        data = json.loads(payload)
        Baseline.objects.get(pk=data['pk']).delete()
        removed += 1

    if removed:
        messages.success(
            request,
            _("Removed %d baselines") % removed,
        )

@permission_required('core.can_run_baselines_tool')
def admin_view(request, context):
    if request.POST:
        step = request.POST['step']
        context['step'] = step

        if step == 'diff':
            admin_diff(request, context)

        elif step == 'apply':
            admin_apply(request, context)

        else:
            raise RuntimeError(f"Unexpected step {step!r}")

    context['parties'] = Party.get_main_parties()
    context['groups'] = Group.objects.all()

    return TemplateResponse(request, 'admin/ozone_tools/generate_baselines.html', context)
