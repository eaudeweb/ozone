import logging
from functools import wraps

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from openpyxl import load_workbook

from ozone.core.models import (
    Decision,
    Meeting,
    User,
    ReportingPeriod,
    TEAPReportType,
    TEAPReport,
    TEAPIndicativeNumberOfReports
)

logger = logging.getLogger(__name__)


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


class Command(BaseCommand):
    help = _(
        "Import TEAP data from Excel"
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

        workbook_row_processors = [
            ('IssueType', self.process_issue_type),
            ('IndicativeNumbers', self.process_indicative_numbers),
            ('Data', self.process_data),
        ]
        if options["purge"]:
            workbook_row_processors.reverse()

        for workbook_name, workbook_processor in workbook_row_processors:
            worksheet = self.wb[workbook_name]
            values = list(worksheet.values)
            headers = values[0]
            for row in values[1:]:
                row = dict(zip(headers, row))
                workbook_processor(row, options["purge"])

    # Workbook row processors
    @catch_exceptions
    def process_issue_type(self, row, purge=False):
        if purge:
            num, summary = TEAPReportType.objects.filter(
                name=row['Issue Type'].strip()
            ).delete()
            if num > 0:
                logger.info(f'Deleted TEAP report type {row["Issue Type"]}.')
            else:
                logger.info(
                    f'No TEAP report type for {row["Issue Type"]} found.'
                )
            return

        obj, created = TEAPReportType.objects.get_or_create(
            name=row['Issue Type'].strip(),
            defaults={
                'sort_order': row['SortOrder']
            }
        )
        if created:
            logger.info(f'Added TEAP report type {row["Issue Type"]}.')
        else:
            logger.info(f'TEAP report type {row["Issue Type"]} already added.')

    @catch_exceptions
    def process_indicative_numbers(self, row, purge=False):
        if purge:
            num, summary = TEAPIndicativeNumberOfReports.objects.filter(
                reporting_period__name=row['Year']
            ).delete()
            if num > 0:
                logger.info(
                    f'Deleted TEAP indicative number for {row["Year"]}.'
                )
            else:
                logger.info(
                    f'No TEAP indicative number for {row["Year"]} found.'
                )
            return

        reporting_period = ReportingPeriod.objects.filter(
            name=row['Year']
        ).first()

        obj, created = TEAPIndicativeNumberOfReports.objects.get_or_create(
            reporting_period_id=reporting_period.id,
            defaults={
                'number_of_reports': row['Indicative number of reports'],
                'remarks': (row['Remarks'] or '').strip()
            }
        )
        if created:
            logger.info(
                f'Added TEAP indicative number of reports for {row["Year"]}.'
            )
        else:
            logger.info(
                f'TEAP indicative number of reports for {row["Year"]} already '
                f'added.'
            )

    @catch_exceptions
    def process_data(self, row, purge=False):
        if purge:
            num, summary = TEAPReport.objects.filter(
                reporting_period__name=row['Year'],
                decision__decision_id=row['DecisionNumber'],
                report_to_be_produced=(
                    row['Report to be produced'] or ''
                ).strip()
            ).delete()
            if num > 0:
                logger.info(
                    f'Deleted TEAP report for {row["Year"]} - '
                    f'{row["DecisionNumber"]} - {row["Report to be produced"]}.'
                )
            else:
                logger.info(
                    f'No TEAP report found for {row["Year"]} - '
                    f'{row["DecisionNumber"]} - {row["Report to be produced"]}.'
                )
            return

        report_type = TEAPReportType.objects.filter(
            name=row['ReportType'].strip()
        ).first()
        reporting_period = ReportingPeriod.objects.filter(
            name=row['Year']
        ).first()
        if row['DecisionNumber'] is not None:
            decision = self.get_or_create_decision(row['DecisionNumber'])
        else:
            decision = None

        obj, created = TEAPReport.objects.get_or_create(
            sort_order=row['SortOrder'],
            reporting_period_id=reporting_period.id,
            report_type_id=report_type.id,
            decision_id=decision.id if decision else None,
            issue=row['Issue'].strip(),
            request_by_parties=row['Request by parties to TEAP'].strip(),
            report_to_be_produced=(row['Report to be produced'] or '').strip(),
            remark_issue_type=(row['RemarkIssueType'] or '').strip(),
            remark_issue=(row['RemarkIssue'] or '').strip(),
            remark_request=(row['RemarkRequest'] or '').strip(),
            remark_report=(row['RemarkReport'] or '').strip()
        )
        if created:
            logger.info(
                f'Added TEAP report for {row["Year"]} - {row["DecisionNumber"]}'
                f' - {row["Report to be produced"]}.'
            )
        else:
            logger.info(
                f'TEAP report for {row["Year"]} - {row["DecisionNumber"]} - '
                f'{row["Report to be produced"]} already added.'
            )

    @transaction.atomic
    def get_or_create_decision(self, decision_id):
        if decision_id.endswith('-'):
            decision_id = decision_id[:-1]
        decision = Decision.objects.filter(decision_id=decision_id).first()
        if not decision:
            if decision_id == 'UNK':
                meeting, created = Meeting.objects.get_or_create(
                    meeting_id='UNK',
                    defaults={
                        'location': 'UNK',
                        'description': 'UNK'
                    }
                )
            else:
                meeting_id = decision_id.split('/')[0]
                meeting = Meeting.objects.get(meeting_id=meeting_id)
            decision = Decision.objects.create(
                decision_id=decision_id,
                meeting=meeting
            )
            logger.info(f"Decision {decision_id} added.")
        return decision
