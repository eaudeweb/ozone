import re
from io import BytesIO
from copy import deepcopy
from collections import OrderedDict
from decimal import Decimal
from functools import partial
from datetime import datetime
from xml.sax.saxutils import escape

from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.db import models

from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import ListFlowable
from reportlab.platypus import ListItem
from reportlab.platypus import Paragraph
from reportlab.platypus import Spacer
from reportlab.platypus import Table
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib import pagesizes
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.units import mm

from ozone.core.models import Party
from ozone.core.models import ReportingPeriod
from ozone.core.models import Submission


STYLES = getSampleStyleSheet()

FONTSIZE_SMALL = 7
FONTSIZE_DEFAULT = 8
FONTSIZE_TABLE = FONTSIZE_SMALL
FONTSIZE_BULLET_LIST = FONTSIZE_DEFAULT - 1
FONTSIZE_H3 = FONTSIZE_DEFAULT + 2
FONTSIZE_H2 = FONTSIZE_H3 + 3
FONTSIZE_H1 = FONTSIZE_H2 + 3

grid_color = (0.4, 0.4, 0.4)
soft_color = (0.8, 0.8, 0.8)
lighter_grey = (0.95, 0.95, 0.95)


TABLE_STYLES_NOBORDER = (
    ('FONTSIZE', (0, 0), (-1, -1), FONTSIZE_TABLE),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 0),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ('LEFTPADDING', (0, 0), (-1, -1), 2),
    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
)

TABLE_STYLES = TABLE_STYLES_NOBORDER + (
    ('GRID', (0, 0), (-1, 0), 0.5, grid_color),
    ('BOX', (0, 0), (-1, -1), 0.5, grid_color),
    ('LINEBEFORE', (0, 0), (-1, -1), 0.1, soft_color),
    ('LINEABOVE', (0, 0), (-1, -1), 0.1, grid_color),
)

DOUBLE_HEADER_TABLE_STYLES = TABLE_STYLES + (
    ('GRID', (0, 0), (-1, 1), 0.5, grid_color),
    ('ALIGN', (0, 0), (-1, 1), 'CENTER'),
    ('BACKGROUND', (0, 0), (-1, 1), colors.lightgrey),
)

SINGLE_HEADER_TABLE_STYLES = TABLE_STYLES + (
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
)


def _style(style_name, **kwargs):
    style = deepcopy(STYLES[style_name])
    if kwargs is not None:
        for k, v in kwargs.items():
            setattr(style, k, v)
    return style


hr = HRFlowable(
    width="100%", thickness=1, lineCap='round', color=colors.lightgrey,
    spaceBefore=1, spaceAfter=1, hAlign='CENTER', vAlign='BOTTOM', dash=None
)

_bodytext = partial(
    _style, 'BodyText', fontSize=FONTSIZE_DEFAULT, fontName='Helvetica'
)

centered_paragraph_style = _bodytext(alignment=TA_CENTER)
centered_grey_paragraph_style = _bodytext(
    alignment=TA_CENTER, color=colors.white
)
left_paragraph_style = _bodytext(alignment=TA_LEFT)
right_paragraph_style = _bodytext(alignment=TA_RIGHT)

bold_centered_paragraph_style = _bodytext(alignment=TA_CENTER, fontName='Helvetica-Bold')
bold_left_paragraph_style = _bodytext(alignment=TA_LEFT, fontName='Helvetica-Bold')
bold_right_paragraph_style = _bodytext(alignment=TA_RIGHT, fontName='Helvetica-Bold')

small_centered_paragraph_style = _bodytext(alignment=TA_CENTER, fontSize=FONTSIZE_SMALL)
small_left_paragraph_style = _bodytext(alignment=TA_LEFT, fontSize=FONTSIZE_SMALL)
small_right_paragraph_style = _bodytext(alignment=TA_RIGHT, fontSize=FONTSIZE_SMALL)

small_bold_centered_paragraph_style = _bodytext(alignment=TA_CENTER, fontSize=FONTSIZE_SMALL,
                                                fontName='Helvetica-Bold')
