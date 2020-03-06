import uuid
import tempfile

import adminactions.actions as actions

from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, RelatedDropdownFilter, RelatedOnlyDropdownFilter
)
from django.contrib import admin, messages
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import logout as auth_logout
from django.contrib.admin import site, AdminSite, TabularInline
from django.contrib.admin.models import LogEntry, DELETION
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import F, Q, Subquery, CharField, TextField
from django.forms import TextInput, Textarea, ModelForm
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.urls import reverse
from django.utils.html import format_html
from django.views.decorators.cache import never_cache
from rest_framework.authtoken.models import Token
from django.utils.translation import gettext_lazy as _
from django.http import FileResponse
from django.http import HttpResponseRedirect

from ozone.core.export.submissions import export_submissions, ExportError
from ozone.core.calculated import baselines
from ozone.core.calculated import limits

# Register your models here.
from .models import (
    Meeting,
    Treaty,
    Region,
    Subregion,
    MDGRegion,
    Party,
    PartyHistory,
    ReportingPeriod,
    Obligation,
    Annex,
    Group,
    Substance,
    Blend,
    BlendComponent,
    Submission,
    SubmissionInfo,
    ReportingChannel,
    SubmissionFormat,
    BaselineType,
    ControlMeasure,
    Baseline,
    Limit,
    PartyRatification,
    PartyDeclaration,
    Nomination,
    ExemptionApproved,
    CriticalUseCategory,
    ApprovedCriticalUse,
    ObligationTypes,
    Transfer,
    Email,
    EmailTemplate,
    EmailTemplateAttachment,
    ProcessAgentDecision,
    ProcessAgentApplication,
    ProcessAgentEmissionLimit,
    ProcessAgentUsesReported,
    Decision,
    DeviationType,
    DeviationSource,
    PlanOfActionDecision,
    PlanOfAction,
    ProdCons,
    ProdConsMT,
    FocalPoint,
    LicensingSystem,
    LicensingSystemFile,
    LicensingSystemURL,
    Website,
    OtherCountryProfileData,
    ReclamationFacility,
    IllegalTrade,
    ORMReport,
    MultilateralFund,
    TEAPReportType,
    TEAPReport,
    TEAPIndicativeNumberOfReports,
    ImpComBody,
    ImpComTopic,
    ImpComRecommendation,
)


User = get_user_model()


class Singleton(type):
    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class OzoneAuthenticationForm(AuthenticationForm):
    """Custom auth form, that allows non-staff users as well."""
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': _(
            "Please enter the correct %(username)s and password for the "
            "account. Note that both fields may be case-sensitive."
        ),
    }
    required_css_class = 'required'


# For some reason this is instantiated twice, somewhere (!?)
# Make it singleton.

class OzoneAdminSite(AdminSite, metaclass=Singleton):
    """Custom admin site"""
    login_form = OzoneAuthenticationForm

    # Text to put at the end of each page's <title>.
    site_title = _('ORS')

    # Text to put in each page's <h1>.
    site_header = _('Ozone Reporting System')

    # Text to put at the top of the admin index page.
    index_title = _('Administration')

    def get_urls(self):
        return [
            path('ozone_tools/generate_baselines/', self.generate_baselines),
            path('ozone_tools/generate_limits/', self.generate_limits),
        ] + super().get_urls()

    def generate_baselines(self, request):
        context = dict(self.each_context(request))
        return baselines.admin_view(request, context)

    def generate_limits(self, request):
        context = dict(self.each_context(request))
        return limits.admin_view(request, context)

    @never_cache
    def login(self, request, extra_context=None):
        response = super(OzoneAdminSite, self).login(request, extra_context=extra_context)
        if request.user.is_authenticated:
            # Set authToken cookie, this is also used by the FrontEnd app
            token, created = Token.objects.get_or_create(user=request.user)
            if request.GET.get('next'):
                response = redirect(request.GET.get('next'))
            response.set_cookie("authToken", token.key)
        return response

    @never_cache
    def logout(self, request, extra_context=None):
        auth_logout(request)
        response = redirect(reverse("admin:login"))
        response.delete_cookie("authToken")
        return response

    @never_cache
    def index(self, request, extra_context=None):
        """Override to prevent infinite redirects."""
        response = super(OzoneAdminSite, self).index(request, extra_context=extra_context)
        if request.user.is_active and not request.user.is_staff:
            # This doesn't work on development.
            return redirect("/")
        return response

    def has_permission(self, request):
        """Override, and remove the is_staff condition. Each resource is
        protected individually, except for the index page.
        """
        return request.user.is_active


