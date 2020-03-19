from collections import defaultdict

from django.utils import timezone

from ozone.core.utils.spreadsheet import OzoneSpreadsheet, OzoneTable
from ozone.core.models import ObligationTypes


tz_default = timezone.get_default_timezone()
tz_utc = timezone.utc


def fix_tz(value):
    return value.astimezone(tz_default).replace(tzinfo=tz_utc)


def substance_or_blend_id(row):
    if row.substance:
        return row.substance.substance_id
    if row.blend:
        return row.blend.legacy_blend_id
    raise RuntimeError("Neither substance nor blend? What is this sorcery?")


class ExportError(RuntimeError):
    """ Error during export """


def export_overall(queryset):
    header = [
        'CntryID', 'PeriodID', 'DataID',

        'Imported', 'Exported', 'Produced', 'Destroyed',
        'NonPartyTrade', 'DateReported', 'AI_ComplRep', 'AII_ComplRep',
        'BI_ComplRep', 'BII_ComplRep', 'BIII_ComplRep', 'CI_ComplRep',
        'CII_ComplRep', 'CIII_ComplRep', 'EI_ComplRep', 'F_ComplRep',
        'Checked_Blanks', 'Blanks', 'Confirm_Blanks',

        'UserCreate', 'UserUpdate', 'DateCreate', 'DateUpdate', 'Remark',
        'SubmissionType', 'TS', 'Emitted', 'HFCDateReported',

        'ReportingOfficer', 'Email', 'CreatedByUserEmail',
    ]

    def remark(submission):
        return (
            f"{submission.questionnaire_remarks_secretariat} "
            f"{submission.questionnaire_remarks_party}"
        ).strip()

    def rows():
        for submission in queryset:

            # Filter out non-art7 submissions
            if submission.obligation._obligation_type not in (
                ObligationTypes.ART7.value,
            ):
                continue

            art7questionnaire = (
                submission.article7questionnaire
                if hasattr(submission, 'article7questionnaire')
                else None
            )

            submission_format = (
                submission.info.submission_format.name
                if submission.info and submission.info.submission_format
                else None
            )

            def _to_int(instance, flag_name):
                # use this instead of int because some flags are optional
                return None if (
                    instance is None or
                    not hasattr(instance, flag_name) or
                    getattr(instance, flag_name) is None
                ) else int(getattr(instance, flag_name))

            yield {
                'CntryID':  submission.party.abbr,
                'PeriodID': submission.reporting_period.name,
                'DataID':   0,

                'Imported':       _to_int(art7questionnaire, 'has_imports'),
                'Exported':       _to_int(art7questionnaire, 'has_exports'),
                'Produced':       _to_int(art7questionnaire, 'has_produced'),
                'Destroyed':      _to_int(art7questionnaire, 'has_destroyed'),
                'NonPartyTrade':  _to_int(art7questionnaire, 'has_nonparty'),
                'Emitted':        _to_int(art7questionnaire, 'has_emissions'),
                'DateReported':   submission.submitted_at,
                'AI_ComplRep':    _to_int(submission, 'flag_has_reported_a1'),
                'AII_ComplRep':   _to_int(submission, 'flag_has_reported_a2'),
                'BI_ComplRep':    _to_int(submission, 'flag_has_reported_b1'),
                'BII_ComplRep':   _to_int(submission, 'flag_has_reported_b2'),
                'BIII_ComplRep':  _to_int(submission, 'flag_has_reported_b3'),
                'CI_ComplRep':    _to_int(submission, 'flag_has_reported_c1'),
                'CII_ComplRep':   _to_int(submission, 'flag_has_reported_c2'),
                'CIII_ComplRep':  _to_int(submission, 'flag_has_reported_c3'),
                'EI_ComplRep':    _to_int(submission, 'flag_has_reported_e'),
                'F_ComplRep':     _to_int(submission, 'flag_has_reported_f'),
                'Checked_Blanks': _to_int(submission, 'flag_checked_blanks'),
                'Blanks':         _to_int(submission, 'flag_has_blanks'),
                'Confirm_Blanks': _to_int(submission, 'flag_confirmed_blanks'),

                'UserCreate':     None,
                'UserUpdate':     None,
                'DateCreate':     fix_tz(submission.created_at),
                'DateUpdate':     fix_tz(submission.updated_at),
                'Remark':         remark(submission),
                'SubmissionType': submission_format,
                'TS': None,
                'HFCDateReported': submission.date_reported_f,

                'ReportingOfficer':     submission.info.reporting_officer,
                'Email':                submission.info.email,
                'CreatedByUserEmail':   submission.created_by.email,
            }

    return OzoneTable(header, rows())


