from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property

from model_utils import FieldTracker

from .exemption import CriticalUseCategory
from .party import Party
from .reporting import ModifyPreventionMixin, Submission
from .substance import BlendComponent, Substance, Blend
from .aggregation import ProdCons, ProdConsMT
from .utils import (
    model_to_dict,
    decimal_zero_if_none,
    DECIMAL_FIELD_DIGITS,
    DECIMAL_FIELD_DECIMALS,
    quantize,
)


__all__ = [
    'Article7Questionnaire',
    'Article7Export',
    'Article7Import',
    'Article7Production',
    'Article7Destruction',
    'Article7NonPartyTrade',
    'Article7Emission',
    'HighAmbientTemperatureProduction',
    'HighAmbientTemperatureImport',
    'DataOther',
    'RAFReport',
    'RAFReportUseCategory',
    'RAFImport',
]


class BlendCompositionMixin:
    """
    Mixin to be used by data report models that accept both substances
    and blends.

    Each model that uses it needs to have the proper `QUANTITY_FIELDS` attribute
    set, e.g.:
    QUANTITY_FIELDS = [
        'quantity_total_new',
        'quantity_total_recovered',
        'quantity_feedstock'
    ]
    Also, all models using it need a field tracker.

    In case a blend-based row is created, additional substance-based rows for
    each blend component will be created.

    NB: order of inheritance - this should come before models.Model!
    """

    def clean(self):
        """
        Overriding the clean() method to ensure that substances and blends are
        not both specified.

        This is called explicitly from the save() method, also overridden in
        this class.
        """
        if self.substance is None and self.blend is None:
            raise ValidationError(
                {
                    'substance': [_(
                        'Data should refer to one substance or one blend'
                    )],
                    'blend': [_(
                        'Data should refer to one substance or one blend'
                    )]
                }
            )
        if self.substance is not None and self.blend is not None:
            raise ValidationError(
                {
                    'substance': [_(
                        'Data should not refer to both a substance and a blend'
                    )],
                    'blend': [_(
                        'Data should not refer to both a substance and a blend'
                    )]
                }
            )

        # If this is a custom blend from a different party, raise an error
        if (
            self.blend is not None
            and self.blend.party is not None
            and self.blend.party != self.submission.party
        ):
            raise ValidationError(
                _("This blend is for a different party!")
            )

        # Also, no changes are allowed on blend_item != null objects
        if self.tracker.changed() and self.tracker.previous('blend_item_id'):
            raise ValidationError(
                _("Substance rows derived from blends cannot be changed!")
            )

        super().clean()

    def save(self, *args, **kwargs):
        """
        This overrides save() to also create rows for each substance (component)
        in a blend.
        """

        # Call clean() to perform either-substance-or-blend validation
        self.full_clean()

        super().save(*args, **kwargs)

        # If blend has changed, child rows should be deleted.
        # Tracker adds an '_id' to foreign key field names.
        if self.tracker.has_changed('blend_id'):
            changed_fields = self.QUANTITY_FIELDS
        else:
            # If any of the QUANTITY_FIELDS have changed for a blend,
            # child rows should be deleted.
            changed_fields = [field for field in self.QUANTITY_FIELDS
                              if self.tracker.has_changed(field)]
        if not changed_fields:
            return

        with transaction.atomic():
            # First delete all child rows (using related_name)
            self.components.all().delete()

            # Then recreate, skipping over substance-less components
            components = BlendComponent.objects.filter(
                blend=self.blend, substance__isnull=False
            )
            for component in components:
                # Init & populate kwargs for each blend component's save()
                field_dictionary = dict()
                for field in self.QUANTITY_FIELDS:
                    # Compute individual substance quantities
                    quantity = getattr(self, field)
                    field_dictionary[field] = quantize(component.percentage * quantity) \
                        if quantity else None

                attributes = model_to_dict(
                    self,
                    exclude=[
                        'id', 'substance_id', 'blend_id', 'blend_item_id',
                        '_state', '_deferred_fields', '_tracker', 'save',
                    ],
                )
                attributes['substance_id'] = component.substance.pk
                attributes['blend_item_id'] = self.pk
                attributes.update(field_dictionary)
                self.__class__.objects.create(**attributes)


