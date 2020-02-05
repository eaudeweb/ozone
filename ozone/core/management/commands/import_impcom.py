import logging
import re

from collections import defaultdict
from functools import wraps

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from openpyxl import load_workbook

from ozone.core.models import (
    User,
    ReportingPeriod,
    ImpComTopic,
    ImpComBody,
    ImpComRecommendation,
)

logger = logging.getLogger(__name__)

sort_counters = defaultdict(int)


def catch_exceptions(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(
                f'Error processing row {args[0] if args else ""}: {e}',
                exc_info=True
            )
            return
    return wrapper


def split_and_strip(text):
    return [
        a.strip() for a in re.split(',|\n', text)
        if a.strip()
    ]


class Command(BaseCommand):
    help = _(
        "Import Kigali licensing systems data from Excel"
    )

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout=None, stderr=None, no_color=False)

        self.wb = None

    def add_arguments(self, parser):
        parser.add_argument('file', help="the xlsx input file")
        parser.add_argument(
            '--purge', action="store_true", default=False,
            help="Purge all entries that were imported"
        )

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

        try:
            # Create as the first admin we find.
            self.admin = User.objects.filter(is_superuser=True)[0]
        except Exception as e:
            logger.critical("Unable to find an admin: %s", e)
            return

        # Load all the data.
        self.wb = load_workbook(filename=options["file"])

        worksheet = self.wb['ImpCom recommendations']
        values = list(worksheet.values)
        headers = values[0]
        for row in values[1:]:
            row = dict(zip(headers, row))
            self.process_data(row, options["purge"])

    @catch_exceptions
    def process_data(self, row, purge=False):
        if not row["Year"]:
            return
        if purge:
            bodies = ImpComBody.objects.filter(
                name__in=split_and_strip(row["Country/Body"])
            ).distinct().values_list('id', flat=True)
            topics = ImpComTopic.objects.filter(
                name__in=split_and_strip(row["Topic"])
            ).distinct().values_list('id', flat=True)

            imp_com_rec = ImpComRecommendation.objects.filter(
                reporting_period__name=row["Year"],
                recommendation_number=row["Rec # or paragraph of report "],
                bodies__id__in=bodies,
                topics__id__in=topics
            ).distinct().first()
            if imp_com_rec is None:
                logger.info(
                    f'No implementation committee recommendation data found '
                    f'for {row["Year"]} - {row["Country/Body"]}'
                )
            else:
                imp_com_rec.delete()
                logger.info(
                    f'Deleted implementation committee recommendation data '
                    f'for {row["Year"]} - {row["Country/Body"]}'
                )
            return

        reporting_period = ReportingPeriod.objects.filter(
            name=row["Year"]
        ).first()
        if reporting_period is None:
            logger.error(f'Could not find reporting period {row["Year"]}')
            return
        sort_order = sort_counters.get(row["Year"], 0) + 1
        sort_counters[row["Year"]] = sort_order
        obj, created = ImpComRecommendation.objects.get_or_create(
            reporting_period_id=reporting_period.id,
            recommendation_number=row["Rec # or paragraph of report "],
            sort_order=sort_order,
            defaults={
                'excerpt': row["Excerpt from the respective meeting report"],
                'table_data': row["tables to embed in cells"] or '',
                'resulting_decisions': row["Resulting Decision Number"],
                'link_to_report': row["link to ImpCom report"]
            }
        )
        if created:
            logger.info(
                f'Created implementation committee recommendation data '
                f'for {row["Year"]} - {row["Country/Body"]}'
            )
        else:
            logger.info(
                f'Implementation committee recommendation data for '
                f'{row["Year"]} - {row["Country/Body"]} already exists.'
            )

        body_list = split_and_strip(row["Country/Body"])
        for body_name in body_list:
            body, created = ImpComBody.objects.get_or_create(name=body_name)
            obj.bodies.add(body)

        topic_list = split_and_strip(row["Topic"])
        for topic_name in topic_list:
            body, created = ImpComTopic.objects.get_or_create(name=topic_name)
            obj.topics.add(body)
