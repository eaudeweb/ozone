from urllib.parse import quote

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.functional import cached_property
from django.urls.base import reverse
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _

from .legal import ReportingPeriod
from .party import Party
from .reporting import Submission
from .substance import Substance
from .meeting import Decision
from .utils import DECIMAL_FIELD_DECIMALS, DECIMAL_FIELD_DIGITS

__all__ = [
    'ProcessAgentDecision',
    'ProcessAgentApplication',
    'ProcessAgentUsesReported',
    'ProcessAgentEmissionLimit',
]


class ProcessAgentDecisionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'decision',
        )


class ProcessAgentDecision(models.Model):
    """
    Process Agents related decisions
    """
    objects = ProcessAgentDecisionManager()

    decision = models.ForeignKey(
        Decision,
        related_name='pa_decisions',
        on_delete=models.PROTECT
    )

    application_validity_start_date = models.DateField(null=True)
    application_validity_end_date = models.DateField(null=True)

    emit_limits_validity_start_date = models.DateField(null=True)
    emit_limits_validity_end_date = models.DateField(null=True)

    @cached_property
    def refers_to_applications(self):
        return (
            self.application_validity_start_date is not None
            or self.application_validity_end_date is not None
        )

    @cached_property
    def refers_to_emit_limits(self):
        return(
            self.emit_limits_validity_start_date is not None
            or self.emit_limits_validity_end_date is not None
        )

    def __str__(self):
        return f'Decision {self.decision.decision_id} ('\
            f'{self.application_validity_start_date}'\
            f' - {self.application_validity_end_date})'

    class Meta:
        verbose_name_plural = 'process agent decisions'
        db_table = 'pa_decision'


class ProcessAgentApplicationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'substance', 'decision', 'decision__decision',
        )


class ProcessAgentApplication(models.Model):
    """
    Applications of controlled substances as process agents, as approved
    in table A of decision X/14 and updated periodically by the Meeting of the
    Parties.
    """

    objects = ProcessAgentApplicationManager()

    decision = models.ForeignKey(
        ProcessAgentDecision,
        null=True,
        blank=True,
        related_name='pa_applications',
        on_delete=models.PROTECT
    )

    counter = models.PositiveIntegerField()

    substance = models.ForeignKey(Substance, on_delete=models.PROTECT)

    application = models.CharField(max_length=256)

    remark = models.CharField(max_length=9999, blank=True)

    @property
    def start_date(self):
        return self.decision.application_validity_start_date

    @property
    def end_date(self):
        return self.decision.application_validity_end_date

    def __str__(self):
        return f'{self.counter} - {self.substance} - ' \
               f'{self.application} | {self.decision}'

    class Meta:
        db_table = 'pa_application'


class ProcessAgentUsesReportedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'submission', 'party', 'reporting_period',
            'decision', 'decision__decision',
            'application', 'application__substance',
        )


class ProcessAgentUsesReported(models.Model):
    """
    Records information on process agent uses reported.
    """
    UNITS = (
        ('MT', 'Metric Tonnes'),
        ('ODP tonnes', 'ODP Tonnes')
    )

    objects = ProcessAgentUsesReportedManager()

    submission = models.ForeignKey(
        Submission,
        null=True,
        blank=True,
        related_name='pa_uses_reported',
        on_delete=models.PROTECT
    )

    party = models.ForeignKey(
        Party,
        null=True,
        blank=True,
        related_name='pa_uses_reported',
        on_delete=models.PROTECT
    )

    reporting_period = models.ForeignKey(
        ReportingPeriod,
        null=True,
        blank=True,
        related_name='pa_uses_reported',
        on_delete=models.PROTECT
    )

    decision = models.ForeignKey(
        ProcessAgentDecision,
        related_name='pa_uses_reported',
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    application = models.ForeignKey(
        ProcessAgentApplication,
        related_name='pa_uses_reported',
        blank=True,
        null=True,
        on_delete=models.PROTECT
    )

    contain_technologies = models.TextField(blank=True)

    makeup_quantity = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)],
        null=True,
        blank=True
    )

    emissions = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)],
        null=True,
        blank=True
    )

    units = models.CharField(
        max_length=64,
        choices=UNITS,
        null=True,
        blank=True
    )

    remark = models.CharField(max_length=9999, blank=True)

    @property
    def api_submission_uri(self):
        if not self.submission:
            return ''

        domain = Site.objects.get_current().domain
        absolute_url = reverse(
            'core:submission-detail', kwargs={'pk': self.submission.id}
        )
        return f'https://{domain}{absolute_url}'

    @property
    def submission_uri(self):
        if not self.submission:
            return ''

        domain = Site.objects.get_current().domain

        # This hardcodes a URL in the frontend but there's no other option
        return (
            f'https://{domain}'
            f'/reporting/submission/procagent?submission='
            f'{quote(self.api_submission_uri, safe="")}'
        )

    def clean(self):
        # If all three fields are populated, they must be consistent
        if self.party and self.reporting_period and self.submission:
            if self.submission.party != self.party:
                raise ValidationError(
                    {
                        'party': [_(
                            "Party does not correspond to submission's party"
                        )]
                    }
                )
            if self.submission.reporting_period != self.reporting_period:
                raise ValidationError(
                    {
                        'reporting_period': [_(
                            "Reporting period does not correspond to "
                            "submission's reporting period"
                        )]
                    }
                )
        super().clean()

    def save(self, *args, **kwargs):
        """
        Overriding to ensure consistency between submission and party/period
        """
        self.full_clean()

        if self.party is None and self.submission is not None:
            self.party = self.submission.party
        if self.reporting_period is None and self.submission is not None:
            self.reporting_period = self.submission.reporting_period

        return super().save(*args, **kwargs)

    def __str__(self):
        party = self.party if self.party else \
            self.submission.party if self.submission else 'Unknown'
        period = self.reporting_period if self.reporting_period else \
            self.submission.reporting_period.name if self.submission else \
            'Unknown'

        if self.application:
            return (
                f'{party} - Process agent reported use of '
                f'{self.application.substance} for {period}'
            )
        return f'{party} - Process agent reported use for {period}'

    class Meta:
        verbose_name_plural = 'process agent uses reported'
        db_table = 'pa_uses_reported'


class ProcessAgentEmissionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'decision', 'decision__decision', 'party'
        )


class ProcessAgentEmissionLimit(models.Model):
    """
    Emission limits for process agent uses, for non-Article 5 parties.
    """
    objects = ProcessAgentEmissionManager()

    decision = models.ForeignKey(
        ProcessAgentDecision,
        null=True,
        blank=True,
        related_name='pa_emission_limits',
        on_delete=models.PROTECT
    )

    party = models.ForeignKey(
        Party,
        related_name='process_agent_emission_limits',
        on_delete=models.PROTECT
    )

    makeup_consumption = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)]
    )

    max_emissions = models.DecimalField(
        max_digits=DECIMAL_FIELD_DIGITS, decimal_places=DECIMAL_FIELD_DECIMALS,
        validators=[MinValueValidator(0.0)]
    )

    remark = models.CharField(max_length=9999, blank=True)

    @property
    def start_date(self):
        return self.decision.emit_limits_validity_start_date

    @property
    def end_date(self):
        return self.decision.emit_limits_validity_end_date

    class Meta:
        db_table = 'limit_pa_emission'