def export_imports_new(queryset):
    header = [
        'CntryID', 'PeriodID', 'SubstID', 'OrgCntryID', 'DataID',

        'ImpNew', 'ImpRecov', 'ImpFeedstock', 'ImpEssenUse',
        'ImpLabUse', 'ImpQuarAppl', 'ImpProcAgent', 'ImpPolyol',

        'UserCreate', 'UserUpdate', 'DateCreate', 'DateUpdate', 'Remark', 'TS',
    ]

    def essential_uses(row):
        return (
            (row.quantity_essential_uses or 0) +  # noqa: W504
            (row.quantity_laboratory_analytical_uses or 0) +  # noqa: W504
            (row.quantity_critical_uses or 0)
        )

    def remark(row):
        return f"{row.remarks_os} {row.remarks_party}".strip()

    def rows():
        for submission in queryset:
            imports_queryset = (
                submission.article7imports
                .filter(blend_item_id__isnull=True)
                .order_by(
                    'substance__substance_id',
                    'blend__legacy_blend_id',
                    'source_party__abbr',
                )
            )
            for row in imports_queryset.all():
                yield {
                    'CntryID':    submission.party.abbr,
                    'PeriodID':   submission.reporting_period.name,
                    'SubstID':    substance_or_blend_id(row),
                    'OrgCntryID': row.source_party.abbr if row.source_party else 'UNK',
                    'DataID':     0,

                    'ImpNew':       row.quantity_total_new,
                    'ImpRecov':     row.quantity_total_recovered,
                    'ImpFeedstock': row.quantity_feedstock,
                    'ImpEssenUse':  essential_uses(row),
                    'ImpLabUse':    row.quantity_laboratory_analytical_uses,
                    'ImpQuarAppl':  row.quantity_quarantine_pre_shipment,
                    'ImpProcAgent': row.quantity_process_agent_uses,
                    'ImpPolyol':    row.quantity_polyols,

                    'UserCreate':   None,
                    'UserUpdate':   None,
                    'DateCreate':   fix_tz(submission.created_at),
                    'DateUpdate':   fix_tz(submission.updated_at),
                    'Remark':       remark(row),
                    'TS':           None,
                }

    return OzoneTable(header, rows())


def aggregate_import_sheet(import_new_sheet):
    header = list(import_new_sheet.header)
    header.remove('OrgCntryID')

    pk_cols = ['CntryID', 'PeriodID', 'SubstID']
    aggregation_cols = [
        'ImpNew', 'ImpRecov', 'ImpFeedstock', 'ImpEssenUse', 'ImpLabUse',
        'ImpQuarAppl', 'ImpProcAgent', 'ImpPolyol',
    ]
    fixed_cols = {
        'DataID': 0,
        'UserCreate': None,
        'UserUpdate': None,
        'DateCreate': None,
        'DateUpdate': None,
        'Remark': None,
        'TS': None,
    }

    aggregations = defaultdict(lambda: {k: 0 for k in aggregation_cols})

    for row in import_new_sheet.rows:
        pk = tuple((k, row[k]) for k in pk_cols)
        for col in aggregation_cols:
            aggregations[pk][col] += (row[col] or 0)

    def rows():
        for pk in sorted(aggregations):
            row = aggregations[pk]
            row.update(dict(pk))
            for col, value in fixed_cols.items():
                row[col] = value
            yield row

    return OzoneTable(header, rows())


