import itertools
from datetime import datetime

from ..util import (
    get_comments_section,
    get_date_of_reporting,
    get_date_of_reporting_diff,
    p_l, p_c, b_c,
    h1_style, no_spacing_style,
    col_widths,
    FONTSIZE_TABLE
)

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


def _kv_diff(obj, previous_obj, label, prop):
    """
        Returns a paragraph in form:
        {label}: {field_value} ({prev_field_value})
    """
    if (
        (not hasattr(obj, prop) or not getattr(obj, prop))
        and (not hasattr(previous_obj, prop) or not getattr(previous_obj, prop))
    ):
        return None
    return Paragraph(
        '%s: %s (%s)' % (
            _(label), getattr(obj, prop, '-'), getattr(previous_obj, prop, '-')
        ),
        style=no_spacing_style
    )


def get_submission_info(info):
    reporter = _kv(info, 'Name of reporting officer', 'reporting_officer')
    if reporter and info.email:
        reporter = Paragraph(
            '%s (%s)' % (reporter.text, info.email),
            style=no_spacing_style
        )
    else:
        reporter = _kv(info, 'E-mail', 'email')

    return (
        reporter,
        _kv(info, 'Designation', 'designation'),
        _kv(info, 'Organization', 'organization'),
        # _kv(info, 'Postal address', 'postal_address'),
        Paragraph(
            '%s: %s' % (_('Address country'), info.country.name),
            style=no_spacing_style
        ) if info.country and info.country.name != info.submission.party.name else None,
        # _kv(info, 'Phone', 'phone'),
        p_l(''),
    )


def get_submission_info_diff(info, previous_info):
    reporter = info.reporting_officer
    if reporter and info.email:
        reporter = '%s (%s)' % (reporter, info.email)
    else:
        reporter = info.email

    previous_reporter = previous_info.reporting_officer
    if previous_reporter and previous_info.email:
        previous_reporter = '%s (%s)' % (previous_reporter, previous_info.email)
    else:
        previous_reporter = previous_info.email
    reporters = Paragraph(
        "%s: %s (%s)" % (
            _('Name of reporting officer'), reporter, previous_reporter
        ),
        style=no_spacing_style
    )

    address_country = None
    previous_address_country = None
    if info.country and info.country.name != info.submission.party.name:
        address_country = info.country.name
    if previous_info.country and previous_info.country.name != previous_info.submission.party.name:
        previous_address_country = previous_info.country.name

    return (
        reporters,
        _kv_diff(info, previous_info, 'Designation', 'designation'),
        _kv_diff(info, previous_info, 'Organization', 'organization'),
        # _kv_diff(info, previous_info, 'Postal address', 'postal_address'),
        Paragraph(
            '%s: %s (%s)' % (
                _('Address country'),
                address_country or info.submission.party.name,
                previous_address_country or previous_info.submission.party.name
            ),
            style=no_spacing_style
        ) if (address_country or previous_address_country) else None,
        # _kv_diff(info, previous_info, 'Phone', 'phone'),
        p_l(''),
    )


def get_questionnaire_table_contents(submission):
    def _yn(condition):
        # Questionnaire flags are nullable booleans
        if condition is None:
            return '-'
        return _('Yes') if condition else _('No')
    return (
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


def get_questionnaire_table(submission):
    contents = get_questionnaire_table_contents(submission)
    row = map(p_c, contents)
    return (
        Table(
                TABLE_INFO_HEADER + (row,),
                colWidths=col_widths([2.47] * 6 + [1.25]*10),
                style=TABLE_INFO_STYLE,
                hAlign='LEFT',
        ),
    )


def get_questionnaire_table_diff(submission, previous_submission):
    row = get_questionnaire_table_contents(submission)
    previous_row = get_questionnaire_table_contents(previous_submission)

    diff_row = []
    found_diff = False
    for item, previous_item in itertools.zip_longest(row, previous_row):
        if item != previous_item:
            diff_row.append(b_c(item))
            found_diff = True
        else:
            diff_row.append(b_c(' '))

    if not found_diff:
        # Return empty tuple so we do not display the table
        return ()

    return (
        Table(
                TABLE_INFO_HEADER + (diff_row,),
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


def export_info_diff(submission, previous_submission):
    provisional = ('(%s)' % (_('Provisional'),)) \
        if submission.flag_provisional else ''
    revision = "%s %s" % (submission.revision, provisional)
    previous_provisional = ('(%s)' % (_('Provisional'),)) \
        if previous_submission.flag_provisional else ''
    previous_revision = "%s %s" % (
        previous_submission.revision, previous_provisional
    )
    title = (
        Paragraph(
            "Comparison for %s %s - %s between revisions %s and %s" % (
                submission.reporting_period.description,
                submission.obligation.name,
                submission.party.name,
                revision,
                previous_revision,
            ),
            h1_style
        ),
    )
    return (
        title
        + (p_l('%s: %s' % (_('Printed at'), datetime.now().strftime('%d %B %Y %H:%M:%S'))),)
        + get_date_of_reporting_diff(submission, previous_submission)
        + get_submission_info_diff(submission.info, previous_submission.info)
        + get_questionnaire_table_diff(submission, previous_submission)
        + get_comments_section(submission, 'questionnaire')
    )