small_bold_left_paragraph_style = _bodytext(alignment=TA_LEFT, fontSize=FONTSIZE_SMALL,
                                            fontName='Helvetica-Bold')
small_bold_right_paragraph_style = _bodytext(alignment=TA_RIGHT, fontSize=FONTSIZE_SMALL,
                                             fontName='Helvetica-Bold')

small_italic_centered_paragraph_style = _bodytext(alignment=TA_CENTER, fontSize=FONTSIZE_SMALL,
                                                  fontName='Helvetica-Oblique')
small_italic_left_paragraph_style = _bodytext(alignment=TA_LEFT, fontSize=FONTSIZE_SMALL,
                                              fontName='Helvetica-Oblique')
small_italic_right_paragraph_style = _bodytext(alignment=TA_RIGHT, fontSize=FONTSIZE_SMALL,
                                               fontName='Helvetica-Oblique')

small_bold_italic_left_paragraph_style = _bodytext(alignment=TA_LEFT, fontSize=FONTSIZE_SMALL,
                                                   fontName='Helvetica-BoldOblique')
small_bold_italic_right_paragraph_style = _bodytext(alignment=TA_RIGHT, fontSize=FONTSIZE_SMALL,
                                                    fontName='Helvetica-BoldOblique')
small_bold_italic_centered_paragraph_style = _bodytext(alignment=TA_CENTER, fontSize=FONTSIZE_SMALL,
                                                       fontName='Helvetica-BoldOblique')

bullet_paragraph_style = _bodytext(alignment=TA_LEFT)
no_spacing_style = _bodytext(alignment=TA_LEFT, spaceBefore=0)
sm_no_spacing_style = _bodytext(alignment=TA_LEFT, fontSize=FONTSIZE_SMALL, spaceBefore=0)


h1_style = _style(
    'Heading1',
    alignment=TA_CENTER,
    fontSize=FONTSIZE_DEFAULT + 6,
    fontName='Helvetica-Bold',
)

h2_style = _style(
    'Heading2',
    alignment=TA_LEFT,
    fontSize=FONTSIZE_DEFAULT + 4,
    fontName='Helvetica-Bold',
)

h3_style = _style(
    'Heading3',
    alignment=TA_LEFT,
    fontSize=FONTSIZE_DEFAULT + 2,
    fontName='Helvetica-Bold',
    spaceBefore=0
)

page_title_style = _style(
    'Heading3', alignment=TA_LEFT,
    fontSize=FONTSIZE_H3, fontName='Helvetica-Bold',
)


p_c = partial(Paragraph, style=centered_paragraph_style)
p_c_g = partial(Paragraph, style=centered_grey_paragraph_style)
p_l = partial(Paragraph, style=left_paragraph_style)
p_r = partial(Paragraph, style=right_paragraph_style)

b_c = partial(Paragraph, style=bold_centered_paragraph_style)
b_l = partial(Paragraph, style=bold_left_paragraph_style)
b_r = partial(Paragraph, style=bold_right_paragraph_style)

sm_c = partial(Paragraph, style=small_centered_paragraph_style)
sm_l = partial(Paragraph, style=small_left_paragraph_style)
sm_r = partial(Paragraph, style=small_right_paragraph_style)

smb_c = partial(Paragraph, style=small_bold_centered_paragraph_style)
smb_l = partial(Paragraph, style=small_bold_left_paragraph_style)
smb_r = partial(Paragraph, style=small_bold_right_paragraph_style)

smi_c = partial(Paragraph, style=small_italic_centered_paragraph_style)
smi_l = partial(Paragraph, style=small_italic_left_paragraph_style)
smi_r = partial(Paragraph, style=small_italic_right_paragraph_style)

smbi_l = partial(Paragraph, style=small_bold_italic_left_paragraph_style)
smbi_r = partial(Paragraph, style=small_bold_italic_right_paragraph_style)
smbi_c = partial(Paragraph, style=small_bold_italic_centered_paragraph_style)


p_bullet = partial(Paragraph, style=bullet_paragraph_style)
page_title = partial(Paragraph, style=page_title_style)

