import xworkflows

from .base import BaseStateDescription, BaseWorkflow


__all__ = [
    'DefaultExemptionWorkflow',
]


class DefaultExemptionWorkflowStateDescription(BaseStateDescription):
    """
    These are the default submission states and transitions
    for Exemption workflow.
    """
    states = (
        ('data_entry', 'Data Entry'),
        ('submitted', 'Submitted'),
        ('processing', 'Processing'),
        ('finalized', 'Finalized'),
    )

    transitions = (
        ('submit', 'data_entry', 'submitted'),
        ('process', ('data_entry', 'submitted'), 'processing'),
        ('finalize', 'processing', 'finalized'),
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
            'processing': [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'submission_format': {
            'data_entry': [True, True, True, False],
            'submitted':  [True, True, True, True],
            'processing': [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'reporting_officer': {
            'data_entry': [False, True, True, False],
            'submitted':  [True, True, True, True],
            'processing': [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'submitted_at': {
            'data_entry': [True, True, True, False],
            'submitted':  [True, True, True, True],
            'processing': [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'other_submission_info_data': {
            'data_entry': [False, True, True, False],
            'submitted':  [True, True, True, True],
            'processing': [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'files': {
            'data_entry': [False, True, True, False],
            'submitted':  [True, False, True, True],
            'processing': [True, False, True, False],
            'finalized':  [True, True, True, True],
        },
        'flag_provisional': {
            'data_entry': [False, True, True, False],
            'submitted':  [True, False, True, False],
            'processing': [True, False, True, False],
            'finalized':  [True, True, True, True],
        },
        'flag_emergency': {
            'data_entry': [False, True, True, False],
            'submitted':  [True, True, True, True],
            'processing': [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'substance_data': {
            'data_entry': [False, True, True, False],
            'submitted':  [True, True, True, True],
            'processing': [True, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'remarks_party': {
            'data_entry': [False, True, True, False],
            'submitted':  [False, True, True, True],
            'processing': [False, True, True, True],
            'finalized':  [True, True, True, True],
        },
        'remarks_secretariat': {
            'data_entry': [False, True, True, False],
            'submitted':  [False, True, True, False],
            'processing': [False, True, True, False],
            'finalized':  [True, True, True, True],
        }
    }


class DefaultExemptionWorkflow(BaseWorkflow):
    """
    Implements custom transition logic for the default Exemption workflow.
    """

    final_states = ['finalized']
    editable_data_states = ['data_entry', 'submitted', 'processing']
    incorrect_data_states = []

    state = DefaultExemptionWorkflowStateDescription()

    @xworkflows.transition_check('submit')
    def check_submit(self):
        return (
            not self.user.is_read_only
            and self.is_secretariat_or_same_party_owner(self.model_instance)
        )

    @xworkflows.transition_check('process')
    def check_process(self):
        # Do not allow secretariat users to directly send party-filled
        # submissions from data_entry to processing.
        if self.in_initial_state:
            if not self.model_instance.filled_by_secretariat:
                return False
        return self.user.is_secretariat and not self.user.is_read_only

    @xworkflows.transition_check('finalize')
    def check_finalize(self):
        return self.user.is_secretariat and not self.user.is_read_only

    @xworkflows.transition('submit')
    def submit(self):
        if self.model_instance.is_submitted_at_automatically_filled(self.user):
            self.model_instance.set_submitted()
