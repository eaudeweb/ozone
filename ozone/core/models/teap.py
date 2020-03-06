from django.db import models

from .legal import ReportingPeriod
from .meeting import Decision

__all__ = [
    'TEAPReportType', 'TEAPReport', 'TEAPIndicativeNumberOfReports'
]


class TEAPReportType(models.Model):

    sort_order = models.IntegerField(null=True, default=0)

    name = models.CharField(
        max_length=256, unique=True, null=False, blank=False
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'teap_report_type'
        verbose_name_plural = 'TEAP report types'
        ordering = ('sort_order',)


class TEAPReportManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'reporting_period', 'report_type', 'decision'
        )


class TEAPReport(models.Model):

    objects = TEAPReportManager()

    sort_order = models.IntegerField(null=True, default=0)

    reporting_period = models.ForeignKey(
        ReportingPeriod,
        related_name='teap_reports',
        on_delete=models.PROTECT
    )

    report_type = models.ForeignKey(
        TEAPReportType,
        related_name='teap_reports',
        on_delete=models.PROTECT
    )

    decision = models.ForeignKey(
        Decision,
        null=True,
        blank=True,
        related_name='teap_reports',
        on_delete=models.PROTECT
    )

    issue = models.CharField(max_length=256)

    request_by_parties = models.CharField(max_length=1024)

    report_to_be_produced = models.CharField(max_length=256, blank=True)

    # Remarks
    remark_issue_type = models.CharField(max_length=512, blank=True)
    remark_issue = models.CharField(max_length=512, blank=True)
    remark_request = models.CharField(max_length=512, blank=True)
    remark_report = models.CharField(max_length=512, blank=True)

    def __str__(self):
        return f'{self.reporting_period.name}/{self.report_type}/{self.issue}/{self.report_to_be_produced}'

    class Meta:
        db_table = 'teap_report'
        verbose_name = 'TEAP report'
        verbose_name_plural = 'TEAP reports'
        ordering = ('reporting_period__name', 'report_type__sort_order', 'sort_order', )


class TEAPIndicativeNumberOfReports(models.Model):

    reporting_period = models.ForeignKey(
        ReportingPeriod,
        on_delete=models.PROTECT
    )

    number_of_reports = models.CharField(max_length=256)

    remarks = models.CharField(max_length=512, blank=True)

    class Meta:
        db_table = 'teap_indicative_number_of_reports'
        verbose_name_plural = 'TEAP indicative numbers of reports'
        ordering = ('-reporting_period', )