nbsp = "\xa0"  # non-breaking space


def col_widths(w_list):
    return list(map(lambda x: x * cm, w_list))


# Returning number as string to avoid 'E' notation
def get_big_float(nr):
    if not nr:
        return ''
    return '{:f}'.format(Decimal(str(nr)))


def format_decimal(nr):
    if nr is None:
        return ''
    if isinstance(nr, int):
        nr = Decimal(nr)
    return '{:,f}'.format(nr.normalize())


def format_decimal_diff(nr, previous_nr):
    if nr is None and previous_nr is None:
        # Just show an empty cell if both values were None
        return ''
    nr = format_decimal(nr)
    previous_nr = format_decimal(previous_nr)
    if nr != previous_nr:
        return '<b>{} ({})</b>'.format(nr, previous_nr)
    return '{} ({})'.format(nr, previous_nr)


def round_big_float(nr, precision):
    if not nr:
        return ''
    format_str = '{0:.%sf}' % (precision,)
    return format_str.format(Decimal(str(nr)))


def as_decimal(nr):
    if not nr:
        return None
    if not isinstance(nr, Decimal):
        return Decimal(repr(nr))
    return nr


# Imitate JavaScript's toPrecision. Returning the number with 'decimals'
# digits starting from the first non-zero digit
def to_precision(nr, decimals):

    if int(nr) > 999:
        return str(int(nr))
    else:
        s_nr = get_big_float(nr)

        # Getting the first non-zero digitindex
        p = re.compile(r'(?=\d)(?=[^0])')

        m = p.search(s_nr)
        f_nonzero = m.span()[0]

        # Complete the number with 0's to have space for nr of decimals
        if len(s_nr) <= f_nonzero + decimals:
            nr = s_nr[0:f_nonzero] + s_nr[f_nonzero:]
            return nr
        else:
            # Checking if substring with the number of decimals
            # has a float point
            if '.' not in s_nr[f_nonzero:f_nonzero + decimals]:
                sub = s_nr[f_nonzero:f_nonzero + decimals]
                next_digit = s_nr[f_nonzero + decimals]

                # In case of numbers with 3 digits before the point
                if next_digit == '.':
                    next_digit = s_nr[f_nonzero + decimals + 1]
            else:
                sub = s_nr[f_nonzero:f_nonzero + decimals + 1]
                # For numbers that start wih a non-zero and have exactly
                # 'decimals' digits
                if len(sub) == len(s_nr):
                    next_digit = 0
                else:
                    next_digit = s_nr[f_nonzero + decimals + 1]

            # Concatenating the string before the first non-zero digit
            n = s_nr[0:f_nonzero] + sub

            # Rounding if the next digit after the number of decimals
            # is greater or equal to 5
            if int(next_digit) >= 5:
                # If the point comes after the number of decimals, the number
                # gets rounded with 1
                if s_nr.find(sub) < s_nr.find('.'):
                    add_with = '1'
                else:
                    # Rounding with the correct value depending of the decimals
                    add_with = '0.' + '0' * len(n[n.find('.') + 1: -1]) + '1'

                n = str(round(float(n) + float(add_with), 10))

            # Getting rid of the 'E' notation
            if 'e' in n:
                return get_big_float(n)
            return n


EXEMPTED_FIELDS = OrderedDict([
    ('laboratory_analytical_uses', _('Laboratory and analytical uses')),
    ('essential_uses', _('Essential uses, other than L&A')),
    ('critical_uses', _('Critical uses')),
    ('high_ambient_temperature', _('High ambient temperature')),
    ('process_agent_uses', _('Process agent uses')),
    ('other_uses', _('Other/unspecified uses')),
])


def instances_equal(instance1, instance2):
    """
    Compares two instances of the same data model.
    Returns True if their data is identical, False otherwise.
    """
    quantity_fields = [
        f.name for f in instance1.__class__._meta.fields
        if isinstance(f, models.fields.DecimalField)
    ]
    for field_name in quantity_fields:
        if getattr(instance1, field_name) != getattr(instance2, field_name):
            return False
    return True


