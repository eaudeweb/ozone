from django.utils.translation import gettext_lazy as _
from reportlab.platypus import Paragraph

from ..util import (
    format_decimal,
    get_quantity,
    get_decision,
    get_comments_section,
    get_group_name,
    get_remarks,
    rows_to_table,
    sm_c, sm_l, sm_r,
    h2_style, col_widths,
    lighter_grey,
    SINGLE_HEADER_TABLE_STYLES,
    DOUBLE_HEADER_TABLE_STYLES,
    EXEMPTED_FIELDS,
)


def to_row(obj, row_index):
    # row_index represents the current number of table rows, including header
    rows = list()
    styles = list()
    # there are no blends in production form, so it's safe to assume a substance

    # Check if there are any non-null exemption fields
    field_names = [f for f in EXEMPTED_FIELDS if getattr(obj, 'quantity_' + f)]
    first_field = field_names.pop(0) if field_names else None

    # Add base row
    rows.append((
        sm_c(get_group_name(obj)),
        sm_l(obj.substance.name),
        sm_r(format_decimal(obj.quantity_total_produced)),
        sm_r(format_decimal(obj.quantity_feedstock)),
        sm_r(format_decimal(obj.quantity_for_destruction)),
        sm_r(format_decimal(get_quantity(obj, first_field))) if first_field else '',
        sm_l(
            '%s %s' % (
                EXEMPTED_FIELDS[first_field],
                get_decision(obj, first_field)
            )
        ) if first_field else '',
        sm_r(format_decimal(obj.quantity_article_5)),
        sm_l(get_remarks(obj)),
    ))

    # Add more rows if there are still fields in field_names
    for f in field_names:
        rows.append((
            # Don't repeat previously shown fields
            '', '', '', '', '',
            sm_r(format_decimal(get_quantity(obj, f))),
            sm_l('%s %s' % (EXEMPTED_FIELDS[f], get_decision(obj, f))),
            '', '',
        ))

    # quantity_quarantine_pre_shipment
    if obj.quantity_quarantine_pre_shipment:
        # Add two rows for QPS
        rows.extend([
            (
                '', '', '', '', '',
                sm_c(_('Amount produced for QPS applications within your country and for export')),
                '', '', '',
            ),
            (
                '', '', '', '', '',
                sm_r(format_decimal(obj.quantity_quarantine_pre_shipment)),
                get_decision(obj, 'quarantine_pre_shipment'),
                '', '',
            )
        ])
        current_row = row_index + len(rows) - 1
        styles.extend([
            ('SPAN', (5, current_row-1), (6, current_row-1)),  # Quantity + Decision (heading)
            ('BACKGROUND', (5, current_row-1), (6, current_row-1), lighter_grey),
            ('ALIGN', (5, current_row-1), (6, current_row-1), 'CENTER'),
        ])

    if len(rows) > 1:
        current_row = row_index + len(rows) - 1
        styles.extend([
            #  Vertical span of common columns for all exempted rows
            ('SPAN', (0, row_index), (0, current_row)),  # Annex Group
            ('SPAN', (1, row_index), (1, current_row)),  # Substance
            ('SPAN', (2, row_index), (2, current_row)),  # Total production
            ('SPAN', (3, row_index), (3, current_row)),  # Feedstock
            ('SPAN', (4, row_index), (4, current_row)),  # Captured for destruction
            ('SPAN', (7, row_index), (7, current_row)),  # Art 5
            ('SPAN', (8, row_index), (8, current_row)),  # Remarks
        ])
    return (rows, styles)


def export_production(submission, queryset):
    data = list(queryset)
    comments = get_comments_section(submission, 'production')

    if not data and not any(comments):
        return tuple()

    subtitle = Paragraph(
        "%s (%s)" % (_('Production'), _('metric tonnes')),
        h2_style
    )

    styles = list(DOUBLE_HEADER_TABLE_STYLES) + [
        ('SPAN', (0, 0), (0, 1)),  # Annex/Group
        ('SPAN', (1, 0), (1, 1)),  # Substance
        ('SPAN', (2, 0), (2, 1)),  # Total production
        ('SPAN', (3, 0), (3, 1)),  # Feedstock
        ('SPAN', (5, 0), (6, 0)),  # Exempted
        ('SPAN', (7, 0), (7, 1)),  # Art 5
        ('SPAN', (8, 0), (8, 1)),  # Remarks
    ]
    header_f1 = [
        (
            sm_c(_('Annex/Group')),
            sm_c(_('Substance')),
            sm_c(_('Total production for all uses')),
            sm_c(_('Production for feedstock uses within your country')),
            '',  # Destruction column is not needed for F/I but
                 # it's added (invisible) to have a single to_row function
            sm_c(_('Production for exempted essential, '
                   'critical or other uses within your country')),
            '',
            sm_c(_('Production for supply to Article 5 countries')),
            sm_c(_('Remarks')),
        ),
        (
            '',
            '',
            '',
            '',
            '',
            sm_c(_('Quantity')),
            sm_c(_('Decision / type of use')),
            '',
            '',
        ),
    ]

    captured_items = list()
    rows = list()

    def prepare_item(obj, num_header_rows):
        (p_rows, p_styles) = to_row(
            p,
            len(rows) + num_header_rows
        )
        rows.extend(p_rows)
        styles.extend(p_styles)

    for p in data:
        if p.substance.is_captured:
            # process them in a second pass
            captured_items.append(p)
            continue
        prepare_item(p, len(header_f1))

    table_f1 = rows_to_table(
        header_f1,
        rows,
        col_widths([1.0, 2.8, 2.5, 5, 0, 2.5, 5, 2.5, 6]),  # 27.3
        styles
    )

    # Start over another table, for captured substances
    header_f2 = [
        (
            # Table header for F/II substances
            '', '',
            sm_c(_('Captured for all uses')),
            sm_c(_('Captured for feedstock uses within your country')),
            sm_c(_('Captured for destruction')),
            '', '', '', ''
        ),
    ]
    styles = list(SINGLE_HEADER_TABLE_STYLES)
    rows = list()
    for p in captured_items:
        prepare_item(p, len(header_f2))

    table_f2 = rows_to_table(
        header_f2,
        rows,
        col_widths([1.0, 2.8, 2.5, 2.5, 2.5, 2.5, 5, 2.5, 6]),  # 27.3
        styles
    )

    return (subtitle, table_f1, table_f2) + comments


def export_production_diff(
    submission, previous_submission, queryset, previous_queryset
):
    pass
