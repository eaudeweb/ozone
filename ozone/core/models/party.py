import datetime
import enum
from functools import lru_cache

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .legal import ReportingPeriod
from .meeting import Treaty
from .utils import RatificationTypes


__all__ = [
    'MDGRegion',
    'Region',
    'Subregion',
    'Party',
    'PartyHistory',
    'Language',
    'PartyRatification',
    'PartyDeclaration',
    'PartyType',
    'Language',
    'eu_party_id',
]


class MDGRegion(models.Model):
    """
    Another classification of countries.

    Seems a bit overkill to create a model for these, but it offers more
    flexibility and easier maintenance.
    """

    @enum.unique
    class IncomeTypes(enum.Enum):
        HIGH = 'High'
        LOW = 'Low'
        LOWER_MIDDLE = 'Lower-middle'
        UPPER_MIDDLE = 'Upper-middle'

    code = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=256, unique=True)

    parent_regions = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='child_regions',
    )

    income_type = models.CharField(
        max_length=128, choices=((x.value, x.name) for x in IncomeTypes),
        null=True, blank=True,
        help_text=", ".join(x.value for x in IncomeTypes)
    )

    remark = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return f'{self.name} ({self.code})'

    class Meta:
        ordering = ('name',)
        db_table = 'mdg_region'
        verbose_name = 'MDG region'


class PartyType(models.Model):
    """
    Party classification.

    Using a model instead of an enum allows for more flexibility.

    A5 = 'Article 5'
    A5G1 = 'Article 5 Group 1'
    A5G2 = 'Article 5 Group 2'
    NA5 = 'Non Article 5'
    NA5G1 = 'Non Article 5 Group 1'
    NA5G2 = 'Non Article 5 Group 2'
    """

    abbr = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=256, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'party_type'


class Region(models.Model):
    """
    Regions for reporting countries.

    Seems a bit overkill to create a model for these, but it offers more
    flexibility and easier maintenance.
    """

    abbr = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=256, unique=True)

    remark = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        db_table = 'region'

    @classmethod
    def get_real_regions(cls):
        return cls.objects.exclude(abbr='UNK')

class SubregionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'region',
        )

class Subregion(models.Model):
    """
    Sub-regions for reporting countries.

    Seems a bit overkill to create a model for these, but it offers more
    flexibility and easier maintenance.
    """

    objects = SubregionManager()

    abbr = models.CharField(max_length=32)
    name = models.CharField(max_length=256)

    region = models.ForeignKey(
        Region, related_name='subregions', on_delete=models.PROTECT
    )

    remark = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return f'{self.region.name} - subregion {self.name}'

    class Meta:
        unique_together = ('abbr', 'region')
        ordering = ('region', 'name')
        db_table = 'subregion'


class PartyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'parent_party', 'subregion', 'subregion__region',
        )