def custom_title_dropdown_filter(title):
    class Wrapper(DropdownFilter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title = title
    return Wrapper


class ReportingPeriodFilter(admin.SimpleListFilter):
    title = 'Period'
    parameter_name = 'reporting_period_id'

    def lookups(self, request, model_admin):
        return model_admin.get_queryset(request).distinct().order_by(
            '-reporting_period__start_date'
        ).values_list(
            'reporting_period_id', 'reporting_period__name'
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(reporting_period_id=self.value())
        else:
            return queryset


def related_dropdown_filter(
    model_class, title, related_field, sort_field, sort_asc=True
):
    class Wrapper(RelatedDropdownFilter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            descending = '' if sort_asc else '-'
            self.lookup_choices = model_class.objects.distinct().order_by(
                f'{descending}{related_field}__{sort_field}'
            ).values_list(
                f'{related_field}__id', f'{related_field}__name'
            )
            self.title = title
    return Wrapper


def substance_dropdown_filter(model_class, related_field='substance'):
    return related_dropdown_filter(
        model_class=model_class,
        title='substance',
        related_field=related_field,
        sort_field='sort_order',
        sort_asc=True,
    )


def party_dropdown_filter(model_class, related_field='party'):
    return related_dropdown_filter(
        model_class=model_class,
        title='party',
        related_field=related_field,
        sort_field='name',
        sort_asc=True,
    )


def reporting_period_dropdown_filter(model_class, related_field='reporting_period'):
    return related_dropdown_filter(
        model_class=model_class,
        title='period',
        related_field=related_field,
        sort_field='start_date',
        sort_asc=False,
    )


# Meeting-related models
@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('meeting_id', 'description', 'location', 'start_date', 'end_date')
    list_filter = ('treaty_flag',)
    search_fields = ['meeting_id', 'description', 'location']


@admin.register(Treaty)
class TreatyAdmin(admin.ModelAdmin):
    list_display = ('name', 'meeting_id', 'date', 'entry_into_force_date')


# Party-related models
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbr')


@admin.register(MDGRegion)
class MDGRegionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'income_type', 'get_parent_regions', 'get_child_regions')
    search_fields = ['code', 'name']

    def get_parent_regions(self, obj):
        return ', '.join(x.name for x in obj.parent_regions.all())
    get_parent_regions.short_description = 'Parents'

    def get_child_regions(self, obj):
        return ', '.join(x.name for x in obj.child_regions.all())
    get_child_regions.short_description = 'Children'


@admin.register(Subregion)
class SubregionAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbr', 'region')
    list_filter = ('region',)
    search_fields = ["abbr", "name"]


class MainPartyFilter(RelatedDropdownFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup_choices = Party.objects.filter(
            is_active=True,
            parent_party__id=F('id'),
        ).order_by('name').values_list('id', 'name')


class ParentPartyFilter(RelatedDropdownFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup_choices = Party.objects.filter(
            is_active=True,
            id__in=Subquery(Party.objects.exclude(
                parent_party__id=F('id'),
            ).values('parent_party_id'))
        ).order_by('name').values_list('id', 'name')


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbr', 'subregion', 'parent_party')
    list_filter = (
        'subregion__region', 'subregion',
        ('parent_party', ParentPartyFilter)
    )
    search_fields = ['name', 'abbr']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        main_parties_queryset = Party.objects.filter(
            is_active=True,
            parent_party__id=F('id'),
        ).order_by('name')
        form.base_fields['parent_party'].queryset = main_parties_queryset
        return form


@admin.register(PartyHistory)
class PartyHistoryAdmin(admin.ModelAdmin):
    list_display = ('party', 'reporting_period', 'party_type')
    list_filter = (
        'party_type',
        ('reporting_period__name', custom_title_dropdown_filter('period')),
        ('party', MainPartyFilter),
    )
    search_fields = ["party__name"]


# Substance-related models
@admin.register(Annex)
class AnnexAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'name', 'description', 'name_alt', 'description_alt', 'control_treaty', 'report_treaty')
    list_filter = ('annex', 'control_treaty', 'report_treaty')


@admin.register(Substance)
class SubstanceAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'group', 'description', 'odp', 'gwp',
        'formula', 'number_of_isomers', 'sort_order',
    )
    list_filter = ('group', 'is_contained_in_polyols', 'is_captured', 'has_critical_uses')
    search_fields = ['name', 'description', 'substance_id']


@admin.register(Blend)
class BlendAdmin(admin.ModelAdmin):
    list_display = (
        'blend_id', 'composition',
        'type', 'party', 'odp', 'gwp',
        'trade_name', 'sort_order',
    )
    list_filter = (
        'type',
        ('party', MainPartyFilter),
    )
    search_fields = ['blend_id', 'legacy_blend_id']


@admin.register(BlendComponent)
class BlendComponentAdmin(admin.ModelAdmin):
    list_display = ('blend', 'substance', 'percentage')
    search_fields = ['blend__blend_id', 'substance__name']
    list_filter = (
        ('blend__blend_id', DropdownFilter),
        'blend__type',
    )


# Reporting-related models
@admin.register(ReportingPeriod)
class ReportingPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'description')
    search_fields = ["name"]
    list_filter = (
        'is_reporting_open', 'is_reporting_allowed',
    )
    ordering = ('-end_date',)


@admin.register(Obligation)
class ObligationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_default', 'is_active')
    exclude = ('has_reporting_periods',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    base_list_display = (
        "username", "first_name", "last_name", "email", "is_secretariat", "is_read_only", "party",
        "is_active", "activated", "last_login",
    )
    superuser_list_display = (
        "login_as",
    )
    search_fields = ["username", "first_name", "last_name"]
    actions = ["reset_password"]
    exclude = ["password", "user_permissions"]
    readonly_fields = ["last_login", "date_joined", "created_by", "activated"]
    list_filter = (
        ("party", MainPartyFilter),
        "is_secretariat", "is_read_only", "is_staff", "is_superuser",
        "is_active", "activated",
    )

    def reset_password(self, request, queryset, template="password_reset"):
        domain_override = request.META.get("HTTP_HOST")
        use_https = request.environ.get("wsgi.url_scheme", "https").lower() == "https"
        users = []

        body = f"registration/{template}_email.html"
        subject = f"registration/{template}_subject.txt"

        for user in queryset:
            form = PasswordResetForm({'email': user.email})
            form.full_clean()
            form.save(
                domain_override=domain_override, use_https=use_https, email_template_name=body,
                subject_template_name=subject,
            )
            users.append(user.username)
        if len(users) > 10:
            self.message_user(request, _("Email sent to %d users for password reset") % len(users),
                              level=messages.SUCCESS)
        else:
            self.message_user(request, _("Email sent to %s for password reset") % ", ".join(users),
                              level=messages.SUCCESS)
    reset_password.short_description = _("Reset user password")

    def login_as(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('impersonate-start', kwargs={"uid": obj.id}),
            _('Login'),
        )

    def get_list_display(self, request):
        if request.user.is_superuser:
            return self.base_list_display + self.superuser_list_display

        return self.base_list_display

    def save_model(self, request, obj, form, change):
        if not change:
            # Set a random password for the new user
            # The user will need to set a new password
            obj.password = str(uuid.uuid4())
            obj.created_by = request.user
            # The user is inactive until a password is set
            obj.activated = False
        super(UserAdmin, self).save_model(request, obj, form, change)
        if not change:
            self.reset_password(request, [obj], template="account_created")


def _build_getter(prefix, name):
    def get_boolean(obj):
        return getattr(obj, prefix + name)
    get_boolean.short_description = name.upper()
    get_boolean.boolean = True
    return get_boolean


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):

    def __getattr__(self, name):
        return _build_getter('flag_has_reported_', name)

    list_display = (
        '__str__', 'party', 'reporting_period', 'obligation', '_current_state',
        'flag_provisional', 'flag_valid', 'flag_superseded',
        'flag_checked_blanks', 'flag_has_blanks', 'flag_confirmed_blanks',
        'flag_emergency',
        'a1', 'a2', 'b1', 'b2', 'b3', 'c1', 'c2', 'c3', 'e', 'f',
    )
    list_filter = (
        'obligation',
        ('reporting_period', reporting_period_dropdown_filter(Submission)),
        ('party', MainPartyFilter),
        '_current_state',
        'flag_provisional', 'flag_valid', 'flag_superseded',
        'flag_checked_blanks', 'flag_has_blanks', 'flag_confirmed_blanks',
        'flag_emergency',
        'flag_has_reported_a1', 'flag_has_reported_a2',
        'flag_has_reported_b1', 'flag_has_reported_b2', 'flag_has_reported_b3',
        'flag_has_reported_c1', 'flag_has_reported_c2', 'flag_has_reported_c3',
        'flag_has_reported_e',
        'flag_has_reported_f'
    )
    search_fields = ['party__name']

    def get_readonly_fields(self, request, obj=None):
        self.readonly_fields = []
        for field in self.model._meta.fields:
            if 'flag' not in field.name and 'state' not in field.name:
                self.readonly_fields.append(field.name)
        return self.readonly_fields

    def get_deleted_objects(self, objs, request):
        deletable_objects, model_count, perms_needed, protected = super(
            SubmissionAdmin, self
        ).get_deleted_objects(objs, request)
        protected = False
        return deletable_objects, model_count, perms_needed, protected

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj._current_state = 'data_entry'
            obj.save()
            obj.delete()

    def delete_model(self, request, obj):
        obj._current_state = 'data_entry'
        obj.save()
        obj.delete()

    def export_legacy_xlsx(self, request, queryset):
        try:
            data = export_submissions(queryset)
        except ExportError as e:
            self.message_user(request, e, messages.ERROR)
            return

        output = tempfile.NamedTemporaryFile()
        data.dump_xlsx(output.name)
        return FileResponse(
            output,
            as_attachment=True,
            filename='legacy_submissions.xlsx',
        )

    export_legacy_xlsx.short_description = "Export legacy XLSX"

    actions = admin.ModelAdmin.actions + [export_legacy_xlsx]


@admin.register(SubmissionInfo)
class SubmissionInfoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'reporting_officer', 'country', 'date')
    list_filter = (
        (
            'submission__reporting_period',
            reporting_period_dropdown_filter(
                model_class=SubmissionInfo,
                related_field='submission__reporting_period'
            )
        ),
        ('submission__party', MainPartyFilter),
        'submission_format',
        'submission__obligation',
    )
    search_fields = ('submission__party__name',)
    readonly_fields = ('submission', )