class PolyolsMixin:
    def clean(self):
        if (not self.substance or not self.substance.is_contained_in_polyols) \
                and self.quantity_polyols:
            raise ValidationError(
                _("Cannot report polyols quantity if substance not in polyols!")
            )
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class AggregationMixin:
    """
    Used by all data-report classes that need to generate aggregated data.
    """

    @classmethod
    def get_fields_sum_by_group(cls, submission, group, field_names, baseline):
        """
        Returns sum of quantities reported for given group_id, for a certain
        submission. Quantities are multiplied by either the ODP or GWP of each
        substance.
        If the baseline argument is True, then quantities are multiplied by
        the substance's gwp_baseline (useful when calculating baselines).
        """
        potential_field = ''
        if baseline is True:
            potential_field = 'substance__gwp_baseline'
        elif group.is_gwp:
            potential_field = 'substance__gwp'
        elif group.is_odp:
            potential_field = 'substance__odp'

        fields_values = cls.objects.filter(
            submission=submission, substance__group__id=group.id
        ).values('id', potential_field, *field_names)

        return {
            field_name: sum(
                [
                    decimal_zero_if_none(value[field_name]) *
                    decimal_zero_if_none(value[potential_field])
                    for value in fields_values
                ]
            )
            for field_name in field_names
        }

    @classmethod
    def fill_aggregated_data(cls, submission=None, reported_groups=[]):
        # Aggregations are unique per Party/Period/AnnexGroup. We need to
        # iterate over the substance groups in this submission.

        if not hasattr(cls, 'AGGREGATION_MAPPING'):
            return

        for group in reported_groups:
            # Find an aggregation if one is already created
            aggregation, created = ProdCons.objects.get_or_create(
                party=submission.party,
                reporting_period=submission.reporting_period,
                group=group
            )

            values = cls.get_fields_sum_by_group(
                submission, group, cls.AGGREGATION_MAPPING.keys(), False
            )
            for model_field, aggr_field in cls.AGGREGATION_MAPPING.items():
                # Add with existing value, as a field in the aggregation
                # table may be populated by aggregating values from several
                # other fields in the data models.
                value = decimal_zero_if_none(getattr(aggregation, aggr_field))
                model_value = decimal_zero_if_none(values[model_field])
                value += model_value
                setattr(aggregation, aggr_field, value)

            # Saving will automatically trigger the calculation of computed
            # values
            aggregation.save(invalidate_cache=True)

    @classmethod
    def fill_aggregated_mt_data(cls, submission, queryset):
        if not hasattr(cls, 'AGGREGATION_MAPPING'):
            return

        for entry in queryset:
            # Add entry to dictionary if necessary
            aggregation, created = ProdConsMT.objects.get_or_create(
                party=submission.party,
                reporting_period=submission.reporting_period,
                substance=entry.substance
            )

            for model_field, aggr_field in cls.AGGREGATION_MAPPING.items():
                # Add with existing value, as a field in the aggregation
                # table may be populated by aggregating values from several
                # other fields in the data models.
                model_value = decimal_zero_if_none(
                    getattr(entry, model_field, None)
                )
                value = decimal_zero_if_none(getattr(aggregation, aggr_field))
                value += model_value
                setattr(aggregation, aggr_field, value)

            obligation_type = submission.obligation.obligation_type
            if obligation_type in aggregation.submissions:
                submissions_set = set(aggregation.submissions[obligation_type])
                submissions_set.add(submission.id)
                aggregation.submissions[obligation_type] = list(submissions_set)
            else:
                aggregation.submissions[obligation_type] = [submission.id,]

            # This will automatically trigger the calculation of computed
            # values
            aggregation.save()

    @classmethod
    def clear_aggregated_data(
        cls, submission, reported_groups=[], invalidate_cache=True
    ):
        """
        Clears all aggregated data generated by submission
        """
        if not hasattr(cls, 'AGGREGATION_MAPPING'):
            return

        for group in reported_groups:
            # Find an aggregation if one is already created
            # This will return None if there is no aggregation
            aggregation = ProdCons.objects.filter(
                party=submission.party,
                reporting_period=submission.reporting_period,
                group=group
            ).first()
            if aggregation is None:
                continue

            if not aggregation.is_empty():
                # Set all aggregation fields coming from this model to zero
                for model_field, aggr_field in cls.AGGREGATION_MAPPING.items():
                    setattr(aggregation, aggr_field, Decimal('0.0'))
                aggregation.save(invalidate_cache=invalidate_cache)

            # If this has left the aggregation empty, delete it
            if aggregation.is_empty():
                aggregation.delete(invalidate_cache=invalidate_cache)

    @classmethod
    def clear_aggregated_mt_data(cls, submission, queryset):
        if not hasattr(cls, 'AGGREGATION_MAPPING'):
            return

        for entry in queryset:
            aggregation = ProdConsMT.objects.filter(
                party=submission.party,
                reporting_period=submission.reporting_period,
                substance=entry.substance
            ).first()
            if aggregation is None:
                continue

            # Set all aggregation fields coming from this model to zero
            for model_field, aggr_field in cls.AGGREGATION_MAPPING.items():
                setattr(aggregation, aggr_field, Decimal('0.0'))

            # Clear this submission from the list of submissions for this aggr
            obligation_type = submission.obligation.obligation_type
            if submission.id in aggregation.submissions.get(obligation_type, []):
                submissions_set = set(aggregation.submissions[obligation_type])
                submissions_set.remove(submission.id)
                aggregation.submissions[obligation_type] = list(submissions_set)
            aggregation.save()

            # If this has left the aggregation empty, delete it; else save
            if aggregation.is_empty():
                aggregation.delete()

    @classmethod
    def get_aggregated_data(
        cls, submission, reported_groups,
        baseline=False, populate_baselines=True
    ):
        """
        Populates reported_groups with newly-calculated aggregation data.

        reported_groups: mapping of form:
        {
            group: ProdCons instance,
            ...
        }

        baseline - if True, then quantities are multiplied by the substance's
        gwp_baseline (useful when calculating baselines)

        populate_baselines - if True, the baselines/limits aggregation fields
        will be populated from the baselines/limits table.

        """
        if not hasattr(cls, 'AGGREGATION_MAPPING'):
            return

        # Since the ProdConsMT entries created here are not persisted, we need
        # to pass the value of is_eu_member to calculate_totals() and
        # is_article5 to populate_limits_and_baselines().
        # The submission's party_history property is cached.
        ph = submission.party_history
        is_article5 = ph.is_article5 if ph else None
        is_eu_member = ph.is_eu_member if ph else None

        # Aggregations are unique per Party/Period/AnnexGroup. We need to
        # iterate over the substance groups in this submission.
        for group, aggregation in reported_groups.items():
            # Initiate a model instance if needed but *do not save* it to the DB
            # This still initiates the fields with the correct default values.
            if aggregation is None:
                aggregation = ProdCons(
                    party=submission.party,
                    reporting_period=submission.reporting_period,
                    group=group
                )
                reported_groups[group] = aggregation

            values = cls.get_fields_sum_by_group(
                submission, group, cls.AGGREGATION_MAPPING.keys(), baseline
            )
            for model_field, aggr_field in cls.AGGREGATION_MAPPING.items():
                # Add with existing value, as a field in the aggregation table
                # may be populated by aggregating values from several other
                # fields in the data models.
                value = decimal_zero_if_none(getattr(aggregation, aggr_field))
                model_value = decimal_zero_if_none(values[model_field])
                value += model_value
                setattr(aggregation, aggr_field, value)

            # Populate limits and baselines; calculate totals
            # Because these aggregation entries have not been written to the DB,
            # the values for aggregation.is_article5 and is_eu_member are not
            # correct and need to be passed as parameters.
            if populate_baselines:
                aggregation.populate_limits_and_baselines(is_article5, is_eu_member)
            aggregation.calculate_totals(is_eu_member, is_article5)

    @classmethod
    def get_aggregated_mt_data(cls, submission, queryset, reported_substances):
        """
        reported_substances: mapping of form:
        {
            substance: ProdConsMT instance,
            ...
        }
        """
        if not hasattr(cls, 'AGGREGATION_MAPPING'):
            return

        # Since the ProdConsMT entries created here are not persisted, we need
        # to pass the value of is_eu_member to calculate_totals().
        # The submission's party_history property is cached.
        ph = submission.party_history
        is_eu_member = ph.is_eu_member if ph else None
        is_article5 = ph.is_article5 if ph else None

        for entry in queryset:
            # Add entry to dictionary if necessary
            if entry.substance not in reported_substances.keys():
                reported_substances[entry.substance] = ProdConsMT(
                    party=submission.party,
                    reporting_period=submission.reporting_period,
                    substance=entry.substance
                )
            # Now we definitely have an aggregation, update it based on this
            # entry's data
            aggregation = reported_substances[entry.substance]

            for model_field, aggr_field in cls.AGGREGATION_MAPPING.items():
                # Add with existing value, as a field in the aggregation
                # table may be populated by aggregating values from several
                # other fields in the data models.
                value = decimal_zero_if_none(getattr(aggregation, aggr_field))
                model_value = decimal_zero_if_none(
                    getattr(entry, model_field, None)
                )
                value += model_value
                setattr(aggregation, aggr_field, value)

            aggregation.calculate_totals(is_eu_member, is_article5)


