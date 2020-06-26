import enum
from datetime import datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .party import Party, PartyType, PartyHistory
from .legal import ReportingPeriod
from .substance import Group
from .utils import DECIMAL_FIELD_DECIMALS, DECIMAL_FIELD_DIGITS


__all__ = [
    'BaselineLimitPermissions',
    'BaselineType',
    'LimitTypes',
    'ControlMeasure',
    'Baseline',
    'Limit',
    'ActualBaselineAndLimit',
]


class BaselineLimitPermissions(models.Model):

    class Meta:

        # No database table creation or deletion operations will be performed
        # for this model. It is just used for creating custom permissions,
        # unattached to a specific model, for the baselines and limits tools.
        managed = False

        default_permissions = []
        permissions = (
            ('can_run_baselines_tool', 'Can run baselines tool'),
            ('can_run_limits_tool', 'Can run limits tool'),
        )


class BaselineType(models.Model):
    """
    Categories of baselines for production, consumption and BDN production.
    """

    name = models.CharField(
        max_length=64,
        help_text="Baseline types can be A5/NA5 Prod/Cons, BDN_pre2k or BDN"
    )
    remarks = models.CharField(
        max_length=9999, blank=True,
        help_text="Remarks for this baseline type"
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'baseline_type'


@enum.unique
class LimitTypes(enum.Enum):
    PRODUCTION = 'Production'
    CONSUMPTION = 'Consumption'
    BDN = 'BDN'


class ControlMeasure(models.Model):
    """
    Restrictions on level of production and consumption for Parties.
    """

    limit_type = models.CharField(
        max_length=64, choices=((s.value, s.name) for s in LimitTypes),
        help_text="Control measure types can be Production, Consumption and BDN"
    )

    group = models.ForeignKey(
        Group, related_name='control_measures', on_delete=models.PROTECT,
        help_text="Annex group"
    )

    party_type = models.ForeignKey(
        PartyType,
        related_name='control_measures',
        on_delete=models.PROTECT
    )

    baseline_type = models.ForeignKey(
        BaselineType, related_name='control_measures', on_delete=models.PROTECT,
        help_text="Baseline type: A5/NA5 Prod/Cons or BDN"
    )

    # this is always required, and can be in the future
    start_date = models.DateField()

    # This can be blank. When not present, it is valid until the end of time
    end_date = models.DateField(blank=True, null=True)

    # This is a percentage
    allowed = models.DecimalField(
        max_digits=6, decimal_places=5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )

    class Meta:
        db_table = 'control_measure'


class Baseline(models.Model):
    """
    Baseline by party and annex group and type (Prod/Cons/BDN)
    """

    party = models.ForeignKey(
        Party, related_name='baselines', on_delete=models.PROTECT
    )
    group = models.ForeignKey(
        Group, related_name='baselines', on_delete=models.PROTECT
    )
    baseline_type = models.ForeignKey(
        BaselineType, related_name='baselines', on_delete=models.PROTECT,
        help_text="Baseline type: A5/NA5 Prod/Cons or BDN"
    )

    baseline = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    class Meta:
        db_table = 'baseline'


class Limit(models.Model):
    """
    Production and Consumption Limits for Substances in a Group / Annex,
    for a Period, for a Party (EDT)
    """

    party = models.ForeignKey(
        Party, related_name='limits', on_delete=models.PROTECT
    )
    reporting_period = models.ForeignKey(
        ReportingPeriod, related_name='limits', on_delete=models.PROTECT
    )
    group = models.ForeignKey(
        Group, related_name='limits', on_delete=models.PROTECT
    )

    limit_type = models.CharField(
        max_length=64, choices=((s.value, s.name) for s in LimitTypes),
        help_text="Limit types can be Production, Consumption and BDN"
    )

    limit = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    class Meta:
        db_table = 'limit_prod_cons'


class ActualBaselineAndLimit(models.Model):
    """
    Actual baselines and limits for a specific party-period-group-type
    combination.
    """
    party = models.ForeignKey(
        Party, related_name='actual_baselines', on_delete=models.PROTECT
    )
    reporting_period = models.ForeignKey(
        ReportingPeriod,
        related_name='actual_baselines',
        on_delete=models.PROTECT
    )
    group = models.ForeignKey(
        Group, related_name='actual_baselines', on_delete=models.PROTECT
    )

    # TODO: should these be null-able?
    baseline_prod = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS,
        decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    baseline_cons = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS,
        decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    baseline_bdn = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS,
        decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    limit_prod = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS,
        decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    limit_cons = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS,
        decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    limit_bdn = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS,
        decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    @classmethod
    def get_actual_data(
        cls, party, reporting_period,
        group=None, is_article5=None, is_eu_member=None
    ):
        """
        Calculates baseline/limit values for all groups, for a
        specific party-reporting period combination.
        If the optional `group` parameter is given, only calculates values for
        that group.
        If the optional is_eu_member and is_article5 parameters are given,
        use them instead of fetching party history. This would be used when
        calculating non-persistent ProdCons data.
        """
        baselines = Baseline.objects.filter(party=party)
        limits = Limit.objects.filter(
            party=party, reporting_period=reporting_period
        )
        if group is not None:
            baselines = baselines.filter(group=group)
            limits = limits.filter(group=group)

        # Get history entry for this party and reporting period
        if is_article5 is None or is_eu_member is None:
            # If the get() fails we let the error propagate, so we don't hide
            # the problem.
            history = PartyHistory.objects.get(
                party=party, reporting_period=reporting_period
            )
            is_article5 = history.is_article5
            is_eu_member = history.is_eu_member

        # First get appropriate baseline types by Article 5 status
        if is_article5:
            prod_bt = 'A5Prod'
            cons_bt = 'A5Cons'
            # Non-existent name
            bdn_bt = None
        else:
            prod_bt = 'NA5Prod'
            cons_bt = 'NA5Cons'
            bdn_bt = 'BDN_NA5'

        # Group baselines by group :)
        baselines_dict = dict()
        limits_dict = dict()
        for baseline in baselines:
            if baseline.group not in baselines_dict:
                baselines_dict[baseline.group] = [baseline]
            else:
                baselines_dict[baseline.group].append(baseline)
        for limit in limits:
            if limit.group not in limits_dict:
                limits_dict[limit.group] = [limit]
            else:
                limits_dict[limit.group].append(limit)

        if group is None:
            groups = Group.get_all_groups()
        else:
            groups = [group]

        ret = dict()
        for group in groups:
            baseline_prod = baseline_cons = baseline_bdn = None
            limit_prod = limit_cons = limit_bdn = None

            for limit in limits_dict.get(group, []):
                if limit.limit_type == LimitTypes.PRODUCTION.value:
                    limit_prod = limit.limit
                elif limit.limit_type == LimitTypes.CONSUMPTION.value:
                    limit_cons = limit.limit
                elif limit.limit_type == LimitTypes.BDN.value:
                    limit_bdn = limit.limit

            for baseline in baselines_dict.get(group, []):
                if baseline.baseline_type.name == prod_bt:
                    # In theory we should check self.is_european_union
                    # but production baselines are not persisted for EU
                    baseline_prod = baseline.baseline
                if baseline.baseline_type.name == cons_bt and not is_eu_member:
                    baseline_cons = baseline.baseline
                # This is actually not correct for all cases - see below
                if baseline.baseline_type.name == bdn_bt:
                    baseline_bdn = baseline.baseline

            # Finally, set or overwrite baseline_bdn if needed.
            # The above-set value is valid only for NA5 parties, year >= 2000
            # and annex groups A/I, A/II, B/I and E/I.
            # For all other cases, the BDN baseline is the A5 or NA5 prod
            # baseline.
            if limit_bdn is not None:
                start_date_2000 = datetime.strptime(
                    '2000-01-01', '%Y-%m-%d'
                ).date()
                if (
                    reporting_period.start_date < start_date_2000
                    or is_article5
                    or group.group_id not in ['AI', 'AII', 'BI', 'EI']
                ):
                    baseline_bdn = baseline_prod

            ret[group] = {
                'baseline_prod': baseline_prod,
                'baseline_cons': baseline_cons,
                'baseline_bdn': baseline_bdn,
                'limit_prod': limit_prod,
                'limit_cons': limit_cons,
                'limit_bdn': limit_bdn,
            }

        # Finally return dict with values for all groups
        return ret

    @classmethod
    def populate_actual_data(
        cls, party, reporting_period,
        group=None, is_article5=None, is_eu_member=None
    ):
        """
        Creates and populates new ActualBaselineAndLimit entries (or updates
        existing ones).
        If the optional `group` parameter is given, only fill entries for that
        group.
        If the optional is_eu_member and is_article5 parameters are given,
        use them instead of fetching party history. This would be used when
        calculating non-persistent ProdCons data.
        """
        calculated_values = cls.get_actual_data(
            party, reporting_period, group, is_article5, is_eu_member
        )
        for group in calculated_values.keys():
            # Update or create actual object for this group
            actual_baseline_limit = cls.objects.update_or_create(
                party=party,
                reporting_period=reporting_period,
                group=group,
                defaults=calculated_values[group]
            )

    class Meta:
        db_table = 'actual_baseline'
