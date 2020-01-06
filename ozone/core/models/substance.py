import datetime
import enum

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from ..exceptions import MethodNotAllowed
from .meeting import Treaty
from .party import Party, PartyRatification

__all__ = [
    'Annex',
    'Group',
    'UsesType',
    'Substance',
    'Blend',
    'BlendComponent',
]


class Annex(models.Model):
    """
    Substance Annex information
    """
    annex_id = models.CharField(max_length=16, unique=True)

    name = models.CharField(max_length=64, unique=True)

    description = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'annexes'
        ordering = ('name',)
        db_table = 'annex'


class GroupManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'annex',
        )


class Group(models.Model):
    """
    Substance Group information
    """

    objects = GroupManager()

    group_id = models.CharField(max_length=16, unique=True)

    annex = models.ForeignKey(
        Annex, related_name='groups', on_delete=models.PROTECT
    )

    name = models.CharField(max_length=64, unique=True, default="")
    name_alt = models.CharField(
        max_length=64,
        blank=True, null=True,
        verbose_name=_("alternate name"),
    )

    description = models.CharField(max_length=256)
    description_alt = models.CharField(
        max_length=1024,
        blank=True, null=True,
        verbose_name=_("alternate description"),
    )

    control_treaty = models.ForeignKey(
        Treaty,
        related_name='control_substance_groups',
        on_delete=models.PROTECT
    )
    report_treaty = models.ForeignKey(
        Treaty,
        related_name='report_substance_groups',
        on_delete=models.PROTECT
    )

    is_odp = models.BooleanField(default=True)
    is_gwp = models.BooleanField(default=False)

    phase_out_year_article_5 = models.DateField(blank=True, null=True)
    phase_out_year_non_article_5 = models.DateField(blank=True, null=True)

    def get_signing_parties_ids(self, reporting_period=None):
        """
        Get list of id's of parties that had ratified, at the start of the given
        reporting_period, the control treaty for this group.
        """
        if not reporting_period:
            max_date = datetime.date.today()
        else:
            max_date = reporting_period.start_date

        # Get all the Parties that had ratified the control treaty at that date
        current_ratifications = PartyRatification.objects.filter(
            entry_into_force_date__lte=max_date,
            treaty=self.control_treaty
        )
        return set(
            current_ratifications.values_list('party__id', flat=True)
        )

    def get_parties(self, reporting_period=None):
        """
        Returns qs of Parties for which the group is controlled
        (i.e. Party had ratified, at the date on which the given
        reporting_period started, the Treaty that defines the Group as
        controlled ).
        """
        return Party.objects.filter(
            id__in=self.get_signing_parties_ids(reporting_period)
        )

    def get_non_parties(self, reporting_period=None):
        """
        Returns qs of Parties for which the group is not controlled
        (i.e. Party had not ratified, at the date on which the given
        reporting_period started, the Treaty that defines the Group as
        controlled ).
        """
        return Party.objects.exclude(
            id__in=self.get_signing_parties_ids(reporting_period)
        )

    @staticmethod
    def _get_ratifications(party, reporting_period=None):
        # return all the current ratifications of this Party
        if party is None:
            return []
        if reporting_period is None:
            max_date = datetime.date.today()
        else:
            max_date = reporting_period.end_date

        # Get all the current ratifications of this Party
        # When the entry into force date is empty, the field has simply not been updated
        return PartyRatification.objects.filter(
            Q(entry_into_force_date__lte=max_date) |
            Q(entry_into_force_date__isnull=True) & Q(ratification_date__lte=max_date),
            party=party,
            treaty__entry_into_force_date__lte=max_date,
        ).values_list('treaty_id', flat=True)

    @staticmethod
    def get_controlled_groups(party, reporting_period=None):
        """
        Returns queryset of all substance Groups for which control measures
        apply for the given party and reporting_period.
        """
        current_ratifications = Group._get_ratifications(party, reporting_period)
        return Group.objects.filter(control_treaty_id__in=current_ratifications)

    @staticmethod
    def get_report_groups(party, reporting_period=None):
        """
        Returns queryset of all substance Groups that party should report in
        given reporting_period.
        """
        current_ratifications = Group._get_ratifications(party, reporting_period)
        return Group.objects.filter(report_treaty_id__in=current_ratifications)

    def __str__(self):
        return f'Group {self.group_id}'

    class Meta:
        ordering = ('annex', 'group_id')
        db_table = 'group'


class SubstanceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'group', 'group__annex',
        )


class Substance(models.Model):
    """
    Stores all info for a specific substance
    """

    objects = SubstanceManager()

    substance_id = models.IntegerField(unique=True)

    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=256)

    # Having a null group means that the substance is not controlled.
    # The annex information is present in the group (`Substance.group.annex`).
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        related_name='substances',
        on_delete=models.PROTECT
    )

    # Ozone-depleting potential
    odp = models.DecimalField(max_digits=20, decimal_places=10)
    # TODO: any info on when the below two are used?
    min_odp = models.DecimalField(max_digits=20, decimal_places=10)
    max_odp = models.DecimalField(max_digits=20, decimal_places=10)

    # Global warming potential
    gwp = models.DecimalField(
        max_digits=20, decimal_places=10, null=True, blank=True
    )

    formula = models.CharField(max_length=256, null=True, blank=True)

    number_of_isomers = models.SmallIntegerField(null=True, blank=True)

    # TODO: what is this?
    gwp2 = models.DecimalField(
        max_digits=20, decimal_places=10, null=True, blank=True
    )
    gwp_error_plus_minus = models.DecimalField(
        max_digits=20, decimal_places=10, null=True, blank=True
    )
    gwp_baseline = models.DecimalField(
        max_digits=20, decimal_places=10, null=True, blank=True
    )

    # Existing data seems to suggest this field is always non-blank,
    # allowing it though just in case...
    carbons = models.CharField(max_length=128, blank=True)

    hydrogens = models.CharField(max_length=128, blank=True)

    fluorines = models.CharField(max_length=128, blank=True)

    chlorines = models.CharField(max_length=128, blank=True)

    bromines = models.CharField(max_length=128, blank=True)

    # Remarks
    remark = models.CharField(max_length=256, blank=True)

    r_code = models.CharField(
        max_length=128, unique=True, blank=True, null=True
    )

    main_usage = models.CharField(max_length=256, blank=True)

    sort_order = models.IntegerField(null=True)

    is_contained_in_polyols = models.BooleanField()

    is_captured = models.BooleanField(default=False)

    has_critical_uses = models.BooleanField(default=False)

    @property
    def is_qps(self):
        """
        Indicates whether this substance can be used for QPS
        """
        if self.group:
            return self.group.annex.annex_id == 'E'
        return False

    @property
    def odp_or_gwp(self):
        if self.group and self.group.is_odp:
            return self.odp
        if self.group and self.group.is_gwp:
            return self.gwp
        return None

    def __str__(self):
        return self.name

    class Meta:
        ordering = [
            'sort_order', 'pk',
        ]
        db_table = 'substance'


