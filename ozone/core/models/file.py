import os

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

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
        db_table = 'core_upload_token'
        ordering = ('-created_at',)

    def __str__(self):
        return f'Upload token for user "{self.user}"'

    def has_expired(self):
        return self.valid_until < (
            timezone.now() + timezone.timedelta(seconds=self.GRACE_SECONDS))


class File(models.Model):
    def get_storage_directory(self, filename):
        raise NotImplementedError

    name = models.CharField(max_length=512)
    file = models.FileField(
        upload_to=get_storage_directory, null=True, blank=True
    )

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


class SubmissionFile(ModifyPreventionMixin, File):
    def get_storage_directory(self, filename):
        return os.path.join(
            self.submission.get_storage_directory(),
            os.path.basename(filename)
        )

    submission = models.ForeignKey(
        Submission, related_name='files', on_delete=models.PROTECT
    )

    file = models.FileField(
        upload_to=get_storage_directory, null=True, blank=True
    )

    def get_storage_directory(self, filename):
        return os.path.join(
            self.submission.get_storage_directory(),
            os.path.basename(filename)
        )

    def get_download_url(self):
        return reverse(
            'core:submission-files-download',
            kwargs={
                'submission_pk': self.submission.id,
                'pk': self.pk,
            }
        )

    @staticmethod
    def has_valid_extension(self, filename):
        return filename.split('.')[-1].lower() in settings.ALLOWED_FILE_EXTENSIONS

    def __str__(self):
        return f'File {self.file.name} for submission {self.submission}'