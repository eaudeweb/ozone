import enum
import os

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from . import (
    Obligation,
    PartyRatification,
    Party,
    ReportingPeriod,
    Submission,
)


@enum.unique
class URLTypes(enum.Enum):
    SUBMISSION = 'Submission'
    PUBLICATION = 'Publication'


class MultilateralFundManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'party'
        )


class MultilateralFund(models.Model):
    objects = MultilateralFundManager()

    party = models.ForeignKey(
        Party, related_name='multilateral_funds', on_delete=models.PROTECT
    )
    funds_approved = models.IntegerField()
    funds_disbursed = models.IntegerField()
    date_approved = models.DateField(null=True)
    date_disbursed = models.DateField(null=True)

    class Meta:
        db_table = "multilateral_fund"
        ordering = ('party__name',)


class ORMReportManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'party', 'reporting_period'
        )


class ORMReport(models.Model):
    objects = ORMReportManager()

    party = models.ForeignKey(
        Party, related_name='orm_reports', on_delete=models.PROTECT
    )
    meeting = models.CharField(max_length=64, blank=True)
    reporting_period = models.ForeignKey(
        ReportingPeriod,
        related_name='orm_reports',
        on_delete=models.PROTECT
    )
    description = models.CharField(max_length=9999, blank=True)
    url = models.URLField('URL', max_length=1024, null=True, blank=True)

    class Meta:
        db_table = "orm_report"
        verbose_name = "ORM report"
        ordering = ('party__name', '-reporting_period__end_date')


class IllegalTradeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'party'
        )


class IllegalTrade(models.Model):
    objects = IllegalTradeManager()

    party = models.ForeignKey(
        Party, related_name='illegal_trades', on_delete=models.PROTECT
    )
    submission_id = models.IntegerField(blank=True, null=True)
    ordering_id = models.IntegerField(default=0)
    submission_year = models.CharField(max_length=256, blank=True)
    seizure_date_year = models.CharField(max_length=256, blank=True)
    substances_traded = models.CharField(max_length=256, blank=True)
    volume = models.CharField(max_length=256, blank=True)
    importing_exporting_country = models.CharField(max_length=256, blank=True)
    illegal_trade_details = models.CharField(max_length=9999, blank=True)
    action_taken = models.CharField(max_length=9999, blank=True)
    remarks = models.CharField(max_length=9999, blank=True)
    reported_by = models.CharField(max_length=9999, blank=True)

    class Meta:
        db_table = "illegal_trade"
        ordering = ('ordering_id',)


class ReclamationFacilityManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'party'
        )


class ReclamationFacility(models.Model):
    objects = ReclamationFacilityManager()

    party = models.ForeignKey(
        Party, related_name='reclamation_facilities', on_delete=models.PROTECT
    )
    date_reported = models.DateField(null=True)
    name = models.CharField(max_length=256, blank=True)
    address = models.CharField(max_length=512, blank=True)
    reclaimed_substances = models.CharField(max_length=512, blank=True)
    capacity = models.CharField(max_length=64, blank=True)
    remarks = models.CharField(max_length=9999, blank=True)

    class Meta:
        db_table = "reclamation_facility"
        verbose_name_plural = "reclamation facilities"
        ordering = ('party__name', '-date_reported')


def get_other_country_profile_upload_to(instance, filename):
    """
    This determines the location at which files for OtherCountryProfileData
    will be saved.
    """
    return os.path.join(
        'public/other-country-profile-data/',
        instance.reporting_period.name,
        instance.party.abbr,
        os.path.basename(filename)
    )


class OtherCountryProfileDataManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'party', 'reporting_period', 'obligation', 'submission'
        )


class OtherCountryProfileData(models.Model):
    objects = OtherCountryProfileDataManager()

    party = models.ForeignKey(
        Party,
        related_name='other_country_profile_data',
        on_delete=models.PROTECT
    )
    reporting_period = models.ForeignKey(
        ReportingPeriod,
        related_name='other_country_profile_data',
        on_delete=models.PROTECT
    )
    obligation = models.ForeignKey(
        Obligation,
        related_name='other_country_profile_data',
        on_delete=models.PROTECT
    )
    submission = models.ForeignKey(
        Submission,
        related_name='other_country_profile_data',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    description = models.CharField(max_length=9999, blank=True)
    file = models.FileField(
        upload_to=get_other_country_profile_upload_to, blank=True, null=True
    )
    url = models.URLField(
        'URL', max_length=1024, null=True, blank=True
    )
    url_type = models.CharField(
        max_length=64, choices=((s.value, s.name) for s in URLTypes),
        null=True,
    )
    remarks_secretariat = models.CharField(max_length=9999, blank=True)

    def clean(self):
        if self.submission:
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
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        db_table = "other_country_profile_data"
        verbose_name_plural = "other country profile data"
        ordering = ("party__name", "-reporting_period__end_date")


class WebsiteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'party'
        )


