import copy

import xworkflows

from .emails import notify_workflow_transitioned


__all__ = [
    'BaseStateDescription',
    'BaseWorkflow',
]


class BaseStateDescription(xworkflows.Workflow):
    """
    Overrides the xworkflows.Workflow to perform sending notification emails in
    the log_transition() method.
    """
    states = ()
    transitions = ()
    initial_state = None
    # Per-state and per-user permissions as nested dictionaries
    permissions = {}

    def log_transition(self, transition, previous_state, workflow):
        """
        Overriding log_transition to send email on each transition.
        """
        notify_workflow_transitioned(workflow, transition)
        super().log_transition(transition, previous_state, workflow)


class BaseWorkflow(xworkflows.WorkflowEnabled):
    """
    Workflow-enabled class that will be instantiated by the model each time
    a transition is performed.
    """
    # States from which submission cannot change state anymore
    final_states = []
    # States in which changing submission data is allowed
    editable_data_states = []
    # States which signify incorrect data has been entered
    incorrect_data_states = []

    state = BaseStateDescription()

    def __init__(self, model_instance, user):
        # We need this to add a back-reference to the
        # `Submission` model instance using this object.
        self.model_instance = model_instance
        self.user = user
        super().__init__()

    @property
    def finished(self):
        return self.state in self.final_states

    @property
    def data_changes_allowed(self):
        return self.state in self.editable_data_states

    @property
    def deletion_allowed(self):
        return self.in_initial_state

    @property
    def in_initial_state(self):
        return self.state == self.state.workflow.initial_state

    @property
    def in_incorrect_data_state(self):
        return self.state in self.incorrect_data_states

    def is_secretariat_or_same_party_owner(self, submission):
        owner = submission.created_by
        return (
            (self.user.is_secretariat and owner.is_secretariat)
            or (self.user.party is not None and self.user.party == owner.party)
        )

    @property
    def permissions_matrix(self):
        """
        Returns the permissions matrix nested dictionaries based on
        current user and submissions creator.
        """
        # TODO: there is no need to modify and return the whole initial matrix,
        # this is only to make initial frontend changes easier.

        position = None
        if self.user is not None:
            created_by_secretariat = self.model_instance.filled_by_secretariat
            #    0 -> created by party, accessed by party
            #    1 -> created by party, accessed by secretariat
            #    2 -> created by secretariat, accessed by party
            #    3 -> created by secretariat, accessed by secretariat
            if self.user.is_secretariat and created_by_secretariat:
                position = 3
            elif self.user.party and created_by_secretariat:
                position = 2
            elif self.user.is_secretariat and not created_by_secretariat:
                position = 1
            elif self.user.party and not created_by_secretariat:
                position = 0

        permissions_dict = copy.deepcopy(self.state.workflow.permissions)

        for key, permission_type_dict in permissions_dict.items():
            permission_list = permission_type_dict.get(self.state.name, [])
            if permission_list and position is not None:
                permission = permission_list[position]
            else:
                # default for non-secretariat & non-party users (or unknown
                # states) is True, which means read-only.
                permission = True

            for sub_key, sub_value in permission_type_dict.items():
                # Set the same value for all elements, to make it easier
                # on the frontend side.
                permission_type_dict[sub_key] = [permission] * len(sub_value)

        return permissions_dict
