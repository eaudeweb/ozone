import xworkflows

from .base import BaseStateDescription, BaseWorkflow


__all__ = [
    'DefaultTransferWorkflow',
]


class DefaultTransferWorkflowStateDescription(BaseStateDescription):
    """
    These are the default submission states and transitions
    for Transfers reporting.
    """
    states = (
        ('data_entry', 'Data Entry'),
        ('submitted', 'Submitted'),
        ('finalized', 'Finalized'),
    )

    transitions = (
        ('submit', 'data_entry', 'submitted'),
        ('finalize', 'submitted', 'finalized'),
    )

    initial_state = 'data_entry'

    # Mapping for the permissions in this workflow, according to state
    #    0 -> created by party, accessed by party
    #    1 -> created by party, accessed by secretariat
    #    2 -> created by secretariat, accessed by party
    #    3 -> created by secretariat, accessed by secretariat
    #
    #    True  -> read-only
    #    False -> not(read-only)
    #
    # Is used by the permissions_matrix() method to return relevant
    # permissions.
    permissions = {
        'reporting_channel': {
            'data_entry': [True, True, True, False],
            'submitted':  [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'submission_format': {
            'data_entry': [True, True, True, False],
            'submitted':  [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'reporting_officer': {
            'data_entry': [False, True, True, False],
            'submitted':  [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'submitted_at': {
            'data_entry': [True, True, True, False],
            'submitted':  [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'other_submission_info_data': {
            'data_entry': [False, True, True, False],
            'submitted':  [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'files': {
            'data_entry': [False, True, True, False],
            'submitted':  [True, False, True, True],
            'finalized':  [True, True, True, True],
        },
        'flag_provisional': {
            'data_entry': [False, True, True, False],
            'submitted':  [True, False, True, False],
            'finalized':  [True, True, True, True],
        },
        'substance_data': {
            'data_entry': [False, True, True, False],
            'submitted':  [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'remarks_party': {
            'data_entry': [False, True, True, False],
            'submitted':  [False, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'remarks_secretariat': {
            'data_entry': [False, True, True, False],
            'submitted':  [False, True, True, False],
            'finalized':  [True, True, True, True],
        }
    }


class DefaultTransferWorkflow(BaseWorkflow):

    """
    Implements custom transition logic for the default transfer workflow.
    """
    final_states = ['finalized']
    editable_data_states = ['data_entry']
    incorrect_data_states = []

    state = DefaultTransferWorkflowStateDescription()

    @xworkflows.transition_check('submit')
    def check_submit(self):
        """
        Ensure that we only allow submitting submissions for there roles:
        * Party-write user from Party to which the submission refers to,
          only if the submission was started by the Party
        * Secretariat-write user, only if the submission was started by
          Secretariat
        """
        return (
            not self.user.is_read_only
            and self.is_secretariat_or_same_party_owner(self.model_instance)
            and self.model_instance.is_submittable()
        )

    @xworkflows.transition('submit')
    def submit(self):
        # Set submitted_at flag
        if self.model_instance.is_submitted_at_automatically_filled(self.user):
            self.model_instance.set_submitted()

    @xworkflows.transition_check('finalize')
    def check_finalize(self):
        """
        Ensure that only secretariat-edit users can finalize submissions
        """
        return not self.user.is_read_only and self.user.is_secretariat
