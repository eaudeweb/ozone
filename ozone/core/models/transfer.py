from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .aggregation import ProdCons, ProdConsMT
from .legal import ReportingPeriod
from .party import Party
from .reporting import Submission, ObligationTypes
from .substance import Substance
from .utils import (
    decimal_zero_if_none, DECIMAL_FIELD_DIGITS, DECIMAL_FIELD_DECIMALS
)

from model_utils import FieldTracker


__all__ = [
    'Transfer',
]


class Transfer(models.Model):
    """
    Records amounts of production rights transferred between Parties.
    """
    TRANSFER_TYPE = (
        ('P', 'Production'),
        ('C', 'Consumption')
    )
    transfer_type = models.CharField(
        max_length=1,
        choices=TRANSFER_TYPE
    )

    source_party = models.ForeignKey(
        Party, related_name='sent_transfers', on_delete=models.PROTECT
    )

    destination_party = models.ForeignKey(
        Party, related_name='received_transfers', on_delete=models.PROTECT
    )

    reporting_period = models.ForeignKey(
        ReportingPeriod, related_name='transfers', on_delete=models.PROTECT
    )

    substance = models.ForeignKey(
        Substance, on_delete=models.PROTECT
    )

    transferred_amount = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)]
    )

    is_basic_domestic_need = models.BooleanField(default=False)

    # Related submissions.
    # This is the submission recorded by the source side
    source_party_submission = models.ForeignKey(
        Submission,
        blank=True,
        null=True,
        related_name='transfers_from',
        on_delete=models.PROTECT,
    )
    # This is the submission recorded by the destination side
    destination_party_submission = models.ForeignKey(
        Submission,
        blank=True,
        null=True,
        related_name='transfers_to',
        on_delete=models.PROTECT,
    )

    tracker = FieldTracker()

    @staticmethod
    def get_aggregation_classes(substance, source_party, reporting_period):
        potential = 1
        if substance.group.is_gwp:
            potential = substance.gwp
        elif substance.group.is_odp:
            potential = substance.odp

        data = [
            (
                ProdCons,
                {
                    'party': source_party,
                    'reporting_period': reporting_period,
                    'group': substance.group,
                },
                potential
            ),
            (
                ProdConsMT,
                {
                    'party': source_party,
                    'reporting_period': reporting_period,
                    'substance': substance,
                },
                1
            )
        ]
        return list(data)

    def populate_aggregated_data(self):
        """
        Populates relevant fields in aggregation tables based on this transfer.
        """
        for klass, params, potential in self.__class__.get_aggregation_classes(
            self.substance, self.source_party, self.reporting_period
        ):
            # Populate aggregation data
            aggregation, created = klass.objects.get_or_create(**params)
            to_add = decimal_zero_if_none(self.transferred_amount) * \
                     decimal_zero_if_none(potential)
            if self.transfer_type == 'P':
                existing_value = decimal_zero_if_none(aggregation.prod_transfer)
                aggregation.prod_transfer = existing_value + to_add
            elif self.transfer_type == 'C':
                existing_value = decimal_zero_if_none(aggregation.cons_transfer)
                aggregation.cons_transfer = existing_value + to_add

            # Populate submissions list
            obligation_type = ObligationTypes.TRANSFER.value
            if obligation_type in aggregation.submissions:
                submissions_set = set(aggregation.submissions[obligation_type])
            else:
                submissions_set = set()
            if self.source_party_submission:
                submissions_set.add(self.source_party_submission.id)
            if self.destination_party_submission:
                submissions_set.add(self.destination_party_submission.id)
            aggregation.submissions[obligation_type] = list(submissions_set)

            aggregation.save()

    def clear_aggregated_data(self, use_old_values=False):
        if use_old_values:
            substance = Substance.objects.filter(
                id=self.tracker.previous('substance_id')
            ).first()
            if not substance:
                # nothing in self.tracker.previous
                return
            amount = self.tracker.previous('transferred_amount')
            source_party = Party.objects.get(
                id=self.tracker.previous('source_party_id')
            )
            reporting_period = ReportingPeriod.objects.get(
                id=self.tracker.previous('reporting_period_id')
            )
            transfer_type = self.tracker.previous('transfer_type')
            source_party_submission = Submission.objects.filter(
                id=self.tracker.previous('source_party_submission_id')
            ).first()
            destination_party_submission = Submission.objects.filter(
                id=self.tracker.previous('destination_party_submission_id')
            ).first()
        else:
            substance = self.substance
            amount = self.transferred_amount
            source_party = self.source_party
            reporting_period = self.reporting_period
            transfer_type = self.transfer_type
            source_party_submission = self.source_party_submission
            destination_party_submission = self.destination_party_submission

        for klass, params, potential in self.__class__.get_aggregation_classes(
            substance, source_party, reporting_period
        ):
            aggregation = klass.objects.filter(**params).first()
            if not aggregation:
                continue

            # Delete the transfer data from the aggregation
            to_subtract = (
                decimal_zero_if_none(amount) *
                decimal_zero_if_none(potential)
            )
            if transfer_type == 'P':
                existing_value = decimal_zero_if_none(aggregation.prod_transfer)
                aggregation.prod_transfer = existing_value - to_subtract
            elif transfer_type == 'C':
                existing_value = decimal_zero_if_none(aggregation.cons_transfer)
                aggregation.cons_transfer = existing_value - to_subtract

            # Clear submissions from list
            obligation_type = ObligationTypes.TRANSFER.value
            if obligation_type in aggregation.submissions:
                submissions_set = set(aggregation.submissions[obligation_type])
            else:
                submissions_set = set()
            if (
                source_party_submission
                and source_party_submission.id in submissions_set
            ):
                submissions_set.remove(source_party_submission.id)
            if (
                destination_party_submission
                and destination_party_submission.id in submissions_set
            ):
                submissions_set.remove(destination_party_submission.id)
            aggregation.submissions[obligation_type] = list(submissions_set)

            aggregation.save()

            # Delete empty aggregations
            if aggregation.is_empty():
                aggregation.delete()

    def clean(self):
        if self.destination_party_submission:
            if self.destination_party_submission.party != self.destination_party:
                raise ValidationError(
                    {
                        'destination_party_submission': [_(
                            "Destination party submission should belong to the "
                            "transfer's destination party."
                        )],
                    }
                )
            if self.destination_party_submission.obligation.obligation_type != ObligationTypes.TRANSFER.value:
                raise ValidationError(
                    {
                        'destination_party_submission': [_(
                            "Destination party submission should be a Transfer "
                            "submission."
                        )],
                    }
                )

        if self.source_party_submission:
            if self.source_party_submission.party != self.source_party:
                raise ValidationError(
                    {
                        'source_party_submission': [_(
                            "Source party submission should belong to the "
                            "transfer's source party"
                        )],
                    }
                )
            if self.source_party_submission.obligation.obligation_type != ObligationTypes.TRANSFER.value:
                raise ValidationError(
                    {
                        'source_party_submission': [_(
                            "Source party submission should be a Transfer "
                            "submission."
                        )],
                    }
                )

            if (
                self.source_party and self.destination_party
                and self.source_party == self.destination_party
            ):
                raise ValidationError(
                    {
                        'source_party': [_(
                            "Source party should be different from destination "
                            "party."
                        )],
                    }
                )

            if (
                self.source_party_submission
                and self.destination_party_submission
                and self.source_party_submission == self.destination_party_submission
            ):
                raise ValidationError(
                    {
                        'source_party': [_(
                            "Source party submission should be different from "
                            "destination party submission."
                        )],
                    }
                )

        super().clean()

    def delete(self, *args, **kwargs):
        self.clear_aggregated_data(use_old_values=False)

        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.pk or not kwargs.get('force_insert', False):
            # If this is an edit, delete anything related to the old values
            self.clear_aggregated_data(use_old_values=True)

        # Populate aggregation data using current values
        self.populate_aggregated_data()

        super().save(*args, **kwargs)

    class Meta:
        db_table = 'reporting_transfer'