class BaseReport(models.Model):
    """
    This will be used as a base for all reporting models.
    """

    # We want to avoid deletion of `Submission`s which contain data reports.
    # In order to delete a non-submitted submission, its associated reports
    # will need to be deleted first.
    submission = models.ForeignKey(
        Submission, related_name='%(class)ss', on_delete=models.PROTECT
    )

    # Each entry in the Article 7 forms can have remarks
    remarks_party = models.CharField(
        max_length=9999, blank=True,
        help_text="Remarks added by the reporting party"
    )
    remarks_os = models.CharField(
        max_length=9999,
        blank=True,
        help_text="Remarks added by the ozone secretariat"
    )

    ordering_id = models.IntegerField(
        default=0,
        help_text="This allows the interface to keep the data entries in their "
                  "original order, as given by the user."
    )

    @classmethod
    def decimal_fields(cls):
        return [
            f.name for f in cls._meta.fields
            if isinstance(f, models.fields.DecimalField)
        ]

    @cached_property
    def decimal_field_names(self):
        return self.__class__.decimal_fields()

    class Meta:
        abstract = True
        ordering = ['ordering_id', ]


class BaseBlendCompositionReport(BlendCompositionMixin, BaseReport):
    """
    This will be used as a base for all reporting models that accept
    both substances and blends.

    Since it uses the blend composition mixin, all models inheriting this
    need the following:
    - a FieldTracker called `tracker`
    - the proper `QUANTITY_FIELDS` attribute set, e.g.:
    QUANTITY_FIELDS = [
        'quantity_total_new',
        'quantity_total_recovered',
        'quantity_feedstock'
    ]

    """

    # `blank=True` is needed for full_clean() calls performed by save()
    substance = models.ForeignKey(
        Substance, blank=True, null=True, on_delete=models.PROTECT,
        help_text="Substance ID"
    )
    blend = models.ForeignKey(
        Blend, blank=True, null=True, on_delete=models.PROTECT,
        help_text="Blend ID"
    )
    # When non-null, this is used to signal that this particular
    # substance entry was automatically generated from an entry containing
    # a blend.
    blend_item = models.ForeignKey(
        'self',
        related_name='components',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True


class BaseImportExportReport(models.Model):
    """
    This will be used as a base for data reporting models on import and export.
    """

    # This needs to be defined in the concrete model for the data validation
    # to work.
    PARTY_FIELD = None

    quantity_total_new = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    quantity_total_recovered = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    quantity_feedstock = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    quantity_polyols = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    decision_polyols = models.CharField(
        max_length=512, blank=True
    )

    @classmethod
    def validate_import_export_data(cls, submission):
        """
        Function for validation of all import/export data in a specific Art 7
        submission. Validation is done in regards to complex, per-form
        validation criteria (see https://github.com/eaudeweb/ozone/issues/81)
        """

        def get_fields_sum(entry_dict, field_names):
            field_values = [
                decimal_zero_if_none(entry_dict.get(f, Decimal(0)))
                for f in field_names
            ]
            return sum(field_values) if field_values else Decimal(0)

        totals_fields = ['quantity_total_new',]
        excluded_fields = ['quantity_polyols', 'quantity_total_recovered']
        party_field = cls.PARTY_FIELD
        quantity_fields = [
            f for f in cls.QUANTITY_FIELDS
            if f not in totals_fields and f not in excluded_fields
        ]

        # Find all entries in this submission that do not have a src/dst country
        # (actually, there should only be one such entry).
        # Then find all substances relating to those entries, taking blend
        # contents into account.
        # From these substances, keep only the ones that are also in at least
        # one entry with a src/dst country.
        partyless_substances = set()
        partyful_substances = set()
        # Only taking into account substance entries (as there already are
        # substance entries auto-generated from blends - and calculating them
        # again is redundant)
        substance_entries = cls.objects.filter(submission=submission).exclude(
            blend__isnull=False
        )
        values = substance_entries.values(
            'id', 'substance', party_field, *totals_fields, *quantity_fields
        )

        for entry in values:
            substance = entry.get('substance', None)
            party = entry.get(party_field, None)

            # If this entry has a party set, it should be checked for
            # consistency at entry level.
            # (see https://github.com/eaudeweb/ozone/issues/1416)
            if party is not None:
                if (
                    get_fields_sum(entry, totals_fields) <
                    get_fields_sum(entry, quantity_fields)
                ):
                    raise ValidationError(
                        f'For {Substance.objects.filter(id=substance).first()},'
                        f' {Party.objects.filter(id=party).first()}, '
                        f'the sum of quantities across this data entry is '
                        f'greater than the sum of totals.'
                    )

            # Populate sets for checks across all data
            if party is None:
                partyless_substances.add(substance)
            else:
                partyful_substances.add(substance)

        # For substances that are only present in party-less rows, we check
        # that each row has totals >= quantities.
        completely_partyless_substances = partyless_substances.difference(
            partyful_substances
        )
        if completely_partyless_substances:
            completely_partyless_entries = (
                v for v in values
                if v.get('substance', None) in completely_partyless_substances
            )
            for entry in completely_partyless_entries:
                if (
                    get_fields_sum(entry, totals_fields) <
                    get_fields_sum(entry, quantity_fields)
                ):
                    raise ValidationError(
                        f'For {Substance.objects.filter(id=substance).first()},'
                        f' the sum of quantities across this data entry is'
                        f'greater than the sum of totals.'
                    )

        # Now check all substances that are present both in partyless and
        # partyful rows.
        related_substances = partyless_substances.intersection(
            partyful_substances
        )
        # Calculate the sums of quantities and totals for each substance
        if related_substances:
            sums_dictionary = {
                substance: {
                    'totals_sum': Decimal(0),
                    'quantities_sum': Decimal(0)
                }
                for substance in related_substances
            }
            # Only fetch data entries containing the related_substances
            related_entries = (
                v for v in values
                if v.get('substance', None) in related_substances
            )
            for entry in related_entries:
                substance = entry.get('substance', None)
                sums_dictionary[substance]['totals_sum'] += get_fields_sum(
                    entry, totals_fields
                )
                sums_dictionary[substance]['quantities_sum'] += get_fields_sum(
                    entry, quantity_fields
                )

            # And finally verify that, for each substance,
            # sum of totals > sum of quantities
            for id, sums in sums_dictionary.items():
                if sums['totals_sum'] < sums['quantities_sum']:
                    raise ValidationError(
                        f'For {Substance.objects.filter(id=id).first()}, the '
                        f'sum of quantities across all data entries is greater '
                        f'than the sum of totals.'
                    )

    class Meta:
        abstract = True


class BaseUses(models.Model):
    """
    This will be used as a base for data reporting models on import, export
    and production.
    This model contains the quantities and the decisions to use controlled
    substances.
    """

    quantity_critical_uses = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    decision_critical_uses = models.CharField(max_length=512, blank=True)

    quantity_essential_uses = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    decision_essential_uses = models.CharField(max_length=512, blank=True)

    quantity_high_ambient_temperature = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    decision_high_ambient_temperature = models.CharField(
        max_length=512, blank=True
    )

    quantity_laboratory_analytical_uses = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    decision_laboratory_analytical_uses = models.CharField(
        max_length=512, blank=True
    )

    quantity_process_agent_uses = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    decision_process_agent_uses = models.CharField(max_length=512, blank=True)

    quantity_quarantine_pre_shipment = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    decision_quarantine_pre_shipment = models.CharField(
        max_length=512, blank=True
    )

    quantity_other_uses = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    decision_other_uses = models.CharField(
        max_length=512, blank=True
    )

    class Meta:
        abstract = True


class Article7Questionnaire(ModifyPreventionMixin, models.Model):
    """
    Model for a simple Article 7 Questionnaire report row
    """
    # There can be only one questionnaire per submission
    submission = models.OneToOneField(
        Submission,
        related_name='article7questionnaire',
        on_delete=models.CASCADE
    )

    has_imports = models.NullBooleanField(
        help_text="If set to true it allows to complete imports data form."
    )

    has_exports = models.NullBooleanField(
        help_text="If set to true it allows to complete exports data form."
    )

    has_produced = models.NullBooleanField(
        help_text="If set to true it allows to complete productions data form."
    )

    has_destroyed = models.NullBooleanField(
        help_text="If set to true it allows to complete destructions data form."
    )

    has_nonparty = models.NullBooleanField(
        help_text="If set to true it allows to complete non-party trades data form."
    )

    has_emissions = models.NullBooleanField(
        help_text="If set to true it allows to complete emissions data form."
    )

    tracker = FieldTracker()

    @property
    def is_filled(self):
        return (
            self.has_imports is not None
            and self.has_exports is not None
            and self.has_produced is not None
            and self.has_destroyed is not None
            and self.has_nonparty is not None
            and self.has_emissions is not None
        )

    class Meta:
        db_table = 'reporting_art7_questionnaire'


class Article7Export(
    AggregationMixin, ModifyPreventionMixin, PolyolsMixin,
    BaseBlendCompositionReport, BaseImportExportReport, BaseUses
):
    """
    Model for a simple Article 7 data report on exports.

    All quantities expressed in metric tonnes.
    """

    # Quantity fields needed for blend-to-substance breakdown
    # quantity_polyols is intentionally not included.
    QUANTITY_FIELDS = [
        'quantity_critical_uses',
        'quantity_essential_uses',
        'quantity_high_ambient_temperature',
        'quantity_laboratory_analytical_uses',
        'quantity_process_agent_uses',
        'quantity_quarantine_pre_shipment',
        'quantity_total_new',
        'quantity_total_recovered',
        'quantity_feedstock',
        'quantity_other_uses',
    ]

    PARTY_FIELD = 'destination_party'

    # {aggregation_field: data_field_1, ...}
    AGGREGATION_MAPPING = {
        'quantity_total_new': 'export_new',
        'quantity_total_recovered': 'export_recovered',
        'quantity_feedstock': 'export_feedstock',
        'quantity_essential_uses': 'export_essential_uses',
        'quantity_quarantine_pre_shipment': 'export_quarantine',
        'quantity_process_agent_uses': 'export_process_agent'
    }

    # FieldTracker does not work on abstract models
    tracker = FieldTracker()

    destination_party = models.ForeignKey(
        Party,
        null=True,
        blank=True,
        related_name='article7exports_to',
        on_delete=models.PROTECT
    )

    class Meta(BaseReport.Meta):
        db_table = 'reporting_art7_exports'
        ordering = [
            'substance__sort_order', 'substance__substance_id',
            'blend__sort_order', 'destination_party__name',
        ]


class Article7Import(
    AggregationMixin, ModifyPreventionMixin, PolyolsMixin,
    BaseBlendCompositionReport, BaseImportExportReport, BaseUses
):
    """
    Model for a simple Article 7 data report on imports.

    All quantities expressed in metric tonnes.
    """

    # Quantity fields needed for blend-to-substance breakdown
    # quantity_polyols is intentionally not included.
    QUANTITY_FIELDS = [
        'quantity_critical_uses',
        'quantity_essential_uses',
        'quantity_high_ambient_temperature',
        'quantity_laboratory_analytical_uses',
        'quantity_process_agent_uses',
        'quantity_quarantine_pre_shipment',
        'quantity_total_new',
        'quantity_total_recovered',
        'quantity_feedstock',
        'quantity_other_uses',
    ]

    # {aggregation_field: data_field_1, ...}
    AGGREGATION_MAPPING = {
        'quantity_total_new': 'import_new',
        'quantity_total_recovered': 'import_recovered',
        'quantity_feedstock': 'import_feedstock',
        'quantity_essential_uses': 'import_essential_uses',
        'quantity_laboratory_analytical_uses': 'import_laboratory_uses',
        'quantity_quarantine_pre_shipment': 'import_quarantine',
        'quantity_process_agent_uses': 'import_process_agent'
    }

    PARTY_FIELD = 'source_party'

    # FieldTracker does not work on abstract models
    tracker = FieldTracker()

    source_party = models.ForeignKey(
        Party,
        null=True,
        blank=True,
        related_name='article7imports_from',
        on_delete=models.PROTECT
    )

    class Meta(BaseReport.Meta):
        db_table = 'reporting_art7_imports'
        ordering = [
            'substance__sort_order', 'substance__substance_id',
            'blend__sort_order', 'source_party__name',
        ]


class Article7Production(
    AggregationMixin, ModifyPreventionMixin,
    BaseReport, BaseUses
):
    """
    Model for a simple Article 7 data report on production.

    All quantities expressed in metric tonnes.
    """

    AGGREGATION_MAPPING = {
        'quantity_total_produced': 'production_all_new',
        'quantity_feedstock': 'production_feedstock',
        'quantity_essential_uses': 'production_essential_uses',
        'quantity_laboratory_analytical_uses': 'production_laboratory_analytical_uses',
        'quantity_article_5': 'production_article_5',
        'quantity_quarantine_pre_shipment': 'production_quarantine',
        'quantity_process_agent_uses': 'production_process_agent',
    }

    substance = models.ForeignKey(Substance, on_delete=models.PROTECT)

    quantity_total_produced = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    quantity_feedstock = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    quantity_for_destruction = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    # "Production for supply to Article 5 countries in accordance
    # with Articles 2A‑2H and 5"
    quantity_article_5 = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    tracker = FieldTracker()

    class Meta(BaseReport.Meta):
        db_table = 'reporting_art7_production'
        ordering = ['substance__sort_order', 'substance__substance_id']


class Article7Destruction(
    AggregationMixin, ModifyPreventionMixin,
    BaseBlendCompositionReport
):
    """
    Model for a simple Article 7 data report on destruction.

    All quantities expressed in metric tonnes.
    """

    # Needed by the BlendCompositionMixin
    tracker = FieldTracker()

    QUANTITY_FIELDS = [
        'quantity_destroyed',
    ]

    AGGREGATION_MAPPING = {
        'quantity_destroyed': 'destroyed',
    }

    quantity_destroyed = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    class Meta(BaseReport.Meta):
        db_table = 'reporting_art7_destruction'
        ordering = ['substance__sort_order', 'substance__substance_id']


class Article7NonPartyTrade(
    AggregationMixin, ModifyPreventionMixin,
    BaseBlendCompositionReport
):
    """
    Model for a simple Article 7 data report on non-party trade.

    All quantities expressed in metric tonnes.
    """

    tracker = FieldTracker()

    QUANTITY_FIELDS = [
        'quantity_import_new',
        'quantity_import_recovered',
        'quantity_export_new',
        'quantity_export_recovered',
    ]

    AGGREGATION_MAPPING = {
        'quantity_import_new': 'non_party_import',
        'quantity_import_recovered': 'non_party_import',
        'quantity_export_new': 'non_party_export',
        'quantity_export_recovered': 'non_party_export',
    }

    trade_party = models.ForeignKey(
        Party, blank=True, null=True, on_delete=models.PROTECT
    )

    quantity_import_new = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    quantity_import_recovered = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    quantity_export_new = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    quantity_export_recovered = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    class Meta(BaseReport.Meta):
        db_table = 'reporting_art7_npt'
        ordering = [
            'substance__sort_order', 'substance__substance_id',
            'blend__sort_order'
        ]

    def clean(self):
        if self.submission.schema_version != 'legacy' and not (
            self.quantity_import_new
            or self.quantity_import_recovered
            or self.quantity_export_new
            or self.quantity_export_recovered
        ):
            raise ValidationError(
                {
                    'quantity_fields': [_(
                        "At least one quantity field should be non-null."
                    )]
                }
            )
        # If it's a blend we skip the validation because we will check every
        # component substance particularly.
        # Don't do any checks for uncontrolled substances (group is None)
        if (
            not self.blend and self.substance and self.trade_party
            and self.submission.schema_version != 'legacy'
            and self.substance.group
        ):
            non_parties = self.substance.group.get_non_parties()
            if self.trade_party not in non_parties:
                raise ValidationError(
                    {
                        'trade_party': [_(
                            "You need to select a non-party, according to the "
                            "selected substance."
                        )]
                    }
                )

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Article7Emission(ModifyPreventionMixin, BaseReport):
    """
    Model for a simple Article 7 data report on HFC-23 emissions.

    All quantities expressed in metric tonnes.
    """

    facility_name = models.CharField(max_length=256, blank=True)

    # Total amount generated
    quantity_generated = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    # Amount generated and captured for all uses
    quantity_captured_all_uses = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    # Amount generated and captured for feedstock use in your country
    quantity_captured_feedstock = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    # Amount generated and captured for destruction
    quantity_captured_for_destruction = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    # Amount used for feedstock without prior capture
    quantity_feedstock = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    # Amount destroyed without prior capture
    quantity_destroyed = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )
    # Amount of generated emissions
    quantity_emitted = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    tracker = FieldTracker()

    @classmethod
    def validate_data(cls, submission):
        """
        Function for validation of all emissions data in a specific Art 7
        submission.
        Validation is performed right before the "submit" transition and
        checks that the facility_name and the quantity_emitted fields are
        filled.
        """
        for entry in cls.objects.filter(submission=submission):
            if entry.facility_name == '':
                raise ValidationError(
                    _(
                        'Please fill-in column Facility name or identifier (1) '
                        'for all Article 7 Emissions entries.'
                    )
                )
            if entry.quantity_emitted is None:
                raise ValidationError(
                    _(
                        'Please fill-in column Amount of generated emissions '
                        '(6) for all Article 7 Emissions entries.'
                    )
                )

    class Meta(BaseReport.Meta):
        db_table = 'reporting_art7_emissions'


