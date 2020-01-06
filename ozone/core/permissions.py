from django.contrib.auth import get_user_model

from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Blend, Submission, Party


User = get_user_model()


class IsSecretariat(BasePermission):
    """
    This is used for evaluating persmissions on all views that can only be
    accessed by secretariat
    """
    def has_permission(self, request, view):
        return request.user.is_secretariat

    def has_object_permission(self, request, view, obj):
        return request.user.is_secretariat


class IsSecretariatOrSameParty(BasePermission):
    """
    Check if user is secretariat or has the same party as that on the object.
    """
    def has_permission(self, request, view):
        # We leave it to has_object_permission to check everything.
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_secretariat:
            return True
        else:
            return request.user.party == obj.party


class IsSecretariatOrSafeMethod(BasePermission):
    """
    Check if user is secretariat or safe method.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return request.user.is_secretariat and not request.user.is_read_only


class IsSecretariatOrSamePartySubmission(BasePermission):
    """
    This is used for evaluating permissions on Submission views.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        # Definitely not a safe method :)
        sub_pk = view.kwargs.get('pk', None)
        if sub_pk:
            # Submission object already exists.
            submission = Submission.objects.get(pk=sub_pk)
            return submission.has_edit_rights(request.user)
        else:
            # It's a create
            party_id = request.data.get('party', None)
            if not party_id:
                return False
            party = Party.objects.get(id=party_id)
            return Submission.has_create_rights_for_party(party, request.user)

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            return obj.has_edit_rights(request.user)
        return obj.has_read_rights(request.user)


