import logging

from django.core.management.base import BaseCommand
from django.db.models import F

from ozone.core.models import (
    Submission, ObligationTypes, Party, ReportingPeriod
)


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Populates date_reported_f field based on submitted_at and has_reported_f
    fields; as it was previously not being updated correctly.
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

        # Find submitted submissions for which `date_reported_f` has not been
        # populated, but `flag_has_reported_f` is set
        submission_queryset = Submission.objects.filter(
            obligation___obligation_type=ObligationTypes.ART7.value,
            date_reported_f__isnull=True,
            flag_has_reported_f=True,
            submitted_at__isnull=False
        )
        if options['party']:
            party = Party.objects.get(abbr=options['party'])
            submission_queryset = submission_queryset.filter(party=party)

        if options['period']:
            period = ReportingPeriod.objects.get(name=options['period'])
            submission_queryset = submission_queryset.filter(
                reporting_period=period
            )

        if not options['confirm']:
            logger.info(
                f"Run with --confirm to process {submission_queryset.count()} "
                f"submissions"
            )

        if options['confirm']:
            count = submission_queryset.update(
                date_reported_f=F('submitted_at')
            )
            logger.info(
                f'Updated date_reported_f for {count} submissions'
            )
