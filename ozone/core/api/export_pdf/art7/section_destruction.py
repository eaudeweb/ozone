from reportlab.platypus import Paragraph
from itertools import zip_longest

from django.utils.translation import gettext_lazy as _

from ..util import (
    instances_equal,
    format_decimal, format_decimal_diff,
    get_comments_section,
    get_substance_or_blend_name,
    get_group_name,
    rows_to_table,
    get_remarks,
    sm_c, sm_r, sm_l,
    h2_style, h3_style,
    SINGLE_HEADER_TABLE_STYLES,
    col_widths,
)


def table_row(obj):
    return (
        sm_c(get_group_name(obj)),
        sm_l(get_substance_or_blend_name(obj)),
        sm_r(format_decimal(obj.quantity_destroyed)),
        sm_l(get_remarks(obj)),
    )


def table_row_diff(obj, previous_obj):
    return (
        sm_c(get_group_name(obj)),
        sm_l(get_substance_or_blend_name(obj)),
        sm_r(
            format_decimal_diff(
                obj.quantity_destroyed, previous_obj.quantity_destroyed
            )
        ),
        sm_l(get_remarks(obj)),
    )


# Used for exporting both submission and diff
subtitle = Paragraph(
    "%s (%s)" % (_('Destroyed'), _('metric tonnes')),
    h2_style
)

table_header = ((
    sm_c(_('Annex/Group')),
    sm_c(_('Substance or mixture')),
    sm_c(_('Quantity destroyed')),
    sm_c(_('Remarks')),
),)


def export_destruction(submission, queryset):
    data = list(queryset)
    comments = get_comments_section(submission, 'destruction')

    if not data and not any(comments):
        return tuple()

    table = rows_to_table(
        table_header,
        tuple(map(table_row, data)),
        col_widths([2.1, 8, 4, 13.2]),
        SINGLE_HEADER_TABLE_STYLES
    )

    return (subtitle, table) + comments


def export_destruction_diff(
    submission, previous_submission, queryset, previous_queryset
):
    data = list(queryset)
    previous_data = list(previous_queryset)
    comments = get_comments_section(submission, 'destruction')
    previous_comments = get_comments_section(previous_submission, 'destruction')

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
        key = (item.substance, item.blend)
        data_dict[key] = item
    # It's OK to use set() on the keys as they are unique
    data_set = set(data_dict.keys())

    previous_data_dict = dict()
    for item in previous_data:
        key = (item.substance, item.blend)
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
            col_widths([2.1, 8, 4, 13.2]),
            SINGLE_HEADER_TABLE_STYLES
        )
        ret += (
            Paragraph(sub_subtitle, h3_style),
            table,
            # Also insert linebreak to keep it beautiful
            Paragraph('<br/>', h3_style)
        )

    # TODO: comments diff
    return ret