def get_quantity(obj, field):
    """
    field is a key in EXEMPTED_FIELDS
    """
    return getattr(obj, 'quantity_' + field) if field else None


def get_decision(obj, field):
    """
    field is a key in EXEMPTED_FIELDS
    """
    return getattr(obj, 'decision_' + field) if field else None


def get_decision_diff(obj, previous_obj, field):
    decision = get_decision(obj, field)
    previous_decision = get_decision(obj, field)

    if decision is None and previous_decision is None:
        return None

    return '{} ({})'.format(decision, previous_decision)


def get_substance_or_blend_name(obj):
    return (
        obj.substance.name
        if obj.substance
        else '%s - %s' % (
            obj.blend.blend_id,
            obj.blend.composition
        )
    )


def get_group_name(obj):
    if obj.substance and obj.substance.group_id:
        if obj.substance.group.group_id == 'F':
            return 'F/II' if obj.substance.is_captured else 'F/I'
        else:
            return obj.substance.group.name
    else:
        return ''


def rows_to_table(header, rows, colWidths, style):
    return Table(
        header + rows,
        colWidths=colWidths,
        style=style,
        hAlign='LEFT',
        repeatRows=len(header)  # repeat header on page break
    ) if rows else None


def exclude_blend_items(data):
    return data.exclude(blend_item__isnull=False)


def filter_lab_uses(data):
    return data.exclude(
        quantity_laboratory_analytical_uses__isnull=True
    ).exclude(
        quantity_laboratory_analytical_uses=0
    )


def get_remarks(item):
    if not item.remarks_party:
        return escape('OzSec:' + item.remarks_os) if item.remarks_os else ''
    else:
        if not item.remarks_os:
            return escape(item.remarks_party)
        else:
            return '%s<br/>OzSec:%s' % (
                escape(item.remarks_party), escape(item.remarks_os)
            )


def get_comments_section(submission, type):
    r_party = escape(
        getattr(submission, type + '_remarks_party', '')
    )
    r_secretariat = escape(
        getattr(submission, type + '_remarks_secretariat', '')
    )

    remarks_party = p_l('%s (%s): %s' % (
        _('Comments'), _('party'), r_party
    ))
    remarks_secretariat = p_l('%s (%s): %s' % (
        _('Comments'), _('secretariat'), r_secretariat
    ))
    return (
        remarks_party if r_party else None,
        remarks_secretariat if r_secretariat else None,
    )


#  Not used, but kept just in case we need bulleted lists
def makeBulletList(list):
    bullets = ListFlowable(
        [
            ListItem(
                p_bullet(x),
                leftIndent=10, bulletColor='black', value='circle',
                bulletOffsetY=-2.88
            ) for x in list
        ],
        bulletType='bullet', bulletFontSize=3, leftIndent=5
    )

    return bullets


# TODO: remove this after revising HAT exports
def table_from_data(
    data, isBlend, header, colWidths, style, repeatRows, emptyData=None
):

    if not data and not emptyData:
        # nothing at all unless explicitly requested
        return ()
    if not data:
        # Just a text, without a table heading
        return (p_l(emptyData))
    # Spanning all columns for the blend components rows
    if isBlend:
        rows = len(data) + repeatRows
        for row_idx in range(repeatRows + 1, rows, 2):
            style += (
                ('SPAN', (0, row_idx), (-1, row_idx)),
                ('ALIGN', (0, row_idx), (-1, row_idx), 'CENTER')
            )

    return Table(
        header + data,
        colWidths=colWidths,
        style=style,
        hAlign='LEFT',
        repeatRows=2  # repeat header on page break
    )


# TODO: remove this after revising HAT exports
def table_with_blends(blends, grouping, make_component, header, style, widths):
    result = []

    for blend_row in blends:
        # Getting the blend object based on the id
        blend = grouping.filter(blend__blend_id=blend_row[1].text).first()
        row_comp = partial(make_component, blend=blend)
        data = tuple(map(row_comp, blend.blend.components.all()))

        result.append(blend_row)
        result.append(((
            Spacer(7, mm),
            Table(header + data, style=style, colWidths=widths),
            Spacer(7, mm),
        )))

    return result


