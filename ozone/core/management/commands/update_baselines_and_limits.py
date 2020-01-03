import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from ozone.core.models import (
    ProdCons,
    Party,
    ReportingPeriod,
)
from ozone.core.utils.cache import invalidate_party_cache

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Calculates and saves (overwriting if needed) the baselines and limits in
    already-existing aggregations for all Article 7 submissions.
    """

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '--party',
            help="Party code (abbreviation), for limiting the calculation to a "
                 "single party."
        )
        parser.add_argument(
            '--eu-only',
            action='store_true',
            default=False,
            help="Only recalculate data for EU members and the EU itself."
        )
        parser.add_argument(
            '--period',
            help="Reporting period code, for limiting the calculation to a "
                 "single reporting period."
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            default=False,
            help="Use to re-populate all baselines/limits data, otherwise "
                 "just dry-run"
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
        if options['party']:
            party = Party.objects.get(abbr=options['party'])
            prodcons_queryset = prodcons_queryset.filter(party=party)

        if options['period']:
            period = ReportingPeriod.objects.get(name=options['period'])
            prodcons_queryset = prodcons_queryset.filter(
                reporting_period=period
            )
        if options['eu_only']:
            prodcons_queryset = prodcons_queryset.filter(
                Q(is_eu_member=True) | Q(party__abbr='EU')
            )

        if not options['confirm']:
            logger.info(
                f"Run with --confirm to update baseline/limit data for "
                f"{prodcons_queryset.count()} aggregations."
            )

        for a in prodcons_queryset:
            if options['confirm']:
                logger.info(f"Updating data for aggregation {a}")
            else:
                logger.debug(f"Found aggregation {a.id}")

            if options['confirm']:
                a.update_limits_and_baselines()
                logger.debug(
                    f"Updated aggregation {a} with:\n"
                    f"baseline production: {a.baseline_prod},\n"
                    f"baseline consumption: {a.baseline_cons},\n"
                    f"baseline bdn: {a.baseline_bdn},\n"
                    f"limit production: {a.limit_prod},\n"
                    f"limit consumption: {a.limit_cons},\n"
                    f"limit bdn: {a.limit_bdn}\n"
                )

        if options['confirm']:
            party_set = set(
                prodcons_queryset.values_list('party_id', flat=True)
            )
            for party in party_set:
                logger.info(f'Invalidating cache for party id: {party}')
                invalidate_party_cache(party)
