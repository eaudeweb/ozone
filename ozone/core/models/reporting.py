import enum
import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.utils import timezone
from model_utils import FieldTracker
from simple_history.models import HistoricalRecords

from .aggregation import ProdCons
from .legal import ReportingPeriod
from .party import Party, PartyHistory
from .substance import Group
from .utils import model_to_dict
from .workflows import (
    BaseWorkflow,
    DefaultArticle7Workflow,
    SimplifiedWorkflow,
    AcceleratedArticle7Workflow,
    DefaultExemptionWorkflow,
    AcceleratedExemptionWorkflow,
    DefaultProcessAgentWorkflow,
    DefaultTransferWorkflow,
)
from ..exceptions import (
    Forbidden,
    MethodNotAllowed,
    TransitionDoesNotExist,
    TransitionNotAvailable,
)
from ..utils.cache import invalidate_aggregation_cache

__all__ = [
    'ModifyPreventionMixin',
    'ObligationTypes',
    'Obligation',
    'Submission',
    'HistoricalSubmission',
    'SubmissionInfo',
    'ReportingChannel',
    'SubmissionFormat',
]

SUBMISSION_ROOT_DIR = 'submissions'


class ModifyPreventionMixin:
    """
    Mixin to be used by models with foreign keys to Submissions which need to
    prevent changes when the referenced submission is not in Data Entry.
    """

    @staticmethod
    def get_exempted_fields():
        return [
            # Secretariat remarks can be changed
            # at any time, while the party remarks cannot.
            "remarks_os",
        ]

    def clean(self):
        if (
            Submission.non_exempted_fields_modified(self)
            and not self.submission.data_changes_allowed
        ):
            raise ValidationError(
                _(
                    "Unable to change submission because it is already "
                    "submitted."
                )
            )
        super().clean()

    def delete(self, *args, **kwargs):
        if not self.submission.deletion_allowed:
            raise MethodNotAllowed(
                _(
                    "Unable to delete data because submission is already "
                    "submitted."
                )
            )
        super().delete()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


@enum.unique
class ObligationTypes(enum.Enum):
    ART7 = 'art7'
    ESSENCRIT = 'essencrit'  # TODO: rename this to RAF
    HAT = 'hat'
    OTHER = 'other'
    EXEMPTION = 'exemption'
    TRANSFER = 'transfer'
    PROCAGENT = 'procagent'
    LABUSES = 'labuses'
    ART4B = 'art4b'
    ART9 = 'art9'
    REQCHANGES = 'reqchanges'
    ODSSTRATEGIES = 'odsstrategies'
    UNWANTEDIMPORTS = 'unwantedimports'


class Obligation(models.Model):

    NOT_CLONEABLE = [
        ObligationTypes.EXEMPTION.value,
        ObligationTypes.TRANSFER.value,
        ObligationTypes.PROCAGENT.value,
        ObligationTypes.OTHER.value,
        ObligationTypes.LABUSES.value,
        ObligationTypes.ART4B.value,
        ObligationTypes.ART9.value,
        ObligationTypes.REQCHANGES.value,
    ]

    AGGREGATABLE = [
        ObligationTypes.ART7.value,
        ObligationTypes.HAT.value,
    ]

    name = models.CharField(
        max_length=256, unique=True,
        help_text="A unique String value identifying this obligation."
    )

    description = models.CharField(max_length=256, blank=True)

    is_active = models.BooleanField(
        default=True,
        help_text="Indicates whether reporting can be performed for this "
                  "obligation."
    )

    # Some obligations require immediate reporting each time an event happens,
    # instead of periodical reporting. This should get special treatment both
    # in backend and frontend.
    has_reporting_periods = models.BooleanField(
        default=True,
        help_text="Indicates whether reporting is done periodically or upon "
                  "certain events (e.g. transfers)"
    )

    # For some obligations, multiple submissions for the same party & period
    # mean different versions of the same submission. For others, they mean
    # separate submissions, which should be visible as such in the UI.
    # This flag differentiates between the two situations.
    has_versions = models.BooleanField(
        default=True,
        help_text="Indicates whether submissions for this obligation can have "
                  "multiple versions"
    )

    _obligation_type = models.CharField(
        max_length=64, choices=((s.value, s.name) for s in ObligationTypes),
        null=True,
        help_text="Used to generate the correct form and filter obligations."
    )

    sort_order = models.IntegerField(null=True)

    other = models.BooleanField(
        default=False,
        help_text="Unset when this obligation is a main one. The main "
                  "ones are: Article 7, Essential and Critical uses (RAF) and "
                  "Transfer or addition of production or consumption."
    )

    is_default = models.NullBooleanField(
        default=None,
        help_text="If set to true it means that the current obligation is used "
                  "as default for 'Data entry submissions' and 'All submissions' sections."
    )

    @property
    def obligation_type (self):
        return self._obligation_type

    @property
    def is_not_cloneable(self):
        return self.obligation_type in self.NOT_CLONEABLE

    @property
    def is_aggregateable(self):
        return self.obligation_type in self.AGGREGATABLE

    def __str__(self):
        return self.name

    @classmethod
    def get_default(cls):
        return (
            cls.objects.filter(is_default=True)
            .first()
        )

    def clean(self):
        default_obligation_qs = Obligation.objects.filter(is_default=True)
        if (
            self.is_default
            and default_obligation_qs.count() > 0
            and self not in default_obligation_qs
        ):
            raise ValidationError(
                _('Unable to set default obligation. Another obligation is already set as default.')
            )

    class Meta:
        db_table = "core_obligation"


class ReportingChannel(models.Model):
    """
    Describes the medium through which the form was submitted.
    """

    name = models.CharField(unique=True, max_length=256)
    description = models.CharField(max_length=256, blank=True)

    # These mark whether this channel is default for party/os
    is_default_party = models.BooleanField(default=False)
    is_default_secretariat = models.BooleanField(default=False)

    # These mark whether this channel can be selected by party/os
    is_party = models.BooleanField(default=False)
    is_secretariat = models.BooleanField(default=False)

    @classmethod
    def get_default(cls, user):
        """
        Returns default reporting channel value for given user.
        If none is found, returns None (because first() returns None).
        """
        if user.is_secretariat:
            return cls.objects.filter(is_default_secretariat=True).first()
        if user.party is not None:
            return cls.objects.filter(is_default_party=True).first()

    def clean(self):
        unique_fields = {
            'is_default_party': 'party',
            'is_default_secretariat': 'secretariat',
        }
        for field in unique_fields.keys():
            queryset = ReportingChannel.objects.filter(**{field: True})

            if (
                getattr(self, field, False) is True
                and queryset.count() > 0
                and self not in queryset
            ):
                raise ValidationError(
                    _(
                        f'Unable to set reporting channel. Another reporting '
                        f'channel is already set as default for '
                        f'{unique_fields[field]}.'
                    )
                )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "reporting_channel"


class SubmissionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'reporting_period', 'obligation', 'party'
        )