@admin.register(ReportingChannel)
class ReportingChannelAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'description',
        'is_party', 'is_default_party',
        'is_secretariat', 'is_default_secretariat',
    )


@admin.register(SubmissionFormat)
class SubmissionFormatAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_default_party')


@admin.register(BaselineType)
class BaselineTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'remarks')


@admin.register(ControlMeasure)
class ControlMeasureAdmin(admin.ModelAdmin):
    list_display = (
        'group', 'party_type', 'limit_type', 'baseline_type', 'start_date', 'end_date', 'allowed',
    )
    list_filter = ('group', 'party_type', 'limit_type', 'baseline_type')


@admin.register(Baseline)
class BaselineAdmin(admin.ModelAdmin):
    list_display = (
        'party', 'group', 'baseline_type', 'baseline',
    )
    list_filter = ('group', 'baseline_type', ('party', MainPartyFilter))
    search_fields = ["party__name"]


@admin.register(Limit)
class LimitAdmin(admin.ModelAdmin):
    list_display = (
        'party', 'group', 'reporting_period', 'limit_type', 'limit',
    )
    list_filter = (
        'group', 'limit_type',
        ('reporting_period__name', custom_title_dropdown_filter('period')),
        ('party', MainPartyFilter)
    )
    search_fields = ['party__name', 'party__abbr']


@admin.register(PartyRatification)
class PartyRatificationAdmin(admin.ModelAdmin):
    list_display = ('party', 'treaty', 'ratification_type', 'ratification_date', 'entry_into_force_date')
    list_filter = (('party', MainPartyFilter), 'treaty', 'ratification_type')
    search_fields = ['party__name', 'treaty__name']


