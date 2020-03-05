import enum

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .party import Party, PartyType
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