def export_exports(queryset):
    header = [
        'CntryID', 'PeriodID', 'SubstID', 'DestCntryID', 'DataID',

        'ExpNew', 'ExpRecov', 'ExpFeedstock',
        'ExpEssenUse', 'ExpQuarAppl', 'ExpProcAgent', 'ExpPolyol',

        'UserCreate', 'UserUpdate', 'DateCreate', 'DateUpdate', 'Remark', 'TS',
    ]

    def exp_essen_use_value(row):
        return (
            (row.quantity_critical_uses or 0) +  # noqa: W504
            (row.quantity_essential_uses or 0)
        )

    def remark(row):
        return f"{row.remarks_os} {row.remarks_party}".strip()

    def rows():
        for submission in queryset:
            exports_queryset = (
                submission.article7exports
                .filter(blend_item_id__isnull=True)
                .order_by(
                    'substance__substance_id',
                    'blend__legacy_blend_id',
                    'destination_party__abbr',
                )
            )
            for row in exports_queryset.all():
                yield {
                    'CntryID':     submission.party.abbr,
                    'PeriodID':    submission.reporting_period.name,
                    'SubstID':     substance_or_blend_id(row),
                    'DestCntryID': row.destination_party.abbr if row.destination_party else 'UNK',
                    'DataID':      0,

                    'ExpNew':       row.quantity_total_new,
                    'ExpRecov':     row.quantity_total_recovered,
                    'ExpFeedstock': row.quantity_feedstock,
                    'ExpEssenUse':  exp_essen_use_value(row),
                    'ExpQuarAppl':  row.quantity_quarantine_pre_shipment,
                    'ExpProcAgent': row.quantity_process_agent_uses,
                    'ExpPolyol':    row.quantity_polyols,

                    'UserCreate':   None,
                    'UserUpdate':   None,
                    'DateCreate':   fix_tz(submission.created_at),
                    'DateUpdate':   fix_tz(submission.updated_at),
                    'Remark':       remark(row),
                    'TS':           None,
                }

    return OzoneTable(header, rows())


def export_produce(queryset):
    header = [
        'CntryID', 'PeriodID', 'SubstID', 'DataID',

        'ProdAllNew', 'ProdFeedstock', 'ProdEssenUse', 'ProdLabUse',
        'ProdArt5', 'ProdQuarAppl', 'ProdProcAgent',

        'UserCreate', 'UserUpdate', 'DateCreate', 'DateUpdate', 'Remark', 'TS',
        'CaptureDest',
    ]

    def prod_essen_use_value(row):
        return (
            (row.quantity_critical_uses or 0) +  # noqa: W504
            (row.quantity_essential_uses or 0) +  # noqa: W504
            (row.quantity_laboratory_analytical_uses or 0)
        )

    def remark(row):
        return f"{row.remarks_os} {row.remarks_party}".strip()

    def rows():
        for submission in queryset:
            productions_queryset = submission.article7productions.order_by(
                'substance__substance_id',
            )
            for row in productions_queryset.all():
                yield {
                    'CntryID':     submission.party.abbr,
                    'PeriodID':    submission.reporting_period.name,
                    'SubstID':     row.substance.substance_id,
                    'DataID':      0,

                    'ProdAllNew':    row.quantity_total_produced,
                    'ProdFeedstock': row.quantity_feedstock,
                    'ProdEssenUse':  prod_essen_use_value(row),
                    'ProdLabUse':    row.quantity_laboratory_analytical_uses,
                    'ProdArt5':      row.quantity_article_5,
                    'ProdQuarAppl':  row.quantity_quarantine_pre_shipment,
                    'ProdProcAgent': row.quantity_process_agent_uses,

                    'UserCreate':   None,
                    'UserUpdate':   None,
                    'DateCreate':   fix_tz(submission.created_at),
                    'DateUpdate':   fix_tz(submission.updated_at),
                    'Remark':       remark(row),
                    'TS':           None,
                    'CaptureDest':  None
                }

    return OzoneTable(header, rows())


def export_destroy(queryset):
    header = [
        'CntryID', 'PeriodID', 'SubstID', 'DataID',

        'Destroyed',

        'UserCreate', 'UserUpdate', 'DateCreate', 'DateUpdate', 'Remark', 'TS',
    ]

    def remark(row):
        return f"{row.remarks_os} {row.remarks_party}".strip()

    def rows():
        for submission in queryset:
            destructions_queryset = (
                submission.article7destructions
                .filter(blend_item_id__isnull=True)
                .order_by(
                    'substance__substance_id',
                    'blend__legacy_blend_id',
                )
            )
            for row in destructions_queryset.all():
                yield {
                    'CntryID':     submission.party.abbr,
                    'PeriodID':    submission.reporting_period.name,
                    'SubstID':     substance_or_blend_id(row),
                    'DataID':      0,

                    'Destroyed': row.quantity_destroyed,

                    'UserCreate':   None,
                    'UserUpdate':   None,
                    'DateCreate':   fix_tz(submission.created_at),
                    'DateUpdate':   fix_tz(submission.updated_at),
                    'Remark':       remark(row),
                    'TS':           None,
                }

    return OzoneTable(header, rows())


