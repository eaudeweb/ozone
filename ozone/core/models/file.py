import os

from django.conf import settings
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from model_utils import FieldTracker

from .reporting import ModifyPreventionMixin, Submission


UPLOAD_TOKEN_LENGTH = 64
UPLOAD_TOKEN_DURATION = 60 * 60  # 60 minutes

__all__ = [
    'UploadToken',
    'SubmissionFile',
]


def default_token():
    return get_random_string(UPLOAD_TOKEN_LENGTH)


def token_valid_until():
    return timezone.now() + timezone.timedelta(seconds=UPLOAD_TOKEN_DURATION)


class UploadToken(models.Model):
    """
    Upload token used by tusd to associate uploads with a specific user and
    submission.
    """
    GRACE_SECONDS = 30

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='upload_tokens',
        on_delete=models.CASCADE
    )
    submission = models.ForeignKey(
        Submission, related_name='upload_tokens', on_delete=models.CASCADE
    )
    token = models.CharField(
        max_length=100, db_index=True,
        unique=True, default=default_token
    )

    filename = models.CharField(max_length=256)
    tus_id = models.CharField(max_length=32, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(default=token_valid_until)

    class Meta:
        db_table = 'upload_token'
        ordering = ('-created_at',)

    def __str__(self):
        return f'Upload token for user "{self.user}"'

    def has_expired(self):
        return self.valid_until < (
            timezone.now() + timezone.timedelta(seconds=self.GRACE_SECONDS)
        )


def default_upload_to(instance, filename):
    raise NotImplementedError


class File(models.Model):
    """
    A File object will be created on all uploads where the file is fully
    transferred to the tusd server, irrespective of whether or not the FileField
    is correctly filled afterwards - that one will be signalled by the
    `upload_successful` flag.
    """

    # The name the file gets in the ORS
    name = models.CharField(max_length=512)

    file = models.FileField(
        upload_to=default_upload_to,
        max_length=1024,
        null=True, blank=True,
    )

    tus_id = models.CharField(max_length=32, blank=True, null=True)
    upload_successful = models.BooleanField(default=False)

    description = models.CharField(max_length=512, blank=True)

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='uploaded_files',
        on_delete=models.PROTECT
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def size(self):
        return self.file.size

    class Meta:
        abstract = True


def submission_file_upload_to(instance, filename):
    return os.path.join(
        instance.submission.get_storage_directory(),
        os.path.basename(filename)
    )


class SubmissionFile(File):
    # The name as given originally by the uploader
    original_name = models.CharField(max_length=512, blank=True, default='')
    # Indicates the suffix in the case of multiple files of same original name
    suffix = models.PositiveSmallIntegerField(default=0)

    submission = models.ForeignKey(
        Submission, related_name='files', on_delete=models.CASCADE
    )

    file = models.FileField(
        upload_to=submission_file_upload_to,
        max_length=1024,
        null=True, blank=True,
    )

    tracker = FieldTracker()

    class Meta:
        db_table = 'submission_file'

    def get_download_url(self):
        return reverse(
            'core:submission-files-download',
            kwargs={
                'submission_pk': self.submission.id,
                'pk': self.pk,
            }
        )

    def get_absolute_url(self):
        """
        Overridden to return the actual through-the-API download URL
        """
        return self.get_download_url()

    @staticmethod
    def has_valid_extension(filename):
        return filename.split('.')[-1].lower() in settings.ALLOWED_FILE_EXTENSIONS

    @transaction.atomic
    def save(self, *args, **kwargs):
        # On any save, we need to check whether the name we are trying to use
        # is taken. This is also called
        self.original_name = self.name
        self.suffix = 0
        if not self.pk or kwargs.get('force_insert', None) is not None:
            current_files = SubmissionFile.objects.filter(
                submission=self.submission,
                name=self.name
            )
            if current_files.exists():
                # There is already at least a file with this name
                self.suffix = current_files.latest('suffix').suffix + 1
                self.name = f'{self.original_name}({self.suffix})'

        super().save(*args, **kwargs)

    def __str__(self):
        return f'File {self.file.name} for submission {self.submission}'
