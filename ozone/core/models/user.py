from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, F
from django.utils.translation import gettext_lazy as _

from guardian.mixins import GuardianUserMixin
from rest_framework.authtoken.models import Token

from .party import Party, Language


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
        else:
            if not self.is_read_only:
                return 'Party Reporter'
            else:
                return 'Party Read-Only'

    def has_edit_rights(self, user):
        if self == user:
            return True
        return False

    def has_read_rights(self, user):
        if self.is_secretariat or self.party == user.party:
            return True
        return False

    def clean(self):
        # Superusers can be allowed to be neither of party & OS
        if not self.is_superuser:
            if self.is_secretariat and self.party is not None:
                raise ValidationError(
                    _('Secretariat users cannot belong to a Party')
                )
            if not self.is_secretariat and self.party is None:
                raise ValidationError(
                    _('User needs to be either Secretariat or Party')
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