class BaseHighAmbientTemperature(models.Model):

    quantity_msac = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True,
        help_text="Used in multi-split air conditioners"
    )
    quantity_sdac = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True,
        help_text="Used in split ducted air conditioners"
    )
    quantity_dcpac = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True,
        help_text="Used in ducted commercial packaged air conditioners",
    )

    class Meta:
        abstract = True


class HighAmbientTemperatureProduction(
    ModifyPreventionMixin, BaseReport, BaseHighAmbientTemperature
):
    """
    Production under the exemption for high-ambient-temperature parties
    """
    substance = models.ForeignKey(
        Substance, on_delete=models.PROTECT
    )

    tracker = FieldTracker()

    class Meta(BaseReport.Meta):
        db_table = 'reporting_hat_production'
        ordering = ['substance__sort_order', 'substance__substance_id']


class HighAmbientTemperatureImport(
    ModifyPreventionMixin, BaseBlendCompositionReport,
    BaseHighAmbientTemperature
):
    """
    Consumption (imports) under the exemption for high-ambient-temperature
    parties
    """

    # Needed because of BaseBlendCompositionReport
    tracker = FieldTracker()

    # Needed because of BaseBlendCompositionReport
    QUANTITY_FIELDS = [
        'quantity_msac',
        'quantity_sdac',
        'quantity_dcpac',
    ]

    class Meta(BaseReport.Meta):
        db_table = 'reporting_hat_import'
        ordering = [
            'substance__sort_order', 'substance__substance_id',
            'blend__sort_order'
        ]