@admin.register(PartyDeclaration)
class PartyDeclarationAdmin(admin.ModelAdmin):
    list_display = ('party', )
    list_filter = (('party', MainPartyFilter),)
    search_fields = ['party__name', 'declaration']
    ordering = ('party__name', )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        main_parties_queryset = Party.objects.filter(
            is_active=True,
            parent_party__id=F('id'),
        ).order_by('name')
        form.base_fields['party'].queryset = main_parties_queryset
        return form


class ExemptionBaseAdmin:
    # TODO: maybe merge with ProcessAgentBaseAdmin
    def get_reporting_period(self, obj):
        return obj.submission.reporting_period
    get_reporting_period.short_description = 'Reporting period'

    def get_party(self, obj):
        return obj.submission.party
    get_party.short_description = 'Party'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        submission_queryset = Submission.objects.filter(
            obligation___obligation_type=ObligationTypes.EXEMPTION.value
        ).order_by('reporting_period__name')
        form.base_fields['submission'].queryset = submission_queryset
        return form


@admin.register(Nomination)
class NominationAdmin(ExemptionBaseAdmin, admin.ModelAdmin):
    list_display = (
        'get_reporting_period', 'get_party',
        'substance',
        'quantity', 'is_emergency',
    )
    search_fields = ['submission__party__name']
    list_filter = (
        (
            'submission__reporting_period',
            reporting_period_dropdown_filter(
                model_class=Nomination,
                related_field='submission__reporting_period'
            )
        ),
        (
            'submission__party',
            party_dropdown_filter(
                model_class=Nomination,
                related_field='submission__party'
            )
        ),
        ('substance', substance_dropdown_filter(Nomination)),
        'is_emergency'
    )
    ordering = ('-submission__reporting_period__name', 'submission__party__name')


class ApprovedCriticalUseInline(admin.TabularInline):
    model = ApprovedCriticalUse
    fields = ['critical_use_category', 'quantity']


class ExemptionApprovedAdminForm(ModelForm):
    class Meta:
        widgets = {
            'remarks_os': Textarea(attrs={'rows': 4, 'cols': 120})
        }


@admin.register(ExemptionApproved)
class ExemptionApprovedAdmin(ExemptionBaseAdmin, admin.ModelAdmin):
    list_display = (
        'get_reporting_period', 'get_party',
        'substance',
        'decision_approved',
        'quantity', 'approved_teap_amount', 'is_emergency',
    )
    search_fields = ['decision_approved', 'submission__party__name']
    list_filter = (
        (
            'submission__reporting_period',
            reporting_period_dropdown_filter(
                model_class=ExemptionApproved,
                related_field='submission__reporting_period'
            )
        ),
        (
            'submission__party',
            party_dropdown_filter(
                model_class=ExemptionApproved,
                related_field='submission__party'
            )
        ),
        ('decision_approved', custom_title_dropdown_filter('decision')),
        ('substance', substance_dropdown_filter(ExemptionApproved)),
        'is_emergency'
    )
    ordering = ('-submission__reporting_period__name', 'submission__party__name')
    form = ExemptionApprovedAdminForm
    inlines = [ApprovedCriticalUseInline]


@admin.register(ApprovedCriticalUse)
class ApprovedCriticalUseAdmin(admin.ModelAdmin):

    class Media:
        # bigger width for select2 widgets
        css = {
            'all': ('css/admin.css',),
        }

    def get_reporting_period(self, obj):
        return obj.exemption.submission.reporting_period
    get_reporting_period.short_description = 'Reporting period'

    def get_party(self, obj):
        return obj.exemption.submission.party
    get_party.short_description = 'Party'

    def get_decision(self, obj):
        return obj.exemption.decision_approved
    get_decision.short_description = 'Decision'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        exemption_queryset = ExemptionApproved.objects.filter(
            substance__has_critical_uses=True
        ).order_by('-submission__reporting_period__name', 'submission__party__name')
        form.base_fields['exemption'].queryset = exemption_queryset
        return form

    list_display = (
        'get_reporting_period', 'get_party',
        'get_decision',
        'critical_use_category',
        'quantity',
    )
    list_filter = (
        ('exemption__submission__reporting_period__name', custom_title_dropdown_filter('period')),
        ('exemption__submission__party', MainPartyFilter),
        ('exemption__decision_approved', custom_title_dropdown_filter('decision')),
        ('critical_use_category__name', custom_title_dropdown_filter('category')),
    )
    search_fields = (
        'critical_use_category__name', 'exemption__decision_approved',
    )
    autocomplete_fields = ('critical_use_category',)

    ordering = ('-exemption__submission__reporting_period__name', 'exemption__submission__party__name')


