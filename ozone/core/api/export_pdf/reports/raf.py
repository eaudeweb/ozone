import collections
from decimal import Decimal

from django.utils.translation import gettext_lazy as _
from reportlab.platypus import Paragraph, Table
from reportlab.platypus import PageBreak

from ozone.core.models import Obligation
from ozone.core.models import ObligationTypes
from ozone.core.models import ApprovedCriticalUse
from ozone.core.models.utils import sum_decimals, subtract_decimals

from ..util import (
    h1_style,
    h2_style,
    left_paragraph_style,
    sm_no_spacing_style,
    sm_l,
    sm_r,
    sm_c,
    smb_c,
    TABLE_STYLES,
    grid_color,
    col_widths,
    format_decimal,
    get_remarks,
    get_date_of_reporting,
)
from ..util import ReportForSubmission
from ..util import get_submissions


__all__ = [
    'get_flowables',
]

TABLE_CUSTOM_STYLES = (
    # ('LINEBELOW', (0, 0), (-1, 2), 0.5, grid_color),
    ('GRID', (0, 0), (-1, 2), 0.5, grid_color),
    ('VALIGN', (0, 0), (-1, 0), 'TOP'),
    ('ALIGN', (0, 0), (-1, 2), 'CENTER'),
    ('ALIGN', (2, 3), (4, -1), 'RIGHT'),
    ('ALIGN', (6, 3), (13, -1), 'RIGHT'),
    ('SPAN', (4, 0), (5, 0)),  # D hspan
    ('SPAN', (4, 1), (5, 1)),  # Imported hspan
    ('SPAN', (0, 1), (0, 2)),  # Year
    ('SPAN', (1, 1), (1, 2)),  # Substance
    ('SPAN', (2, 1), (2, 2)),  # Exempted
    ('SPAN', (3, 1), (3, 2)),  # Production
    ('SPAN', (6, 1), (6, 2)),  # Total acquired
    ('SPAN', (7, 1), (7, 2)),  # Authorized
    ('SPAN', (8, 1), (8, 2)),  # On hand start
    ('SPAN', (9, 1), (9, 2)),  # Available for use
    ('SPAN', (10, 1), (10, 2)),  # Used
    ('SPAN', (11, 1), (11, 2)),  # Exported
    ('SPAN', (12, 1), (12, 2)),  # Destroyed
    ('SPAN', (13, 1), (13, 2)),  # On hand end
    ('SPAN', (14, 1), (14, 2)),  # Emergency
    ('SPAN', (15, 1), (15, 2)),  # Remark
)


def get_header(party_name, report_title):
    return [
        Paragraph(party_name.upper(), style=h1_style),
        Paragraph(report_title, style=h2_style),
    ]


def get_table_header_essen():
    return [
        (
            smb_c('A'),
            smb_c('B'),
            smb_c('C³'),
            smb_c('D'),
            smb_c('E'),
            '',
            smb_c('F<br/>(D+E)'),
            smb_c('G<br/>(C-F)'),
            smb_c('H¹'),
            smb_c('I<br/>(H+F)'),
            smb_c('J'),
            smb_c('K'),
            smb_c('L'),
            smb_c('M²<br/>(I-J-L)'),
            '',
            '',
        ),
        (
            sm_c(_('Year')),
            sm_c(_('Substance')),
            sm_c(_('Amount exempted')),
            sm_c(_('Production')),
            sm_c(_('Imported quantities')),
            '',
            sm_c(_('Total amount acquired')),
            sm_c(_('Authorized but not acquired')),
            sm_c(_('On hand start of the year')),
            sm_c(_('Available for use')),
            sm_c(_('Amount used for essential use')),
            sm_c(_('Contained in exported products')),
            sm_c(_('Amount destroyed')),
            sm_c(_('On hand end of the year')),
            sm_c(_('Emergency')),
            sm_c(_('Remark')),
        ),
        (
            '',
            '',
            '',
            '',
            sm_c(_('Amount')),
            sm_c(_('Source country')),
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
        ),
    ]


