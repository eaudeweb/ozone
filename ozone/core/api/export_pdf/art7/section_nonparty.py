from itertools import zip_longest
from reportlab.platypus import Paragraph

from django.utils.translation import gettext_lazy as _

from ..util import format_decimal, format_decimal_diff
from ..util import get_comments_section
from ..util import (
    instances_equal,
    get_group_name,
    get_substance_or_blend_name,
    rows_to_table,
    get_remarks,
    sm_c, sm_r, sm_l,
    h2_style, h3_style,
    DOUBLE_HEADER_TABLE_STYLES,
    col_widths,
)

subtitle = Paragraph(
    _("Imports from and/or exports to non-parties"),
    h2_style
)

table_header = (
    (
        sm_c(_('Annex/Group')),
        sm_c(_('Substance or mixture')),
        sm_c(_('Exporting or destination country/region/territory')),
        sm_c(_('Quantity of imports from non-parties')),
        '',
        sm_c(_('Quantity of exports from non-parties')),
        '',
        sm_c(_('Remarks')),
    ),
    (
        '',
        '',
        '',
        sm_c(_('New imports')),
        sm_c(_('Recovered and reclaimed imports')),
        sm_c(_('New exports')),
        sm_c(_('Recovered and reclaimed exports')),
        '',
    )
)

table_style = DOUBLE_HEADER_TABLE_STYLES + (
    ('SPAN', (0, 0), (0, 1)),  # Annex group
    ('SPAN', (1, 0), (1, 1)),  # Substance
    ('SPAN', (2, 0), (2, 1)),  # Party
    ('SPAN', (3, 0), (4, 0)),  # Imports
    ('SPAN', (5, 0), (6, 0)),  # Exports
    ('SPAN', (7, 0), (7, 1)),  # Remarks
)


def table_row(obj):
    return (
        sm_c(get_group_name(obj)),
        sm_l(get_substance_or_blend_name(obj)),
        sm_l(obj.trade_party.name if obj.trade_party else ''),
        sm_r(format_decimal(obj.quantity_import_new)),
        sm_r(format_decimal(obj.quantity_import_recovered)),
        sm_r(format_decimal(obj.quantity_export_new)),
        sm_r(format_decimal(obj.quantity_export_recovered)),
        sm_l(get_remarks(obj)),
    )


def table_row_diff(obj, previous_obj):
    tp_name = obj.trade_party.name if obj.trade_party else ''
    previous_tp_name = previous_obj.trade_party.name \
        if previous_obj.trade_party else ''
    if tp_name or previous_tp_name:
        trade_party = '{} ({})'.format(tp_name, previous_tp_name)
    else:
        trade_party = ''
    return (
        sm_c(get_group_name(obj)),
        sm_l(get_substance_or_blend_name(obj)),
        sm_l(trade_party),
        sm_r(
            format_decimal_diff(
                obj.quantity_import_new, previous_obj.quantity_import_new
            )
        ),
        sm_r(
            format_decimal_diff(
                obj.quantity_import_recovered,
                previous_obj.quantity_import_recovered
            )
        ),
        sm_r(
            format_decimal_diff(
                obj.quantity_export_new, previous_obj.quantity_export_new
            )
        ),
        sm_r(
            format_decimal_diff(
                obj.quantity_export_recovered,
                previous_obj.quantity_export_recovered
            )
        ),
        # TODO: add remarks diff
        sm_l(get_remarks(obj)),
    )


def export_nonparty(submission, queryset):
    data = list(queryset)
    comments = get_comments_section(submission, 'nonparty')

    if not data and not any(comments):
        return tuple()

    table = rows_to_table(
        table_header,
        tuple(map(table_row, data)),
        col_widths([2.1, 5, 4, 2.3, 2.6, 2.3, 2.6, 6.4]),
        table_style
    )

    return (subtitle, table) + comments


def export_nonparty_diff(
    submission, previous_submission, queryset, previous_queryset
):
    data = list(queryset)
    previous_data = list(previous_queryset)
    comments = get_comments_section(submission, 'nonparty')
    previous_comments = get_comments_section(previous_submission, 'nonparty')

    # Do not display any nonparty diff if there is nothing to display
    if (
        not data
        and not previous_data
        and not any(comments)
        and not any(previous_comments)
    ):
        return tuple()

    data_dict = dict()
    for item in data:
        key = (item.substance, item.trade_party)
        data_dict[key] = item
    # It's OK to use set() on the keys as they are unique
    data_set = set(data_dict.keys())

    previous_data_dict = dict()
    for item in previous_data:
        key = (item.substance, item.trade_party)
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
        # Nothing has been changed, return empty paragraph
        return Paragraph(' ', h3_style),

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
            col_widths([2.1, 5, 4, 2.3, 2.6, 2.3, 2.6, 6.4]),
            table_style
        )
        ret += (
            Paragraph(sub_subtitle, h3_style),
            table,
            # Also insert linebreak to keep it beautiful
            Paragraph('<br/>', h3_style)
        )

    # TODO: take comments into account
    return ret