class DataOther(ModifyPreventionMixin, BaseReport):
    """
    Model for Data Other reports.
    """

    tracker = FieldTracker()

    class Meta:
        db_table = 'reporting_other'


class RAFReport(ModifyPreventionMixin, BaseReport):
    """
    Model for RAF reports.

    These behave the same as Article 7 reports in regards to workflow, cloning,
    etc.
    """

    # These reports only refer to substances
    substance = models.ForeignKey(Substance, on_delete=models.PROTECT)

    # criticality is inferred from substance, only emergency flag is needed
    is_emergency = models.BooleanField(default=False)

    quantity_exempted = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    quantity_production = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    quantity_used = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    quantity_exported = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    quantity_destroyed = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    on_hand_start_year = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    tracker = FieldTracker()

    @property
    def quantity_imports(self):
        if self.imports:
            return sum([imp.get('quantity', 0) for imp in self.imports])
        return 0

    @property
    def is_critical(self):
        return self.substance.has_critical_uses

    def clone(self, new_instance=None):
        """
        Clone imports & use categories data for this model instance and attach
        them to "new_instance".
        """
        if not new_instance:
            return

        for related in ['imports', 'use_categories']:
            if not hasattr(self, related):
                continue
            for related_instance in getattr(self, related).all():
                attributes = model_to_dict(
                    related_instance,
                    exclude=[
                        'id', 'report_id', '_state', '_deferred_fields',
                        '_tracker', 'save', 'clean',
                    ]
                )
                attributes['report_id'] = new_instance.pk
                related_instance.__class__.objects.create(
                    **attributes
                )

    class Meta:
        db_table = 'reporting_raf'
        ordering = ['substance__sort_order', 'substance__substance_id']


