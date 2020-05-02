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
