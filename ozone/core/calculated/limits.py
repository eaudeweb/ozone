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
from ozone.core.models import ControlMeasure
from ozone.core.models import Group
from ozone.core.models import Limit
from ozone.core.models import LimitTypes
from ozone.core.models import Party
from ozone.core.models import PartyType
from ozone.core.models import PartyHistory
from ozone.core.models import ProdCons
from ozone.core.models import ReportingPeriod
from ozone.core.models.utils import round_decimal_half_up


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CalculationError(Exception):
    pass


class LimitCalculator:

    def __init__(self):
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
        self.party_types = [_pt.name for _pt in PartyType.objects.all()]

        # The number of control measures is relatively low; so to avoid
        # repeatedly querying the DB, we can keep all ControlMeasure objects
        # in a dictionary with:
        # - keys: (group_id, party_type.name, limit_type)
        # - values: lists of ControlMeasure objects, ordered by start_date
        self.control_measures = {
            (_group, _party_type, _limit_type.value): []
            for _group in self.groups.keys()
            for _party_type in self.party_types
            for _limit_type in LimitTypes
        }
        for cm in ControlMeasure.objects.select_related(
            'group', 'party_type', 'baseline_type'
        ).order_by('start_date'):
            key = (cm.group.group_id, cm.party_type.name, cm.limit_type)
            self.control_measures[key].append(cm)

    @lru_cache(maxsize=1)
    def _party_in_eu(self, party, period):
        return party in Party.get_eu_members_at(period)

    @lru_cache(maxsize=1)
    def _get_control_measure_objects(self, group, period):
        """
        Returns ControlMeasure objects relevant for given group and period
        """
        return None

    def get_limit(self, limit_type, group, party, party_type, is_eu_member, period):

        if party.abbr == 'EU' and limit_type in (
            LimitTypes.BDN.value,
            LimitTypes.PRODUCTION.value
        ):
            # No BDN or Prod limits for EU/ECE(European Union)
            return None

        if is_eu_member and limit_type == LimitTypes.CONSUMPTION.value:
            # No consumption baseline for EU member states
            return None

        # Get the control measure objects for these limits
        key = (group.group_id, party_type.name, limit_type)
        cm_objects = self.control_measures[key]
        cm_objects = [
            o for o in cm_objects
            if (
                o.start_date <= period.end_date
                and (o.end_date == None or o.end_date >= period.start_date)
            )
        ]

        cm_count = len(cm_objects)
        if cm_count == 0:
            # No control measures here
            return None
        elif cm_count == 1:
            cm = cm_objects[0]
            baseline = self._get_baseline(party, group, cm.baseline_type)
            if baseline is None:
                return Decimal('0')
            else:
                return round_decimal_half_up(
                    baseline * cm.allowed,
                    self._get_decimals_for_limits(group, party)
                )
        elif cm_count == 2:
            # This happens for NA5 BDN limits, AI/BI/EI
            # because control measure becomes applicable in July 28, 2000
            cm1 = cm_objects[0]
            cm2 = cm_objects[1]
            baseline1 = self._get_baseline(party, group, cm1.baseline_type)
            baseline2 = self._get_baseline(party, group, cm2.baseline_type)
            if baseline1 is None or baseline2 is None:
                return Decimal('0')
            days1 = (cm1.end_date - period.start_date).days + 1
            days2 = (period.end_date - cm2.start_date).days + 1
            limit = sum((
                cm1.allowed * days1 * baseline1,
                cm2.allowed * days2 * baseline2,
            )) / ((period.end_date - period.start_date).days + 1)
            return round_decimal_half_up(
                limit,
                self._get_decimals_for_limits(group, party)
            )

    @lru_cache(maxsize=1)
    def _get_baselines_for_party(self, party):
        ret = {}
        for b in Baseline.objects.filter(party=party).select_related(
            'group', 'baseline_type'
        ):
            key = (b.group.group_id, b.baseline_type.name)
            ret[key] = b
        return ret

    def _get_baseline(self, party, group, baseline_type):
        if group.group_id in ('CII', 'CIII'):
            # Fake baseline, because control measures start with phase-out
            return Decimal(0)
        else:
            baselines = self._get_baselines_for_party(party)
            key = (group.group_id, baseline_type.name)
            baseline = baselines.get(key, None)
            if baseline is None:
                return None
            else:
                return baseline.baseline

    def _get_decimals_for_limits(self, group, party):
        """
            Limits must use the same number of decimals as baselines.
            Meaning that for C/I we only use one decimal, unless party is
              in that special list, because C/I baseline for A5
              is the everage of 2009 and 2010
        """
        if group.group_id == 'F':
            return 0

        special_cases = ProdCons.special_cases_2009 + ProdCons.special_cases_2010
        if group.group_id == 'CI' and (party.abbr in special_cases):
            return 2

        return 1