class IsSecretariatOrSamePartySubmissionRemarks(BasePermission):
    """
    This is used for evaluating permissions on Submission-related views (e.g.
    Article 7 reports etc).
    `submission_pk` will *always* be set to something in this case.
    """
    def has_permission(self, request, view):
        submission_id = view.kwargs.get('submission_pk', None)
        if not submission_id:
            return False
        submission = Submission.objects.get(pk=submission_id)
        if request.method not in SAFE_METHODS:
            # The serializer will look more closely at the modified fields
            return submission.can_edit_remarks(request.user)
        else:
            # Whoever can view the submission can also view its remarks
            return submission.has_read_rights(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            return obj.can_edit_remarks(request.user)
        return obj.has_read_rights(request.user)


class IsSecretariatOrSamePartySubmissionFlags(BasePermission):
    """
    This is used for evaluating permissions on Submission-related views (e.g.
    Article 7 reports etc).
    `submission_pk` will *always* be set to something in this case.
    """
    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            submission_id = view.kwargs.get('submission_pk', None)
            if not submission_id:
                return False
            submission = Submission.objects.get(pk=submission_id)
            # The serializer will look more closely at the modified fields
            # and also reject some changes based on state and flag-user mapping
            return submission.can_edit_flags(request.user)

        # No need to call has_read_rights here, as queryset is filtered
        return True

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            return obj.can_edit_flags(request.user)
        return obj.submission.has_read_rights(request.user)


class IsSecretariatOrSamePartySubmissionClone(BasePermission):
    """
    This is used for deciding whether the user has, in principle, permission
    to clone this specific submission.
    DRF allows specifying permission classes per action (i.e. in the params of
    the @action decorator). However, since in the URL the action name is not
    followed by any pk, only the return value of has_permission() will be taken
    into account; has_object_permission() is never called in this case.
    """
    def has_permission(self, request, view):
        """
        In principle, if a user can see a certain submission, he/she can also
        clone it, *if* he is not read-only. :)
        """
        if request.user.is_read_only:
            return False

        submission_id = view.kwargs.get('pk', None)
        if not submission_id:
            return False
        submission = Submission.objects.get(pk=submission_id)
        return submission.has_read_rights(request.user)

    def has_object_permission(self, request, view, obj):
        return True


class IsSecretariatOrSamePartySubmissionTransition(BasePermission):
    """
    This is used for deciding whether the user has, in principle, permission
    to perform transitions on this specific submission.
    DRF allows specifying permission classes per action (i.e. in the params of
    the @action decorator). However, since in the URL the action name is not
    followed by any pk, only the return value of has_permission() will be taken
    into account; has_object_permission() is never called in this case.
    """
    def has_permission(self, request, view):
        """
        In principle, if a user can see a certain submission, he/she can also
        call the endpoint to perform a transition on it,
        *if* he is not read-only. :)
        Still, certain transitions can only be performed by Party/Secretariat,
        but that is being checked at workflow level! This only deals with being
        in principle able to call the endpoint or not.
        """
        if request.user.is_read_only:
            return False

        submission_id = view.kwargs.get('pk', None)
        if not submission_id:
            return False
        submission = Submission.objects.get(pk=submission_id)
        return submission.has_read_rights(request.user)

    def has_object_permission(self, request, view, obj):
        return True


class IsSecretariatOrSamePartySubmissionRelated(BasePermission):
    """
    This is used for evaluating permissions on Submission-related views (e.g.
    Article 7 reports etc) for models that have a submission as FK.
    `submission_pk` will *always* be set to something in this case.
    """
    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            submission_id = view.kwargs.get('submission_pk', None)
            if not submission_id:
                return False
            submission = Submission.objects.get(pk=submission_id)
            # All Submission-related fields have remarks!
            # It is up to the serializer/model to further check whether
            # remarks or data have been changed by someone who shouldn't have
            return (
                submission.has_edit_rights(request.user)
                or submission.can_edit_remarks(request.user)
            )
        # No need to call has_read_rights here, as queryset is filtered
        return True

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            # All Submission-related fields have remarks!
            # It is up to the serializer/model to further check whether
            # remarks or data have been changed by someone who shouldn't have
            return (
                obj.submission.has_edit_rights(request.user)
                or obj.submission.can_edit_remarks(request.user)
            )
        return obj.submission.has_read_rights(request.user)


class IsSecretariatOrSamePartyBlend(BasePermission):
    """
    This is used for evaluating permissions on Blend views.

    It allows unauthenticated users to list non-custom blends.
    """
    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            blend_pk = view.kwargs.get('pk', None)
            if blend_pk:
                # Blend object already exists.
                blend = Blend.objects.get(pk=blend_pk)
                return blend.has_edit_rights(request.user)
            else:
                # It's a create
                party_id = request.data.get('party', None)
                if not party_id:
                    return False
                party = Party.objects.get(id=party_id)
                return Blend.has_create_rights_for_party(party, request.user)

        return True

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            return obj.has_edit_rights(request.user)
        return obj.has_read_rights(request.user)


class IsCorrectObligation(BasePermission):
    """Check if the API is for the correct obligation type."""

    def has_permission(self, request, view):
        # Explicit is better than implicit.
        if view.obligation_types is None:
            return True
        submission_id = view.kwargs.get('submission_pk', None)
        if not submission_id:
            return False
        obligation_type = Submission.objects.get(pk=submission_id).obligation.obligation_type
        return obligation_type in view.obligation_types


class IsSecretariatOrSamePartyUser(BasePermission):
    """
    Check if user can view/update the profile of another user.
    """

    def has_permission(self, request, view):
        user_pk = view.kwargs.get('pk', None)
        if user_pk:
            user = User.objects.get(pk=user_pk)
            if request.method not in SAFE_METHODS:
                return user.has_edit_rights(request.user)
            else:
                return user.has_read_rights(request.user)

        # It means that we only want the current logged in user;
        # get_queryset will take care of this.
        return True


class IsSecretariatOrSamePartyAggregation(BasePermission):
    """
    This is used for evaluating permissions on aggregation views.

    For now at least, aggregation views are read-only.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            return False
        return True


class IsSecretariatOrSamePartyLimit(BasePermission):
    """
    This is used for evaluating permissions on limits views.

    For now at least, limits views are read-only.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            return False
        return True


class IsSecretariatOrSamePartySubmissionRelatedRO(BasePermission):
    """
    This is used for evaluating permissions on Transfer views.

    For now at least, Transfer views are read-only.
    """
    def has_permission(self, request, view):
        submission_id = view.kwargs.get('submission_pk', None)
        if not submission_id:
            return False
        sub = Submission.objects.get(pk=submission_id)

        return (
            request.method in SAFE_METHODS
            and sub.has_read_rights(request.user)
        )

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            return False
        return True
