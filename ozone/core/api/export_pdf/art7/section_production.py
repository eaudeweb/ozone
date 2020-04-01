from django.utils.translation import gettext_lazy as _
from reportlab.platypus import Paragraph

from ..util import (
    format_decimal, format_decimal_diff,
    instances_equal,
    get_decision, get_decision_diff,
    get_comments_section,
    get_group_name,
    get_remarks,
    rows_to_table,
    sm_c, sm_l, sm_r,
    h2_style, h3_style, col_widths,
    lighter_grey,
    SINGLE_HEADER_TABLE_STYLES,
    DOUBLE_HEADER_TABLE_STYLES,
    EXEMPTED_FIELDS,
)


def to_row(obj, row_index, diff=False, previous_obj=None):
    """
    - row_index represents the current number of table rows, including header
    - if diff is True, will display row containing both current (obj) and
      previous value (previous_obj)
    """
    rows = list()
    styles = list()
    # there are no blends in production form, so it's safe to assume a substance

    # Check if there are any non-null exemption fields
    field_names = [
        f for f in EXEMPTED_FIELDS
        if getattr(obj, 'quantity_' + f)
        or getattr(previous_obj, 'quantity_' + f, None)
    ]
    first_field = field_names.pop(0) if field_names else None

    # Build up dictionary of field_name: formatted_value
    field_dict = {}
    for f in obj.decimal_field_names:
        if not diff:
            field_dict[f] = format_decimal(getattr(obj, f))
        else:
            field_dict[f] = format_decimal_diff(
                getattr(obj, f), getattr(previous_obj, f)
            )

    decision = get_decision(obj, first_field) if not diff \
        else get_decision_diff(obj, previous_obj, first_field)

    # Add base row
    rows.append((
        sm_c(get_group_name(obj)),
        sm_l(obj.substance.name),
        sm_r(field_dict['quantity_total_produced']),
        sm_r(field_dict['quantity_feedstock']),
        sm_r(field_dict['quantity_for_destruction']),
        sm_r(field_dict['quantity_' + first_field] if first_field else ''),
        sm_l(
            '%s %s' % (
                EXEMPTED_FIELDS[first_field],
                decision
            )
        ) if first_field else '',
        sm_r(field_dict['quantity_article_5']),
        # TODO: diff the remarks
        sm_l(get_remarks(obj)),
    ))

    # Add more rows if there are still fields in field_names
    for f in field_names:
        decision = get_decision(obj, f) if not diff else \
            get_decision_diff(obj, previous_obj, f)
        rows.append((
            # Don't repeat previously shown fields
            '', '', '', '', '',
            sm_r(field_dict['quantity_' + f]),
            sm_l('%s %s' % (EXEMPTED_FIELDS[f], decision)),
            '', '',
        ))

    # quantity_quarantine_pre_shipment
    if field_dict['quantity_quarantine_pre_shipment']:
        decision = get_decision(
            obj, 'quantity_quarantine_pre_shipment'
        ) if not diff else get_decision_diff(
            obj, previous_obj, 'quantity_quarantine_pre_shipment'
        )
        # Add two rows for QPS
        rows.extend([
            (
                '', '', '', '', '',
                sm_c(_('Amount produced for QPS applications within your country and for export')),
                '', '', '',
            ),
            (
                '', '', '', '', '',
                sm_r(field_dict['quantity_quarantine_pre_shipment']),
                decision,
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
    return rows, styles


# These will be used for
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
# Header for captured substances
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


def export_production(submission, queryset):
    data = list(queryset)
    comments = get_comments_section(submission, 'production')

    if not data and not any(comments):
        return tuple()

    captured_items = list()
    rows = list()

    for p in data:
        if p.substance.is_captured:
            # process them in a second pass
            captured_items.append(p)
            continue
        (p_rows, p_styles) = to_row(
            p,
            len(rows) + len(header_f1)
        )
        rows.extend(p_rows)
        styles.extend(p_styles)

    table_f1 = rows_to_table(
        header_f1,
        rows,
        col_widths([1.0, 2.8, 2.5, 5, 0, 2.5, 5, 2.5, 6]),  # 27.3
        styles
    )

    # Start over another table, for captured substances
    captured_styles = list(SINGLE_HEADER_TABLE_STYLES)
    rows = list()
    for p in captured_items:
        (p_rows, p_styles) = to_row(
            p,
            len(rows) + len(header_f2)
        )
        rows.extend(p_rows)
        captured_styles.extend(p_styles)

    table_f2 = rows_to_table(
        header_f2,
        rows,
        col_widths([1.0, 2.8, 2.5, 2.5, 2.5, 2.5, 5, 2.5, 6]),  # 27.3
        captured_styles
    )

    return (subtitle, table_f1, table_f2) + comments


def export_production_diff(
    submission, previous_submission, queryset, previous_queryset
):
    data = list(queryset)
    previous_data = list(previous_queryset)
    comments = get_comments_section(submission, 'production')
    previous_comments = get_comments_section(previous_submission, 'production')

    # If it's all empty do not return anything
    if (
        not data
        and not previous_data
        and not any(comments)
        and not any(previous_comments)
    ):
        return tuple()

    data_dict = dict()
    for item in data:
        key = item.substance
        data_dict[key] = item
    # It's OK to use set() on the keys as they are unique
    data_set = set(data_dict.keys())

    previous_data_dict = dict()
    for item in previous_data:
        key = item.substance
        previous_data_dict[key] = item
    # It's OK to use set() on the keys as they are unique
    previous_data_set = set(previous_data_dict.keys())

    # Compute added, changed and removed keys, taking into account they are
    # unique.
    added_keys = list(data_set.difference(previous_data_set))
    changed_keys = [
        key
        for key in data_set.intersection(previous_data_set)
        if instances_equal(data_dict[key], previous_data_dict[key]) is False
    ]
    removed_keys = list(previous_data_set.difference(data_set))

    if not added_keys and not changed_keys and not removed_keys:
        # Nothing has been changed, return empty tuple
        return ()

    # Now populate PDF
    ret = (subtitle,)
    all_data = (
        (_('Added'), added_keys, data_dict, {}),
        (_('Changed'), changed_keys, data_dict, previous_data_dict),
        (_('Removed'), removed_keys, {}, previous_data_dict),
    )
    for sub_subtitle, keys, dictionary, previous_dictionary in all_data:
        if not keys:
            # Do not add anything if there are no keys for this sub-section
            continue

        captured_items = list()
        rows = list()

        for key in keys:
            diff = False
            previous_item = None
            if not previous_dictionary:
                item = dictionary[key]
            elif not dictionary:
                item = previous_dictionary[key]
            else:
                diff = True
                item = dictionary[key]
                previous_item = previous_dictionary[key]

            if item.substance.is_captured:
                # process them in a second pass
                captured_items.append((item, previous_item, diff,))
                continue
            (p_rows, p_styles) = to_row(
                item,
                len(rows) + len(header_f1),
                diff,
                previous_item
            )
            rows.extend(p_rows)
            styles.extend(p_styles)

        table_f1 = rows_to_table(
            header_f1,
            rows,
            col_widths([1.0, 2.8, 2.5, 5, 0, 2.5, 5, 2.5, 6]),  # 27.3
            styles
        )

        # Start over another table, for captured substances
        captured_styles = list(SINGLE_HEADER_TABLE_STYLES)
        rows = list()
        for item, previous_item, diff in captured_items:
            (p_rows, p_styles) = to_row(
                item,
                len(rows) + len(header_f2),
                diff,
                previous_item
            )
            rows.extend(p_rows)
            captured_styles.extend(p_styles)

        table_f2 = rows_to_table(
            header_f2,
            rows,
            col_widths([1.0, 2.8, 2.5, 2.5, 2.5, 2.5, 5, 2.5, 6]),  # 27.3
            captured_styles
        )

        ret += (
            Paragraph(sub_subtitle, h3_style),
            table_f1,
            table_f2,
            # Also insert linebreak to keep it beautiful
            Paragraph('<br/>', h3_style)
        )

    # TODO: also diff between comments and previous_comments?!
    return ret