class Submission(models.Model):
    """
    One specific data submission (version!)
    """

    # This keeps a mapping between the DB-persisted workflow and
    # its actual implementation class.
    WORKFLOW_MAPPING = {
        'empty': None,
        'base': BaseWorkflow,
        'default': DefaultArticle7Workflow,
        'accelerated': AcceleratedArticle7Workflow,
        'simplified': SimplifiedWorkflow,
        'default_exemption': DefaultExemptionWorkflow,
        'accelerated_exemption': AcceleratedExemptionWorkflow,
        'default_transfer': DefaultTransferWorkflow,
        'default_process_agent': DefaultProcessAgentWorkflow
    }

    # This describes all possible submission-related data; each item contains:
    # (related_manager_name, is_aggregation_data_populated_from_submission).
    # In cases where the OS inputs data via the Admin interface and *then*
    # links a non-data submission (e.g. Transfers, Proc Agents), no aggregation
    # calculations should be performed at Submission.save().
    # Also, some submission-related data is not numerical; they will also have
    # False as the second item in the tuple.
    RELATED_DATA = [
        ('article7exports', True),
        ('article7imports', True),
        ('article7productions', True),
        ('article7destructions', True),
        ('article7nonpartytrades', True),
        ('article7emissions', True),
        ('highambienttemperatureproductions', True),
        ('highambienttemperatureimports', True),
        ('dataothers', True),
        ('nominations', True),
        ('exemptionapproveds', True),
        ('rafreports', True),
        ('pa_uses_reported', False),
        ('transfers_from', False),
        ('transfers_to', False),
    ]

    # Maps flags names to group IDs, as group IDs are the closest to immutable
    # field on the Group model.
    GROUP_FLAGS_MAPPING = {
        'flag_has_reported_a1': 'AI',
        'flag_has_reported_a2': 'AII',
        'flag_has_reported_b1': 'BI',
        'flag_has_reported_b2': 'BII',
        'flag_has_reported_b3': 'BIII',
        'flag_has_reported_c1': 'CI',
        'flag_has_reported_c2': 'CII',
        'flag_has_reported_c3': 'CIII',
        'flag_has_reported_e': 'EI',
        'flag_has_reported_f': 'F',
    }
    FLAG_GROUPS_MAPPING = {
        value: key
        for key, value in GROUP_FLAGS_MAPPING.items()
    }

    # Only create historical records when changing these fields
    WATCHED_FIELDS = ('_current_state',)

    objects = SubmissionManager()

    obligation = models.ForeignKey(
        Obligation, related_name='submissions', on_delete=models.PROTECT
    )

    schema_version = models.CharField(max_length=64)

    reporting_period = models.ForeignKey(
        ReportingPeriod, related_name='submissions', on_delete=models.PROTECT
    )

    # `party` is always the Party for which data is reported
    party = models.ForeignKey(
        Party, related_name='submissions', on_delete=models.PROTECT
    )

    # Is set only at *the first* transition to Submitted
    submitted_at = models.DateField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(
        get_user_model(),
        related_name='submissions_created',
        on_delete=models.PROTECT
    )
    last_edited_by = models.ForeignKey(
        get_user_model(),
        related_name='submissions_last_edited',
        on_delete=models.PROTECT
    )

    # Per Obligation-ReportingPeriod-Party
    version = models.PositiveSmallIntegerField(default=1)

    # This implements a major.minor versioning mechanism.
    # Default values are None so we only set these at "submit" time.
    revision_major = models.PositiveSmallIntegerField(
        null=True, blank=True, default=None)
    revision_minor = models.PositiveSmallIntegerField(
        null=True, blank=True, default=None
    )

    cloned_from = models.ForeignKey(
        'self',
        related_name='clones',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    # Persisted workflow class for this submission. We want this to be only set
    # at submission creation, so it will have no setter implementation.
    _workflow_class = models.CharField(
        max_length=32,
        choices=((w, w.capitalize()) for w in WORKFLOW_MAPPING.keys()),
        default='empty',
        db_column='workflow_class'
    )
    # States will be accessed through properties to enable custom logic
    # on state transitions.
    # We will impose no restriction on state name choices, as there is no
    # way of knowing them before runtime. Instead, the associated workflow
    # object (`self.workflow`) will be responsible for sane transitions.
    _current_state = models.CharField(
        max_length=64, null=True, blank=True, db_column='current_state'
    )
    # We need previous_state for un-recalling submissions
    _previous_state = models.CharField(
        max_length=64, null=True, blank=True, db_column='previous_state'
    )

    # Flags
    flag_provisional = models.BooleanField(
        default=False,
        verbose_name='provisional',
        help_text="If set to true it signals that future changes are foreseen."
    )
    flag_valid = models.NullBooleanField(
        default=None,
        verbose_name='valid',
        help_text="If set to true it signals that the data in the current "
        "version is considered correct. Can be set by the Secretariat during "
        "Processing or at the transition between the Processing or Finalized states."
    )
    flag_superseded = models.BooleanField(
        default=False,
        verbose_name='superseded',
        help_text="If set to true it means that the current version is not "
        "relevant anymore. When a newer version of data is Submitted, "
        "the current one is automatically flagged as Superseded."
    )
    flag_checked_blanks = models.BooleanField(
        default=False,
        verbose_name='checked blanks',
    )
    flag_has_blanks = models.BooleanField(
        default=False,
        verbose_name='has blanks',
    )
    flag_confirmed_blanks = models.BooleanField(
        default=False,
        verbose_name='confirmed blanks',
    )
    flag_has_reported_a1 = models.BooleanField(
        default=False,
        verbose_name='has reported A/I',
        help_text="If set to true it means that substances under "
                  "Annex A Group 1 were reported."
    )
    flag_has_reported_a2 = models.BooleanField(
        default=False,
        verbose_name='has reported A/II',
        help_text="If set to true it means that substances under "
                  "Annex A Group 2 were reported."
    )
    flag_has_reported_b1 = models.BooleanField(
        default=False,
        verbose_name='has reported B/I',
        help_text="If set to true it means that substances under "
                  "Annex B Group 1 were reported."
    )
    flag_has_reported_b2 = models.BooleanField(
        default=False,
        verbose_name='has reported B/II',
        help_text="If set to true it means that substances under "
                  "Annex B Group 2 were reported."
    )
    flag_has_reported_b3 = models.BooleanField(
        default=False,
        verbose_name='has reported B/III',
        help_text="If set to true it means that substances under "
                  "Annex B Group 3 were reported."
    )
    flag_has_reported_c1 = models.BooleanField(
        default=False,
        verbose_name='has reported C/I',
        help_text="If set to true it means that substances under "
                  "Annex C Group 1 were reported."
    )
    flag_has_reported_c2 = models.BooleanField(
        default=False,
        verbose_name='has reported C/II',
        help_text="If set to true it means that substances under "
                  "Annex C Group 2 were reported."
    )
    flag_has_reported_c3 = models.BooleanField(
        default=False,
        verbose_name='has reported C/III',
        help_text="If set to true it means that substances under "
                  "Annex C Group 3 were reported."
    )
    flag_has_reported_e = models.BooleanField(
        default=False,
        verbose_name='has reported E/I',
        help_text="If set to true it means that substances under "
                  "Annex E were reported."
    )
    flag_has_reported_f = models.BooleanField(
        default=False,
        verbose_name='has reported F',
        help_text="If set to true it means that substances under "
                  "Annex F were reported."
    )

    date_reported_f = models.DateField(
        null=True,
        blank=True,
        help_text="Date at which substances under Annex F were reported."
    )

    # Art7 Remarks
    questionnaire_remarks_party = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the reporting "
                  "party for questionnaire"
    )
    questionnaire_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the ozone "
                  "secretariat for questionnaire"
    )
    imports_remarks_party = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the reporting "
                  "party for imports"
    )
    imports_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the ozone "
                  "secretariat for imports"
    )
    exports_remarks_party = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the reporting "
                  "party for exports"
    )
    exports_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the ozone "
                  "secretariat for exports"
    )
    production_remarks_party = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the reporting "
                  "party for production"
    )
    production_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the ozone "
                  "secretariat for production"
    )
    destruction_remarks_party = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the reporting "
                  "party for destruction"
    )
    destruction_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the ozone "
                  "secretariat for destruction"
    )
    nonparty_remarks_party = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the reporting "
                  "party for nonparty"
    )
    nonparty_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the ozone "
                  "secretariat for nonparty"
    )
    emissions_remarks_party = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the reporting "
                  "party for emissions"
    )
    emissions_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="General Article7 obligation remarks added by the ozone "
                  "secretariat for emissions"
    )
    # HAT Remarks
    hat_production_remarks_party = models.CharField(
        max_length=9999, blank=True,
        help_text="General HAT obligation remarks added by the reporting party "
                  "for production"
    )
    hat_production_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="General HAT obligation remarks added by the ozone "
                  "secretariat for production"
    )
    hat_imports_remarks_party = models.CharField(
        max_length=9999, blank=True,
        help_text="General HAT obligation remarks added by the reporting party "
                  "for imports"
    )
    hat_imports_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="General HAT obligation remarks added by the ozone "
                  "secretariat for imports"
    )
    # Exemption
    exemption_nomination_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="Exemption nomination remarks added by the ozone secretariat"
    )
    exemption_approved_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="Exemption approved remarks added by the ozone secretariat"
    )
    # RAF
    raf_remarks_party = models.CharField(
        max_length=9999, blank=True,
        help_text="General RAF remarks added by the reporting party"
    )
    raf_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="General RAF remarks added by the ozone secretariat"
    )

    # Transfers Remarks
    transfers_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        help_text="General Transfers remarks added by the ozone secretariat"
    )

    # Process agent Remarks
    pa_uses_reported_remarks_secretariat = models.CharField(
        max_length=9999, blank=True,
        verbose_name="process agent uses reported remarks",
        help_text="General Process agent uses reported remarks added "
                  "by the ozone secretariat"
    )

    reporting_channel = models.ForeignKey(
        ReportingChannel,
        related_name="submission",
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    # Exemption related flags
    flag_emergency = models.BooleanField(
        default=False,
        verbose_name='Emergency',
        help_text="If set to true it means that ozone secretariat "
                  "can fill out only the Approved form directly."
    )

    # Needed to track state changes and help with custom logic
    tracker = FieldTracker()

    history = HistoricalRecords()

    @cached_property
    def is_versionable(self):
        return self.obligation.has_versions

    @cached_property
    def filled_by_secretariat(self):
        return self.created_by.is_secretariat

    @cached_property
    def workflow_class(self):
        """Just a getter so we can access the class"""
        return self._workflow_class

    def workflow(self, user=None):
        """
        Creates workflow instance and set last *persisted* state on it
        """
        wf = self.WORKFLOW_MAPPING[self._workflow_class](
            model_instance=self,
            user=user
        )
        state = self.tracker.previous('_current_state') \
            if self.tracker.has_changed('_current_state') \
            else self.current_state
        wf.state = state or wf.state.workflow.initial_state
        return wf

    @property
    def current_state(self):
        return self._current_state

    @property
    def previous_state(self):
        """
        Previous state will only be changed indirectly when changing
        current_state; only a getter is needed.
        """
        return self._previous_state

    @property
    def data_changes_allowed(self):
        """
        Check whether data changes are allowed in current state.
        """
        return self.workflow().data_changes_allowed

    @property
    def deletion_allowed(self):
        """
        Check whether deletion is allowed in current state.
        """
        return self.workflow().deletion_allowed

    @property
    def available_states(self):
        """
        List of states that can be reached directly from current state.
        No pre-transition checks are taken into account at this point.

        """
        return [t.target.name for t in self.workflow().state.transitions()]

    @property
    def editable_states(self):
        return self.workflow().editable_data_states

    @property
    def incorrect_states(self):
        return self.workflow().incorrect_data_states

    @property
    def in_incorrect_state(self):
        return self.workflow().in_incorrect_data_state

    @property
    def in_initial_state(self):
        return self.workflow().in_initial_state

    @property
    def in_final_state(self):
        return self.workflow().finished

    @property
    def is_current(self):
        if self.flag_superseded or self.in_initial_state:
            return False
        return True

    def is_cloneable(self, user):
        is_cloneable, message = self.check_cloning(user)
        return is_cloneable

    def available_transitions(self, user):
        """
        List of transitions that can be performed from current state.

        """
        # Simply avoid needless processing
        if user.is_read_only:
            return []

        transitions = []
        wf = self.workflow(user)
        for transition in wf.state.transitions():
            if hasattr(wf, 'check_' + transition.name):
                if getattr(wf, 'check_' + transition.name)():
                    transitions.append(transition.name)
            else:
                transitions.append(transition.name)
        return transitions

    def call_transition(self, trans_name, user, increment_minor=None):
        """
        Interface for calling a specific transition name on the workflow.

        It automatically persists the previous and current states.

        increment_major can only be used for "submit" transitions, to specify
        whether the major version should be incremented in the case of
        OS-filled submissions.

        """
        # Call this now so we don't recreate the self.workflow object ad nauseam
        workflow = self.workflow(user)

        # This is a `TransitionList` and supports the `in` operator
        if trans_name not in workflow.state.workflow.transitions:
            raise TransitionDoesNotExist(
                _(
                    f'Workflow error. Transition {trans_name} does not exist '
                    f'in this workflow'
                )
            )

        # This is a list of `Transition`s and doesn't support the `in` operator
        # without explicitly referencing `name`
        if trans_name not in [t.name for t in workflow.state.transitions()]:
            raise TransitionNotAvailable(
                _(
                    f'Workflow error. Transition {trans_name} does not start '
                    f'from current state'
                )
            )

        # Transition names are available as attributes on the workflow object
        transition = getattr(workflow, trans_name)

        if not transition.is_available():
            raise TransitionNotAvailable(
                _(
                    "Workflow error. Transition checks not satisfied or "
                    "you may not have the necessary permissions"
                )
            )

        # Set the `increment_minor` attribute on the submission,
        # since there are no other good ways of sending parameters to the
        # transition.
        setattr(self, 'increment_minor', increment_minor)

        # Call the transition; this should work (bar exceptions in pre/post
        # transition hooks, which will get caught later down the line if they
        # occur)
        transition()

        # If everything went OK, persist the result and the transition.
        self._previous_state = self._current_state
        self._current_state = workflow.state.name

        # This field will be automatically added to update_fields in save()
        self.last_edited_by = user
        self.save(update_fields=('_previous_state', '_current_state',))

    def get_next_revision(self, user, increment_minor=None):
        # Only take into account submitted peers of this submission.
        submissions = Submission.objects.filter(
            obligation=self.obligation,
            party=self.party,
            reporting_period=self.reporting_period
        ).exclude(
            _current_state__in=self.editable_states
        ).exclude(
            revision_major__isnull=True
        ).exclude(
            revision_minor__isnull=True
        )
        if not submissions:
            # First submitted revision will always be 1.0
            return 1, 0
        # Get current major and minor revisions
        revisions = submissions.values_list('revision_major', 'revision_minor')
        revision_major = max(
            [
                r[0] if r[0] is not None else 0
                for r in revisions
            ]
        )
        if revision_major == 0:
            return 1, 0
        revision_minor = max(
            [
                r[1] if r[1] is not None else 0
                for r in revisions
                if r[0] == revision_major
            ]
        )
        if not self.filled_by_secretariat and user.party is not None:
            # Party user, party-filled submission
            return revision_major + 1, 0
        if self.filled_by_secretariat and user.is_secretariat:
            if increment_minor is True:
                return revision_major, revision_minor + 1
            else:
                # If increment_minor was not specified or is False,
                # increment major version
                return revision_major + 1, 0

    def set_revision(self, user, increment_minor):
        if not self.is_versionable:
            return
        self.revision_major, self.revision_minor = self.get_next_revision(
            user, increment_minor
        )
        self.save(update_fields=('revision_major', 'revision_minor',))

    def is_submittable(self):
        """
        Checks that all required info has been filled before submission.
        """
        if (
            self.info.reporting_officer is ''
            or self.info.email is None
            or self.filled_by_secretariat and self.submitted_at is None
        ):
            return False

        return True

    def check_imports_exports(self):
        """
        Performs checks on all imports and exports data in this submission
        based on the validation rules described in
        https://github.com/eaudeweb/ozone/issues/81/
        If validation fails, this will raise a validation error.
        """
        if self.obligation.obligation_type == ObligationTypes.ART7.value:
            if hasattr(self, "article7imports") and self.article7imports:
                self.article7imports.model.validate_import_export_data(self)
            if hasattr(self, "article7exports") and self.article7exports:
                self.article7exports.model.validate_import_export_data(self)

    def check_emissions(self):
        """
        Performs pre-submit checks on emissions data in this submission.
        This allows saving temporary data with facility name or emission
        totals not yet specified.
        """
        if self.obligation.obligation_type == ObligationTypes.ART7.value:
            if hasattr(self, "article7emissions") and self.article7emissions:
                self.article7emissions.model.validate_data(self)

    def permissions_matrix(self, user):
        wf = self.workflow(user)
        return wf.permissions_matrix

    def can_edit_flags(self, user):
        """
        Returns True if user can set *any* flags on this submission,
        based strictly on read/write rights and ownership
        (i.e. does not take submission state into account)
        """
        if (
            user.is_secretariat
            or (user.party == self.party and not self.filled_by_secretariat)
        ):
            return not user.is_read_only

    def get_changeable_flags(self, user):
        """
        Returns list of flags that can be changed by the current user in the
        current state.
        N.B.: flag_superseded cannot be changed directly by users, it is
        only changed automatically by the system.
        """
        # First do a quick check based on actual permissions
        # This also restricts changes only to secretariat or party users.
        if not self.can_edit_flags(user):
            return []

        # Treat exemption case separately
        if self.obligation.obligation_type == ObligationTypes.EXEMPTION.value:
            if user.is_secretariat:
                if self.in_initial_state:
                    return ['flag_emergency']
            return []

        flags_list = []
        # For all other forms, flags are similar to Article 7
        if user.is_secretariat:
            if not self.filled_by_secretariat and self.in_initial_state:
                # Secretariat cannot change anything on party submission while
                # it is in Data Entry!
                return []

            flags_list.extend([
                'flag_provisional', 'flag_checked_blanks',
                'flag_has_blanks', 'flag_confirmed_blanks',
            ])

            if self.in_initial_state:
                flags_list.extend([
                    'flag_has_reported_a1', 'flag_has_reported_a2',
                    'flag_has_reported_b1', 'flag_has_reported_b2',
                    'flag_has_reported_b3', 'flag_has_reported_c1',
                    'flag_has_reported_c2', 'flag_has_reported_c3',
                    'flag_has_reported_e', 'flag_has_reported_f',
                ])
            else:
                # valid & approved flags can only be set after submitting
                flags_list.extend(['flag_valid',])
        elif user.party is not None:
            # Party user
            if self.in_initial_state:
                if self.filled_by_secretariat:
                    return []

                flags_list.extend([
                    'flag_provisional',
                    'flag_has_reported_a1', 'flag_has_reported_a2',
                    'flag_has_reported_b1', 'flag_has_reported_b2',
                    'flag_has_reported_b3', 'flag_has_reported_c1',
                    'flag_has_reported_c2', 'flag_has_reported_c3',
                    'flag_has_reported_e', 'flag_has_reported_f',
                ])

        return flags_list

    def check_flags(self, user, flags):
        """
        Raise error if user has changed flags he was not allowed to change
        in the current state; return True otherwise.
        """
        wrongly_modified_flags = [
            field_name for field_name, value in flags.items()
            if field_name.startswith('flag_') and
            field_name not in self.get_changeable_flags(user) and
            getattr(self, field_name) != value
        ]
        if len(wrongly_modified_flags) > 0:
            raise ValidationError({
                field: [_('User does not have permission to change this flag.')]
                for field in wrongly_modified_flags
            })
        return True

    def can_edit_remarks(self, user):
        """
        Returns True if user can edit at least one remark on this submission.
        This is based purely on submission ownership!
        """
        # Party users should not be able to change party remarks on
        # secretariat-filled submissions
        if user.is_secretariat or (user.party == self.party and not self.filled_by_secretariat):
            return not user.is_read_only
        return False

    def can_change_remark(self, user, field_name):
        """
        Verifies whether user can change remark field `field_name`, based on
        both submission ownership/permissions and remarks mappings (OS vs party)
        """
        # First do a quick check based purely on ownership.
        # This also restricts changes only to secretariat or party users.
        if not self.can_edit_remarks(user):
            return False

        # If in initial state, do not allow party to modify OS-filled
        # submissions (and vice-versa)
        if self.in_initial_state:
            if (
                (user.is_secretariat and not self.filled_by_secretariat)
                or (user.party is not None and self.filled_by_secretariat)
            ):
                return False

        if self.current_state not in self.editable_states and field_name.endswith("_party"):
            # The user cannot modify any of the party fields, if the
            # submission isn't in an editable state (e.g. `data_entry`)
            return False
        if not self.filled_by_secretariat and user.is_secretariat and field_name.endswith("_party"):
            # Secretariat users cannot modify any of the party fields, if the
            # submission was filled by a party.
            return False
        elif not user.is_secretariat and field_name.endswith("_secretariat"):
            # Non-OS users cannot modify any of the secretariat remark fields
            return False

        return True

    def check_remarks(self, user, remarks):
        """
        Raise error if the user has change any remarks he was not allowed to
        change.
        """

        wrongly_modified_remarks = []

        # XXX Logic duplicated in DataCheckRemarksMixInBase.check_remarks
        for field_name, new_value in remarks.items():
            if new_value == getattr(self, field_name):
                # No value changed
                continue

            if not self.can_change_remark(user, field_name):
                wrongly_modified_remarks.append(field_name)

        if len(wrongly_modified_remarks) > 0:
            raise ValidationError({
                field: [_('User does not have permission to change this remark.')]
                for field in wrongly_modified_remarks
            })
        return True

    def check_reporting_channel_modified(self):
        if 'reporting_channel_id' in self.tracker.changed().keys():
            return True
        return False

    def can_change_reporting_channel(self, user):
        if user.is_secretariat and self.filled_by_secretariat:
            return not user.is_read_only and self.in_initial_state
        return False

    @staticmethod
    def has_read_rights_for_party(party, user):
        if (
            user.is_secretariat
            or user.party is not None and user.party == party
            or (
                user.is_cap
                and user.party_group is not None
                and party in user.party_group.parties.all()
            )
        ):
            return True
        return False

    def has_read_rights(self, user):
        return self.has_read_rights_for_party(self.party, user)

    @staticmethod
    def has_create_rights_for_party(party, user):
        if (
            user.is_secretariat
            or user.party is not None and user.party == party
        ):
            return not user.is_read_only
        return False

    def has_edit_rights(self, user):
        """
        Returns whether user has edit rights on this submission based on
        user type & who it was created by (state not taken into account).
        """
        if self.obligation.obligation_type == ObligationTypes.EXEMPTION.value:
            if (
                user.is_secretariat
                or user.party == self.party and not self.filled_by_secretariat
            ):
                return not user.is_read_only
        else:
            if (
                user.is_secretariat and self.filled_by_secretariat
                or user.party == self.party and not self.filled_by_secretariat
            ):
                return not user.is_read_only
        return False

    def can_edit_data(self, user):
        if self.has_edit_rights(user):
            if (
                self.obligation.obligation_type == ObligationTypes.EXEMPTION.value
                and not user.is_secretariat and user.party is not None
            ):
                return self.in_initial_state
            else:
                return self.data_changes_allowed
        return False

    def can_delete_data(self, user):
        if self.has_edit_rights(user):
            return self.deletion_allowed
        return False

    def can_upload_files(self, user):
        """
        Party cannot upload files to secretariat-filled submissions.
        Secretariat cannot upload files on party submissions if they are in
        data entry
        """
        if user.is_secretariat:
            if not self.filled_by_secretariat and self.in_initial_state:
                return False
        else:
            if self.filled_by_secretariat or self.party != user.party:
                return False
        return not user.is_read_only

    @staticmethod
    def get_exempted_fields():
        """
        List of exempted fields - fields that can be modified no matter in what
        state the current submission is.
        """
        return [
            "_current_state",
            "_previous_state",
            "flag_provisional",
            "flag_valid",
            "flag_superseded",
            "flag_checked_blanks",
            "flag_has_blanks",
            "flag_confirmed_blanks",
            "flag_has_reported_a1",
            "flag_has_reported_a2",
            "flag_has_reported_b1",
            "flag_has_reported_b2",
            "flag_has_reported_b3",
            "flag_has_reported_c1",
            "flag_has_reported_c2",
            "flag_has_reported_c3",
            "flag_has_reported_e",
            "flag_has_reported_f",
            # Exemption flags
            "flag_emergency",
            # Remarks, secretariat remarks can be changed
            # at any time, while the party remarks cannot.
            # "questionnaire_remarks_party",
            "questionnaire_remarks_secretariat",
            # "imports_remarks_party",
            "imports_remarks_secretariat",
            # "exports_remarks_party",
            "exports_remarks_secretariat",
            # "production_remarks_party",
            "production_remarks_secretariat",
            # "destruction_remarks_party",
            "destruction_remarks_secretariat",
            # "nonparty_remarks_party",
            "nonparty_remarks_secretariat",
            # "emissions_remarks_party",
            "emissions_remarks_secretariat",
            # "hat_production_remarks_party",
            "hat_production_remarks_secretariat",
            # "hat_imports_remarks_party",
            "hat_imports_remarks_secretariat",
            # "raf_remarks_party",
            "raf_remarks_secretariat",
            "transfers_remarks_secretariat",
            "exemption_nomination_remarks_secretariat",
            "exemption_approved_remarks_secretariat",
            "pa_uses_reported_remarks_secretariat",
            "reporting_channel_id",
            "submitted_at",
            # Since various fields on the submission can be changed even after
            # submit (based on other checks), updated_at and last_edited_by
            # need to be always update-able.
            "updated_at",
            "last_edited_by_id"
        ]

    @staticmethod
    def non_exempted_fields_modified(obj):
        """
        Checks whether one of the non-exempted fields was modified.
        """
        exempted_fields = obj.__class__.get_exempted_fields()
        modified_fields = obj.tracker.changed()
        for field in modified_fields.keys():
            if field not in exempted_fields:
                return True
        return False

    @staticmethod
    def has_initial_state_peers_by_same_user_type(peers, user):
        """
        This is used for checking whether a submission has an initial state peer
        (same party-period-obligation combination) created by the same type
        (Secretariat, party) of user.
        At any time, only one submission in initial state can exist per
        type of user and party-period-obligation.
        Since this is also used in save(), it takes a queryset as argument;
        this should contain its peers. Caller must ensure that this is properly
        constructed.
        """
        actor = "Secretariat" if user.is_secretariat else "party"
        message = _(
            f"Another submission created by {actor} for "
            f"this party/obligation/year already exists in Data Entry."
        )

        for sub in peers:
            if sub.in_initial_state:
                if sub.filled_by_secretariat and user.is_secretariat:
                    return True, message
                if not sub.filled_by_secretariat and not user.is_secretariat:
                    return True, message
        return False, None

    def check_cloning(self, user):
        """
        Checks whether the current submission can be cloned and the current user
        has the necessary permissions.
        """

        if (
            user.is_read_only or
            not (user.is_secretariat or self.party == user.party)
        ):
            return (
                False,
                Forbidden(
                    _("You do not have permission to perform this action.")
                )
            )

        if self.obligation.is_not_cloneable:
            return (
                False,
                ValidationError(
                    _(
                        "You cannot create a new version of this submission "
                        "with this type of obligation"
                    )
                )
            )

        # Only non-superseded "past" submissions can be cloned
        if not self.reporting_period.is_reporting_open:
            if self.flag_superseded:
                return (
                    False,
                    ValidationError(
                        _(
                            "You cannot create a new version of this submission"
                            " from a previous period if it's superseded."
                        )
                    )
                )

        # Submissions can't be cloned if there is already a data entry one
        # created by the same user type (OS, party) for the same
        # party-period-obligation
        peers = Submission.objects.filter(
            party=self.party,
            obligation=self.obligation,
            reporting_period=self.reporting_period
        )
        has_peers, message = self.has_initial_state_peers_by_same_user_type(
            peers, user
        )
        if has_peers:
            return False, ValidationError(message)

        return True, None

    def clone(self, user):
        is_cloneable, e = self.check_cloning(user)
        if is_cloneable:
            channel = ReportingChannel.get_default(user)
            clone = Submission.objects.create(
                party=self.party,
                reporting_period=self.reporting_period,
                obligation=self.obligation,
                cloned_from=self,
                created_by=user,
                last_edited_by=user,
                reporting_channel=channel
            )
            if hasattr(self, 'info'):
                # Clone submission might already have some pre-populated
                # info due to how save() works. These need to be updated.
                SubmissionInfo.objects.update_or_create(
                    submission=clone,
                    defaults={
                        'reporting_officer': self.info.reporting_officer,
                        'designation': self.info.designation,
                        'organization': self.info.organization,
                        'postal_address': self.info.postal_address,
                        'country': self.info.country,
                        'phone': self.info.phone,
                        'email': self.info.email,
                        'date': self.info.date,
                        'submission_format': self.info.submission_format,
                    }
                )
        else:
            raise e

        # We treat Article7Questionnaire separately because it has a one-to-one
        # relation with submission and this way we avoid nasty verifications
        exclude = [
            'id', 'submission_id', '_state', '_deferred_fields', '_tracker',
            'save',
        ]
        if (
            hasattr(self, "article7questionnaire")
            and self.article7questionnaire is not None
        ):
            attributes = model_to_dict(
                self.article7questionnaire, exclude=exclude
            )
            attributes['submission_id'] = clone.pk
            self.article7questionnaire.__class__.objects.create(**attributes)

        for related_data, aggr_flag in self.RELATED_DATA:
            for instance in getattr(self, related_data).all():
                if hasattr(instance, 'blend_item') and instance.blend_item:
                    continue
                attributes = model_to_dict(instance, exclude=exclude)
                attributes['submission_id'] = clone.pk
                instance_clone = instance.__class__.objects.create(**attributes)

                # Related data instances might also have their related data;
                # in this case they should implement a "clone" method.
                if hasattr(instance, 'clone'):
                    instance.clone(new_instance=instance_clone)

        return clone

    def get_storage_directory(self):
        """
        This determines the location at which files related to the submission
        will be saved.
        """
        return os.path.join(
            SUBMISSION_ROOT_DIR,
            self.reporting_period.name,
            self.obligation.obligation_type,
            self.party.abbr,
            str(self.version)
        )

    def delete_disk_file(self, file_name):
        """
        Used to delete an existing file from disk.
        """
        env_file = os.path.join(
            self.get_storage_directory(),
            file_name
        )
        try:
            os.remove(env_file)
        except FileNotFoundError:
            pass

    def make_current(self):
        # Avoid race conditions
        with transaction.atomic():
            # Find all non-superseded (current) versions and make them
            # superseded, also purging any aggregated data they generated
            # (there should actually be at most one such version, but erring
            # on the safe side).
            current_versions = (
                Submission.objects.select_for_update()
                .filter(
                    party=self.party,
                    reporting_period=self.reporting_period,
                    obligation=self.obligation,
                    flag_superseded=False
                )
                .exclude(pk=self.pk)
                .exclude(_current_state__in=self.editable_states)
            )
            for version in current_versions:
                version.flag_superseded = True
                version.save(update_fields=('flag_superseded',))
                version.purge_aggregated_data(invalidate_cache=False)
            self.flag_superseded = False
            self.save(update_fields=('flag_superseded',))

        # Populate submission-specific aggregated data
        self.fill_aggregated_data()

    def make_previous_current(self):
        """
        When current submission is set to recalled, a different one should be
        set as current (not invalid & non-superseded) if available.

        Please note that a submission that has flag_valid set to None
        (which means that it has not yet been fully checked by OS) can become
        current.
        However, an invalid or recalled submission cannot become current.
        """
        # Avoid race conditions
        with transaction.atomic():
            versions = (
                Submission.objects.select_for_update()
                .filter(
                    party=self.party,
                    reporting_period=self.reporting_period,
                    obligation=self.obligation,
                )
                .exclude(flag_valid=False)
                .exclude(pk=self.pk)
                .exclude(_current_state__in=self.editable_states)
                .exclude(_current_state__in=self.incorrect_states)
                .order_by('-version')
            )
            latest = versions.first()
            if latest:
                latest.flag_superseded = False
                latest.save(update_fields=('flag_superseded',))

        # Populate submission-specific aggregated data. Kept out of the atomic
        # block due to execution time.
        if latest:
            latest.fill_aggregated_data()
        else:
            # If no submission is now current, purge all related aggregated data
            self.purge_aggregated_data()

    @classmethod
    @transaction.atomic
    def latest_submitted_for_parties(cls, obligation, reporting_period, parties):
        rv = {}

        versions = (
            Submission.objects.select_for_update()
            .filter(
                party__in=parties,
                reporting_period=reporting_period,
                obligation=obligation,
            )
            .exclude(flag_valid=False)
            .order_by('version')
        )

        for submission in versions:
            if submission.data_changes_allowed:
                continue
            if submission.in_incorrect_state:
                continue

            # overwrite previous versions
            rv[submission.party] = submission

        return rv

    @classmethod
    def latest_submitted(cls, obligation, party, reporting_period):
        res = cls.latest_submitted_for_parties(obligation, reporting_period, [party])
        return res.get(party)

    @property
    def versions(self):
        return Submission.objects.filter(
            party=self.party,
            reporting_period=self.reporting_period,
            obligation=self.obligation,
        ).prefetch_related('created_by')

    def get_previous_version(self):
        # TODO: implement this properly - maybe based on HistoricalSubmission
        # or just on latest() on the superseded versions queryset
        if self.version == 1:
            return None
        return Submission.objects.filter(
            obligation=self.obligation,
            party=self.party,
            reporting_period=self.reporting_period,
            version=(self.version - 1)
        ).first()

    def get_change_history(self):
        """
        Returns a list of relevant changes (i.e. state changes for now) for
        all versions pertaining to this submission's party/period/obligation,
        together with the time of change and user which performed the change.
        """
        display_fields = ['version', 'history_date', 'history_user',]
        return HistoricalSubmission.objects.filter(
            party=self.party,
            reporting_period=self.reporting_period,
            obligation=self.obligation,
        ).order_by(
            'history_date'
        ).values(
            *self.WATCHED_FIELDS, *display_fields,
        )

    def has_filled_nominations(self):
        return self.nominations.exists()

    def has_filled_approved_exemptions(self):
        return self.exemptionapproveds.exists()

    def is_emergency(self):
        return self.flag_emergency

    def can_change_submitted_at(self, user):
        if self.obligation.obligation_type == ObligationTypes.EXEMPTION.value:
            if user.is_secretariat and not self.in_final_state:
                return True

        return (
            not user.is_read_only
            and user.is_secretariat
            and self.filled_by_secretariat
            and self.in_initial_state
        )

    def is_submitted_at_visible(self, user):
        if user.is_secretariat:
            return True
        elif user.party is not None and user.party == self.party:
            return not self.data_changes_allowed

    def is_submitted_at_mandatory(self, user):
        return self.can_change_submitted_at(user)

    def is_submitted_at_automatically_filled(self, user):
        """
        Return True if the user is a Party Reporter.
        """
        return user.party is not None

    def set_annex_f_reported(self):
        """
        Called at Submit to mark the time at which substances in annex group F
        have been reported.
        """
        if self.flag_has_reported_f is True and self.date_reported_f is None:
            self.date_reported_f = timezone.now().date()
            self.save(update_fields=('date_reported_f',))

    def check_submitted_at_modified(self):
        if 'submitted_at' in self.tracker.changed().keys():
            return True
        return False

    def get_reported_groups(self):
        """
        Returns the substance groups reported in this submission.
        """
        reported_groups = [
            value for key, value in self.GROUP_FLAGS_MAPPING.items()
            if getattr(self, key, False) is True
        ]
        return Group.objects.filter(group_id__in=reported_groups)

    @cached_property
    def party_history(self):
        """
        Returns the PartyHistory entry corresponding to this submission's party
        and reporting_period.
        """
        return PartyHistory.objects.filter(
            party=self.party, reporting_period=self.reporting_period
        ).first()

    def purge_aggregated_data(self, invalidate_cache=True):
        """
        Deletes the aggregated data generated by this submission.
        """
        if not self.obligation.is_aggregateable:
            return

        groups = self.get_reported_groups()

        # Clear this submission from the list of submissions for its related
        # aggregations
        for group in groups:
            aggregation = ProdCons.objects.filter(
                party=self.party,
                reporting_period=self.reporting_period,
                group=group
            ).first()
            if aggregation is None:
                continue
            obligation_type = self.obligation.obligation_type
            if self.id in aggregation.submissions.get(obligation_type, []):
                submissions_set = set(aggregation.submissions[obligation_type])
                submissions_set.remove(self.id)
                aggregation.submissions[obligation_type] = list(submissions_set)
            aggregation.save(invalidate_cache=False)

        # Set to 0 all values that had been populated by this submission.
        # Any aggregation row that becomes full-zero after that is deleted.
        for related, aggr_flag in self.RELATED_DATA:
            if not aggr_flag:
                continue
            # Clear ODP aggregations
            related_manager = getattr(self, related)
            if hasattr(related_manager.model, 'clear_aggregated_data'):
                related_manager.model.clear_aggregated_data(
                    submission=self,
                    reported_groups=groups,
                    invalidate_cache=invalidate_cache
                )
            # Clear MT aggregations
            if related_manager.count() > 0:
                if hasattr(related_manager.model, 'clear_aggregated_mt_data'):
                    related_manager.model.clear_aggregated_mt_data(
                        submission=self,
                        queryset=related_manager.all().filter(
                            substance__isnull=False
                        )
                    )

    def fill_aggregated_data(self):
        """
        Fill aggregated data from this submission into the corresponding
        aggregation model instance.

        Returns list of ID's of ProdCons objects that have been created or
        modified.
        """
        if not self.obligation.is_aggregateable:
            return

        groups = self.get_reported_groups()

        # Create all-zero ProdCons rows for all reported groups.
        # For ProdConsMT this is not necessary.
        ret = []
        for group in groups:
            aggregation, created = ProdCons.objects.get_or_create(
                party=self.party,
                reporting_period=self.reporting_period,
                group=group
            )
            obligation_type = self.obligation.obligation_type
            if obligation_type in aggregation.submissions:
                submissions_set = set(aggregation.submissions[obligation_type])
                submissions_set.add(self.id)
                aggregation.submissions[obligation_type] = list(submissions_set)
            else:
                aggregation.submissions[obligation_type] = [self.id,]
            # Do not invalidate cache as it's already been done
            aggregation.save(invalidate_cache=False)
            ret.append(aggregation.id)

        for related, aggr_flag in self.RELATED_DATA:
            if not aggr_flag:
                continue
            related_manager = getattr(self, related)
            if related_manager.count() > 0:
                if hasattr(related_manager.model, 'fill_aggregated_data'):
                    related_manager.model.fill_aggregated_data(
                        submission=self, reported_groups=groups
                    )
                if hasattr(related_manager.model, 'fill_aggregated_mt_data'):
                    related_manager.model.fill_aggregated_mt_data(
                        submission=self,
                        queryset=related_manager.all().filter(
                            substance__isnull=False
                        )
                    )
        return ret

    def get_aggregated_data(self, baseline=False, populate_baselines=True):
        """
        Returns dict of non-persistent calculated aggregated data for this
        submission, without writing to the database.

        baseline - if True, then quantities are multiplied by the substance's
        gwp_baseline (useful when calculating baselines)

        populate_baselines - if True, the baselines/limits aggregation fields
        will be populated from the baselines/limits table.
        """

        group_mapping = {
            group: ProdCons(
                party=self.party,
                reporting_period=self.reporting_period,
                group=group
            )
            for group in self.get_reported_groups()
        }
        # Pre-calculate all totals in case there is no actual related data
        for aggregation in group_mapping.values():
            if baseline is True:
                # Override prodcons.decimals, because GWP should be rounded to 0
                # and there are some values ending in .45, which become
                # the next integer upon double rounding.
                aggregation.decimals = 15

            if populate_baselines:
                aggregation.populate_limits_and_baselines()
            aggregation.calculate_totals()

        for related, aggr_flag in self.RELATED_DATA:
            if not aggr_flag:
                continue
            related_manager = getattr(self, related)
            if related_manager.count() > 0:
                if hasattr(related_manager.model, 'get_aggregated_data'):
                    related_manager.model.get_aggregated_data(
                        submission=self,
                        reported_groups=group_mapping,
                        baseline=baseline,
                        populate_baselines=populate_baselines
                    )

        return group_mapping

    def get_aggregated_mt_data(self):
        """
        Returns dict of non-persistent calculated MT aggregated data for this
        submission, without touching the database.
        """

        subst_mapping = {}

        for related, aggr_flag in self.RELATED_DATA:
            if not aggr_flag:
                continue
            related_manager = getattr(self, related)
            if related_manager.count() > 0:
                if hasattr(related_manager.model, 'get_aggregated_mt_data'):
                    related_manager.model.get_aggregated_mt_data(
                        submission=self,
                        queryset=related_manager.all().filter(
                            substance__isnull=False
                        ),
                        reported_substances=subst_mapping,
                    )

        return subst_mapping

    def __str__(self):
        revision = '-' if self.revision_major is None else \
            f'{self.revision_major}.{self.revision_minor}'
        return f'{self.party.name} report on {self.obligation.name} ' \
               f'for {self.reporting_period.name} - # {revision}'

    class Meta:
        # TODO: this constraint may not be true in the corner case of
        # obligations where reporting is done per-case (e.g. transfers).
        # It may happen that several transfers take place in the same
        # reporting period - this means that the constraint should be checked
        # using custom logic on save() rather than enforced here. Investigate!
        unique_together = (
            'party', 'reporting_period', 'obligation', 'version'
        )
        db_table = 'submission'

    def delete(self, *args, **kwargs):
        if not self.deletion_allowed:
            raise MethodNotAllowed(
                _("Unable to delete submission because it is submitted.")
            )
        # We need to delete all related data entries before being able to
        # delete the submission. We leave it to the interface to ask "are you
        # sure?" to the user.
        with transaction.atomic():
            for related_data, aggr_flag in self.RELATED_DATA:
                related_qs = getattr(self, related_data).all()
                if related_qs:
                    related_qs.delete()

            super().delete(*args, **kwargs)

    def clean(self):
        if not self.reporting_period.is_reporting_allowed:
            raise ValidationError(
                _("Unable to start reporting for this period.")
            )

        if (
            Submission.non_exempted_fields_modified(self)
            and not self.data_changes_allowed
        ):
            raise ValidationError(
                _("Unable to change submission because it is already submitted.")
            )

        if (
            self.flag_confirmed_blanks is True
            and self.flag_checked_blanks is False
        ):
            raise ValidationError(
                _("Unable to confirm blanks if blanks are not checked first")
            )

        super().clean()

    @transaction.atomic
    def save(
        self,
        force_insert=False, force_update=False, using=None, update_fields=None
    ):
        # Several actions need to be performed on first save
        # No need to check `update_fields`, since this is the first
        # save. If other fields are changed during an update, they
        # must be added to the `update_fields` list, since we are using
        # the PartialUpdateMixIn.
        if not self.pk or force_insert:

            # Auto-increment submission version if saving for a
            # party-obligation-period combo which already has submissions.
            # select_for_update() is used to lock the rows and ensure proper
            # concurrency.
            submissions = Submission.objects.select_for_update().filter(
                party=self.party,
                obligation=self.obligation
            )
            current_submissions = submissions.filter(
                reporting_period=self.reporting_period
            )
            # Check that OS and party have only one data_entry submission
            has_peers, message = self.has_initial_state_peers_by_same_user_type(
                current_submissions, self.created_by
            )
            if has_peers:
                raise ValidationError(message)

            if current_submissions:
                self.version = current_submissions.latest('version').version + 1

            # On first save we need to instantiate the submission's workflow
            if self.obligation.obligation_type in (
                ObligationTypes.ART7.value,
                ObligationTypes.ESSENCRIT.value,
                ObligationTypes.HAT.value,
            ):
                self._workflow_class = 'default'
            elif self.obligation.obligation_type == ObligationTypes.EXEMPTION.value:
                self._workflow_class = 'default_exemption'
            # TODO: merge simplified, transfer and process_agent workflows
            # and migrate existing data (also HistoricalSubmissions)
            elif self.obligation.obligation_type == ObligationTypes.TRANSFER.value:
                self._workflow_class = 'default_transfer'
            elif self.obligation.obligation_type == ObligationTypes.PROCAGENT.value:
                self._workflow_class = 'default_process_agent'
            else:
                self._workflow_class = 'simplified'
            self._current_state = \
                self.workflow().state.workflow.initial_state.name

            # The default value for reporting channel is 'Web form'
            # when creating a new submission.
            # The prefill will be skipped if it's a clone action or a
            # legacy import.
            if not getattr(self, 'reporting_channel'):
                self.reporting_channel = ReportingChannel.get_default(
                    self.created_by
                )

            # Prefill Art 7 has_reported flags
            if self.obligation.obligation_type == ObligationTypes.ART7.value:
                if self.cloned_from:
                    for flag in self.GROUP_FLAGS_MAPPING.keys():
                        setattr(self, flag, getattr(self.cloned_from, flag))
                else:
                    groups = Group.get_report_groups(
                        self.party, self.reporting_period
                    )
                    for g in groups:
                        setattr(
                            self, self.FLAG_GROUPS_MAPPING[g.group_id], True
                        )

            # Prefill blank-related flags if needed
            if self.obligation.obligation_type in [
                ObligationTypes.ART7.value, ObligationTypes.HAT.value
            ]:
                if not self.filled_by_secretariat:
                    self.flag_checked_blanks = True
                    self.flag_confirmed_blanks = True
                    self.flag_has_blanks = False

            self.clean()
            ret = super().save(
                force_insert=force_insert, force_update=force_update,
                using=using, update_fields=update_fields
            )

            # Prefill "Submission info" with values from the most recent
            # submission when creating a new submission for the same obligation
            # and party.
            # The prefill will be skipped if it's a clone action.
            if not hasattr(self, 'info'):
                latest_submission = submissions.exclude(
                    pk=self.pk
                ).order_by('-updated_at').first()
                if latest_submission and hasattr(latest_submission, 'info'):
                    latest_info = latest_submission.info
                    info = SubmissionInfo.objects.create(
                        submission=self,
                        reporting_officer=latest_info.reporting_officer,
                        designation=latest_info.designation,
                        organization=latest_info.organization,
                        postal_address=latest_info.postal_address,
                        country=latest_info.country,
                        phone=latest_info.phone,
                        email=latest_info.email,
                        date=latest_info.date,
                        # Don't clone the submission format, it's only needed
                        # for Art 7 and there is already a default value for it
                        # submission_format=latest_info.submission_format
                    )
                else:
                    info = SubmissionInfo.objects.create(submission=self)

            return ret

        else:
            # This is not the first save
            # Make sure that update-related fields (updated_at, last_edited_by)
            # are properly updated even for partial updates.
            if update_fields is not None:
                update_fields = list(
                    set(list(update_fields) + ['updated_at', 'last_edited_by'])
                )

            self.clean()

            # Only create a history entry if any of the WATCHED_FIELDS
            # has changed.
            enable_history = any(
                [self.tracker.has_changed(f) for f in self.WATCHED_FIELDS]
            )
            if not enable_history:
                self.skip_history_when_saving = True
            try:
                ret = super().save(
                    force_insert=force_insert, force_update=force_update,
                    using=using, update_fields=update_fields
                )
            finally:
                if not enable_history:
                    del self.skip_history_when_saving
            return ret

    def set_submitted(self):
        self.submitted_at = timezone.now().date()
        self.save(update_fields=('submitted_at',))


class SubmissionFormat(models.Model):
    """
    Describes type of submission.
    """

    name = models.CharField(unique=True, max_length=256)
    description = models.CharField(max_length=256, blank=True)

    is_default_party = models.BooleanField(
        default=False,
        verbose_name='Is default for parties',
        help_text="Indicates whether this submission format is default for party."
    )

    @classmethod
    def get_default(cls, user):
        if user.party is not None:
            return cls.objects.filter(is_default_party=True).first()
        return None

    def clean(self):
        unique_fields = {
            'is_default_party': 'party',
        }
        for field in unique_fields.keys():
            queryset = SubmissionFormat.objects.filter(**{field: True})

            if (
                getattr(self, field, False) is True
                and queryset.count() > 0
                and self not in queryset
            ):
                raise ValidationError(
                    _(
                        f'Unable to set default submission format. Another submission format is already set as default for '
                        f'{unique_fields[field]}.'
                    )
                )

    class Meta:
        db_table = "submission_format"

    def __str__(self):
        return self.name


class SubmissionInfoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            # Not using select_related because it triggers an error in clone()
            # at statement SubmissionInfo.objects.update_or_create
            'country',
            'submission',
            'submission__reporting_period',
            'submission__obligation',
            'submission__party',
        )


class SubmissionInfo(ModifyPreventionMixin, models.Model):
    """
    Model for storing submission info.
    """
    objects = SubmissionInfoManager()

    submission = models.OneToOneField(
        Submission,
        related_name='info',
        on_delete=models.CASCADE
    )

    reporting_officer = models.CharField(max_length=256, blank=True)
    designation = models.CharField(max_length=256, blank=True)
    organization = models.CharField(max_length=256, blank=True)
    postal_address = models.CharField(max_length=512, blank=True)
    country = models.ForeignKey(
        Party,
        related_name='infos',
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )
    phone = models.CharField(max_length=128, blank=True)
    email = models.EmailField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    submission_format = models.ForeignKey(
        SubmissionFormat,
        related_name="infos",
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    tracker = FieldTracker()

    class Meta:
        db_table = "submission_info"

    def __str__(self):
        return f'{self.submission} - Info'