def get_table_header_crit():
    return [
        (
            smb_c('A'),
            '',  # fake column for substance
            smb_c('B¹'),
            smb_c('C'),
            smb_c('D'),
            '',
            smb_c('E<br/>(C+D)'),
            smb_c('F<br/>(B-E)'),
            smb_c('G²'),
            smb_c('H<br/>(E+G)'),
            smb_c('I'),
            smb_c('J'),
            smb_c('K'),
            smb_c('L³<br/>(H-I-J-K)'),
            '',
            '',
        ),
        (
            sm_c(_('Year')),
            '',  # fake column for substance
            sm_c(_('Amount exempted')),
            sm_c(_('Production')),
            sm_c(_('Imported quantities')),
            '',
            sm_c(_('Total amount acquired')),
            sm_c(_('Authorized but not acquired')),
            sm_c(_('On hand start of the year')),
            sm_c(_('Available for use')),
            sm_c(_('Amount used for critical use')),
            sm_c(_('Amount exported')),
            sm_c(_('Amount destroyed')),
            sm_c(_('On hand end of the year')),
            sm_c(_('Emergency')),
            sm_c(_('Remark')),
        ),
        (
            '',
            '',  # fake column for substance
            '',
            '',
            sm_c(_('Amount')),
            sm_c(_('Source country')),
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
        ),
    ]


def get_table_header_crit_categories():
    return [
        (
            sm_c(_('Year')),
            sm_c(_('Critical use category')),
            sm_c(_('Amount exempted')),
            sm_c(_('Decision')),
            sm_c(_('Amount used')),
        ),
    ]


def get_table_data_essen_crit(data, reporting_period, base_row_index, on_hand_func):
    rows = list()
    styles = list()
    for item in data:
        imports = list(item.imports.filter(
            quantity__gt=0  # filter the default Unspecified=0 rows persisted
        ).order_by('party__name').all())
        total_imported = Decimal(0.0)
        for imp in imports:
            total_imported = sum_decimals(
                total_imported,
                imp.quantity
            )
        total_acquired = sum_decimals(item.quantity_production, total_imported)
        authorized_not_acquired = subtract_decimals(item.quantity_exempted, total_acquired)
        total_available = sum_decimals(item.on_hand_start_year, total_acquired)
        on_hand_end_year = on_hand_func(total_available, item)
        first_import = imports.pop(0) if imports else None
        source_party = ''
        if first_import:
            if first_import.party:
                source_party = first_import.party.name
            elif first_import.quantity:
                source_party = _('Unspecified')
        rows.append((
            sm_c(reporting_period.name),  # A
            sm_l(item.substance.name),  # B (essen) or hidden (crit)
            sm_r(format_decimal(item.quantity_exempted)),  # C | B
            sm_r(format_decimal(item.quantity_production)),  # D | C
            sm_r(format_decimal(first_import.quantity)) if first_import else '',  # E|D - amount
            sm_l(source_party),  # E|D - source country
            sm_r(format_decimal(total_acquired)),  # F|E
            sm_r(format_decimal(authorized_not_acquired)),  # G|F
            sm_r(format_decimal(item.on_hand_start_year)),  # H|G
            sm_r(format_decimal(total_available)),  # I|H
            sm_r(format_decimal(item.quantity_used)),  # J|I
            sm_r(format_decimal(item.quantity_exported)),  # K|J
            sm_r(format_decimal(item.quantity_destroyed)),  # L|K
            sm_r(format_decimal(on_hand_end_year)),  # M|L
            sm_c(_('Yes')) if item.is_emergency else '',  # Emergency
            sm_l(get_remarks(item)),  # Remark
        ))
        row_index = base_row_index + len(rows)
        for imp in imports:
            # Add more rows if multiple import sources
            rows.append((
                # Don't repeat previously shown fields, only show E
                '', '', '', '',
                sm_r(format_decimal(imp.quantity)),
                sm_l(imp.party.name) if imp.party else _('Unspecified') if imp.quantity else '',
                '', '', '', '', '', '', '', '', '', '',
            ))
        if imports:
            # merge rows when multiple import sources (except columns E)
            span_columns = (*range(0, 4), *range(6, 16))
            styles.extend([
                #  Vertical span of common columns for all exempted rows
                ('SPAN', (col, row_index), (col, row_index + len(imports)))
                for col in span_columns
            ])

    return rows, styles