class Party(models.Model):
    """
    Reporting Party (generally country)
    """

    objects = PartyManager()

    name = models.CharField(max_length=256, unique=True)
    abbr = models.CharField(max_length=32, unique=True)

    # Subregion also includes region information
    subregion = models.ForeignKey(
        Subregion, related_name='parties', on_delete=models.PROTECT
    )

    # Some parties (e.g. EU) can encompass several other full-featured parties
    # TODO: come up with better name (and better related_name)
    parent_party = models.ForeignKey(
        'self',
        related_name='child_parties',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    remark = models.CharField(max_length=9999, blank=True)

    mdg_region = models.ForeignKey(
        MDGRegion,
        null=True, blank=True,
        related_name='party',
        on_delete=models.PROTECT
    )

    iso_alpha3_code = models.CharField(max_length=3, blank=True)
    abbr_alt = models.CharField(max_length=6, blank=True)
    name_alt = models.CharField(max_length=256, blank=True)

    # Date when Vienna Convention was signed
    sign_date_vc = models.DateField(null=True, blank=True)
    # Date when Montreal Protocol was signed
    sign_date_mp = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(
        default=True,
        help_text="Indicates whether the party can submit new reports."
                  "Only necessary for backwards compatibility"
    )

    @property
    def is_eu(self):
        return self.abbr == 'EU'

    @classmethod
    def get_main_parties(cls):
        return cls.objects.filter(
            id=models.F('parent_party_id'),
            is_active=True,
        )

    @classmethod
    def get_eu_members(cls):
        """ Returns the current EU member states
        """
        return Party.get_eu_members_at(ReportingPeriod.get_current_period())

    @classmethod
    def get_eu_members_at(cls, reporting_period):
        """ Returns the EU member states at specified time
        """
        return cls.objects.filter(
            history__is_eu_member=True,
            history__reporting_period=reporting_period,
            is_active=True,
        )

    def is_eu_member_at(self, reporting_period):
        ph = PartyHistory.objects.filter(
            party=self,
            reporting_period=reporting_period
        ).first()
        if ph and ph.is_eu_member:
            return True
        return False

    def is_art5_at(self, reporting_period):
        ph = PartyHistory.objects.filter(
            party=self,
            reporting_period=reporting_period
        ).first()
        # TODO: remove field from model and use party type?
        if ph and ph.is_article5:
            return True
        return False

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'parties'
        ordering = ('name',)
        db_table = 'party'


class PartyGroup(models.Model):
    """
    Used for modelling access for UNEP CAP users.
    """
    name = models.CharField(max_length=256)

    parties = models.ManyToManyField(Party)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


def current_year():
    return datetime.date.today().year


def max_value_current_year(value):
    """
    Wrapping the MaxValueValidator in a function avoids a new migration
    every year.
    """
    return MaxValueValidator(current_year())(value)


class PartyHistoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'party', 'reporting_period', 'party_type'
        )


class PartyHistory(models.Model):
    """
    Detailed Party information, per year (population, flags etc) can change
    based on the specified period.
    """

    objects = PartyHistoryManager()

    party = models.ForeignKey(
        Party, related_name='history', on_delete=models.PROTECT
    )

    # This will still require form choices to be generated based on the same
    # start year.
    reporting_period = models.ForeignKey(
        ReportingPeriod,
        related_name='party_histories',
        on_delete=models.PROTECT
    )

    party_type = models.ForeignKey(
        PartyType,
        related_name='party_histories',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    population = models.IntegerField()

    is_high_ambient_temperature = models.BooleanField()

    # Reflects EU membership for that specific year
    is_eu_member = models.BooleanField()

    # Reflects Country Economy In Transition for that specific year
    is_ceit = models.BooleanField()

    is_article5 = models.BooleanField()

    # Remarks
    remark = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return f'{self.party.name} - {self.reporting_period}'

    def is_group2(self):
        return self.party_type.abbr.endswith('G2')

    class Meta:
        unique_together = ('party', 'reporting_period')
        ordering = ('party', 'reporting_period')
        verbose_name_plural = 'parties history'
        db_table = 'party_history'


class PartyRatification(models.Model):
    """
    Ratification information of all treaties and amendments, for each party.
    """

    party = models.ForeignKey(
        Party, related_name='ratifications', on_delete=models.PROTECT
    )

    treaty = models.ForeignKey(
        Treaty, related_name='ratifications', on_delete=models.PROTECT
    )

    ratification_type = models.CharField(
        max_length=40,
        choices=((s.value, s.name) for s in RatificationTypes),
        blank=True
    )

    ratification_date = models.DateField()

    entry_into_force_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'party_ratification'


class PartyDeclaration(models.Model):
    """
    Associated notes (HTML text) related to ratification of VC and MP.
    """

    party = models.ForeignKey(
        Party, related_name='declarations', on_delete=models.PROTECT
    )

    declaration = models.TextField()

    def __str__(self):
        return f'{self.party.name} (declaration)'

    class Meta:
        db_table = 'party_declaration'


class Language(models.Model):
    """
    Model for languages used by Ozone Secretariat.
    """

    # This is a sane default (English language) based on the current fixtures
    DEFAULT_LANGUAGE_ID = 3

    language_id = models.CharField(max_length=16, unique=True)

    iso = models.CharField(max_length=5, unique=True)

    name = models.CharField(max_length=64, unique=True)

    remark = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        db_table = 'language'


@lru_cache(maxsize=1)
def eu_party_id():
    return Party.objects.get(abbr='EU').id
