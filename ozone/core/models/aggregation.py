from datetime import datetime
from decimal import Decimal

from django.contrib.postgres import fields
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.functional import cached_property

from .legal import ReportingPeriod
from .party import Party, PartyHistory
from .substance import Group, Substance
from .utils import round_decimal_half_up, DECIMAL_FIELD_DECIMALS, DECIMAL_FIELD_DIGITS
from .control import Limit, LimitTypes, Baseline


__all__ = [
    'ProdCons',
    'ProdConsMT'
]


class BaseProdCons(models.Model):
    """
    Base *abstract* aggregation model for Production/consumption data reports.

    Only one entry per party/reporting_period/group - when a new submission
    becomes current for that party & reporting period, the values in the entry
    will be automatically updated.
    """
    def get_roundable_fields(self):
        """
        Returns fields that should be rounded after all calculations are
        performed, together with the number of decimals to be rounded to.
        """
        # Needs to be implemented in each subclass for rounding to work
        raise NotImplementedError

    party = models.ForeignKey(
        Party,
        related_name="%(class)s_aggregations",
        on_delete=models.PROTECT,
        help_text="Party for which this aggregation was calculated",
    )

    reporting_period = models.ForeignKey(
        ReportingPeriod,
        related_name="%(class)s_aggregations",
        on_delete=models.PROTECT,
        help_text="Reporting Period for which this aggregation was calculated",
    )

    # These flags are redundant, as they are already present in the PartyHistory
    # model, but they are added here to enable easy API filtering based on them.
    # The values for them will be automatically added at first save.
    is_article5 = models.NullBooleanField(blank=True)
    is_eu_member = models.NullBooleanField(blank=True)

    submissions = fields.JSONField(default=dict)

    # Aggregated quantity fields (derived from data reports)
    # Production
    production_all_new = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    production_feedstock = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    production_essential_uses = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    production_laboratory_analytical_uses = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    production_article_5 = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    production_quarantine = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    production_process_agent = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    # Destruction
    destroyed = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    # Imports
    import_new = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    import_recovered = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    import_feedstock = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    import_essential_uses = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    import_laboratory_uses = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    import_quarantine = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    import_process_agent = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    # Exports
    export_new = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    export_recovered = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    export_feedstock = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    export_essential_uses = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    export_quarantine = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    export_process_agent = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    # Non-party: these values are an aggregation of art7 non-party trade
    # ([import/export]_[new/recovered])
    non_party_import = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    non_party_export = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    # Transfers
    prod_transfer = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )
    cons_transfer = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        default=Decimal('0.0'), validators=[MinValueValidator(0.0)]
    )

    # Totals computed based on the above fields.
    # Though these could have been implemented as properties (as they can be
    # deterministically derived from the values of the above fields), having
    # them as fields in the models allows greater flexibility in use.
    # They are null-able so entries can be saved without these being calculated.
    calculated_production = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        null=True, blank=True, default=None
    )

    calculated_consumption = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        null=True, blank=True, default=None
    )

    calculated_qps_production = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        null=True, blank=True, default=None
    )

    calculated_qps_consumption = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        null=True, blank=True, default=None
    )

    calculated_laboratory_production = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        null=True, blank=True, default=None
    )

    calculated_laboratory_consumption = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        null=True, blank=True, default=None
    )

    updated_at = models.DateTimeField(auto_now=True, null=True)

    @classmethod
    def decimal_fields(cls):
        return [
            f.name for f in cls._meta.fields
            if isinstance(f, models.fields.DecimalField)
        ]

    @cached_property
    def decimal_field_names(self):
        return self.__class__.decimal_fields()

    def is_empty(self):
        """Returns True if aggregation has all-zero values"""
        for field in self.__class__._meta.get_fields():
            if (
                isinstance(field, models.DecimalField)
                and field.name not in self.get_roundable_fields()
                and field.value_from_object(self) != Decimal(0.0)
            ):
                return False
        return True

    @classmethod
    def cleanup_aggregations(cls, party, reporting_period):
        """
        This resets all aggregation data for the given party/period.

        For now this simply means deleting all corresponding rows, but this
        might change in the future if more data sources (besides Art7) are added
        """
        aggregations = cls.objects.filter(
            party=party, reporting_period=reporting_period
        )
        for aggregation in aggregations:
            if aggregation.is_empty():
                aggregation.delete()

    special_cases_2009 = [
        'CD', 'CG', 'DZ', 'EC', 'ER', 'GQ', 'GW', 'HT', 'LC', 'MA', 'MK',
        'MZ', 'NE', 'NG', 'SZ', 'FJ', 'PK', 'PH'
    ]
    special_cases_2010 = [
        'DZ', 'EC', 'ER', 'HT', 'LC', 'LY', 'MA', 'NG', 'PE', 'SZ', 'TR',
        'YE', 'FJ', 'PK', 'PH'
    ]

    @classmethod
    def get_decimals(cls, period, group, party):
        """
        Returns the number of decimals according to the following
        rounding rules.
        """
        if group and group.group_id == 'CI':
            if (
                period.start_date >= datetime.strptime('2011-01-01', "%Y-%m-%d").date()
                or period.name == '2009' and party.abbr in cls.special_cases_2009
                or period.name == '2010' and party.abbr in cls.special_cases_2010
            ):
                return 2
        if group and group.group_id == 'F':
            return 0
        return 1

    @property
    def decimals(self):
        """
        Needs to be implemented in concrete classes for save() to work properly
        """
        raise NotImplementedError

    @staticmethod
    def has_read_rights_for_party(party, user):
        if (
            user.is_secretariat
            or user.party is not None and user.party == party
        ):
            return True
        return False

    def has_read_rights(self, user):
        return self.has_read_rights_for_party(self.party, user)

    @cached_property
    def is_european_union(self):
        return self.party.abbr == 'EU'

    @cached_property
    def is_after_2010(self):
        start_date_2010 = datetime.strptime('2010-01-01', "%Y-%m-%d").date()
        if self.reporting_period.start_date >= start_date_2010:
            return True
        return False

    @cached_property
    def is_china_or_brazil(self):
        return self.party.abbr == "CN" or self.party.abbr == "BR"

    def get_production_process_agent(self):
        if (
            not self.is_article5
            or (self.is_china_or_brazil and self.is_after_2010)
        ):
            return self.production_process_agent
        return Decimal(0.0)

    def get_import_process_agent(self):
        if (
            not self.is_article5
            or (self.is_china_or_brazil and self.is_after_2010)
        ):
            return self.import_process_agent
        return Decimal(0.0)

    def get_export_feedstock(self):
        if self.production_all_new > Decimal(0.0):
            return self.export_feedstock
        return Decimal(0.0)

    def get_export_process_agent(self):
        if self.production_all_new > Decimal(0.0):
            return self.export_process_agent
        return Decimal(0.0)

    def get_export_quarantine(self):
        if self.production_quarantine > Decimal(0.0):
            return self.export_quarantine
        return Decimal(0.0)

    def get_export_or_production_quarantine(self):
        if self.production_quarantine >= self.export_quarantine:
            return self.export_quarantine
        else:
            return self.production_quarantine

    def apply_rounding(self):
        for field_name, decimals in self.get_roundable_fields().items():
            field_value = getattr(self, field_name)
            if field_value is not None and field_value != '':
                setattr(
                    self, field_name,
                    round_decimal_half_up(field_value, decimals)
                )

    def get_calc_consumption(self):
        """
            Formula for non-EU members is needed for their C/I baselines
        """
        return (
            self.production_all_new
            - self.production_feedstock
            - self.production_quarantine
            - self.get_production_process_agent()
            - self.destroyed
            - self.export_new
            + self.get_export_quarantine()
            + self.non_party_export
            + self.import_new
            - self.import_feedstock
            - self.get_import_process_agent()
            - self.import_quarantine
        )

    def calculate_totals(self, is_eu_member=None, is_article5=None):
        """
        Called on save() to automatically update fields.
        Calculates values for:
            - calculated_production
            - calculated_consumption
        """
        # Check whether this instance has the is_eu_member and is_article5 fields
        # properly populated. If not (which may happen when the method is called
        # for generating non-persistent data, then the method parameters are used
        if self.is_eu_member is None:
            self.is_eu_member = is_eu_member
        if self.is_article5 is None:
            self.is_article5 = is_article5
        # Production
        if self.is_european_union:
            self.calculated_production = None
        else:
            self.calculated_production = (
                self.production_all_new
                - self.production_feedstock
                - self.production_quarantine
                - self.get_production_process_agent()
                - self.destroyed
                - self.get_export_feedstock()
                - self.get_export_process_agent()
            )

        # Consumption
        if self.is_eu_member:
            self.calculated_consumption = None
        else:
            self.calculated_consumption = self.get_calc_consumption()

        # QPS production & consumption (QPSProd, QPSCons)
        if self.is_european_union:
            self.calculated_qps_production = None
        else:
            self.calculated_qps_production = self.production_quarantine

        if self.is_eu_member:
            self.calculated_qps_consumption = None
        else:
            self.calculated_qps_consumption = (
                self.production_quarantine
                + self.import_quarantine
                - self.get_export_or_production_quarantine()
            )

        # Laboratory production & consumption (LabProd, LabCons)
        if self.is_european_union:
            self.calculated_laboratory_production = None
        else:
            self.calculated_laboratory_production = \
                self.production_laboratory_analytical_uses

        if self.is_eu_member:
            self.calculated_laboratory_consumption = \
                self.production_laboratory_analytical_uses
        elif self.is_european_union:
            self.calculated_laboratory_consumption = \
                self.import_laboratory_uses
        else:
            self.calculated_laboratory_consumption = (
                self.import_laboratory_uses
                + self.production_laboratory_analytical_uses
            )
        # Apply rounding to everything that needs it.
        self.apply_rounding()

    class Meta:
        abstract = True


class ProdConsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'party', 'reporting_period', 'group'
        )


class ProdCons(BaseProdCons):
    """
    Concrete model for ODP-based aggregations.
    These aggregate totals per substance group.
    """
    def get_roundable_fields(self):
        """
        Returns fields that should be rounded after all calculations are
        performed, together with the number of decimals to be rounded to.
        """
        # self.decimals is a cached property, so it's ok to call it several
        # times
        return {
            'baseline_prod': self.decimals,
            'baseline_cons': self.decimals,
            'baseline_bdn': self.decimals,
            'limit_prod': self.decimals,
            'limit_cons': self.decimals,
            'limit_bdn': self.decimals,
            'calculated_production': self.decimals,
            'calculated_consumption': self.decimals,
            'calculated_qps_production': self.decimals,
            'calculated_qps_consumption': self.decimals,
            'calculated_laboratory_production': 5,
            'calculated_laboratory_consumption': 5,
        }

    objects = ProdConsManager()

    group = models.ForeignKey(
        Group,
        related_name="%(class)s_aggregations",
        on_delete=models.PROTECT,
        help_text="Annex Group for which this aggregation was calculated",
    )

    # Baselines - they can be null!
    baseline_prod = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        blank=True, null=True, default=None
    )

    baseline_cons = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        blank=True, null=True, default=None
    )

    baseline_bdn = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        blank=True, null=True, default=None
    )

    # Limits
    limit_prod = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        blank=True, null=True, default=None
    )

    limit_cons = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        blank=True, null=True, default=None
    )

    limit_bdn = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        blank=True, null=True, default=None
    )

    @cached_property
    def decimals(self):
        """
        Returns the number of rounding decimals for this particular instance,
        based on reporting period, group and party.
        Using getattr instead of the standard self.field_name as this property
        can be used on unsaved and inconsistent (e.g. party==None) model
        instances, in which case Django will complain.
        """
        return BaseProdCons.get_decimals(
            self.reporting_period,
            getattr(self, 'group', None),
            getattr(self, 'party', None),
        )

    def populate_limits_and_baselines(self, is_article5=None, is_eu_member=None):
        """
        At save we fetch the limits/baselines from the corresponding tables.
        This assumes that said tables are pre-populated, which should happen
        in practice. Otherwise, this method might be triggered by other means.

        We may also fetch the limits/baselines data without having first saved
        the instance. In this case the is_article5 parameter is used.
        """
        # If this instance had already been saved, fields is_article5
        # and is_eu_member should already be populated with a coherent value.
        # If the instance has not been saved (as in the case of non-persistent
        # instances used to generate on-the-fly data), then use the
        # externally-provided parameter.
        if self.is_article5 is None:
            self.is_article5 = is_article5
        if self.is_eu_member is None:
            self.is_eu_member = is_eu_member

        # Reset baselines and limits to None, in case previous values exist
        self.limit_prod = self.limit_cons = self.limit_bdn = None
        self.baseline_prod = self.baseline_cons = self.baseline_bdn = None

        # Populate limits
        for limit in Limit.objects.filter(
            party=self.party,
            reporting_period=self.reporting_period,
            group=self.group
        ):
            if limit.limit_type == LimitTypes.PRODUCTION.value:
                self.limit_prod = limit.limit
            elif limit.limit_type == LimitTypes.CONSUMPTION.value:
                self.limit_cons = limit.limit
            elif limit.limit_type == LimitTypes.BDN.value:
                self.limit_bdn = limit.limit

        # Populate baselines; first get appropriate baseline types
        if self.is_article5:
            prod_bt = 'A5Prod'
            cons_bt = 'A5Cons'
            # Non-existent name
            bdn_bt = None
        else:
            prod_bt = 'NA5Prod'
            cons_bt = 'NA5Cons'
            bdn_bt = 'BDN_NA5'

        for baseline in Baseline.objects.filter(
            party=self.party,
            group=self.group
        ).values('baseline_type__name', 'baseline'):
            if (baseline['baseline_type__name'] == prod_bt):
                # In theory we should check self.is_european_union
                # but production baselines are not persisted for EU
                self.baseline_prod = baseline['baseline']
            if (baseline['baseline_type__name'] == cons_bt
                    and not self.is_eu_member):
                self.baseline_cons = baseline['baseline']
            # This is actually not correct for all cases - see below
            if (baseline['baseline_type__name'] == bdn_bt):
                self.baseline_bdn = baseline['baseline']

        # Finally, set or overwrite baseline_bdn if needed.
        # The above-set value is valid only for NA5 parties, year >= 2000
        # and annex groups A/I, A/II, B/I and E/I.
        # For all other cases, the BDN baseline is the A5 or NA5 prod baseline.
        if self.limit_bdn is not None:
            start_date_2000 = datetime.strptime('2000-01-01', '%Y-%m-%d').date()
            if (
                self.reporting_period.start_date < start_date_2000
                or self.is_article5
                or self.group.group_id not in ['AI', 'AII', 'BI', 'EI']
            ):
                self.baseline_bdn = self.baseline_prod

    def update_limits_and_baselines(self, invalidate_cache=False):
        """
        Used when needing to save just baselines and limits without performing
        any extra totals calculations.
        """
        self.populate_limits_and_baselines()
        super().save(invalidate_cache)

    def __str__(self):
        return f'Aggregation for {self.party.name}, ' \
               f'{self.reporting_period.name}, group {self.group.group_id}'

    def save(self, *args, **kwargs):
        """
        Overridden to perform extra actions.
        """

        # Used for marking whether cache should be invalidated at the end.
        # If the param is not specified, default action is to invalidate.
        invalidate_cache = kwargs.pop('invalidate_cache', True)

        # If this is the first save, only invalidate cache if values have been
        # provided for the decimal fields.
        if not self.pk or kwargs.pop('force_insert', False) is True:
            # If any decimal fields have changed, cache must be invalidated
            invalidate_cache = True if not self.is_empty() else False

        # At each save, we need to recalculate the totals.
        self.calculate_totals()

        # Fill article5 and EU flags and also populate baselines and limits.
        ph = PartyHistory.objects.filter(
            party=self.party,
            reporting_period=self.reporting_period
        ).first()
        self.is_article5 = ph.is_article5 if ph else None
        self.is_eu_member = ph.is_eu_member if ph else None
        self.populate_limits_and_baselines()

        super().save(*args, **kwargs)

        # If all went well, send the clear_cache signal.
        # send_robust() is used to avoid save() not completing in case there
        # is an error when invalidating the cache.
        if invalidate_cache is True:
            from ..signals import clear_aggregation_cache_signal
            clear_aggregation_cache_signal.send_robust(
                sender=self.__class__, instance=self
            )

    def delete(self, *args, **kwargs):
        """
        Overridden to perform cache invalidation if needed.
        """
        # Used for marking whether cache should be invalidated at the end.
        # If the param is not specified, default action is to invalidate.
        invalidate_cache = kwargs.pop('invalidate_cache', True)

        super().delete(*args, **kwargs)

        # If all went well, send the clear_cache signal.
        # send_robust() is used to avoid save() not completing in case there
        # is an error when invalidating the cache.
        if invalidate_cache is True:
            from ..signals import clear_aggregation_cache_signal
            clear_aggregation_cache_signal.send_robust(
                sender=self.__class__, instance=self
            )

    class Meta(BaseProdCons.Meta):
        db_table = "aggregation_prod_cons"
        unique_together = ("party", "reporting_period", "group")
        verbose_name_plural = 'Production consumptions'


class ProdConsMTManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'party', 'reporting_period', 'substance', 'substance__group'
        )


class ProdConsMT(BaseProdCons):
    """
    Concrete model for MT-based aggregations.
    These aggregate totals per substance.
    """
    def get_roundable_fields(self):
        """
        Returns fields that should be rounded after all calculations are
        performed, together with the number of decimals to be rounded to.
        MT aggregations should not be rounded.
        """
        return {}

    objects = ProdConsMTManager()

    substance = models.ForeignKey(
        Substance,
        related_name="%(class)s_aggregations",
        on_delete=models.PROTECT,
        help_text="Substance for which this aggregation was calculated",
    )

    @cached_property
    def decimals(self):
        return BaseProdCons.get_decimals(
            self.reporting_period, self.substance.group, self.party
        )

    def __str__(self):
        return f'MT Aggregation for {self.party.name}, ' \
               f'{self.reporting_period.name}, substance {self.substance.name}'

    def save(self, *args, **kwargs):
        """
        At each save, we need to recalculate the totals.
        """
        self.calculate_totals()

        # Fill article5 and EU flags.
        ph = PartyHistory.objects.filter(
            party=self.party,
            reporting_period=self.reporting_period
        ).first()
        self.is_article5 = ph.is_article5 if ph else None
        self.is_eu_member = ph.is_eu_member if ph else None

        super().save(*args, **kwargs)

    class Meta(BaseProdCons.Meta):
        db_table = "aggregation_prod_cons_mt"
        unique_together = ("party", "reporting_period", "substance")
        verbose_name_plural = 'Production consumptions metric tonnes'