# TODO: remove this after revising HAT exports
def mk_table_substances(grouping, row_fct):
    # Excluding items with no substance,
    # then getting the ones that are not a blend
    objs = grouping.exclude(substance=None).filter(blend_item=None)
    row = partial(row_fct, isBlend=False)
    return map(row, objs)


# TODO: remove this after revising HAT exports
def mk_table_blends(grouping, row_fct, comp_fct, c_header, c_style, c_widths):
    objs = grouping.filter(substance=None)
    row = partial(row_fct, isBlend=True)

    blends = map(row, objs)

    return table_with_blends(
        blends=blends,
        grouping=grouping,
        make_component=comp_fct,
        header=c_header,
        style=c_style,
        widths=c_widths
    )


def format_date(date_obj):
    return date_obj.strftime('%d %B %Y') if date_obj else None


def get_submission_dates(submission):
    """ Returns two date objects:
        When multiple versions have been submitted:
        - date received, the original date of submission
        - date revised, the latest date of submission
        When no previous versions have been submitted and not recalled:
        - date received is the date of the current submission
        - date revised is None
    """
    if submission.obligation.has_versions:
        # This is not the first version, must check history
        versions = (
            Submission.objects.filter(
                obligation=submission.obligation,
                party=submission.party,
                reporting_period=submission.reporting_period,
            )
            .exclude(_current_state__in=submission.editable_states)
            .exclude(_current_state__in=submission.incorrect_states)
            .order_by('submitted_at')
        )
        first = versions.first()
        if first:
            first_date = first.submitted_at
            revised_date = submission.submitted_at or submission.info.date
        else:
            first_date = submission.submitted_at or submission.info.date
            revised_date = None
    else:
        first_date = submission.submitted_at or submission.info.date
        revised_date = None
    return first_date, revised_date


def get_date_of_reporting(submission):
    date_received, date_revised = get_submission_dates(submission)
    extra_text = ''
    if submission.in_initial_state:
        extra_text = '(%s)' % (_('Not yet submitted'),)
    elif submission.in_incorrect_state:
        extra_text = '(%s)' % (_('Recalled'),)
    elif submission.flag_superseded:
        extra_text = '(%s)' % (_('Superseded'),)

    if date_revised:
        return (
            Paragraph('%s: %s, %s: %s %s' % (
                _('Date first received'),
                format_date(date_received),
                _('Date revised'),
                format_date(date_revised),
                extra_text,
            ), style=no_spacing_style),
            p_l(''),
        )
    elif date_received:
        return (
            Paragraph('%s: %s %s' % (
                _('Date received'),
                format_date(date_received),
                extra_text,
            ), style=no_spacing_style),
            p_l(''),
        )
    else:
        return (None,)


class TableBuilder:

    def __init__(self, styles, column_widths, repeat_rows=None):
        self.styles = list(styles)
        self.column_widths = column_widths
        self.repeat_rows = repeat_rows
        self.rows = []

    @property
    def current_row(self):
        return len(self.rows) - 1

    def add_row(self, row):
        self.rows.append(row)

    def add_heading(self, text, style=small_bold_left_paragraph_style):
        self.rows.append([Paragraph(text, style=style)])
        self.styles.append(('SPAN', (0, self.current_row), (-1, self.current_row)))

    def done(self):
        kwargs = dict(
            colWidths=self.column_widths,
            style=self.styles,
            hAlign='LEFT',
        )

        if self.repeat_rows:
            kwargs['repeatRows'] = self.repeat_rows

        return Table(self.rows, **kwargs)


def add_page_footer(canvas, doc, footnote=None):
    canvas.saveState()
    if footnote:
        footer = Paragraph(footnote, left_paragraph_style)
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.rightMargin, h / 2)

    footer = Paragraph('%s %d' % (_('Page'), canvas._pageNumber), right_paragraph_style)
    w, h = footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.rightMargin, h)

    canvas.restoreState()