class RAFReportUseCategory(ModifyPreventionMixin, models.Model):
    """
    Breakdown of `quantity_used` from a RAFReport, based on critical use
    category.

    Only allowed for critical use RAF reports.
    """
    report = models.ForeignKey(
        RAFReport,
        related_name='use_categories',
        on_delete=models.CASCADE
    )

    critical_use_category = models.ForeignKey(
        CriticalUseCategory,
        null=True,
        related_name='use_categories',
        on_delete=models.CASCADE
    )

    quantity = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)], blank=True, null=True
    )

    remarks = models.CharField(max_length=9999, blank=True)

    tracker = FieldTracker()

    @property
    def submission(self):
        """
        This is necessary for ModifyPreventionMixin to work properly.
        """
        return self.report.submission

    def clean(self):
        """
        Ensure that use category breakdowns are only saved for critical uses.
        """
        if not self.report.is_critical:
            raise ValidationError(
                _(
                    "Breakdown per critical use category can only be saved for "
                    "critical reports!"
                )
            )
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'reporting_raf_use_category'


class RAFImport(ModifyPreventionMixin, models.Model):
    """
    This is used for modelling multiple import quantities/country of origin
    pairs on each RAFReport row.

    Substance is the one from the RAFReport entry, so no need for it here.
    """
    report = models.ForeignKey(
        RAFReport, blank=False, null=False, on_delete=models.CASCADE,
        related_name='imports'
    )

    party = models.ForeignKey(
        Party,
        blank=True,
        null=True,
        on_delete=models.PROTECT
    )

    # This needs to have a quantity specified
    quantity = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)]
    )

    tracker = FieldTracker()

    @property
    def submission(self):
        """
        This is necessary for ModifyPreventionMixin to work properly.
        """
        return self.report.submission

    class Meta:
        db_table = 'reporting_raf_import'
