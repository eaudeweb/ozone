import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from ozone.core.models import (
    ProdCons,
    ProdConsMT,
    Party,
    ReportingPeriod,
)
from ozone.core.utils.cache import invalidate_party_cache

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Re-calculates and saves the calculated fields for all ODP and MT
    aggregations.
    """

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '--party',
            help="Party code (abbreviation), for limiting the calculation to a "
                 "single party."
        )
        parser.add_argument(
            '--period',
            help="Reporting period code, for limiting the calculation to a "
                 "single reporting period."
        )
        parser.add_argument(
            '--eu-only',
            action='store_true',
            default=False,
            help="Only recalculate data for EU members and the EU itself."
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            default=False,
            help="Use to re-calculate all data, otherwise just dry-run"
        )

    def handle(self, *args, **options):
        stream = logging.StreamHandler()
        stream.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(message)s'
        ))
        logger.addHandler(stream)
        logger.setLevel(logging.INFO)

        if int(options['verbosity']) > 1:
            logger.setLevel(logging.DEBUG)

        prodcons_queryset = ProdCons.objects.all()
        prodcons_mt_queryset = ProdConsMT.objects.all()

        if options['party']:
            party = Party.objects.get(abbr=options['party'])
            prodcons_queryset = prodcons_queryset.filter(party=party)
            prodcons_mt_queryset = prodcons_mt_queryset.filter(party=party)

        if options['period']:
            period = ReportingPeriod.objects.get(name=options['period'])
            prodcons_queryset = prodcons_queryset.filter(
                reporting_period=period
            )
            prodcons_mt_queryset = prodcons_mt_queryset.filter(
                reporting_period=period
            )

        if options['eu_only']:
            prodcons_queryset = prodcons_queryset.filter(
                Q(is_eu_member=True) | Q(party__abbr='EU')
            )
            prodcons_mt_queryset = prodcons_mt_queryset.filter(
                Q(is_eu_member=True) | Q(party__abbr='EU')
            )

        if not options['confirm']:
            logger.info(
                f"Run with --confirm to process and update "
                f"{prodcons_queryset.count()} existing ODP aggregations and "
                f"{prodcons_mt_queryset.count()} existing MT aggregations."
            )

        for a in prodcons_queryset:
            if options['confirm']:
                logger.info(f"Recalculating ODP data for {a}")
                # This triggers a recalculation of the totals
                a.save(invalidate_cache=False)
            else:
                logger.debug(f"Found ODP aggregation {a.id}")

        for a in prodcons_mt_queryset:
            if options['confirm']:
                logger.info(f"Recalculating MT data for {a}")
                # This triggers a recalculation of the totals
                a.save()
            else:
                logger.debug(f"Found MT aggregation {a.id}")

        if options['confirm']:
            party_set = set(
                prodcons_queryset.values_list('party_id', flat=True)
            )
            for party in party_set:
                logger.info(f'Invalidating cache for party id: {party}')
                invalidate_party_cache(party)
