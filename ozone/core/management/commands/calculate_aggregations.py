import logging

from django.core.management.base import BaseCommand

from ozone.core.models import (
    Submission,
    ProdCons,
    Party,
    ReportingPeriod,
    ObligationTypes,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Calculates and saves (overwriting if needed) aggregations for all Article 7
    submissions.
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
            help="Use to re-populate all data, otherwise just dry-run"
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
        # Only use Article 7 submissions.
        # Also only use the "current" ones, it seems better to do this using
        # filter than to use the is_current property for each one at a time.
        # Will not exclude submissions that have 'flag_valid' set to False or
        # are recalled. Will show a warning for this case and not compute any
        # data.
        submission_queryset = Submission.objects.filter(
            obligation___obligation_type=ObligationTypes.ART7.value,
            flag_superseded=False,
            submitted_at__isnull=False,
        )
        if options['party']:
            party = Party.objects.get(abbr=options['party'])
            prodcons_queryset = prodcons_queryset.filter(party=party)
            submission_queryset = submission_queryset.filter(party=party)

        if options['period']:
            period = ReportingPeriod.objects.get(name=options['period'])
            prodcons_queryset = prodcons_queryset.filter(
                reporting_period=period
            )
            submission_queryset = submission_queryset.filter(
                reporting_period=period
            )

        if not options['confirm']:
            logger.info(
                f"Run with --confirm to process {submission_queryset.count()} "
                f"submissions, delete {prodcons_queryset.count()} aggregations "
                f"and create from scratch around "
                f"{9 * submission_queryset.count()} aggregations."
            )
        else:
            prodcons_queryset.delete()

        for s in submission_queryset:
            if s.flag_valid is False:
                logger.info(
                    f"Submission {s} has flag_valid set to False and will "
                    f"not be processed."
                )
                continue
            if s.in_incorrect_state:
                logger.info(
                    f"Submission {s} has been recalled and will not be "
                    f"processed."
                )
                continue

            if options['confirm']:
                logger.info(f"Aggregating data for submission {s.id}")
            else:
                logger.debug(f"Found submission {s.id}")

            if options['confirm']:
                s.purge_all_related_aggregated_data()
                created_aggregations = s.fill_aggregated_data()
                for a in ProdCons.objects.filter(id__in=created_aggregations):
                    logger.debug(
                        f"Created aggregation for group {a.group} with "
                        f"calculated production: {a.calculated_production}, "
                        f"calculated consumption: {a.calculated_consumption}."
                    )
