from decimal import Decimal
from reportlab.platypus import Paragraph
from itertools import zip_longest

from django.utils.translation import gettext_lazy as _

from ozone.core.models.utils import sum_decimals
from ..util import (
    format_decimal, format_decimal_diff,
    get_substance_or_blend_name,
    get_group_name,
    rows_to_table,
    sm_c, sm_r, sm_l,
    h2_style, h3_style,
    SINGLE_HEADER_TABLE_STYLES,
    col_widths,
)


def instances_equal(item, previous_item):
    """
    Compares two dicts containing production/consumption data.
    """
    for field in ('production', 'consumption'):
        if item[field] != previous_item[field]:
            return False
    return True


def table_row(item):
    return (
        sm_c(item['group']),
        sm_l(item['substance']),
        sm_r(format_decimal(item['production'])),
        sm_r(format_decimal(item['consumption'])),
        sm_l(item['remark']),
    )


def table_row_diff(item, previous_item):
    return (
        sm_c(item['group']),
        sm_l(item['substance']),
        sm_r(
            format_decimal_diff(
                item['production'], previous_item['production']
            )
        ),
        sm_r(
            format_decimal_diff(
                item['consumption'], previous_item['consumption']
            )
        ),
        sm_l(item['remark']),
    )


def join_labuse_data(imports, production):
    data = {}

    for item in imports:
        substance_name = get_substance_or_blend_name(item)
        if substance_name not in data:
            data[substance_name] = {
                'group': get_group_name(item),
                'substance': substance_name,
                'consumption': item.quantity_laboratory_analytical_uses,
                'production': Decimal('0.0'),
                'remark': item.decision_laboratory_analytical_uses or '',
            }
        else:
            data[substance_name]['consumption'] = sum_decimals(
                data[substance_name]['consumption'],
                item.quantity_laboratory_analytical_uses
            )
            data[substance_name]['remark'] = ' '.join(filter(None, [
                data[substance_name]['remark'],
                item.decision_laboratory_analytical_uses
            ]))

    for item in production:
        substance_name = get_substance_or_blend_name(item)
        if substance_name not in data:
            data[substance_name] = {
                'group': get_group_name(item),
                'substance': substance_name,
                'consumption': Decimal('0.0'),
                'production': item.quantity_laboratory_analytical_uses,
                'remark': item.decision_laboratory_analytical_uses or '',
            }
        else:
            data[substance_name]['production'] = sum_decimals(
                data[substance_name]['production'],
                item.quantity_laboratory_analytical_uses
            )
            data[substance_name]['remark'] = ' '.join(filter(None, [
                data[substance_name]['remark'],
                item.decision_laboratory_analytical_uses
            ]))

    return data


subtitle = Paragraph(
    "%s (%s)" % (
        _('Laboratory and analytical uses under the global exemption'),
        _('metric tonnes')
    ), h2_style
)

table_header = ((
    sm_c(_('Annex/Group')),
    sm_c(_('Substance name')),
    sm_c(_('Production')),
    sm_c(_('Consumption')),
    sm_c(_('Remarks')),
),)


def export_labuses(imports, production):
    data = join_labuse_data(imports, production)
    if not data:
        return tuple()

    table = rows_to_table(
        table_header,
        tuple(map(table_row, data.values())),
        col_widths([1.0, 3, 4, 4, 15.3]),
        SINGLE_HEADER_TABLE_STYLES
    )

    return (subtitle, table)


def export_labuses_diff(
    imports, production, previous_imports, previous_production
):
    data = join_labuse_data(imports, production)
    previous_data = join_labuse_data(previous_imports, previous_production)
    if not data and not previous_data:
        return tuple()

    # It's OK to use set() on the keys as they are unique (substance names)
    data_set = set(data.keys())
    previous_data_set = set(previous_data.keys())

    # Compute added, changed and removed keys, taking into account they are
    # unique.
    added_keys = list(data_set.difference(previous_data_set))
    changed_keys = [
        key
        for key in data_set.intersection(previous_data_set)
        if instances_equal(data[key], previous_data[key]) is False
    ]
    removed_keys = list(previous_data_set.difference(data_set))

    if not added_keys and not changed_keys and not removed_keys:
        # Nothing has been changed, return empty tuple
        return ()

    # Now populate PDF
    ret = (subtitle,)
    all_data = (
        (_('Added'), added_keys, data, {}),
        (_('Changed'), changed_keys, data, previous_data),
        (_('Removed'), removed_keys, {}, previous_data),
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
            col_widths([1.0, 3, 4, 4, 15.3]),
            SINGLE_HEADER_TABLE_STYLES
        )
        ret += (
            Paragraph(sub_subtitle, h3_style),
            table,
            # Also insert linebreak to keep it beautiful
            Paragraph('<br/>', h3_style)
        )

    # TODO: comments
    return ret