def get_table_data_essen(submission, base_row_index):
    data = submission.rafreports.exclude(substance__has_critical_uses=True)

    def on_hand_func(total_available, item):
        return subtract_decimals(
            total_available,
            sum_decimals(item.quantity_used, item.quantity_destroyed)
        )

    return get_table_data_essen_crit(
        data,
        submission.reporting_period,
        base_row_index,
        on_hand_func
    )


def get_table_data_crit(submission, base_row_index):
    data = submission.rafreports.filter(substance__has_critical_uses=True)

    def on_hand_func(total_available, item):
        return subtract_decimals(
            total_available,
            sum_decimals(
                item.quantity_used,
                sum_decimals(item.quantity_exported, item.quantity_destroyed)
            )
        )

    return get_table_data_essen_crit(
        data,
        submission.reporting_period,
        base_row_index,
        on_hand_func
    )


def get_table_data_crit_categories(submission, base_row_index):
    data = submission.rafreports.filter(substance__has_critical_uses=True)
    rows = list()
    styles = list()
    for item in data:
        approved_uses = ApprovedCriticalUse.objects.filter(
            exemption__substance=item.substance,
            exemption__submission__party=submission.party,
            exemption__submission__reporting_period=submission.reporting_period,
        )
        # sometimes there can be multple exemptions for the same substance, period and category
        # see Australia, 2011
        all_approved_categories = collections.defaultdict(list)
        for approved_use in approved_uses:
            all_approved_categories[approved_use.critical_use_category.name].append(approved_use)

        use_categories = list(item.use_categories.all())
        for use_category in use_categories:
            category_name = use_category.critical_use_category.name
            if not use_category.quantity:
                continue
            approved_uses = all_approved_categories.pop(category_name, None)
            appr = approved_uses.pop() if approved_uses else None
            rows.append((
                sm_c(submission.reporting_period.name),
                sm_l(category_name),
                sm_r(format_decimal(appr.quantity if appr else None)),
                sm_c(appr.exemption.decision_approved) if appr else '',
                sm_r(format_decimal(use_category.quantity)),
            ))
            if approved_uses:
                # multiple amounts approved, append rows and merge cells
                row_index = base_row_index + len(rows)
                for appr in approved_uses:
                    rows.append((
                        '', '',
                        sm_r(format_decimal(appr.quantity if appr else None)),
                        sm_c(appr.exemption.decision_approved) if appr else '',
                        '',
                    ))
                span_columns = (0, 1, 4,)
                styles.extend([
                    #  Vertical span of common columns
                    ('SPAN', (col, row_index), (col, row_index + len(approved_uses)))
                    for col in span_columns
                ])
        # check for unused approvals
        for unused_approval in all_approved_categories.values():
            for appr in unused_approval:
                rows.append((
                    sm_c(appr.exemption.submission.reporting_period.name),
                    sm_l(appr.critical_use_category.name),
                    sm_r(format_decimal(appr.quantity)),
                    sm_c(appr.exemption.decision_approved),
                    sm_r('-'),
                ))

    return rows, styles


def get_table_essen(submissions):
    styles = list(TABLE_STYLES + TABLE_CUSTOM_STYLES)
    rows = get_table_header_essen()
    num_header_rows = len(rows)
    for submission in submissions:
        row_data, row_styles = get_table_data_essen(submission, len(rows) - 1)
        rows += row_data
        styles += row_styles
    widths = col_widths([0.9, 2.5, 1.5, 1.5, 1.3, 2.5, 1.5, 1.5, 1.5, 1.5, 1.8, 1.5, 1.3, 1.2, 0.8, 4.0])
    if len(rows) == num_header_rows:
        return None
    return Table(rows, colWidths=widths, style=styles, hAlign='LEFT', repeatRows=3)


def get_table_crit(submissions):
    styles = list(TABLE_STYLES + TABLE_CUSTOM_STYLES)
    rows = get_table_header_crit()
    num_header_rows = len(rows)
    for submission in submissions:
        row_data, row_styles = get_table_data_crit(submission, len(rows) - 1)
        rows += row_data
        styles += row_styles
    widths = col_widths([0.9, 0, 1.5, 1.5, 1.3, 2.5, 1.5, 1.5, 1.5, 1.5, 1.8, 1.5, 1.3, 1.2, 0.8, 6.5])
    if len(rows) == num_header_rows:
        return None
    return Table(rows, colWidths=widths, style=styles, hAlign='LEFT', repeatRows=3)


