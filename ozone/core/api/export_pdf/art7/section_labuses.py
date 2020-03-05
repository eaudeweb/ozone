from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from reportlab.platypus import Paragraph

from ozone.core.models.utils import sum_decimals

from ..util import (
    format_decimal,
    get_substance_or_blend_name,
    get_group_name,
    rows_to_table,
    sm_c, sm_r, sm_l,
    h2_style,
    SINGLE_HEADER_TABLE_STYLES,
    col_widths,
)


def table_row(item):
    return (
        sm_c(item['group']),
        sm_l(item['substance']),
        sm_r(format_decimal(item['production'])),
        sm_r(format_decimal(item['consumption'])),
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


def export_labuses(imports, production):
    data = join_labuse_data(imports, production)
    if not data:
        return tuple()

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

    table = rows_to_table(
        table_header,
        tuple(map(table_row, data.values())),
        col_widths([1.0, 3, 4, 4, 15.3]),
        SINGLE_HEADER_TABLE_STYLES
    )

    return (subtitle, table)