def expected_limits(parties, reporting_periods, groups):
    calculator = LimitCalculator()

    for party in parties:
        qs = PartyHistory.objects.filter(
            party=party,
            reporting_period__in=reporting_periods
        ).order_by('reporting_period__start_date')

        for party_history in qs:
            party = party_history.party
            party_type = party_history.party_type
            is_eu_member = party_history.is_eu_member
            period = party_history.reporting_period

            if period.is_control_period:
                # No limits for control periods
                continue

            if period not in reporting_periods:
                continue

            for group in groups:
                for limit_type in LimitTypes:
                    limit = calculator.get_limit(
                        limit_type.value,
                        group,
                        party,
                        party_type,
                        is_eu_member,
                        period,
                    )
                    if limit is None:
                        continue

                    yield {
                        'limit_type': limit_type,
                        'group': group,
                        'party': party,
                        'reporting_period': period,
                        'limit': limit,
                    }


def limits_diff(parties, reporting_periods, groups):
    def record_key(record):
        return (
            record['party'].id,
            record['reporting_period'].id,
            record['limit_type'].value,
            record['group'].id,
        )

    def row_key(row):
        return (
            row.party_id,
            row.reporting_period_id,
            row.limit_type,
            row.group_id,
        )

    expected = {
        record_key(record): record
        for record in expected_limits(
            list(parties),
            list(reporting_periods),
            list(groups),
        )
    }

    obsolete = []
    different = []

    existing_limits = (
        Limit.objects
        .filter(party__in=parties)
        .filter(reporting_period__in=reporting_periods)
        .filter(group__in=groups)
    )
    for row in existing_limits.iterator():
        key = row_key(row)
        try:
            expected_record = expected.pop(key)
        except KeyError:
            obsolete.append({'row': row})
        else:
            new_value = expected_record['limit']
            if new_value != row.limit:
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

    reporting_periods = ReportingPeriod.objects.all()
    if request.POST['reporting_period'] != '*':
        reporting_periods = reporting_periods.filter(pk=request.POST['reporting_period'])

    groups = Group.objects.all()
    if request.POST['group'] != '*':
        groups = groups.filter(pk=request.POST['group'])

    diff = limits_diff(parties, reporting_periods, groups)

    for record in diff['missing']:
        record['checkbox_value'] = json.dumps({
            'party_id': record['party'].id,
            'reporting_period_id': record['reporting_period'].id,
            'limit_type': record['limit_type'].value,
            'group_id': record['group'].id,
            'limit': str(record['limit']),
        })

    for record in diff['different']:
        record['checkbox_value'] = json.dumps({
            'pk': record['row'].pk,
            'limit': str(record['new_value']),
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
        Limit.objects.create(**data)
        created += 1

    if created:
        messages.success(
            request,
            _("Created %d limits") % created,
        )

    updated = 0

    for payload in request.POST.getlist('different'):
        data = json.loads(payload)
        row = Limit.objects.get(pk=data['pk'])
        row.limit = Decimal(data['limit'])
        row.save()
        updated += 1

    if updated:
        messages.success(
            request,
            _("Updated %d limits") % updated,
        )

    removed = 0

    for payload in request.POST.getlist('obsolete'):
        data = json.loads(payload)
        Limit.objects.get(pk=data['pk']).delete()
        removed += 1

    if removed:
        messages.success(
            request,
            _("Removed %d limits") % removed,
        )


@permission_required('core.can_run_limits_tool')
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
    context['reporting_periods'] = ReportingPeriod.objects.order_by('-start_date').all()
    context['groups'] = Group.objects.all()

    return TemplateResponse(request, 'admin/ozone_tools/generate_limits.html', context)
