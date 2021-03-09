import logging

from django.core.management.base import BaseCommand

from ozone.core.models import (
    ActualBaselineAndLimit,
    Party,
    PartyHistory,
    ReportingPeriod,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Calculates and saves (overwriting existing data, if any) the actual
    baselines and limits in ActualBaselineAndLimit.
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
            '--confirm',
            action='store_true',
            default=False,
            help="Use to re-populate all ActualBaselineAndLimit data, "
                 "otherwise just dry-run"
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

        if options['party']:
            parties = [Party.objects.get(abbr=options['party'])]
        else:
            parties = Party.get_main_parties()

        if options['period']:
            periods = [ReportingPeriod.objects.get(name=options['period'])]
        else:
            # Only use reporting periods for which there are PartyHistory
            # entries
            existing_histories = PartyHistory.objects.all().values_list(
                'reporting_period__name', flat=True
            )
            periods = list(ReportingPeriod.objects.filter(
                name__in=existing_histories)
            )

        if not options['confirm']:
            logger.info(
                f"Run with --confirm to update actual baseline/limit data for "
                f"{10 * len(parties) * len(periods)} ActualBaselineAndLimit"
                f"objects."
            )

        for period in periods:
            for party in parties:
                if options['confirm']:
                    logger.info(f"Updating data for {period} - {party}")
                else:
                    logger.debug(f"Would update data for {period} - {party}")

                if options['confirm']:
                    values = ActualBaselineAndLimit.populate_actual_data(
                        party, period
                    )
                    logger.debug(values)
