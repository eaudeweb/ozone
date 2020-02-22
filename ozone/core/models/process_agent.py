from django.core.validators import MinValueValidator
from django.db import models
from django.utils.functional import cached_property

from .party import Party
from .reporting import Submission
from .substance import Substance
from .meeting import Decision
from .utils import DECIMAL_FIELD_DECIMALS, DECIMAL_FIELD_DIGITS

__all__ = [
    'ProcessAgentDecision',
    'ProcessAgentContainTechnology',
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


class ProcessAgentContainTechnology(models.Model):
    """
    Reported containment technologies
    """

    description = models.CharField(max_length=9999)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name_plural = 'process agent contain technologies'
        db_table = 'pa_contain_technology'


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
        return f'{self.substance} - {self.application} ({self.decision})'

    class Meta:
        db_table = 'pa_application'


class ProcessAgentUsesReportedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'submission', 'submission__party', 'submission__reporting_period',
            'decision', 'decision__decision',
            'application', 'application__substance',
        ).prefetch_related(
            'contain_technologies',
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

    contain_technologies = models.ManyToManyField(
        ProcessAgentContainTechnology,
        blank=True,
    )

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

    def __str__(self):
        if self.application:
            return (
                f'{self.submission.party} - Process agent reported use of '
                f'{self.application.substance} for '
                f'{self.submission.reporting_period.name}'
            )
        return (
            f'{self.submission.party} - Process agent reported use for '
            f'{self.submission.reporting_period.name}'
        )

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
