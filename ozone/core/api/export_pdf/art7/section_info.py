from ..util import (
    get_comments_section,
    get_date_of_reporting_str,
    p_l, p_c,
    h1_style, no_spacing_style,
    col_widths,
    FONTSIZE_TABLE
)

from datetime import datetime
from django.utils.translation import gettext_lazy as _
from reportlab.platypus import Paragraph
from reportlab.platypus import Table
from reportlab.lib import colors

TABLE_INFO_HEADER = (
    (
        p_c('Questionnaire'), '', '', '', '', '',
        p_c(_('Annex/Group reported in full?')),
    ),
    (
        p_c(_('Imports')),
        p_c(_('Exports')),
        p_c(_('Production')),
        p_c(_('Destruction')),
        p_c(_('Non-party trade')),
        p_c(_('Emissions')),
        p_c(_('A/I')),
        p_c(_('A/II')),
        p_c(_('B/I')),
        p_c(_('B/II')),
        p_c(_('B/III')),
        p_c(_('C/I')),
        p_c(_('C/II')),
        p_c(_('C/III')),
        p_c(_('E/I')),
        p_c(_('F')),
    ),
)
TABLE_INFO_STYLE = (
    ('FONTSIZE', (0, 0), (-1, -1), FONTSIZE_TABLE),
    ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BOX', (0, 0), (5, 2), 0.5, colors.grey),
    ('BOX', (6, 0), (15, 2), 0.5, colors.grey),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('SPAN', (0, 0), (5, 0)),
    ('SPAN', (6, 0), (15, 0)),
)


def get_date_of_reporting(submission):
    date_of_reporting = get_date_of_reporting_str(submission)
    if not date_of_reporting:
        return (None,)
    else:
        return (
            p_l('%s: %s' % (
                _('Date of reporting'),
                date_of_reporting,
            )),
        )


def _kv(obj, label, prop):
    """
        Returns a paragraph in form "{label}: {field_value}"
    """
    if not hasattr(obj, prop) or not getattr(obj, prop):
        return None
    return Paragraph(
        '%s: %s' % (_(label), getattr(obj, prop)),
        style=no_spacing_style
    )


def get_submission_info(info):
    return (
        _kv(info, 'Name of reporting officer', 'reporting_officer'),
        _kv(info, 'Designation', 'designation'),
        _kv(info, 'Organization', 'organization'),
        _kv(info, 'Postal address', 'postal_address'),
        Paragraph(
            '%s: %s' % (_('Address country'), info.country.name),
            style=no_spacing_style
        ) if info.country else '',
        _kv(info, 'Phone', 'phone'),
        _kv(info, 'E-mail', 'email'),
        p_l(''),
    )


def get_questionnaire_table(submission):
    def _yn(condition):
        return p_c(_('Yes') if condition else _('No'))
    row = (
        _yn(submission.article7questionnaire.has_imports)
        if hasattr(submission, 'article7questionnaire') else '-',
        _yn(submission.article7questionnaire.has_exports)
        if hasattr(submission, 'article7questionnaire') else '-',
        _yn(submission.article7questionnaire.has_produced)
        if hasattr(submission, 'article7questionnaire') else '-',
        _yn(submission.article7questionnaire.has_destroyed)
        if hasattr(submission, 'article7questionnaire') else '-',
        _yn(submission.article7questionnaire.has_nonparty)
        if hasattr(submission, 'article7questionnaire') else '-',
        _yn(submission.article7questionnaire.has_emissions)
        if hasattr(submission, 'article7questionnaire') else '-',

        _yn(submission.flag_has_reported_a1),
        _yn(submission.flag_has_reported_a2),
        _yn(submission.flag_has_reported_b1),
        _yn(submission.flag_has_reported_b2),
        _yn(submission.flag_has_reported_b3),
        _yn(submission.flag_has_reported_c1),
        _yn(submission.flag_has_reported_c2),
        _yn(submission.flag_has_reported_c3),
        _yn(submission.flag_has_reported_e),
        _yn(submission.flag_has_reported_f),
    )
    return (
        Table(
                TABLE_INFO_HEADER + (row,),
                colWidths=col_widths([2.47] * 6 + [1.25]*10),
                style=TABLE_INFO_STYLE,
                hAlign='LEFT',
        ),
    )


def export_info(submission):
    title = (
        Paragraph("%s %s - %s %s" % (
            submission.reporting_period.description,
            submission.obligation.name,
            submission.party.name,
            ('(%s)' % (_('Provisional'),)) if submission.flag_provisional else '',
        ), h1_style),
    )
    return (
        title
        + (p_l('%s: %s' % (_('Printed at'), datetime.now().strftime('%d %B %Y %H:%M:%S'))),)
        + get_date_of_reporting(submission)
        + get_submission_info(submission.info)
        + get_questionnaire_table(submission)
        + get_comments_section(submission, 'questionnaire')
    )