@admin.register(CriticalUseCategory)
class CriticalUseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )
    exclude = ('code',)
    search_fields = ['name']


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = (
        'reporting_period', 'source_party', 'destination_party', 'substance', 'transferred_amount',
    )
    list_filter = (
        ('source_party', MainPartyFilter),
        ('destination_party', MainPartyFilter),
        ('reporting_period__name', custom_title_dropdown_filter('period')),
        ('substance__name', custom_title_dropdown_filter('substance')),
    )
    search_fields = (
        'source_party__name', 'destination_party__name', 'substance__name'
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        main_parties_queryset = Party.objects.filter(
            is_active=True,
            parent_party__id=F('id'),
        ).order_by('name')
        source_sub_queryset = dest_sub_queryset = Submission.objects.filter(
            obligation___obligation_type=ObligationTypes.TRANSFER.value
        ).order_by('reporting_period__name')
        if obj is not None:
            source_sub_queryset = source_sub_queryset.filter(
                party=obj.source_party
            )
            dest_sub_queryset = dest_sub_queryset.filter(
                party=obj.destination_party
            )
        form.base_fields['source_party_submission'].queryset = source_sub_queryset
        form.base_fields['destination_party_submission'].queryset = dest_sub_queryset
        form.base_fields['source_party'].queryset = main_parties_queryset
        form.base_fields['destination_party'].queryset = main_parties_queryset
        return form


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ('date', 'subject', 'to', 'submission')
    list_filter = (
        ('submission__reporting_period__name', custom_title_dropdown_filter('period')),
        ('submission__party', MainPartyFilter),
    )


class EmailTemplateAttachmentInline(TabularInline):
    model = EmailTemplateAttachment
    extra = 1


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', )
    search_fields = ['name', 'subject', 'description', ]
    inlines = [
        EmailTemplateAttachmentInline,
    ]


@admin.register(ProcessAgentDecision)
class ProcessAgentDecisionAdmin(admin.ModelAdmin):
    list_display = (
        'decision',
        'application_validity_start_date',
        'application_validity_end_date',
        'emit_limits_validity_start_date',
        'emit_limits_validity_end_date',
    )


class ProcessAgentDecisionFilter(DropdownFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = 'Decision'
        self.lookup_choices = ProcessAgentDecision.objects.values_list(
            'decision__decision_id', flat=True
        )


@admin.register(ProcessAgentApplication)
class ProcessAgentApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'counter', 'start_date', 'end_date', 'substance',
        'application', 'decision', 'remark'
    )
    list_filter = (
        ('substance', substance_dropdown_filter(ProcessAgentApplication)),
        (
            'decision__decision__decision_id',
            ProcessAgentDecisionFilter
        ),
        ('counter', custom_title_dropdown_filter('counter'))
    )
    search_fields = (
        'decision__decision__decision_id', 'substance__name', 'application', 'remark'
    )
    formfield_overrides = {
        CharField: {'widget': TextInput(attrs={'size': '120'})},
        TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 120})},
    }


@admin.register(ProcessAgentEmissionLimit)
class ProcessAgentEmissionLimitAdmin(admin.ModelAdmin):
    list_display = (
        'party', 'start_date', 'end_date',
        'decision', 'makeup_consumption', 'max_emissions'
    )
    list_filter = (
        ('party', RelatedOnlyDropdownFilter),
        (
            'decision__decision__decision_id',
            ProcessAgentDecisionFilter
        )
    )
    search_fields = ('party__name', 'decision__decision__decision_id')


class ProcessAgentBaseAdmin:
    class Media:
        # bigger width for select2 widgets
        css = {
            'all': ('css/admin.css',),
        }

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        submission_queryset = Submission.objects.filter(
            obligation___obligation_type=ObligationTypes.PROCAGENT.value
        ).order_by('reporting_period__name')
        form.base_fields['submission'].queryset = submission_queryset
        return form