class Blend(models.Model):
    """
    Description of blends
    """

    @enum.unique
    class BlendTypes(enum.Enum):
        ZEOTROPE = 'Zeotrope'
        AZEOTROPE = 'Azeotrope'
        MeBr = 'Methyl bromide'
        OTHER = 'Other'
        CUSTOM = 'Custom'

    blend_id = models.CharField(
        max_length=64, unique=True,
        help_text="A unique String value identifying this blend."
    )

    legacy_blend_id = models.IntegerField(
        null=True, blank=True, unique=True,
        help_text="Used by data import management command, for reports that "
                  "contain blends, instead of substances."
    )

    # Custom blends will always be associated with (and only available for)
    # the Party by which they have been created (in case they've been created
    # by Secretariat using the reporting interface, they will be associated
    # with the Party to which the Submission belongs).
    party = models.ForeignKey(
        Party,
        related_name='custom_blends',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        help_text="Only custom blends will be associated with a Party."
    )

    # This is a plain-text description of the composition; see `BlendComponent`
    # model for a relational one
    composition = models.CharField(
        max_length=256, blank=True,
        help_text="Plain-test description of the composition of the blend."
    )

    other_names = models.CharField(max_length=256, blank=True)

    type = models.CharField(
        max_length=128, choices=((s.value, s.name) for s in BlendTypes),
        help_text="Blend types can be Zeotrope, Azeotrope, Methyl bromide, "
                  "Other or Custom."
    )

    odp = models.DecimalField(
        max_digits=20, decimal_places=10, null=True, blank=True
    )

    gwp = models.DecimalField(
        max_digits=20, decimal_places=10, null=True, blank=True
    )

    hfc = models.NullBooleanField()

    hcfc = models.NullBooleanField()

    main_usage = models.CharField(max_length=256, blank=True)

    remark = models.CharField(max_length=256, blank=True)

    trade_name = models.CharField(max_length=256, blank=True)
    composition_alt = models.CharField(max_length=256, blank=True)
    cnumber = models.CharField(max_length=256, blank=True)

    sort_order = models.IntegerField(null=True, default=0)

    @property
    def custom(self):
        return self.party is not None

    @property
    def is_qps(self):
        return any(
            [
                c.substance.is_qps
                for c in self.components.all() if c.substance
            ]
        )

    def get_substance_ids(self):
        """Returns list of substance id's contained in this blend"""
        return [
            c.substance.id
            for c in self.components.all() if c.substance
        ]

    def get_substance_ids_percentages(self):
        """Returns list of substance id's contained in this blend"""
        return [
            (c.substance.id, c.percentage)
            for c in self.components.all() if c.substance
        ]

    def has_read_rights(self, user):
        if self.party is None:
            return True
        # This is a custom blend; can only be seen by OS or same-party users.
        if user is None:
            return False
        return user.is_secretariat or self.party == user.party

    @staticmethod
    def has_create_rights_for_party(party, user):
        """
        Returns True if `user` can create a custom blend associated with `party`
        """
        if (
            party is None
            or user is None
            or user.is_anonymous
            or user.is_read_only
        ):
            return False
        return user.is_secretariat or party == user.party

    @staticmethod
    def has_edit_rights_for_party(party, user):
        """
        Returns True if `user` can change a custom blend
        associated with `party`.
        """
        if (
            party is None
            or user is None
            or user.is_anonymous
            or user.is_read_only
        ):
            return False
        return user.is_secretariat or party == user.party

    def has_edit_rights(self, user):
        """
        Returns True if `user` can change composition of this custom blend
        """
        return self.has_edit_rights_for_party(self.party, user)

    def __str__(self):
        return self.blend_id

    class Meta:
        db_table = "blend"
        ordering = [
            'sort_order', 'pk',
        ]


class BlendComponent(models.Model):
    """
    Model describing the substances composition of each blend
    """

    blend = models.ForeignKey(
        Blend, related_name='components', on_delete=models.PROTECT
    )

    substance = models.ForeignKey(
        Substance,
        null=True,
        blank=True,
        related_name='blends',
        on_delete=models.PROTECT
    )

    percentage = models.DecimalField(
        max_digits=6, decimal_places=5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )

    component_name = models.CharField(max_length=256, blank=True)

    cnumber = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return f'Blend {self.blend.blend_id} - component {self.component_name}'

    def clean(self):
        if not self.component_name and not self.substance:
            raise ValidationError(
                {
                    'component_name': [_(
                        "Substance or component name must be set."
                    )],
                    'substance': [_(
                        "Substance or component name must be set."
                    )]
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.component_name:
            # If a component name is not given, set it to substance.name.
            # This avoids creating a property returning one of the two, which
            # would cause problems with DRF's serializers
            self.component_name = self.substance.name
        return super().save(*args, **kwargs)

    class Meta:
        ordering = [
            'blend__sort_order', 'substance__sort_order'
        ]
        db_table = "blend_component"


class UsesType(models.Model):
    """
    The different categories of uses of controlled substances that need to be
    reported.
    """

    uses_type_id = models.CharField(max_length=16, unique=True)

    name = models.CharField(max_length=128, unique=True)

    remark = models.CharField(max_length=256, blank=True)

    decision_flag = models.BooleanField()

    forms = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        db_table = "uses_type"