def get_website_upload_to(instance, filename):
    """
    This determines the location at which files for Website will be saved.
    """
    return os.path.join(
        'public/website/',
        instance.party.abbr,
        os.path.basename(filename)
    )


class Website(models.Model):
    objects = WebsiteManager()

    party = models.ForeignKey(
        Party, related_name='websites', on_delete=models.PROTECT
    )

    file = models.FileField(
        upload_to=get_website_upload_to, blank=True, null=True
    )

    url = models.URLField(
        'URL', max_length=1024, null=True, blank=True
    )
    description = models.CharField(max_length=9999, blank=True)
    is_url_broken = models.BooleanField(default=False)

    ordering_id = models.IntegerField(default=0)

    class Meta:
        db_table = "website"
        ordering = ("party__name",)


class LicensingSystemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'party', 'submission'
        ).prefetch_related(
            'files', 'urls'
        )


class LicensingSystem(models.Model):
    objects = LicensingSystemManager()

    party = models.ForeignKey(
        Party, related_name='licensing_systems', on_delete=models.PROTECT
    )
    has_ods = models.BooleanField(default=False)
    date_reported_ods = models.DateField(null=True, blank=True)
    has_hfc = models.BooleanField(default=False)
    date_reported_hfc = models.DateField(null=True, blank=True)

    remarks = models.CharField(max_length=9999, blank=True)

    submission = models.ForeignKey(
        Submission,
        related_name='licensing_systems',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    @property
    def date_kigali_ratification(self):
        kigali_ratification = PartyRatification.objects.filter(
            treaty__treaty_id='KA', party=self.party
        ).first()
        if kigali_ratification is not None:
            return kigali_ratification.ratification_date
        return None

    class Meta:
        db_table = "licensing_system"
        ordering = ("party__name", "-date_reported_hfc", "-date_reported_ods")


def get_licensing_system_file_upload_to(instance, filename):
    """
    This determines the location at which files for LicensingSystemFile
    will be saved.
    """
    return os.path.join(
        'public/other-country-profile-data/',
        instance.licensing_system.party.abbr,
        os.path.basename(filename)
    )


class LicensingSystemFileManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'licensing_system', 'licensing_system__party'
        )


class LicensingSystemFile(models.Model):
    objects = LicensingSystemFileManager()

    licensing_system = models.ForeignKey(
        LicensingSystem, related_name='files', on_delete=models.CASCADE
    )
    file = models.FileField(upload_to=get_licensing_system_file_upload_to)
    title = models.CharField(max_length=256)

    class Meta:
        db_table = "licensing_system_file"


class LicensingSystemURL(models.Model):
    licensing_system = models.ForeignKey(
        LicensingSystem, related_name='urls', on_delete=models.CASCADE
    )
    url = models.URLField('URL', max_length=1024)
    title = models.CharField(max_length=256)

    class Meta:
        db_table = "licensing_system_url"


class FocalPointManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'party', 'submission'
        )


class FocalPoint(models.Model):
    objects = FocalPointManager()

    party = models.ForeignKey(
        Party, related_name='focal_points', on_delete=models.PROTECT
    )
    name = models.CharField(max_length=256, blank=True)
    designation = models.CharField(max_length=512, blank=True)
    tel = models.CharField(max_length=128, blank=True)
    email = models.CharField(max_length=256, blank=True)
    fax = models.CharField(max_length=256, blank=True)

    organisation = models.CharField(max_length=9999, blank=True)
    city = models.CharField(max_length=9999, blank=True)
    country = models.CharField(max_length=9999, blank=True)
    address = models.CharField(max_length=9999, blank=True)

    is_licensing_system = models.BooleanField(default=False)
    is_national = models.BooleanField(default=False)

    submission = models.ForeignKey(
        Submission,
        related_name='focal_points',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    ordering_id = models.IntegerField(default=0)

    class Meta:
        db_table = "focal_point"
        ordering = ('ordering_id',)