def export_nonparty_new(queryset):
    header = [
        'CntryID', 'PeriodID', 'SubstID', 'DataID', 'SrcDestCntryID',

        'NPTImpNew', 'NPTImpRecov', 'NPTExpNew', 'NPTExpRecov',

        'UserCreate', 'UserUpdate', 'DateCreate', 'DateUpdate', 'Remark', 'TS',
    ]

    def remark(row):
        return f"{row.remarks_os} {row.remarks_party}".strip()

    def rows():
        for submission in queryset:
            nonparty_queryset = submission.article7nonpartytrades.order_by(
                'substance__substance_id',
                'trade_party__abbr',
            )
            for row in nonparty_queryset.all():
                yield {
                    'CntryID':        submission.party.abbr,
                    'PeriodID':       submission.reporting_period.name,
                    'SubstID':        row.substance.substance_id,
                    'DataID':         0,
                    'SrcDestCntryID': row.trade_party.abbr if row.trade_party else 'UNK',

                    'NPTImpNew':   row.quantity_import_new,
                    'NPTImpRecov': row.quantity_import_recovered,
                    'NPTExpNew':   row.quantity_export_new,
                    'NPTExpRecov': row.quantity_export_recovered,

                    'UserCreate':   None,
                    'UserUpdate':   None,
                    'DateCreate':   fix_tz(submission.created_at),
                    'DateUpdate':   fix_tz(submission.updated_at),
                    'Remark':       remark(row),
                    'TS':           None,
                }

    return OzoneTable(header, rows())


def aggregate_nonparty_sheet(import_new_sheet):
    header = [
        'CntryID', 'PeriodID', 'SubstID',
        'DataID', 'SrcDestCntryID',
        'Import', 'Export',
        'UserCreate', 'UserUpdate', 'DateCreate', 'DateUpdate', 'Remark', 'TS',
    ]

    pk_cols = ['CntryID', 'PeriodID', 'SubstID']
    aggregation_cols = {
        'Import': ['NPTImpNew', 'NPTImpRecov'],
        'Export': ['NPTExpNew', 'NPTExpRecov'],
    }
    fixed_cols = {
        'DataID': 0,
        'SrcDestCntryID': None,
        'UserCreate': None,
        'UserUpdate': None,
        'DateCreate': None,
        'DateUpdate': None,
        'Remark': None,
        'TS': None,
    }

    aggregations = defaultdict(lambda: {k: 0 for k in aggregation_cols})

    for row in import_new_sheet.rows:
        pk = tuple((k, row[k]) for k in pk_cols)
        for col, src_cols in aggregation_cols.items():
            for src in src_cols:
                aggregations[pk][col] += (row[src] or 0)

    def rows():
        for pk in sorted(aggregations):
            row = aggregations[pk]
            row.update(dict(pk))
            for col, value in fixed_cols.items():
                row[col] = value
            yield row

    return OzoneTable(header, rows())


def export_submissions(queryset):
    queryset = queryset.order_by('party__abbr', 'reporting_period__name')
    import_new_sheet = export_imports_new(queryset)
    nonparty_new_sheet = export_nonparty_new(queryset)
    out = OzoneSpreadsheet()
    out.tables['Overall'] = export_overall(queryset)
    out.tables['Import'] = aggregate_import_sheet(import_new_sheet)
    out.tables['ImportNew'] = import_new_sheet
    out.tables['Export'] = export_exports(queryset)
    out.tables['Produce'] = export_produce(queryset)
    out.tables['Destroy'] = export_destroy(queryset)
    out.tables['NonPartyTrade'] = aggregate_nonparty_sheet(nonparty_new_sheet)
    out.tables['NonPartyTradeNew'] = nonparty_new_sheet
    return out
