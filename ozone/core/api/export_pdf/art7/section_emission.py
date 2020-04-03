from itertools import zip_longest
from reportlab.platypus import Paragraph

from django.utils.translation import gettext_lazy as _

from ..util import (
    instances_equal,
    format_decimal, format_decimal_diff,
    get_comments_section,
    get_remarks,
    rows_to_table,
    sm_c, sm_l, sm_r,
    h2_style, h3_style,
    DOUBLE_HEADER_TABLE_STYLES,
    col_widths,
)

subtitle = Paragraph(
    "%s (%s)" % (_("Emissions of HFC-23"), _("metric tonnes")),
    h2_style
)

table_header = (
    (
        sm_c(_('Facility name or identifier')),
        sm_c(_('Total amount generated')),
        sm_c(_('Amount generated and captured')),
        '',
        '',
        sm_c(_('Amount used for feedstock without prior capture')),
        sm_c(_('Amount destroyed without prior capture')),
        sm_c(_('Amount of generated emissions')),
        sm_c(_('Remarks')),
    ),
    (
        '',
        '',
        sm_c(_('For all uses')),
        sm_c(_('For feedstock use in your country')),
        sm_c(_('For destruction')),
        '',
        '',
        '',
        '',
    )
)
table_style = DOUBLE_HEADER_TABLE_STYLES + (
    ('SPAN', (0, 0), (0, 1)),  # Facility
    ('SPAN', (1, 0), (1, 1)),  # Total amount
    ('SPAN', (2, 0), (4, 0)),  # Amount generated and captured
    ('SPAN', (5, 0), (5, 1)),  # Feedstock
    ('SPAN', (6, 0), (6, 1)),  # Destroyed
    ('SPAN', (7, 0), (7, 1)),  # Emissions
    ('SPAN', (8, 0), (8, 1)),  # Remarks
)


def table_row(obj):
    fields = (
        obj.quantity_generated,
        obj.quantity_captured_all_uses,
        obj.quantity_captured_feedstock,
        obj.quantity_captured_for_destruction,
        obj.quantity_feedstock,
        obj.quantity_destroyed,
        obj.quantity_emitted,
    )
    return (
        sm_l(obj.facility_name),
    ) + tuple(
        sm_r(format_decimal(field))
        for field in fields
    ) + (
        sm_l(get_remarks(obj)),
    )


def table_row_diff(obj, previous_obj):
    fields = (
        (obj.quantity_generated, previous_obj.quantity_generated),
        (
            obj.quantity_captured_all_uses,
            previous_obj.quantity_captured_all_uses
        ),
        (
            obj.quantity_captured_feedstock,
            previous_obj.quantity_captured_feedstock
        ),
        (
            obj.quantity_captured_for_destruction,
            previous_obj.quantity_captured_for_destruction
        ),
        (obj.quantity_feedstock, previous_obj.quantity_feedstock),
        (obj.quantity_destroyed, previous_obj.quantity_destroyed),
        (obj.quantity_emitted, previous_obj.quantity_emitted)
    )
    return (
        sm_l(obj.facility_name),
    ) + tuple(
        sm_r(format_decimal_diff(field))
        for field in fields
    ) + (
        sm_l(get_remarks(obj)),
    )


def export_emission(submission, queryset):
    data = list(queryset)
    comments = get_comments_section(submission, 'emissions')

    if not data and not any(comments):
        return tuple()

    table = rows_to_table(
        table_header,
        tuple(map(table_row, data)),
        col_widths([4, 2.5, 2.4, 2.8, 2.4, 2.6, 2.6, 2.4, 5.6]),
        table_style
    )

    return (subtitle, table) + comments


def export_emission_diff(
    submission, previous_submission, queryset, previous_queryset
):
    data = list(queryset)
    previous_data = list(previous_queryset)
    comments = get_comments_section(submission, 'emissions')
    previous_comments = get_comments_section(previous_submission, 'emissions')

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
        key = item.facility_name
        data_dict[key] = item
    # It's OK to use set() on the keys as they are unique
    data_set = set(data_dict.keys())

    previous_data_dict = dict()
    for item in previous_data:
        key = item.facility_name
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

        if not previous_dictionary:
            data = tuple(map(table_row, dictionary.values()))
        elif not dictionary:
            data = tuple(map(table_row, previous_dictionary.values()))
        else:
            data = tuple(
                map(
                    table_row_diff,
                    zip_longest(
                        dictionary.values(), previous_dictionary.values()
                    )
                )
            )

        table = rows_to_table(
            table_header,
            data,
            col_widths([4, 2.5, 2.4, 2.8, 2.4, 2.6, 2.6, 2.4, 5.6]),
            table_style
        )

        ret += (
            Paragraph(sub_subtitle, h3_style),
            table,
            # Also insert linebreak to keep it beautiful
            Paragraph('<br/>', h3_style)
        )

    # TODO: comments diff
    return ret
