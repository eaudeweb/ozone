from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, F
from django.utils.translation import gettext_lazy as _

from guardian.mixins import GuardianUserMixin
from rest_framework.authtoken.models import Token

from .party import Party, PartyGroup, Language


class User(GuardianUserMixin, AbstractUser):

    party = models.ForeignKey(
        Party, related_name='users',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        limit_choices_to=Q(parent_party_id=F('id'))
    )
    created_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    activated = models.BooleanField(default=True)

    is_secretariat = models.BooleanField(default=False)

    # UNEP CAP users support the counties in submitting their data correctly;
    # they have read-only access to all (including draft) data for certain
    # groups of countries.
    is_cap = models.BooleanField(default=False)
    # Only relevant for UNEP CAP users
    party_group = models.ForeignKey(
        PartyGroup,
        related_name='users',
        default=None,
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    # Both Party and Secretariat users can be read-only
    is_read_only = models.BooleanField(default=True)

    language = models.ForeignKey(
        Language,
        default=Language.DEFAULT_LANGUAGE_ID,
        related_name='users',
        on_delete=models.PROTECT
    )

    email = models.EmailField(_('email address'))
    is_notified = models.BooleanField(
        default=True,
        verbose_name='is notified',
        help_text="Automatic e-mail notifications are not sent if set to false"
    )

    @property
    def role(self):
        if self.is_secretariat:
            if not self.is_read_only:
                return 'Secretariat Edit'
            else:
                return 'Secretariat Read-Only'
        elif self.party:
            if not self.is_read_only:
                return 'Party Reporter'
            else:
                return 'Party Read-Only'
        elif self.is_cap:
            return 'UNEP CAP Read-only'

    def has_edit_rights(self, user):
        if self == user:
            return True
        return False

    def has_read_rights(self, user):
        if self.is_secretariat or self.party == user.party:
            return True
        return False

    def clean(self):
        # Users have to be either:
        # - OS
        # - CAP
        # - Party
        user_types = [
            self.is_secretariat,
            self.is_cap,
            self.party is not None
        ]
        if user_types.count(True) != 1:
            raise ValidationError(
                _('User needs to be either Secretariat, CAP or Party')
            )

        # CAP users cannot have access to the admin interface
        if self.is_cap and self.is_staff:
            raise ValidationError(
                _('CAP users cannot have access to the admin interface')
            )

        super().clean()

    def save(self, *args, **kwargs):
        # Create authentication token only on first-time save
        first_save = False
        if not self.pk or kwargs.get('force_insert', False):
            first_save = True

        self.clean()
        super().save(*args, **kwargs)
        if first_save:
            Token.objects.create(user=self)

    class Meta:
        verbose_name = 'user'