def get_table_crit_categories(submissions):
    styles = list(TABLE_STYLES)
    rows = get_table_header_crit_categories()
    num_header_rows = len(rows)
    for submission in submissions:
        row_data, row_styles = get_table_data_crit_categories(submission, len(rows) - 1)
        rows += row_data
        styles += row_styles
    widths = col_widths([3, 8, 5, 6, 5])
    if len(rows) == num_header_rows:
        return None
    return Table(rows, colWidths=widths, style=styles, hAlign='LEFT', repeatRows=3)


def get_footer_essen():
    notes = [
        "(All quantities expressed in metric tonnes.)",

        """¹ National Governments may not be able to estimate quantities on hand as
        at 1 January 1996 but can track the subsequent inventory of ODS produced
        for essential uses (Column M).""",
        "² Carried forward as \"On hand start of year\" for next year.",
        """³ Note that essential use for a particular year may be the sum of quantities
        authorized by decision in more than one year.""",
    ]
    return [
        Paragraph(_(note), sm_no_spacing_style) for note in notes
    ]


def get_footer_crit():
    notes = [
        "(All quantities expressed in metric tonnes.)",

        """¹ Exempted by the parties to the Montreal Protocol.
        Note that the critical use for a particular year may be the sum of quantities
        authorized by decision in more than one year.""",
        """² Where possible, national Governments should include quantities on hand
        as of 1 January 2005 and for each year thereafter.
        National Governments that are not able to estimate quantities on hand as of
        1 January 2005 can track the subsequent inventory of methyl bromide produced
        for critical uses (column L).""",
        "³ Carried forward as \"Amount on hand at start of year\" for next year.",
    ]
    return [
        Paragraph(_(note), sm_no_spacing_style) for note in notes
    ]


def get_flowables(party_name, submissions):
    essen_title = Paragraph(
        _("Reporting accounting framework for essential uses \
        other than laboratory and analytical applications"),
        style=h2_style
    )
    # essen_title.keepWithNext = True
    essen_table = get_table_essen(submissions)
    essen_flowables = [
        essen_title,
        essen_table,
        *get_footer_essen(),
    ] if essen_table else []

    crit_title = Paragraph(
        _("Reporting accounting framework for critical uses of methyl bromide"),
        style=h2_style
    )
    # crit_title.keepWithNext = True
    crit_table = get_table_crit(submissions)

    crit_flowables = [
        crit_title,
        crit_table,
        *get_footer_crit(),
    ] if crit_table else []

    crit_categories_title = Paragraph(
        _("Details of consumption by individual critical use exemption"),
        style=h2_style
    )
    crit_categories_table = get_table_crit_categories(submissions)
    crit_flowables += [
        crit_categories_title,
        crit_categories_table,
    ] if crit_categories_table else []

    date_of_reporting_flowables = list()
    for submission in submissions:
        date_of_reporting_flowables.extend(
            get_date_of_reporting(submission)
        )

    flowables = [
        Paragraph(party_name.upper(), style=h1_style),
        Paragraph('', style=h1_style),
        *date_of_reporting_flowables,
        *essen_flowables,
        *crit_flowables,
        Paragraph('', style=h1_style),
        PageBreak(),
    ]
    return flowables


def export_submissions(submissions):
    flowables = list()
    # Regroup submissions by party
    data = collections.defaultdict(list)
    for submission in submissions:
        data[submission.party.name].append(submission)

    for party in sorted(data.keys()):
        flowables += get_flowables(party, data[party])
    if not flowables:
        flowables = [Paragraph('No data', left_paragraph_style)]

    return flowables


class RafReport(ReportForSubmission):

    name = "raf"
    has_party_param = True
    has_period_param = True
    display_name = "Reporting accounting framework essential and critical uses"
    description = _("Select one or more parties and one or more reporting periods")
    landscape = True

    def get_flowables(self):
        if self.submission:
            submissions = [self.submission]

        else:
            raf = Obligation.objects.get(_obligation_type=ObligationTypes.ESSENCRIT.value)
            submissions = get_submissions(raf, self.periods, self.parties)

        yield from export_submissions(submissions)
