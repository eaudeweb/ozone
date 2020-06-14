import logging
from decimal import Decimal

from django.core.management.base import BaseCommand

from ozone.core.models import (
    Submission,
    ProdCons,
    ProdConsMT,
    Party,
    ReportingPeriod,
    ObligationTypes,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Recalculates without overwriting existing aggregations for all Article 7
    Doesn't consider transfers
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
            prodcons_mt_queryset = prodcons_mt_queryset.filter(party=party)
            submission_queryset = submission_queryset.filter(party=party)

        if options['period']:
            period = ReportingPeriod.objects.get(name=options['period'])
            submission_queryset = submission_queryset.filter(
                reporting_period=period
            )

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
            if s.in_initial_state:
                logger.info(
                    f"Submission {s} is in data entry state been recalled "
                    f"and will not be processed."
                )
                continue

            submission_name = f"{s.id} {s.party}/{s.reporting_period}"
            logger.debug(f"Checking data for submission {submission_name}")
            aggregations = s.get_aggregated_data()
            qs1 = prodcons_queryset.filter(
                party=s.party,
                reporting_period=s.reporting_period,
            )
            count_db = qs1.count()
            if count_db != len(aggregations):
                logger.warning(
                    f"Number of rows is different ({len(aggregations)} vs {count_db})"
                    " in ProdCons for {submission_name}"
                )
            for group, prodcons in aggregations.items():
                prodcons_db = qs1.filter(
                    group=group,
                ).first()
                if not prodcons_db:
                    logger.warning(f"Group {group} not found in DB for {submission_name}")
                    continue
                if (
                    prodcons_db.calculated_production != prodcons.calculated_production
                    and not (
                        prodcons_db.calculated_production is None and
                        prodcons.calculated_production == Decimal(0)
                    )
                ):
                    logger.warning(
                        f"Calculated production different ({prodcons.calculated_production}"
                        f" vs {prodcons_db.calculated_production}) for {submission_name}/{group}"
                    )
                if (
                    prodcons_db.calculated_consumption != prodcons.calculated_consumption
                    and not (
                        prodcons_db.calculated_consumption is None and
                        prodcons.calculated_consumption == Decimal(0)
                    )
                ):
                    logger.warning(
                        f"Calculated consumption different ({prodcons.calculated_consumption}"
                        f" vs {prodcons_db.calculated_consumption}) for {submission_name}/{group}"
                    )
            # Now check MT data
            aggregations_mt = s.get_aggregated_mt_data()
            qs2 = prodcons_mt_queryset.filter(
                party=s.party,
                reporting_period=s.reporting_period,
            )
            count_db = qs2.count()
            if count_db != len(aggregations_mt):
                logger.warning(
                    f"Number of rows is different in ProdConsMT ({len(aggregations_mt)} vs {count_db})"
                    f" in ProdConsMT for {submission_name}"
                )
                # Check if transfers
                for prodconsmt_db in qs2:
                    if 'transfer' in prodconsmt_db.submissions:
                        logger.info(f"{submission_name} has transfers for substance {prodconsmt_db.substance}")
            for substance, prodconsmt in aggregations_mt.items():
                prodconsmt_db = qs2.filter(
                    substance=substance,
                ).first()
                if not prodconsmt_db:
                    logger.warning(f"Substance {substance} not found in DB for {submission_name}")
                    continue
                if (
                    prodconsmt_db.calculated_production != prodconsmt.calculated_production
                ):
                    logger.warning(
                        f"Calculated production different ({prodconsmt.calculated_production}"
                        f" vs {prodconsmt_db.calculated_production}) for {submission_name}/{substance}"
                    )
                if (
                    prodconsmt_db.calculated_consumption != prodconsmt.calculated_consumption
                ):
                    logger.warning(
                        f"Calculated consumption different ({prodconsmt.calculated_consumption}"
                        f" vs {prodconsmt_db.calculated_consumption}) for {submission_name}/{substance}"
                    )
