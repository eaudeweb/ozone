import logging

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from ozone.core.models import ImpComBody, Party

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = _("Update sort order for ImpCom bodies")

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout=None, stderr=None, no_color=False)

    def handle(self, *args, **options):
        stream = logging.StreamHandler()
        stream.setFormatter(
            logging.Formatter(
                '%(asctime)s %(levelname)s %(message)s'
            )
        )
        logger.addHandler(stream)
        logger.setLevel(logging.WARNING)
        if int(options['verbosity']) > 0:
            logger.setLevel(logging.INFO)
        if int(options['verbosity']) > 1:
            logger.setLevel(logging.DEBUG)

        party_names_list = Party.objects.all().values_list('name', flat=True)

        # Set a default sort order value for bodies that are not parties
        count = ImpComBody.objects.update(sort_order=10)
        logger.info(f'Set sort_order to 10 for {count} bodies.')

        # Then set it higher for parties
        count = ImpComBody.objects.filter(name__in=party_names_list).update(
            sort_order=20
        )
        logger.info(f'Set sort_order to 20 for {count} bodies.')