def get_doc_template(landscape=False):
    buff = BytesIO()
    # A4 size is 21cm x 29.7cm
    if landscape:
        doc = SimpleDocTemplate(
            buff,
            pagesize=pagesizes.landscape(pagesizes.A4),
            leftMargin=1 * cm,
            rightMargin=1 * cm,
            topMargin=1 * cm,
            bottomMargin=1 * cm,
        )
    else:
        doc = SimpleDocTemplate(
            buff,
            pagesize=pagesizes.A4,
            leftMargin=0.8 * cm,
            rightMargin=0.8 * cm,
            topMargin=1 * cm,
            bottomMargin=1 * cm,
        )
    return buff, doc


def get_parties(request):
    if request.user.is_secretariat:
        qs = Party.get_main_parties()
    else:
        related_parties = [
            request.user.party_id
        ] if request.user.party_id else []
        if request.user.party_group:
            related_parties += request.user.party_group.parties.values_list('id', flat=True)
        qs = Party.objects.filter(
            pk__in=related_parties
        )
    parties = request.GET.getlist(key='party')
    if parties:
        qs = qs.filter(pk__in=parties)
    return qs.order_by('name')


def get_periods(request):
    reporting_periods = request.GET.getlist(key='period')
    qs = ReportingPeriod.get_past_periods()
    if reporting_periods:
        qs = qs.filter(pk__in=reporting_periods)
    return qs.order_by('-start_date')


def get_submissions(obligation, periods, parties):
    submissions = list()
    for period in periods:
        for party in parties:
            sub = Submission.latest_submitted(
                obligation, party, period
            )
            if sub:
                submissions.append(sub)
    return submissions


def response_pdf(base_name, buf_pdf):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{base_name}_{timestamp}.pdf'
    resp = HttpResponse(buf_pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    resp['Access-Control-Expose-Headers'] = 'Content-Disposition'
    return resp


class Report:

    name = None  # must be defined in subclasses
    display_name = None  # must be defined in subclasses
    description = None  # must be defined in subclasses
    has_party_param = False
    has_period_param = False
    landscape = False

    @classmethod
    def api_description(cls):
        return {
            'name': cls.name,
            'display_name': cls.display_name,
            'description': cls.description,
            'has_party_param': cls.has_party_param,
            'has_period_param': cls.has_period_param,
        }

    @classmethod
    def from_request(cls, request):
        kwargs = {}
        if cls.has_party_param:
            kwargs['parties'] = get_parties(request)
        if cls.has_period_param:
            kwargs['periods'] = get_periods(request)
        return cls(**kwargs)

    def __init__(self, **kwargs):
        if self.has_party_param:
            self.parties = kwargs.pop('parties')
        if self.has_period_param:
            self.periods = kwargs.pop('periods')
        assert not kwargs, f"Unexpected parameters: {kwargs!r}"

    def get_basename(self):
        base_name = self.name
        if self.has_party_param:
            base_name += "_" + "_".join(p.abbr for p in self.parties)
        if self.has_period_param:
            base_name += "_" + "_".join(p.name for p in self.periods)
        return base_name

    def render_to_response(self):
        base_name = self.get_basename()
        pdf_buf = self.render()
        return response_pdf(base_name, pdf_buf)

    def render(self):
        buff, doc = get_doc_template(landscape=self.landscape)

        doc.build(
            list(self.get_flowables()),
            onFirstPage=add_page_footer,
            onLaterPages=add_page_footer
        )

        buff.seek(0)
        return buff

    def get_flowables(self):
        raise NotImplementedError


class ReportForSubmission(Report):
    """ A special report type that can be generated for a given submission """

    submission = None

    @classmethod
    def for_submission(cls, submission):
        self = cls(parties=[submission.party], periods=[submission.reporting_period])
        self.submission = submission
        return self

    def get_basename(self):
        if self.submission:
            return f'{self.name}_{self.submission.party.abbr}_{self.submission.reporting_period.name}'
        else:
            return super().get_basename()