class PADecisionFilter(RelatedDropdownFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup_choices = ProcessAgentDecision.objects.order_by(
            'application_validity_start_date'
        ).values_list('id', 'decision__decision_id')


@admin.register(ProcessAgentUsesReported)
class ProcessAgentUsesReportedAdmin(ProcessAgentBaseAdmin, admin.ModelAdmin):
    def get_application(self, obj):
        return (
            f'{obj.application.counter}. {obj.application.application}'
            if obj.application else ''
        )
    get_application.short_description = 'Application'

    def get_substance(self, obj):
        return obj.application.substance.name if obj.application and obj.application.substance else ''
    get_substance.short_description = 'Substance'

    def get_decision(self, obj):
        return obj.decision.decision.decision_id if obj.decision else ''
    get_decision.short_description = 'Decision'

    def get_containment(self, obj):
        return obj.contain_technologies if obj.contain_technologies else ''
    get_containment.short_description = 'Containment technologies'

    def get_view_on_site_url(self, obj=None):
        if obj is None or obj.submission is None:
            return None
        return obj.submission_uri

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["party", "reporting_period"]
        else:
            return []

    def get_form(self, request, obj=None, **kwargs):
        """
        Overriding get_form to:
        - add support for clone-type requests
        - restrict possible values in the second step based on data entered
          in the first step.
        """
        form = super().get_form(request, obj, **kwargs)

        if request.GET:
            clone_id = request.GET.get('clone_id')
            submission_id = request.GET.get('submission_id')

            if clone_id:
                # If this is a clone request for a valid object, set initial
                # values in form to the cloned object's field values
                obj = ProcessAgentUsesReported.objects.filter(
                    id=clone_id
                ).first()
                if obj:
                    for field in form.base_fields.keys():
                        form.base_fields[field].initial = getattr(
                            obj, field, None
                        )
                    # Now just return "cloned" form
                    return form
            if submission_id:
                # If this is a prefill request for a valid submission, set
                # initial values in form to the submission's attributes
                submission = Submission.objects.filter(id=submission_id).first()
                if submission:
                    form.base_fields['submission'].initial = submission
                    for field in ['party', 'reporting_period']:
                        form.base_fields[field].initial = getattr(
                            submission, field, None
                        )
                    # Now just return pre-filled form
                    return form

        party = None
        period = None
        step = request.POST.get('step')

        if obj is None and step == 'continue':
            # If party/period are in the request, take them into account
            party = request.POST.get('party') if request.POST else None
            period = request.POST.get('period') if request.POST else None

            if party:
                form.base_fields['party'].initial = Party.objects.get(id=party)
                form.base_fields['party'].queryset = \
                    Party.objects.filter(id=party)
            if period:
                form.base_fields['reporting_period'].initial = \
                    ReportingPeriod.objects.get(id=period)
                form.base_fields['reporting_period'].queryset = \
                    ReportingPeriod.objects.filter(id=period)

        # If party and period are not set from the request, get them from the
        # object, if present (get_form is used both for "add" and "change").
        party = obj.party.id if (obj and party is None) else party
        period = obj.reporting_period.id if (obj and period is None) else period

        if party and period:
            submissions_qs = Submission.objects.filter(
                obligation___obligation_type=ObligationTypes.PROCAGENT.value,
                party_id=party,
                reporting_period_id=period
            ).order_by('reporting_period__name')
            form.base_fields['submission'].queryset = submissions_qs

        if period:
            # Restrict choices of decision based on chosen reporting period
            rp = ReportingPeriod.objects.get(id=period)
            decision_qs = ProcessAgentDecision.objects.filter(
                (
                    (
                        Q(application_validity_start_date__lte=rp.end_date)
                        | Q(application_validity_start_date__isnull=True)
                    )
                    & (
                        Q(application_validity_end_date__gte=rp.start_date)
                        | Q(application_validity_end_date__isnull=True)
                    )
                )
                & (
                    (
                        Q(emit_limits_validity_start_date__lte=rp.end_date)
                        | Q(emit_limits_validity_start_date__isnull=True)
                    )
                    & (
                        Q(emit_limits_validity_end_date__gte=rp.start_date)
                        | Q(emit_limits_validity_end_date__isnull=True)
                    )
                )
            )
            form.base_fields['decision'].queryset = decision_qs

            # Restrict choices of application based on chosen reporting period
            applications_qs = ProcessAgentApplication.objects.filter(
                (
                    Q(decision__application_validity_start_date__lte=rp.end_date)
                    | Q(decision__application_validity_start_date__isnull=True)
                )
                & (
                    Q(decision__application_validity_end_date__gte=rp.start_date)
                    | Q(decision__application_validity_end_date__isnull=True)
                )
            ).order_by('counter')
            form.base_fields['application'].queryset = applications_qs

        return form

    def add_view(self, request, form_url='', extra_context=None):
        """
        Overriding add_view to implement two-step creation of new UsesReported
        instances.
        """
        step = None
        party = None
        period = None
        submission = None
        clone_id = None
        submission_id = None
        if request.POST:
            step = request.POST.get('step', None)
            party = request.POST.get('party')
            period = request.POST.get('period')
            submission = request.POST.get('submission')
        if request.GET:
            clone_id = request.GET.get('clone_id')
            submission_id = request.GET.get('submission_id')

        context = {}
        if (
            request.method == 'GET'
            and clone_id is None and submission_id is None
            and step is None and submission is None
            and party is None and period is None
        ):
            # This is the first step; inject parties and periods into context
            # so that they can be used by the template.
            context['periods'] = ReportingPeriod.objects.all().order_by('name')
            context['default_period'] = ReportingPeriod.get_current_period()
            context['parties'] = Party.objects.filter(
                parent_party__id=F('id')
            ).order_by('name')
            return TemplateResponse(
                request, 'admin/add_proc_agent.html', context
            )

        if step == 'continue':
            # Manipulate request to simulate GET, as we need to display the
            # add page as if it was freshly requested.
            request.method = 'GET'
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Overriding change_view to implement custom "Clone" functionality.
        There is no need to check for the same conditions in the add_view,
        because only saved instances will be clone-able.
        """
        if request.POST and '_clone' in request.POST:
            clone_id = request.POST.get("to_clone")
            url = f"{reverse('admin:core_processagentusesreported_add')}" \
                  f"?clone_id={clone_id}"
            return HttpResponseRedirect(url)

        return super().change_view(request, object_id, form_url, extra_context)

    list_display = (
        'id', 'reporting_period', 'party',
        'makeup_quantity', 'emissions', 'units',
        'get_application', 'get_decision', 'get_substance',
        'get_containment',
    )
    list_filter = (
        (
            'reporting_period',
            reporting_period_dropdown_filter(ProcessAgentUsesReported)
        ),
        ('party', party_dropdown_filter(ProcessAgentUsesReported)),
        ('decision', PADecisionFilter),
        ('application__substance', substance_dropdown_filter(
            model_class=ProcessAgentUsesReported,
            related_field='application__substance',
        )),
    )
    search_fields = (
        'reporting_period__name',
        'party__name',
        'contain_technologies',
        'application__application',
        'application__substance__name',
        'decision__decision__decision_id',
    )
    # When using autocomplete_fields, you must define search_fields on the
    # related object’s ModelAdmin because the autocomplete search uses it.
    # autocomplete_fields = ['application',]
    change_form_template = 'admin/finalize_proc_agent.html'
    formfield_overrides = {
        CharField: {'widget': TextInput(attrs={'size': '120'})},
        TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 120})},
    }


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ('decision_id', 'name', 'meeting')
    search_fields = ('decision_id', 'name')
    list_filter = (
        ('meeting__description', custom_title_dropdown_filter('meeting')),
    )


@admin.register(DeviationType)
class DeviationTypeAdmin(admin.ModelAdmin):
    list_display = ('deviation_type_id', 'description', 'deviation_pc')
    search_fields = ('deviation_type_id', 'deviation_pc')


@admin.register(DeviationSource)
class DeviationSourceAdmin(admin.ModelAdmin):
    list_display = (
        'party', 'reporting_period', 'group', 'deviation_type',
        'production', 'consumption'
    )
    search_fields = (
        'reporting_period__name', 'party__name',
        'deviation_type__deviation_type_id'
    )
    list_filter = (
        ('party', MainPartyFilter),
        ('reporting_period__name', custom_title_dropdown_filter('Period')),
        'group'
    )


@admin.register(PlanOfActionDecision)
class PlanOfActionDecisionAdmin(admin.ModelAdmin):
    list_display = ('decision', 'party', 'year_adopted')
    search_fields = ('decision', 'party__name', 'year_adopted')
    list_filter = (
        ('party', MainPartyFilter),
    )


@admin.register(PlanOfAction)
class PlanOfActionAdmin(admin.ModelAdmin):
    list_display = (
        'party', 'reporting_period', 'group', 'benchmark',
        'annex_group_description', 'combined_id', 'is_valid', 'decision',
    )
    search_fields = (
        'reporting_period__name', 'party__name', 'group__group_id',
    )
    list_filter = (
        ('reporting_period__name', custom_title_dropdown_filter('Period')),
        ('party', MainPartyFilter),
        'group',
        'is_valid',
    )


@admin.register(ProdCons)
class ProdConsAdmin(admin.ModelAdmin):
    list_display = (
        'party', 'reporting_period', 'group',
        'calculated_production', 'calculated_consumption',
        'baseline_prod', 'baseline_cons', 'limit_prod', 'limit_cons'
    )
    list_filter = (
        ('reporting_period', reporting_period_dropdown_filter(ProdCons)),
        ('party', MainPartyFilter),
        'group'
    )


@admin.register(ProdConsMT)
class ProdConsMTAdmin(admin.ModelAdmin):
    def get_group(self, obj):
        return obj.substance.group
    get_group.short_description = 'Group'

    list_display = (
        'party', 'reporting_period', 'get_group', 'substance',
        'calculated_production', 'calculated_consumption'
    )
    list_filter = (
        ('reporting_period', reporting_period_dropdown_filter(ProdConsMT)),
        ('party', MainPartyFilter),
        ('substance__name', custom_title_dropdown_filter('substance')),
        'substance__group'
    )


class BaseCountryPofileAdmin:
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        main_parties_queryset = Party.objects.filter(
            #  don't filter by is_active
            #  because there is some legacy data for Yugoslavia
            parent_party__id=F('id'),
        ).order_by('name')
        form.base_fields['party'].queryset = main_parties_queryset
        return form

    formfield_overrides = {
        CharField: {'widget': TextInput(attrs={'size': '120'})},
        TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 120})},
    }


@admin.register(FocalPoint)
class FocalPointAdmin(BaseCountryPofileAdmin, admin.ModelAdmin):
    list_display = (
        'party', 'name', 'designation', 'email', 'is_licensing_system', 'is_national'
    )
    search_fields = ('party__name', 'name', 'designation')
    list_filter = (
        ('party', MainPartyFilter),
        'is_licensing_system', 'is_national'
    )
    ordering = ('ordering_id', )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        submission_queryset = Submission.objects.filter(
            obligation___obligation_type=ObligationTypes.OTHER.value
        ).order_by('reporting_period__name')
        form.base_fields['submission'].queryset = submission_queryset
        return form


class LicensingSystemFileInline(TabularInline):
    model = LicensingSystemFile
    extra = 1


class LicensingSystemURLInline(TabularInline):
    model = LicensingSystemURL
    extra = 1


@admin.register(LicensingSystem)
class LicensingSystemAdmin(BaseCountryPofileAdmin, admin.ModelAdmin):

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        submission_queryset = Submission.objects.filter(
            obligation___obligation_type=ObligationTypes.ART4B.value
        ).order_by('reporting_period__name')
        form.base_fields['submission'].queryset = submission_queryset
        return form

    list_display = (
        'party', 'has_ods', 'date_reported_ods', 'has_hfc', 'date_reported_hfc',
        'date_kigali_ratification', 'remarks',
    )
    inlines = (
        LicensingSystemFileInline,
        LicensingSystemURLInline,
    )
    search_fields = ('party__name', )
    list_filter = (
        ('party', MainPartyFilter),
        'has_ods', 'has_hfc'
    )
    ordering = ('party__name', )
    readonly_fields = ('date_kigali_ratification', )


@admin.register(Website)
class WebsiteAdmin(BaseCountryPofileAdmin, admin.ModelAdmin):
    list_display = (
        'party', 'url', 'file', 'description', 'is_url_broken'
    )
    search_fields = ('party__name', )
    list_filter = (
        ('party', MainPartyFilter),
        'is_url_broken'
    )
    ordering = ('ordering_id', )


class OtherCountryProfileDataObligationFilter(RelatedDropdownFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup_choices = Obligation.objects.filter(
            _obligation_type__in=[
                ObligationTypes.ART9.value,
                ObligationTypes.ODSSTRATEGIES.value,
                ObligationTypes.UNWANTEDIMPORTS.value,
                ObligationTypes.OTHER.value,
            ]
        ).values_list('id', 'name')


@admin.register(OtherCountryProfileData)
class OtherCountryProfileDataAdmin(BaseCountryPofileAdmin, admin.ModelAdmin):

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        submission_queryset = Submission.objects.filter(
            obligation___obligation_type__in=[
                ObligationTypes.ART9.value,
                ObligationTypes.ODSSTRATEGIES.value,
                ObligationTypes.UNWANTEDIMPORTS.value,
                ObligationTypes.OTHER.value,
            ]
        ).order_by('reporting_period__name')
        obligation_queryset = Obligation.objects.filter(
            _obligation_type__in=[
                ObligationTypes.ART9.value,
                ObligationTypes.ODSSTRATEGIES.value,
                ObligationTypes.UNWANTEDIMPORTS.value,
                ObligationTypes.OTHER.value,
            ]
        )
        form.base_fields['submission'].queryset = submission_queryset
        form.base_fields['obligation'].queryset = obligation_queryset
        return form

    list_display = (
        'party', 'reporting_period', 'obligation', 'url', 'file', 'description',
        'remarks_secretariat'
    )
    search_fields = ('party__name', )
    list_filter = (
        ('party', MainPartyFilter),
        ('obligation', OtherCountryProfileDataObligationFilter),
        ('reporting_period__name', custom_title_dropdown_filter('period')),
    )
    ordering = ('party__name', 'reporting_period__name')


@admin.register(ReclamationFacility)
class ReclamationFacilityAdmin(BaseCountryPofileAdmin, admin.ModelAdmin):
    list_display = (
        'party', 'date_reported', 'name', 'address', 'reclaimed_substances',
        'capacity', 'remarks'
    )
    search_fields = ('party__name', 'name')
    list_filter = (
        ('party', MainPartyFilter),
    )


@admin.register(IllegalTrade)
class IllegalTradeAdmin(BaseCountryPofileAdmin, admin.ModelAdmin):
    list_display = (
        'party', 'submission_id', 'submission_year', 'seizure_date_year', 'substances_traded',
        'volume', 'importing_exporting_country'
    )
    search_fields = ('party__name',)
    list_filter = (
        ('party', MainPartyFilter),
    )


@admin.register(ORMReport)
class ORMReportAdmin(BaseCountryPofileAdmin, admin.ModelAdmin):
    list_display = (
        'party', 'meeting', 'reporting_period', 'description', 'url'
    )
    search_fields = ('party__name',)
    list_filter = (
        ('party', MainPartyFilter),
        ('reporting_period__name', custom_title_dropdown_filter('period')),
    )


@admin.register(MultilateralFund)
class MultilateralFund(BaseCountryPofileAdmin, admin.ModelAdmin):
    list_display = (
        'party',
        'funds_approved', 'funds_disbursed',
        'date_approved', 'date_disbursed',
    )
    search_fields = ('party__name',)
    list_filter = (
        ('party', MainPartyFilter),
    )


@admin.register(ImpComTopic)
class ImpComTopicAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ('name', )
    ordering = ('name', )


@admin.register(ImpComBody)
class ImpComBodyAdmin(admin.ModelAdmin):
    list_display = ('sort_order', 'name', )
    search_fields = ('name', )
    ordering = ('sort_order', 'name', )


@admin.register(ImpComRecommendation)
class ImpComRecommendationAdmin(admin.ModelAdmin):
    def get_topics(self, obj):
        return ', '.join(
            [t.name for t in obj.topics.all()]
        ) if obj.topics else ''
    get_topics.short_description = 'Topics'

    def get_bodies(self, obj):
        return ', '.join(
            [b.name for b in obj.bodies.all()]
        ) if obj.bodies else ''
    get_bodies.short_description = 'Bodies'

    list_display = (
        'reporting_period', 'recommendation_number', 'get_bodies', 'get_topics'
    )
    search_fields = ('recommendation_number', 'excerpt', 'table_data', 'resulting_decisions')
    autocomplete_fields = ('bodies', 'topics')
    list_filter = (
        ('topics', RelatedDropdownFilter),
        ('bodies', RelatedDropdownFilter),
        (
            'reporting_period',
            reporting_period_dropdown_filter(ImpComRecommendation)
        ),
    )
    ordering = ('-reporting_period__name', 'sort_order')

    formfield_overrides = {
        CharField: {'widget': Textarea(attrs={'rows': 4, 'cols': 120})},
        TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 120})},
    }


@admin.register(TEAPReportType)
class TEAPReportTypeAdmin(admin.ModelAdmin):
    list_display = ('sort_order', 'name')
    ordering = ('sort_order', )


@admin.register(TEAPIndicativeNumberOfReports)
class TEAPIndicativeNumberOfReportsAdmin(admin.ModelAdmin):
    list_display = ('reporting_period', 'number_of_reports', 'remarks')
    search_fields = ('reporting_period__name',)
    list_filter = (
        ('reporting_period__name', custom_title_dropdown_filter('period')),
    )
    ordering = ('reporting_period__name',)


@admin.register(TEAPReport)
class TEAPReportAdmin(admin.ModelAdmin):
    list_display = (
        'sort_order', 'reporting_period', 'report_type', 'decision',
        'report_to_be_produced',
    )
    search_fields = ('reporting_period__name', 'decision__decision_id')
    list_filter = (
        'report_type',
        ReportingPeriodFilter,
    )
    ordering = ('sort_order',)

    formfield_overrides = {
        CharField: {'widget': TextInput(attrs={'size': '120'})},
        TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 120})},
    }


class LogEntryChangeList(ChangeList):
    def url_for_result(self, result):
        if result.action_flag == DELETION:
            return '%s' % (result.pk, )
        return '/admin/%s/%s/%s/' % (
            result.content_type.app_label,
            result.content_type.model,
            result.object_id
        )


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):

    list_display = (
        'object_id',
        'content_type',
        'object_repr',
        'user',
        'action_flag',
        'change_message',
        'action_time',
    )

    ordering = ('-action_time', )
    list_filter = (
        'action_flag',
        ('content_type__model', custom_title_dropdown_filter('content type')),
        ('user__username', custom_title_dropdown_filter('user')),
    )

    def get_changelist(self, request, **kwargs):
        return LogEntryChangeList

    def get_queryset(self, request):
        return super(LogEntryAdmin, self).get_queryset(
            request
        ).select_related('content_type', 'user')


# register all adminactions
actions.add_to_site(site)
