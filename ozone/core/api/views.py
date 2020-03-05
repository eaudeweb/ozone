from base64 import b64encode
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from decimal import Decimal
from functools import partial
from datetime import datetime
import logging
import urllib.parse
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.db.models.query import QuerySet, F, Q
from django.http import HttpResponse
from django_filters import rest_framework as filters
from django.utils.translation import gettext_lazy as _
from impersonate.views import stop_impersonate

from rest_framework import viewsets, mixins, status, generics, views
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import action
from rest_framework.filters import (
    BaseFilterBackend, OrderingFilter, SearchFilter
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.reverse import reverse
from rest_framework.viewsets import GenericViewSet

from ..exceptions import InvalidRequest

from ..models import (
    Region,
    Subregion,
    Party,
    ReportingPeriod,
    ReportingChannel,
    Obligation,
    Submission,
    SubmissionInfo,
    SubmissionFile,
    UploadToken,
    Article7Questionnaire,
    Article7Destruction,
    Article7Production,
    Article7Export,
    Article7Import,
    Article7NonPartyTrade,
    Article7Emission,
    HighAmbientTemperatureProduction,
    HighAmbientTemperatureImport,
    Transfer,
    ProcessAgentUsesReported,
    DataOther,
    Group,
    Substance,
    Blend,
    Nomination,
    ExemptionApproved,
    RAFReport,
    SubmissionFormat,
    ProdCons,
    ProdConsMT,
    Limit,
    Email,
    EmailTemplate,
    CriticalUseCategory,
    DeviationType,
    DeviationSource,
    PlanOfActionDecision,
    PlanOfAction,
    HistoricalSubmission,
    FocalPoint,
    LicensingSystem,
    Website,
    OtherCountryProfileData,
    ReclamationFacility,
    IllegalTrade,
    ORMReport,
    MultilateralFund,
    TEAPReportType,
    TEAPReport,
    TEAPIndicativeNumberOfReports,
    ImpComRecommendation,
    ImpComBody,
    ImpComTopic,
    eu_party_id,
)
from ..permissions import (
    IsSecretariatOrSamePartySubmission,
    IsSecretariatOrSamePartySubmissionRemarks,
    IsSecretariatOrSamePartySubmissionFlags,
    IsSecretariatOrSamePartySubmissionClone,
    IsSecretariatOrSamePartySubmissionTransition,
    IsSecretariatOrSamePartySubmissionRelated,
    IsSecretariatOrSamePartyBlend,
    IsCorrectObligation,
    IsSecretariatOrSamePartyUser,
    IsSecretariatOrSafeMethod,
    IsSecretariatOrSamePartyAggregation,
    IsSecretariatOrSamePartyLimit,
    IsSecretariatOrSamePartySubmissionRelatedRO,
    IsSecretariat,
    IsSecretariatOrSameParty,
)
from ..serializers import (
    CurrentUserSerializer,
    AuthTokenByValueSerializer,
    RegionSerializer,
    SubregionSerializer,
    PartySerializer,
    PartyRatificationSerializer,
    ReportingPeriodSerializer,
    ObligationSerializer,
    UserSerializer,
    SubmissionSerializer,
    ListSubmissionSerializer,
    CreateSubmissionSerializer,
    Article7QuestionnaireSerializer,
    Article7DestructionSerializer,
    Article7ProductionSerializer,
    Article7ExportSerializer,
    Article7ImportSerializer,
    Article7NonPartyTradeSerializer,
    Article7EmissionSerializer,
    HighAmbientTemperatureProductionSerializer,
    HighAmbientTemperatureImportSerializer,
    TransferSerializer,
    ProcessAgentUsesReportedSerializer,
    DataOtherSerializer,
    GroupSerializer,
    GroupSubstanceSerializer,
    SubstanceSerializer,
    BlendSerializer,
    CreateBlendSerializer,
    SubmissionHistorySerializer,
    SubmissionTransitionsSerializer,
    SubmissionInfoSerializer,
    UpdateSubmissionInfoSerializer,
    SubmissionFlagsSerializer,
    SubmissionRemarksSerializer,
    SubmissionFileSerializer,
    UploadTokenSerializer,
    ExemptionNominationSerializer,
    ExemptionApprovedSerializer,
    RAFSerializer,
    SubmissionFormatSerializer,
    ReportingChannelSerializer,
    AggregationSerializer,
    AggregationMTSerializer,
    AggregationDestructionSerializer,
    AggregationDestructionMTSerializer,
    LimitSerializer,
    EmailSerializer,
    EmailTemplateSerializer,
    CriticalUseCategorySerializer,
    DeviationSourceSerializer,
    DeviationTypeSerializer,
    PlanOfActionDecisionSerializer,
    PlanOfActionSerializer,
    FocalPointSerializer,
    LicensingSystemSerializer,
    WebsiteSerializer,
    OtherCountryProfileDataSerializer,
    ReclamationFacilitySerializer,
    IllegalTradeSerializer,
    ORMReportSerializer,
    MultilateralFundSerializer,
    TEAPReportTypeSerializer,
    TEAPReportSerializer,
    TEAPIndicativeNumberOfReportsSerializer,
    ImpComRecommendationSerializer,
    ImpComTopicSerializer,
    ImpComBodySerializer,
    EssentialCriticalSerializer,
    EssentialCriticalMTSerializer,
)

from ..models.utils import round_decimal_half_up

from ozone.core.api.export_pdf import reports

User = get_user_model()

log = logging.getLogger(__name__)


class ReadOnlyMixin:
    """Does what it says on the tin"""

    def _allowed_methods(self):
        return ['GET', 'OPTIONS']


class BulkCreateUpdateMixin:
    """
    Allows bulk creation and update of resources (given as a list in a JSON),
    while still permitting a single resource to be created.

    put() has been added as otherwise it is not available on the ViewSet. A
    concrete update() method needs to be implemented in the corresponding
    serializer.

    If the view receives a list of objects to be updated, get_object() returns
    a queryset referencing the existing objects corresponding to this
    submission. The (multiple-)update() implementation in the serializer needs
    to take this into account.

    This needs to be used by a `ModelViewSet` to properly work.
    """

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def get_object(self):
        try:
            return super().get_object()
        except AssertionError:
            # If it's not one we return many!
            return self.get_queryset()


class IsOwnerFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return queryset.none()
        elif request.user.is_secretariat:
            # Secretariat user
            return queryset
        else:
            # Party user
            if queryset is not None and queryset.model in (Submission, ProdCons, Limit):
                return queryset.filter(party=request.user.party)
            elif queryset is not None and queryset.model in (Transfer,):
                return queryset.filter(
                    Q(destination_party=request.user.party) |
                    Q(source_party=request.user.party)
                )
            elif queryset is not None:
                return queryset.filter(submission__party=request.user.party)
            else:
                return queryset


class SerializerRequestContextMixIn(object):
    """Adds the current request to the serializer context."""

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class SerializerDataContextMixIn(SerializerRequestContextMixIn):
    """Adds the current submission to the serializer context."""

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if "submission_pk" in self.kwargs:
            context['submission'] = Submission.objects.get(
                pk=self.kwargs["submission_pk"]
            )
        return context


class CurrentUserViewSet(
    ReadOnlyMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
    mixins.ListModelMixin, GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = CurrentUserSerializer
    permission_classes = (IsAuthenticated, IsSecretariatOrSamePartyUser)

    def get_queryset(self):
        if self.kwargs.get('pk'):
            return self.queryset.filter(id=self.kwargs.get('pk'))
        else:
            return self.queryset.filter(id=self.request.user.pk)


class RegionViewSet(ReadOnlyMixin, viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = (IsAuthenticated,)


class SubregionViewSet(ReadOnlyMixin, viewsets.ModelViewSet):
    queryset = Subregion.objects.all()
    serializer_class = SubregionSerializer
    permission_classes = (IsAuthenticated,)


class PartyViewSet(ReadOnlyMixin, viewsets.ModelViewSet):
    queryset = Party.objects.filter(
        is_active=True,
    ).prefetch_related(
        'subregion', 'subregion__region'
    ).order_by('name')
    serializer_class = PartySerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=True, methods=["get"])
    def controlled_groups(self, request, pk=None, **kwargs):
        """
        Returns the list of substance groups (Group.group_id) that must comply
        with the applicable control measures for the party and the reporting period
        given as param by name (`period`).
        If no param is given, it returns the list for the current date.
        """
        period = ReportingPeriod.objects.filter(
            name=request.query_params.get('period', '')
        ).first()
        groups = Group.get_controlled_groups(
            Party.objects.filter(pk=pk).first(), period
        )
        if groups:
            groups = groups.values_list('group_id', flat=True)
        return Response(groups)

    @action(detail=True, methods=["get"])
    def report_groups(self, request, pk=None, **kwargs):
        """
        Returns the list of substance groups (Group.group_id) that the party
        must report on for the reporting period given as param by name (`period`).
        If no param is given, it returns the list for the current date.
        """
        period = ReportingPeriod.objects.filter(
            name=request.query_params.get('period', '')
        ).first()
        groups = Group.get_report_groups(
            Party.objects.filter(pk=pk).first(), period
        )
        if groups:
            groups = groups.values_list('group_id', flat=True)
        return Response(groups)

    @action(detail=True, methods=["get"])
    def approved_exemptions(self, request, pk=None, **kwargs):
        reporting_period = ReportingPeriod.objects.filter(
            name=request.query_params.get('period', '')
        ).first()
        party = Party.objects.filter(pk=pk).first()
        return Response(
            ExemptionApproved.get_approved_amounts(
                party,
                reporting_period,
            )
        )


class PartyRatificationViewSet(ReadOnlyMixin, generics.ListAPIView):
    serializer_class = PartyRatificationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Party.get_main_parties().prefetch_related(
            'subregion', 'ratifications', 'ratifications__treaty', 'declarations',
        )
        if self.kwargs.get('party_id'):
            queryset = queryset.filter(id=self.kwargs['party_id'])
        return queryset


class GetNonPartiesViewSet(ReadOnlyMixin, views.APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, period_name):
        groups = Group.objects.all()
        all_non_parties = {}

        period = ReportingPeriod.objects.get(name=period_name) \
            if period_name else None

        for group in groups:
            queryset = group.get_non_parties(period)
            non_parties_per_group = {
                id: True for id in queryset.values_list('id', flat=True)
            }
            all_non_parties[group.group_id] = non_parties_per_group
        return Response(all_non_parties)


class ReportingPeriodViewSet(ReadOnlyMixin, viewsets.ModelViewSet):
    queryset = ReportingPeriod.objects.all()
    serializer_class = ReportingPeriodSerializer
    permission_classes = (IsAuthenticated,)


class ObligationViewSet(ReadOnlyMixin, viewsets.ModelViewSet):
    queryset = Obligation.objects.all()
    serializer_class = ObligationSerializer
    permission_classes = (IsAuthenticated,)


class GroupViewSet(ReadOnlyMixin, viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated,)


class GroupSubstanceViewSet(ReadOnlyMixin, viewsets.ModelViewSet):
    """
    list:
    Get the list of substances grouped by their Group.
    """

    queryset = Group.objects.all()
    serializer_class = GroupSubstanceSerializer
    # Allows unauthenticatd GET requests
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Group.objects.all().prefetch_related('substances')

    def list(self, request, *args, **kwargs):
        serializer = GroupSubstanceSerializer(
            self.filter_queryset(self.get_queryset()),
            many=True,
            context={"request": request},
        )

        data = deepcopy(serializer.data)
        data.append(
            OrderedDict(
                [
                    ('group_id', 'uncontrolled'),
                    (
                        'substances',
                        SubstanceSerializer(
                            Substance.objects.filter(group__isnull=True),
                            many=True,
                            read_only=True,
                            context={"request": request}
                        ).data
                    )
                ]
            )
        )
        return Response(data)


class BlendViewSet(viewsets.ModelViewSet):
    """
    list:
    Get the list of all non-custom blends, plus the custom ones that belongs
    to the user's party.
    """
    # Allows unauthenticated GET requests
    permission_classes = (
        IsAuthenticatedOrReadOnly, IsSecretariatOrSamePartyBlend,
    )

    def get_queryset(self):
        queryset = Blend.objects.all().prefetch_related(
            'components__substance__group__annex'
        )
        party = getattr(self.request.user, 'party', None) or \
            self.request.query_params.get('party', None)
        if party is not None:
            queryset = queryset.filter(
                party=party
            ) | queryset.filter(party=None)
        return queryset

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return CreateBlendSerializer
        return BlendSerializer


class UserViewSet(ReadOnlyMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)


class AggregationPaginator(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"


class MultiValueCharFilter(filters.BaseCSVFilter, filters.CharFilter):
    def filter(self, qs, value):
        # Value is either a list or an 'empty' value
        if value:
            new_qs = qs.model.objects.none()
            for v in value:
                new_qs = new_qs | super().filter(qs, v)
            return new_qs.distinct()
        return qs


class MultiValueNumberFilter(filters.BaseCSVFilter, filters.NumberFilter):
    def filter(self, qs, value):
        # Value is either a list or an 'empty' value
        if value:
            new_qs = qs.model.objects.none()
            for v in value:
                new_qs = new_qs | super().filter(qs, v)
            return new_qs.distinct()
        return qs


class SwitchableOrFilterset(filters.FilterSet):
    def filter_queryset(self, queryset):
        # Remove `or_fields` from filters, as it is not a direct filter but a
        # behavior modifier.
        or_fields = self.form.cleaned_data.pop('or_fields', [])
        or_fields = or_fields if or_fields is not None else []

        # First of all perform all AND-based filtering
        for name, value in self.form.cleaned_data.items():
            if name in or_fields:
                continue
            queryset = self.filters[name].filter(queryset, value)
            assert isinstance(queryset, QuerySet), \
                "Expected '%s.%s' to return a QuerySet, but got a %s instead." \
                % (type(self).__name__, name, type(queryset).__name__)

        # Now perform OR-based filtering. If not applicable, return.
        if not or_fields:
            return queryset

        # If any of the field names specified in or_fields does not have
        # a specific value set in the query, it means that we should filter
        # based on all possible values for that field. Since this is an OR-based
        # filter, all existing values will satisfy it. So we will
        # just return the queryset without performing any additional filtering.
        if any(
            [
                (self.form.cleaned_data.get(name, None) is None)
                for name in or_fields
            ]
        ):
            return queryset

        # Construct list of querysets filtered for each of the or_fields
        or_querysets = [
            self.filters[name].filter(queryset, self.form.cleaned_data[name])
            for name in or_fields
        ]
        if not or_querysets:
            return queryset

        # And finally return distinct results based on all filtered querysets.
        ret = or_querysets[0]
        for q in or_querysets[1:]:
            ret = ret | q
            ret = ret.distinct()
        return ret


class BaseAggregationViewFilterSet(SwitchableOrFilterset):
    """
    Base filterset for aggregation views.
    """
    or_fields = MultiValueCharFilter(
        "or_fields",
        help_text="Use OR instead of AND for the specified request params"
    )
    party = MultiValueNumberFilter(
        "party", help_text="Filter by party ID"
    )
    iso_code = MultiValueCharFilter(
        field_name="party__iso_alpha3_code",
        lookup_expr='iexact',
        help_text="Filter by party.iso_alpha3_code",
    )
    reporting_period = MultiValueNumberFilter(
        "reporting_period", help_text="Filter by Reporting Period ID"
    )
    is_article5 = filters.BooleanFilter(
        field_name="is_article5",
        help_text="Filter by party_history.is_article5",
    )
    is_eu_member = filters.BooleanFilter(
        field_name="is_eu_member",
        help_text="Filter by party_history.is_eu_member",
    )
    region = MultiValueNumberFilter(
        field_name="party__subregion__region_id",
        help_text="Filter by party's region_id",
    )
    subregion = MultiValueNumberFilter(
        field_name="party__subregion_id",
        help_text="Filter by party's subregion_id",
    )


class AggregationViewFilterSet(BaseAggregationViewFilterSet):
    """
    The Aggregation view can be filtered & ordered based on Annex Group
    """
    group = MultiValueNumberFilter(
        "group", help_text="Filter by Annex Group ID"
    )
    ordering = filters.OrderingFilter(
        fields=(
            ('reporting_period__start_date', 'reporting_period'),
            ('party__name', 'party'),
            ('group__group_id', 'group'),
        )
    )


class AggregationMTViewFilterSet(BaseAggregationViewFilterSet):
    """
    The Aggregation view can be filtered & ordered based on Annex Group
    """
    group = MultiValueNumberFilter(
        field_name="substance__group",
        help_text="Filter by Group ID"
    )
    ordering = filters.OrderingFilter(
        fields=(
            ('reporting_period__start_date', 'reporting_period'),
            ('party__name', 'party'),
            ('substance__group_id', 'group'),
        )
    )


def filter_eu_items(field, items_list, exclude_eu_and_members):
    def is_consumption_field(field_name):
        if field_name.startswith('import_') or field_name.startswith('export_'):
            return True
        return False

    def is_production_field(field_name):
        if (
            field_name.startswith('production_')
            or field_name.startswith('destroyed')
        ):
            return True
        return False

    if not exclude_eu_and_members:
        # No filtering to perform, just yield everything
        yield from items_list
    else:
        for item in items_list:
            if is_consumption_field(field):
                # Ignore EU members when aggregating consumption-related
                # fields.
                if item['is_eu_member'] is False:
                    yield item
            elif is_production_field(field):
                if item['party'] != eu_party_id():
                    yield item
            else:
                yield item


def populate_aggregation(
        aggregation, mt, fields, to_add, exclude_eu_and_members
    ):
    """
    Helper function to populate an aggregation dictionary's fields based on a
    list of dictionaries containing key-value pairs for those fields.
    """
    if mt:
        # Do not round metric tons values when populating MT aggregations
        rounding_method = lambda x: x
    else:
        # ODP tons values should be rounded
        rounding_method = partial(round_decimal_half_up, decimals=2)

    # These fields should be aggregated using a special rule: if any value is
    # null, then the sum of all values is considered null.
    limit_fields = ('limit_prod', 'limit_cons')

    for field in fields:
        # A null value in any limit field means that the sum of all
        # values for that field across an aggregation should be null
        # (because null means no limits)
        if field in limit_fields:
            aggregation[field] = (
                None if any([a[field] is None for a in to_add]) else
                rounding_method(sum([a[field] for a in to_add]))
            )
        else:
            filtered_to_add = list(
                filter_eu_items(
                    field, to_add, exclude_eu_and_members
                )
            )
            aggregation[field] = (
                None if all([a[field] is None for a in filtered_to_add]) else
                rounding_method(
                    sum([a[field] or Decimal(0) for a in filtered_to_add])
                )
            )


def filter_aggregated_data_by_grouping(grouping_fields, values_list):
    """
    Helper function that returns a dictionary:
    - with keys being all permutations of different values
      for grouping_fields found in values_list
    - with values being lists of elements from values_list that
      correspond to each permutation
    """
    if not grouping_fields:
        return {(): values_list}

    filtered_values = dict()
    for value in values_list:
        value_key = tuple(value[field] for field in grouping_fields)
        if value_key in filtered_values:
            filtered_values[value_key].append(value)
        else:
            filtered_values[value_key] = [value, ]
    return filtered_values


class AggregationViewSet(viewsets.ReadOnlyModelViewSet):
    # Data for this view is in ODP tons for annexes A-E and
    # CO2-eq tonnes for annex F
    queryset = ProdCons.objects.filter(
        party=F('party__parent_party')
    ).select_related(
        'party__subregion__region'
    )
    serializer_class = AggregationSerializer

    filter_backends = (
        # Aggregations are public information, no need to enforce filtering
        # With the exception of Destruction data by annex group
        # IsOwnerFilterBackend,
        filters.DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    )
    filterset_class = AggregationViewFilterSet
    search_fields = (
        "party__name", "reporting_period__name"
    )
    ordering = ("-reporting_period__start_date", "party", "group")
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartyAggregation,
    )
    pagination_class = AggregationPaginator

    # Custom class attributes needed for our custom list() implementation to
    # work properly in subclasses
    model_class = ProdCons
    group_field = 'group'
    mt = False
    allowed_aggregates = ('party', 'group',)

    def get_queryset(self):
        return ProdCons.objects.filter(
            party=F('party__parent_party')
        ).select_related(
            'party__subregion__region'
        )

    @action(methods=["get",], detail=False)
    def last_updated(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.exclude(updated_at=None)
        updated = None if not queryset.exists() else queryset.latest(
            'updated_at'
        ).updated_at

        return Response({'last_updated': updated})

    def list_aggregated_data(
        self, queryset, aggregates, groupings
    ):
        # Maps grouping param value to field names to be retrieved
        # Keys are possible values for the 'group_by' parameter.
        # Values are corresponding values of field_name
        grouping_mapping = {
            'is_article5': 'is_article5',
            'is_eu_member': 'is_eu_member',
            'region': 'party__subregion__region'
        }

        # All decimal fields need to be retrieved from DB
        fields = self.model_class.decimal_fields()
        # Using `distinct()` does not work because this queryset is
        # ordered by fields from related models, which makes similar
        # values seem distinct.
        periods = set(
            queryset.values_list('reporting_period', flat=True)
        )
        groups = set(
            queryset.values_list(self.group_field, flat=True)
        )
        parties = set(queryset.values_list('party', flat=True))
        all_values = queryset.values(
            'id',
            *fields,
            'party', 'reporting_period', self.group_field,
            *grouping_mapping.values()
        )

        # Field names that will be used for grouping, based on the 'group_by'
        # parameter
        grouping_fields = [
            value for key, value in grouping_mapping.items() if key in groupings
        ]
        # List of values that will be returned
        values = []
        # Use a dictionary of list of dictionaries for in-memory storage to
        # optimize DB queries.
        values_dict = {period: [] for period in periods}
        for value in all_values:
            values_dict[value['reporting_period']].append(value)

        if aggregates and 'party' in aggregates:
            exclude_eu_and_members = True
        else:
            exclude_eu_and_members = False

        # Now iterate over all periods and produce the data
        for period in periods:
            values_for_period = values_dict.get(period, [])
            # Take grouping fields into account to possibly generate several
            # objects for the same reporting period
            filtered_values = filter_aggregated_data_by_grouping(
                grouping_fields, values_for_period
            )
            for key in filtered_values.keys():
                # We must construct an aggregation for each key-value item
                # in the filtered_values dictionary
                grouping_fields_values = dict(zip(grouping_fields, key))
                to_add = filtered_values[key]
                params_dict = {
                    key: grouping_fields_values.get(value, None)
                    for key, value in grouping_mapping.items()
                }

                if 'party' in aggregates and 'group' in aggregates:
                    # Sum values for all groups/substances and all parties
                    # for this reporting period.
                    aggregation = dict({
                        'reporting_period': period,
                        'party': None,
                        'group': None,
                        **params_dict
                    })
                    populate_aggregation(
                        aggregation, self.mt, fields, to_add,
                        exclude_eu_and_members
                    )
                    values.append(aggregation)
                elif 'party' in aggregates:
                    for group in groups:
                        entries = [
                            value for value in to_add
                            if value[self.group_field] == group
                        ]
                        if entries:
                            aggregation = dict({
                                'group': group,
                                'reporting_period': period,
                                'party': None,
                                **params_dict
                            })
                            populate_aggregation(
                                aggregation, self.mt, fields, entries,
                                exclude_eu_and_members
                            )
                            values.append(aggregation)
                elif 'group' in aggregates:
                    entries = {party: [] for party in parties}
                    for value in to_add:
                        entries[value['party']].append(value)
                    for party in parties:
                        if entries.get(party, []):
                            aggregation = dict({
                                'party': party,
                                'reporting_period': period,
                                'group': None,
                                **params_dict
                            })
                            populate_aggregation(
                                aggregation, self.mt, fields, entries[party],
                                exclude_eu_and_members
                            )
                            values.append(aggregation)
                elif 'substance_to_group' in aggregates:
                    # This is used to aggregate MT values (in which entries are
                    # per substance) into entries that contain total values for
                    # each group (as this is what the endpoint should actually
                    # list).
                    # It is only done when no other aggregation is performed, as
                    # any of the above aggregations will already have converted
                    # the per-substance entries to per-group entries.
                    entries = {
                        (party, group): []
                        for group in groups for party in parties
                    }
                    for value in to_add:
                        key = (value['party'], value[self.group_field])
                        entries[key].append(value)
                    for group in groups:
                        for party in parties:
                            if entries.get((party, group), []):
                                aggregation = dict({
                                    'party': party,
                                    'group': group,
                                    'reporting_period': period,
                                    **params_dict
                                })
                                populate_aggregation(
                                    aggregation, self.mt,
                                    fields, entries[(party, group)],
                                    exclude_eu_and_members
                                )
                                values.append(aggregation)

        # Aggregating disables pagination. However that is ok given the
        # small number of results that will be returned.
        # Ordering is also lost due to the use of set().
        return Response(values)

    def list(self, request, *args, **kwargs):
        """
        We need to override the default ViewSet list method to handle the
        custom `aggregation` parameter.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Handle aggregation & grouping
        aggregates = request.query_params.get('aggregation', None)
        aggregates = aggregates.split(',') if aggregates else []
        aggregates = [
            agg for agg in aggregates if agg in self.allowed_aggregates
        ]
        groupings = request.query_params.get('group_by', None)
        groupings = groupings.split(',') if groupings else []
        if aggregates:
            return self.list_aggregated_data(queryset, aggregates, groupings)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AggregationMTViewSet(AggregationViewSet):
    """
    This view displays Metric Tons data for all annex groups.
    """
    queryset = ProdConsMT.objects.filter(
        party=F('party__parent_party')
    ).prefetch_related(
        'substance__group'
    ).exclude(
        substance__group=None
    )
    # Actually, in all use cases of this ViewSet, everything will be serialized
    # through the AggregationSerializer. However, we need this here to avoid
    # errors in Django's magic inner workings.
    serializer_class = AggregationMTSerializer

    filterset_class = AggregationMTViewFilterSet
    search_fields = (
        "party__name", "reporting_period__name"
    )
    ordering = ("-reporting_period__start_date", "party", "substance__group")

    # Custom class attributes needed for our custom list() implementation to
    # work properly in subclasses
    model_class = ProdConsMT
    group_field = 'substance__group'
    mt = True
    allowed_aggregates = ('party', 'group', 'substance_to_group',)

    def get_queryset(self):
        return ProdConsMT.objects.filter(
            party=F('party__parent_party')
        ).prefetch_related(
            'substance__group'
        ).exclude(
            substance__group=None
        )


class AggregationDestructionViewFilterSet(BaseAggregationViewFilterSet):
    """
    Used specifically for the destruction endpoint; allows all filtering
    available on the aggregation endpoint, except for group/substance
    """
    ordering = filters.OrderingFilter(
        fields=(
            ('reporting_period__start_date', 'reporting_period'),
            ('party__name', 'party'),
        )
    )


class AggregationDestructionViewSet(AggregationViewSet):
    """
    Overrides the read-only AggregationViewSet to:
    - show only destruction-related information
    - ensure data is not broken down by group
    """
    serializer_class = AggregationDestructionSerializer

    filterset_class = AggregationDestructionViewFilterSet
    ordering = ("-reporting_period__start_date", "party",)

    # Custom class attribute needed for our custom list() implementation to
    # work properly in subclasses
    group_or_substance = 'group'
    mt = False

    def list(self, request, *args, **kwargs):
        """
        We need to override the default ViewSet list method to handle the
        custom `aggregation` parameter.
        """

        # Maps grouping param value to field names to be retrieved
        # Keys are possible values for the 'group_by' parameter.
        # Values are corresponding values of field_name
        grouping_mapping = {
            'is_article5': 'is_article5',
            'is_eu_member': 'is_eu_member',
            'region': 'party__subregion__region'
        }

        queryset = self.filter_queryset(self.get_queryset())

        # Using `distinct()` does not work because this queryset is
        # ordered by fields from related models, which makes similar
        # values seem distinct.
        periods = set(queryset.values_list('reporting_period', flat=True))
        parties = set(queryset.values_list('party', flat=True))
        all_values = queryset.values(
            'id',
            'destroyed', 'party', 'reporting_period',
            self.group_or_substance,
            *grouping_mapping.values()
        )

        # Handle aggregation. In this case we always aggregate by group, since
        # only the total destructions sum per party/period is public.
        aggregates = request.query_params.get('aggregation', None)
        aggregates = aggregates.split(',') if aggregates else None
        groupings = request.query_params.get('group_by', None)
        groupings = groupings.split(',') if groupings else []

        # Field names that will be used for grouping, based on the 'group_by'
        # parameter
        grouping_fields = [
            value for key, value in grouping_mapping.items() if key in groupings
        ]

        # Use a dictionary of list of dictionaries for in-memory storage to
        # optimize DB queries.
        values_dict = {period: [] for period in periods}
        for value in all_values:
            values_dict[value['reporting_period']].append(value)

        if aggregates and 'party' in aggregates:
            exclude_eu_and_members = True
        else:
            exclude_eu_and_members = False

        # List of values that will be returned
        values = []
        for period in periods:
            # These are all the values retrieved from the DB for the given
            # reporting period; however they may need to be broken down further
            # based on grouping.
            values_for_period = values_dict.get(period, [])

            # Take grouping fields into account to possibly generate several
            # objects for the same reporting period
            filtered_values = filter_aggregated_data_by_grouping(
                grouping_fields, values_for_period
            )
            for key in filtered_values.keys():
                # We must construct an aggregation for each key-value item
                # in the filtered_values dictionary
                grouping_fields_values = dict(zip(grouping_fields, key))
                to_add = filtered_values[key]
                params_dict = {
                    key: grouping_fields_values.get(value, None)
                    for key, value in grouping_mapping.items()
                }

                if aggregates and 'party' in aggregates:
                    # Sum values for all groups (or substances) and all parties
                    # for this reporting period & grouping
                    aggregation = dict({
                        'reporting_period': period,
                        'party': None,
                        'group': None,
                        **params_dict
                    })
                    populate_aggregation(
                        aggregation, self.mt, ['destroyed',], to_add,
                        exclude_eu_and_members
                    )
                    values.append(aggregation)
                else:
                    # Sum values for all groups/substances for this reporting
                    # period & grouping
                    for party in parties:
                        entries = [
                            value for value in to_add
                            if value['party'] == party
                        ]
                        if entries:
                            if not groupings:
                                # If there is no grouping, since the only
                                # aggregation performed here is by group,
                                # it is OK to use the values found
                                # in the first entry for article5, eu_member
                                # and region.
                                for key in params_dict.keys():
                                    value = entries[0][grouping_mapping[key]]
                                    params_dict[key] = value
                            aggregation = dict({
                                'party': party,
                                'reporting_period': period,
                                'group': None,
                                **params_dict
                            })
                            populate_aggregation(
                                aggregation, self.mt, ['destroyed',], entries,
                                exclude_eu_and_members
                            )
                            values.append(aggregation)

        # Aggregating disables pagination. However that is ok given the small
        # number of results that will be returned.
        # Ordering is also lost due to the use of set().
        return Response(values)


class AggregationDestructionMTViewSet(AggregationDestructionViewSet):
    """
    Overrides the read-only AggregationDestructionViewSet to:
    - show only destruction-related information
    - ensure data is not broken down by substance

    This view displays Metric Tons data for all annex groups
    """
    # Exclude any non-controlled substances from queryset, they should not be
    # taken into account.
    queryset = ProdConsMT.objects.filter(
        party=F('party__parent_party')
    ).exclude(substance__group=None)
    serializer_class = AggregationDestructionMTSerializer

    filterset_class = AggregationDestructionViewFilterSet
    ordering = ("-reporting_period__start_date", "party",)

    # Custom class attribute needed for our custom list() implementation
    # (from AggregationDestructionViewSet) to work properly in this subclass.
    group_or_substance = 'substance'
    mt = True

    def get_queryset(self):
        """
        Exclude any non-controlled substances from queryset, they should not be
        taken into account.
        """
        return ProdConsMT.objects.filter(
            party=F('party__parent_party')
        ).exclude(substance__group=None)


class LimitPaginator(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"


class LimitViewFilterSet(filters.FilterSet):
    party = filters.NumberFilter("party", help_text="Filter by party ID")
    reporting_period = filters.NumberFilter(
        "reporting_period", help_text="Filter by Reporting Period ID"
    )
    group = filters.NumberFilter(
        "group", help_text="Filter by Annex Group ID"
    )


class LimitViewSet(viewsets.ModelViewSet):
    # Will only allow GET for now on this view
    http_method_names = ['get']

    queryset = Limit.objects.filter(party=F('party__parent_party'))
    serializer_class = LimitSerializer

    filter_backends = (
        IsOwnerFilterBackend,
        filters.DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    )
    filterset_class = LimitViewFilterSet
    search_fields = (
        "party__name", "reporting_period__name"
    )
    ordering_fields = {
        "party": "party",
        "reporting_period": "reporting_period",
        "group": "group",
    }
    ordering = ("-reporting_period", "party", "group")
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartyLimit,
    )
    pagination_class = LimitPaginator

    def get_queryset(self):
        return Limit.objects.filter(party=F('party__parent_party'))


class DeviationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DeviationTypeSerializer
    # We are only allowing Secretariat users to view deviation types.
    permission_classes = (
        IsAuthenticated,
        IsSecretariat,
    )
    queryset = DeviationType.objects.all()


class DeviationSourcePaginator(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"


class DeviationSourceFilterSet(filters.FilterSet):
    party = filters.NumberFilter("party", help_text="Filter by party ID")
    reporting_period = filters.NumberFilter(
        "reporting_period", help_text="Filter by Reporting Period ID"
    )
    group = filters.NumberFilter(
        "group", help_text="Filter by Annex Group ID"
    )


class DeviationSourceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DeviationSource.objects.all()
    serializer_class = DeviationSourceSerializer
    permission_classes = (
        IsAuthenticated,
        IsSecretariat,
    )

    filter_backends = (
        IsOwnerFilterBackend,
        OrderingFilter,
        filters.DjangoFilterBackend,
        SearchFilter,
    )
    filterset_class = DeviationSourceFilterSet

    ordering_fields = (
        "-reporting_period__start_date", "party__name", "group__group_id"
    )
    pagination_class = DeviationSourcePaginator

    def get_queryset(self):
        return DeviationSource.objects.all()


class PlanOfActionDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlanOfActionDecisionSerializer
    # We are only allowing Secretariat users to view plans of action decisions.
    permission_classes = (
        IsAuthenticated,
        IsSecretariat,
    )
    queryset = PlanOfActionDecision.objects.all()


class PlanOfActionPaginator(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"


class PlanOfActionFilterSet(filters.FilterSet):
    party = filters.NumberFilter("party", help_text="Filter by party ID")
    reporting_period = filters.NumberFilter(
        "reporting_period", help_text="Filter by Reporting Period ID"
    )
    group = filters.NumberFilter(
        "group", help_text="Filter by Annex Group ID"
    )
    is_valid = filters.BooleanFilter(
        "is_valid", help_text="Filter by is_valid field"
    )
    combined_id = filters.BooleanFilter(
        "combined_id", help_text="Filter by combined_id field"
    )


class PlanOfActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlanOfAction.objects.all()
    serializer_class = PlanOfActionSerializer
    permission_classes = (
        IsAuthenticated,
        IsSecretariatOrSameParty,
    )

    filter_backends = (
        IsOwnerFilterBackend,
        OrderingFilter,
        filters.DjangoFilterBackend,
        SearchFilter,
    )
    filterset_class = PlanOfActionFilterSet

    ordering_fields = (
        "-reporting_period__start_date", "party__name", "group__group_id"
    )
    pagination_class = PlanOfActionPaginator

    def get_queryset(self):
        return PlanOfAction.objects.all()


class SubmissionChangePaginator(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"


class IsHistoryOwnerFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return queryset.none()
        elif request.user.is_secretariat:
            # Secretariat user
            return queryset
        else:
            # Party user
            return queryset.filter(party=request.user.party)


class SubmissionChangeFilterSet(filters.FilterSet):
    party = filters.NumberFilter("party", help_text="Filter by party ID")
    reporting_period = filters.NumberFilter(
        "reporting_period", help_text="Filter by Reporting Period ID"
    )
    obligation = filters.NumberFilter(
        "obligation", help_text="Filter by Obligation ID"
    )

    class Meta:
        model = HistoricalSubmission
        fields = ('party', 'obligation', 'reporting_period',)


class SubmissionChangeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HistoricalSubmission.objects.all()
    serializer_class = SubmissionHistorySerializer
    permission_classes = (
        IsAuthenticated,
        IsSecretariatOrSameParty,
    )

    filter_backends = (
        IsHistoryOwnerFilterBackend,
        OrderingFilter,
        filters.DjangoFilterBackend,
        SearchFilter,
    )
    filterset_class = SubmissionChangeFilterSet
    search_fields = (
        "party__name", "obligation__name", "reporting_period__name"
    )
    ordering = (
        "obligation__sort_order",
        "-reporting_period__start_date",
        "party__name",
        "-history_date",
    )

    pagination_class = SubmissionChangePaginator

    def get_queryset(self):
        return HistoricalSubmission.objects.all()


class SubmissionPaginator(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"


class SubmissionViewFilterSet(filters.FilterSet):
    party = filters.NumberFilter("party", help_text="Filter by party ID")
    obligation = filters.NumberFilter(
        "obligation", help_text="Filter by Obligation ID"
    )
    reporting_period = filters.NumberFilter(
        "reporting_period", help_text="Filter by Reporting Period ID"
    )
    is_superseded = filters.BooleanFilter(
        method="filter_superseded",
        help_text="If set to true only show superseded submissions. "
                  "If set to false only show non-superseded submissions. "
    )
    from_period = filters.DateFilter(
        "reporting_period__start_date",
        "gte",
        help_text="Only get results for reporting periods that start "
        "at a later date than this.",
    )
    to_period = filters.DateFilter(
        "reporting_period__end_date",
        "lte",
        help_text="Only get results for reporting periods that end "
        "at a earlier date than this.",
    )
    current_state = filters.CharFilter(
        "_current_state", help_text="Filter by the submission state."
    )

    order_by_field = 'ordering'
    ordering = filters.OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('obligation__sort_order', 'obligation'),
            ('reporting_period__start_date', 'reporting_period'),
            ('party__name', 'party'),
            ('version', 'version'),
            ('_current_state', 'current_state'),
            ('updated_at', 'updated_at'),
        )
    )

    def filter_superseded(self, queryset, name, value):
        if value:
            return queryset.filter(flag_superseded=True)
        else:
            return queryset.exclude(flag_superseded=True)

    class Meta:
        model = Submission
        fields = [
            'party', 'obligation', 'reporting_period',
            'from_period', 'to_period', 'current_state'
        ]


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    versions:
    Get a list of all submissions versions, including the one specified in the
    primary key.

    history:
    Get a list of all historical states for this specific submission version.
    Note historical states for other versions are not included.
    """
    queryset = Submission.objects.all().prefetch_related(
        "reporting_period", "created_by", "party", "obligation"
    )
    filter_backends = (
        IsOwnerFilterBackend,
        OrderingFilter,  # only for default ordering, see SubmissionViewFilterSet
        filters.DjangoFilterBackend,
        SearchFilter,
    )
    filterset_class = SubmissionViewFilterSet
    search_fields = (
        "party__name", "obligation__name", "reporting_period__name"
    )
    ordering = (
        "-reporting_period__start_date", "obligation__sort_order",
        "party__name", "-updated_at",
    )
    permission_classes = (IsAuthenticated, IsSecretariatOrSamePartySubmission, )
    pagination_class = SubmissionPaginator

    def get_queryset(self):
        return Submission.objects.all().prefetch_related(
            "reporting_period", "created_by", "party", "obligation"
        )

    def update(self, *args, **kwargs):
        # Uses PartialUpdateMixIn to prevent race conditions
        # see https://github.com/encode/django-rest-framework/issues/2648
        kwargs["partial"] = True
        return super().update(*args, **kwargs)

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return CreateSubmissionSerializer
        return SubmissionSerializer

    def _list_submission(self, queryset, request):
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ListSubmissionSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = ListSubmissionSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        return self._list_submission(self.get_queryset(), request)

    @action(detail=True, methods=["get"])
    def versions(self, request, pk=None):
        return self._list_submission(
            Submission.objects.get(pk=pk).versions, request
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsSecretariatOrSamePartySubmissionClone]
    )
    def clone(self, request, pk=None):
        submission = Submission.objects.get(pk=pk)
        clone = submission.clone(request.user)
        return Response(
            {
                "url": reverse(
                    'core:submission-detail',
                    request=request,
                    kwargs={'pk': clone.id}
                )
            }
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="call-transition",
        permission_classes = [IsSecretariatOrSamePartySubmissionTransition]
    )
    def call_transition(self, request, pk=None):
        """
        Request example:
        {
            "transition": "submit"
        }
        """

        if request.data.get("transition"):
            submission = Submission.objects.get(pk=pk)
            submission.call_transition(request.data["transition"], request.user)
            serializer = SubmissionSerializer(
                submission, many=False, context={"request": request}
            )
            return Response(serializer.data)
        else:
            raise InvalidRequest(
                _(
                    "Invalid request: request body should contain 'transition' "
                    "key."
                )
            )

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        historical_records = Submission.objects.get(pk=pk).history.all()
        serializer = SubmissionHistorySerializer(historical_records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def change_history(self, request, pk=None):
        historical_records = Submission.objects.get(pk=pk).get_change_history()
        return Response(historical_records)

    @action(detail=True, methods=["get"])
    def export_pdf(self, request, pk=None):
        submission = Submission.objects.get(pk=pk)
        obligation = submission.obligation._obligation_type

        if obligation == 'art7':
            cls = reports.Art7RawdataReport
        elif obligation == 'raf':
            cls = reports.RafReport
        else:
            raise RuntimeError(f"Unknown obligation {obligation!r}")

        report = cls.for_submission(submission)
        return report.render_to_response()

    @action(detail=True, methods=["get"])
    def export_prodcons_pdf(self, request, pk=None):
        submission = Submission.objects.get(pk=pk)
        report = reports.ProdConsReport.for_submission(submission)
        return report.render_to_response()

    @action(detail=True, methods=["get"])
    def aggregations(self, request, submission_pk=None, pk=None):
        sub = Submission.objects.get(pk=pk)
        return Response(
            [
                AggregationSerializer(aggregation).data
                for group, aggregation in sub.get_aggregated_data().items()
            ]
        )

    @action(detail=True, methods=["get"])
    def aggregations_mt(self, request, submission_pk=None, pk=None):
        sub = Submission.objects.get(pk=pk)
        return Response(
            [
                AggregationMTSerializer(aggregation).data
                for subst, aggregation in sub.get_aggregated_mt_data().items()
            ]
        )


class SubmissionTransitionsViewSet(viewsets.ModelViewSet):
    obligation_types = None
    serializer_class = SubmissionTransitionsSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)
    http_method_names = ['get']

    def get_queryset(self):
        return Submission.objects.filter(
            id=self.kwargs['submission_pk']
        )


class SubmissionInfoViewSet(viewsets.ModelViewSet):
    obligation_types = None
    serializer_class = SubmissionInfoSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)
    http_method_names = ['get', 'put']

    def put(self, request, *args, **kwargs):
        info = Submission.objects.get(pk=self.kwargs['submission_pk']).info
        reporting_channel = request.data.get('reporting_channel')
        submitted_at = self.request.data.get('submitted_at')
        submission_format = request.data.get('submission_format')
        serializer = UpdateSubmissionInfoSerializer(
            info,
            data=request.data,
            context={
                'reporting_channel': reporting_channel,
                'submitted_at': submitted_at,
                'submission_format': submission_format,
                'request': request
            }
        )
        # Horrible hack to allow date to be an empty string
        if serializer.initial_data.get('date', None) == '':
            serializer.initial_data['date'] = None
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        return SubmissionInfo.objects.filter(
            submission=self.kwargs['submission_pk']
        ).select_related('submission__reporting_channel')


class GetSubmissionFormatsViewSet(ReadOnlyMixin, generics.ListAPIView):
    """
    retrieve:
    Get the available options for the submission format.
    """

    queryset = SubmissionFormat.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = SubmissionFormatSerializer


class GetReportingChannelsViewSet(ReadOnlyMixin, generics.ListAPIView):
    """
    retrieve:
    Get the available options for the reporting channel.
    """

    queryset = ReportingChannel.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ReportingChannelSerializer


class SubmissionFlagsViewSet(
    mixins.UpdateModelMixin, mixins.ListModelMixin,
    GenericViewSet, SerializerRequestContextMixIn
):
    obligation_types = None
    serializer_class = SubmissionFlagsSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionFlags,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)
    http_method_names = ['get', 'put']

    def put(self, request, *args, **kwargs):
        sub = Submission.objects.get(pk=self.kwargs['submission_pk'])
        # Uses PartialUpdateMixIn to prevent race conditions
        # see https://github.com/encode/django-rest-framework/issues/2648
        serializer = self.get_serializer(sub, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        return Submission.objects.filter(
            pk=self.kwargs['submission_pk']
        )


class SubmissionRemarksViewSet(
    mixins.UpdateModelMixin, mixins.ListModelMixin,
    GenericViewSet, SerializerRequestContextMixIn
):
    """
    list:
    Get the general remarks for this specific submission. These are in pairs for
    each data form: remarks that have been added by the reporting party and remarks
    that have been added by the Ozone Secretariat.

    update:
    Update the general remarks for this specific submission.
    """
    # XXX TODO Check if this should be available for all #497
    obligation_types = None
    serializer_class = SubmissionRemarksSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRemarks,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)
    http_method_names = ['get', 'put']

    def put(self, request, *args, **kwargs):
        sub = Submission.objects.get(pk=self.kwargs['submission_pk'])
        # Uses PartialUpdateMixIn to prevent race conditions
        # see https://github.com/encode/django-rest-framework/issues/2648
        serializer = self.get_serializer(sub, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        return Submission.objects.filter(
            pk=self.kwargs['submission_pk']
        )


class Article7QuestionnaireViewSet(viewsets.ModelViewSet):
    obligation_types = ("art7",)
    serializer_class = Article7QuestionnaireSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return Article7Questionnaire.objects.filter(
            submission=self.kwargs['submission_pk']
        )

    def put(self, request, *args, **kwargs):
        article7questionnaire = Submission.objects.get(
            pk=self.kwargs['submission_pk']
        ).article7questionnaire
        serializer = Article7QuestionnaireSerializer(
            article7questionnaire, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class Article7DestructionViewSet(
    BulkCreateUpdateMixin, SerializerDataContextMixIn, viewsets.ModelViewSet
):
    obligation_types = ("art7",)
    serializer_class = Article7DestructionSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return Article7Destruction.objects.filter(
            submission=self.kwargs['submission_pk']
        ).filter(
            blend_item__isnull=True
        ).select_related(
            'substance', 'substance__group'
        )

    # Needed to ensure that serializer uses the correct submission
    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class Article7ProductionViewSet(
    BulkCreateUpdateMixin, SerializerDataContextMixIn, viewsets.ModelViewSet
):
    obligation_types = ("art7",)
    serializer_class = Article7ProductionSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return Article7Production.objects.filter(
            submission=self.kwargs['submission_pk']
        ).select_related(
            'substance', 'substance__group'
        )

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class Article7ExportViewSet(
    BulkCreateUpdateMixin, SerializerDataContextMixIn, viewsets.ModelViewSet
):
    obligation_types = ("art7",)
    serializer_class = Article7ExportSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return Article7Export.objects.filter(
            submission=self.kwargs['submission_pk']
        ).filter(
            blend_item__isnull=True
        ).select_related(
            'substance', 'substance__group'
        )

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class Article7ImportViewSet(
    BulkCreateUpdateMixin, SerializerDataContextMixIn, viewsets.ModelViewSet
):
    obligation_types = ("art7",)
    serializer_class = Article7ImportSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return Article7Import.objects.filter(
            submission=self.kwargs['submission_pk']
        ).filter(
            blend_item__isnull=True
        ).select_related(
            'substance', 'substance__group'
        )

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class Article7NonPartyTradeViewSet(
    BulkCreateUpdateMixin, SerializerDataContextMixIn, viewsets.ModelViewSet
):
    obligation_types = ("art7",)
    serializer_class = Article7NonPartyTradeSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return Article7NonPartyTrade.objects.filter(
            submission=self.kwargs['submission_pk']
        ).filter(
            blend_item__isnull=True
        ).select_related(
            'substance', 'substance__group'
        )

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class Article7EmissionViewSet(
    BulkCreateUpdateMixin, SerializerDataContextMixIn, viewsets.ModelViewSet
):
    obligation_types = ("art7",)
    serializer_class = Article7EmissionSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return Article7Emission.objects.filter(
            submission=self.kwargs['submission_pk']
        )

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class HighAmbientTemperatureImportViewSet(
    BulkCreateUpdateMixin, SerializerDataContextMixIn, viewsets.ModelViewSet
):
    obligation_types = ("hat",)
    serializer_class = HighAmbientTemperatureImportSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return HighAmbientTemperatureImport.objects.filter(
            submission=self.kwargs['submission_pk']
        ).filter(blend_item__isnull=True)

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class HighAmbientTemperatureProductionViewSet(
    BulkCreateUpdateMixin, SerializerDataContextMixIn, viewsets.ModelViewSet
):
    obligation_types = ("hat",)
    serializer_class = HighAmbientTemperatureProductionSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return HighAmbientTemperatureProduction.objects.filter(
            submission=self.kwargs['submission_pk']
        )

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class DataOtherViewSet(SerializerDataContextMixIn, viewsets.ModelViewSet):
    obligation_types = ("other",)
    serializer_class = DataOtherSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return DataOther.objects.filter(
            submission=self.kwargs['submission_pk']
        )

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class ExemptionNominationViewSet(
    BulkCreateUpdateMixin, SerializerDataContextMixIn, viewsets.ModelViewSet
):
    obligation_types = ("exemption",)
    serializer_class = ExemptionNominationSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSafeMethod, IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return Nomination.objects.filter(
            submission=self.kwargs['submission_pk']
        )

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class ExemptionApprovedViewSet(
    BulkCreateUpdateMixin, SerializerDataContextMixIn, viewsets.ModelViewSet,
):
    obligation_types = ("exemption",)
    serializer_class = ExemptionApprovedSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSafeMethod, IsCorrectObligation
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return ExemptionApproved.objects.filter(
            submission=self.kwargs['submission_pk']
        )

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs['submission_pk'])


class RAFViewSet(
    BulkCreateUpdateMixin, SerializerDataContextMixIn, viewsets.ModelViewSet,
):
    obligation_types = ("essencrit",)
    serializer_class = RAFSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return RAFReport.objects.filter(
            submission=self.kwargs['submission_pk']
        )


class TransferViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This only needs to be read-only for now
    """
    obligation_types = ("transfer",)
    serializer_class = TransferSerializer
    permission_classes = (
        IsAuthenticated,
        IsSecretariatOrSamePartySubmissionRelatedRO,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return Transfer.objects.filter(
            Q(source_party_submission=self.kwargs['submission_pk']) |
            Q(destination_party_submission=self.kwargs['submission_pk'])
        )


class ProcessAgentUsesReportedViewSet(viewsets.ReadOnlyModelViewSet):
    obligation_types = ("procagent",)
    serializer_class = ProcessAgentUsesReportedSerializer
    permission_classes = (
        IsAuthenticated,
        IsSecretariatOrSamePartySubmissionRelatedRO,
        IsCorrectObligation,
    )
    filter_backends = (IsOwnerFilterBackend,)

    def get_queryset(self):
        return ProcessAgentUsesReported.objects.filter(
            submission=self.kwargs['submission_pk']
        )


class SubmissionFileViewSet(BulkCreateUpdateMixin, viewsets.ModelViewSet):
    """
    download:
    Download the submission file.
    """
    obligation_types = None
    serializer_class = SubmissionFileSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
        IsCorrectObligation,
    )

    def get_queryset(self):
        return SubmissionFile.objects.filter(
            submission=self.kwargs['submission_pk']
        )

    @action(detail=True, methods=["get"])
    def download(self, request, submission_pk=None, pk=None):
        obj = self.get_object()
        if isinstance(obj, QuerySet):
            obj = obj.get(pk=pk)

        # We could try to guess the correct mime type here.
        response = HttpResponse(
            obj.file.read(), content_type="application/octet-stream"
        )
        file_name = urllib.parse.quote(obj.name)
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{file_name}; filename=\"{file_name}\""
        return response


class EmailViewSet(
    SerializerDataContextMixIn,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    permission_classes = (IsAuthenticated, IsSecretariat)
    serializer_class = EmailSerializer

    def get_queryset(self):
        return Email.objects.filter(
            submission=self.kwargs['submission_pk']
        )


class EmailTemplateViewSet(mixins.ListModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated, IsSecretariat)
    serializer_class = EmailTemplateSerializer
    queryset = EmailTemplate.objects.all()


class UploadHookViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    """
    Handles upload notifications for tusd hooks:
        - ``pre-create``
        - ``post-create``
        - ``post-finish``
        - ``post-terminate``
        - ``post-receive``
    tusd should be configured to point to the URL associated with this view.

    """
    @staticmethod
    def handle_pre_create(request):
        """
        Handles a pre-create notification from `tusd`.

        Sets the file name on the token.

        Returns an OK response only if:
         - the upload `token` the `MetaData` field is validated
         - the token's user is authenticated
         - a `filename` field is present in `MetaData`
        """
        log.info(f'UPLOAD pre-create: {request.data}')
        upload = request.data.get('Upload', {})
        meta_data = upload.get('MetaData', {})
        tok = meta_data.get('token', '')
        filename = meta_data.get('filename')
        try:
            token = UploadToken.objects.get(token=tok)

            if token.has_expired():
                token.delete()
                log.error('UPLOAD denied: EXPIRED TOKEN')
                return Response(
                    {'error': 'expired token'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not token.user.is_authenticated:
                log.error(
                    f'UPLOAD denied for "{token.user}": NOT ALLOWED'
                )
                return Response(
                    {'error': 'user not authenticated'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if filename is None:
                log.error(f'UPLOAD denied for "{token.user}": filename missing')
                return Response(
                    {'error': 'filename not in MetaData'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not SubmissionFile.has_valid_extension(filename):
                log.error(
                    f'UPLOAD denied for "{token.user}": bad file extension'
                )
                return Response(
                    {'error': 'bad file extension'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token.filename = filename
            token.save()

            log.info(
                f'UPLOAD authorized for "{token.user}" '
                f'on submission {token.submission}'
            )

        except UploadToken.DoesNotExist:
            log.error('UPLOAD denied: INVALID TOKEN')
            return Response(
                {'error': 'invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response()

    @staticmethod
    def handle_post_receive(request):
        """
        Handles a post-receive notification from `tusd`.
        Currently has no side-effects, exists only to avoid
        'hook not implemented' errors in `tusd`.
        """
        log.info(f'UPLOAD post-receive: {request.data}')
        return Response()

    @staticmethod
    def handle_post_create(request):
        """
        Handles a post-create notification from `tusd`.
        Sets the newly issued tus ID on the token.
        """
        log.info(f'UPLOAD post-create: {request.data}')
        upload = request.data.get('Upload', {})
        meta_data = upload.get('MetaData', {})
        tok = meta_data.get('token', '')
        try:
            token = UploadToken.objects.get(token=tok)
            token.tus_id = upload.get('ID')
            token.save()
        except UploadToken.DoesNotExist:
            log.error('UPLOAD denied: INVALID TOKEN')
            return Response(
                {'error': 'invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response()

    @staticmethod
    def handle_post_finish(request):
        """
        Handles a post-finish notification from `tusd`.
        The uploaded file is used to create an EnvelopeFile, or replace its
        underlying file on disk if one with the same name exists.
        """
        log.info(f'UPLOAD post-finish: {request.data}')
        upload = request.data.get('Upload', {})
        meta_data = upload.get('MetaData', {})
        tok = meta_data.get('token', '')
        description = meta_data.get('description', '')
        # filename presence was enforced during pre-create
        file_name = meta_data['filename']
        file_ext = file_name.split('.')[-1].lower()

        try:
            token = UploadToken.objects.get(token=tok)
            if not token.user.is_authenticated:
                log.error(f'UPLOAD denied for "{token.user}": NOT ALLOWED')
                return Response(
                    {'error': 'user not authenticated'},
                    status=status.HTTP_403_FORBIDDEN
                )

            upload_id = upload.get('ID')

            submission_file = SubmissionFile.objects.create(
                submission=token.submission,
                name=file_name,
                uploader=token.user,
                tus_id=upload_id,
                description=description,
                upload_successful=False
            )

            file_path = os.path.join(
                settings.TUSD_UPLOADS_DIR,
                upload_id
            )
            file_info_path = os.path.join(
                settings.TUSD_UPLOADS_DIR,
                f'{upload_id}.info'
            )

            file_path = Path(file_path).resolve()
            file_info_path = Path(file_info_path).resolve()

            for f in (file_path, file_info_path):
                if not f.is_file():
                    raise FileNotFoundError(f'UPLOAD tusd file not found: {f}')

            log.info(f'file extension: {file_ext}')
            log.info(f'allowed extensions: {settings.ALLOWED_FILE_EXTENSIONS}')

            # At this point, submission_file.file_name is not necessarily
            # identical to the original file name
            submission_file.file.save(
                submission_file.name, File(file_path.open(mode='rb'))
            )
            submission_file.uploader = token.user
            submission_file.upload_successful = True
            submission_file.save()

            # Finally, remove the token and the tusd files pair
            token.delete()
            file_path.unlink()
            file_info_path.unlink()

        except UploadToken.DoesNotExist:
            log.error(f'UPLOAD denied for "{tok}": INVALID TOKEN')
            return Response(
                {'error': 'invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except FileNotFoundError as err:
            log.error(f'{err}')
            return Response(
                {'error': 'file not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response()

    @staticmethod
    def handle_post_terminate(request):
        """
        Handles a post-terminate notification from `tusd`.
        Deletes the token issued for the upload.
        """
        log.info(f'UPLOAD post-terminate: {request.data}')
        upload = request.data.get('Upload', {})
        meta_data = upload.get('MetaData', {})
        tok = meta_data.get('token', '')
        try:
            token = UploadToken.objects.get(token=tok)
            token.delete()
        except UploadToken.DoesNotExist:
            log.warning(
                'UPLOAD could not find token to delete on post-terminate.'
            )
        return Response()

    def create(self, request):
        """
        Dispatches notifications from `tusd` to appropriate handler.
        """
        # Original header name sent by tusd is `Hook-Name`, Django mangles it
        hook_name = self.request.META.get('HTTP_HOOK_NAME')
        try:
            hook_handler = getattr(
                self, f'handle_{hook_name.replace("-", "_")}'
            )
        except AttributeError:
            return Response(
                {'hook_not_supported': hook_name},
                status=status.HTTP_400_BAD_REQUEST
            )

        return hook_handler(request)


class UploadTokenViewSet(viewsets.ModelViewSet):
    queryset = UploadToken.objects.all()
    serializer_class = UploadTokenSerializer
    permission_classes = (
        IsAuthenticated, IsSecretariatOrSamePartySubmissionRelated,
    )

    def create(self, request, submission_pk):
        """
        Creates an ``UploadToken`` for the submission.
        Used by `tusd` uploads server for user/submission correlation.
        Upload tokens cannot be issued for non-editable submissions

        Returns::

            {
              'token': <base64 encoded token>
            }

        """
        submission = Submission.objects.get(pk=submission_pk)

        if not submission.can_upload_files(request.user):
            return Response(
                {
                    'error': _(
                        'You do not have permission to upload files for this submission'
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        token = submission.upload_tokens.create(user=request.user)
        response = {'token': token.token}

        # Include base64 encoded token in development environments
        if settings.DEBUG:
            response['token_base64'] = b64encode(token.token.encode())

        return Response(response)

    def list(self, request, submission_pk):
        """
        Returns the tokens issued for a given submission.
        """
        queryset = UploadToken.objects.filter(submission=submission_pk)
        serializer = self.serializer_class(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)


class AuthTokenViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    lookup_field = 'key'
    lookup_url_kwarg = 'token'
    serializer_class = AuthTokenByValueSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Token.objects.filter(user=self.request.user)
        else:
            return Token.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = AuthTokenSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        response = Response({'token': token.key})
        response.set_cookie("authToken", token.key)
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        try:
            user_token = Token.objects.get(user=request.user)
        except Token.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if user_token != instance:
            return Response(status=status.HTTP_404_NOT_FOUND)

        self.perform_destroy(instance)

        response = Response(status=status.HTTP_204_NO_CONTENT)
        if "_impersonate" in request.session:
            real_user = User.objects.get(pk=request.session["_auth_user_id"])
            stop_impersonate(request)
            # Set the token of the "real user", that has been impersonating
            # this user.
            token, created = Token.objects.get_or_create(user=real_user)
            response.set_cookie("authToken", token.key)
        else:
            # Also remove any active session.
            request.session.delete()
            response.delete_cookie("authToken")
        return response


class DefaultValuesViewSet(ReadOnlyMixin, views.APIView):
    """
    retrieve:
    Get the default values for 'Obligation' and 'Reporting Period'.
    """
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request):
        default_obligation_obj = Obligation.get_default()
        default_obligation = (
            default_obligation_obj.name
            if default_obligation_obj
            else None
        )

        default_reporting_period_obj = ReportingPeriod.get_most_recent()
        default_reporting_period = (
            default_reporting_period_obj.name
            if default_reporting_period_obj
            else None
        )

        default_reporting_channel_obj = ReportingChannel.get_default(
            request.user
        )
        default_reporting_channel = (
            default_reporting_channel_obj.name
            if default_reporting_channel_obj
            else None
        )

        default_submission_format_obj = SubmissionFormat.get_default(
            request.user
        )
        default_submission_format = (
            default_submission_format_obj.name
            if default_submission_format_obj
            else None
        )

        return Response({
            'obligation': default_obligation,
            'reporting_period': default_reporting_period,
            'reporting_channel': default_reporting_channel,
            'submission_format': default_submission_format,
        })


class ReportsViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        return Response([r.api_description() for r in reports.registry])

    def retrieve(self, request, pk):
        try:
            report = reports.by_name[pk]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return report.from_request(request).render_to_response()


class CriticalUseCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CriticalUseCategorySerializer
    queryset = CriticalUseCategory.objects.all()


class BaseCountryProfileFilterSet(filters.FilterSet):
    party = filters.NumberFilter("party", help_text="Filter by party ID")


class FocalPointFilterSet(BaseCountryProfileFilterSet):
    is_licensing_system = filters.BooleanFilter(
        "is_licensing_system", help_text="Filter by is_licensing_system boolean field"
    )
    is_national = filters.BooleanFilter(
        "is_national", help_text="Filter by is_national boolean field"
    )


class FocalPointViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = FocalPoint.objects.all()
    serializer_class = FocalPointSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
    )
    filterset_class = FocalPointFilterSet


class LicensingSystemFilterSet(BaseCountryProfileFilterSet):
    has_ods = filters.BooleanFilter(
        "has_ods", help_text="Filter by has_ods boolean field"
    )
    has_hfc = filters.BooleanFilter(
        "has_hfc", help_text="Filter by has_hfc boolean field"
    )
    party = MultiValueNumberFilter(
        "party", help_text="Filter by party ID"
    )


class LicensingSystemViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = LicensingSystem.objects.all()
    serializer_class = LicensingSystemSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
    )
    filterset_class = LicensingSystemFilterSet


class WebsiteViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
    )
    filterset_class = BaseCountryProfileFilterSet


class OtherFilterSet(BaseCountryProfileFilterSet):
    reporting_period = filters.NumberFilter(
        "reporting_period", help_text="Filter by Reporting Period ID"
    )
    obligation = filters.NumberFilter(
        "obligation", help_text="Filter by Obligation ID"
    )


class OtherViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = OtherCountryProfileData.objects.all()
    serializer_class = OtherCountryProfileDataSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
    )
    filterset_class = OtherFilterSet


class ReclamationFacilityViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = ReclamationFacility.objects.all()
    serializer_class = ReclamationFacilitySerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
    )
    filterset_class = BaseCountryProfileFilterSet


class IllegalTradeViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = IllegalTrade.objects.all()
    serializer_class = IllegalTradeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
    )
    filterset_class = BaseCountryProfileFilterSet


class ORMReportFilterSet(BaseCountryProfileFilterSet):
    reporting_period = filters.NumberFilter(
        "reporting_period", help_text="Filter by Reporting Period ID"
    )


class ORMReportViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = ORMReport.objects.all()
    serializer_class = ORMReportSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
    )
    filterset_class = ORMReportFilterSet


class MultilateralFundViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = MultilateralFund.objects.all()
    serializer_class = MultilateralFundSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
    )
    filterset_class = BaseCountryProfileFilterSet


class TEAPReportTypeViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = TEAPReportType.objects.all()
    serializer_class = TEAPReportTypeSerializer
    permission_classes = (IsAuthenticated,)


class TEAPIndicativeNumberOfReportsViewSet(
    mixins.ListModelMixin, GenericViewSet
):
    queryset = TEAPIndicativeNumberOfReports.objects.all()
    serializer_class = TEAPIndicativeNumberOfReportsSerializer
    permission_classes = (IsAuthenticated,)


class TEAPReportFilterSet(filters.FilterSet):
    party = MultiValueNumberFilter(
        "party", help_text="Filter by party ID"
    )
    reporting_period = MultiValueNumberFilter(
        "reporting_period", help_text="Filter by Reporting Period ID"
    )
    report_type = MultiValueCharFilter(
        "report_type__name", help_text="Filter by report type"
    )
    decision = MultiValueCharFilter(
        "decision__decision_id", help_text="Filter by decision number"
    )


class TEAPReportViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = TEAPReport.objects.all()
    serializer_class = TEAPReportSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
    )
    filterset_class = TEAPReportFilterSet


class ImpComRecommendationFilterSet(filters.FilterSet):
    reporting_period = MultiValueNumberFilter(
        "reporting_period", help_text="Filter by Reporting Period ID"
    )
    recommendation_number = MultiValueCharFilter(
        "recommendation_number", help_text="Filter by recommendation number"
    )
    # TODO: maybe these should match with "contains"
    body = MultiValueCharFilter(
        "body", help_text="Filter by Country/Body"
    )
    topic = MultiValueCharFilter(
        "topic", help_text ="Filter by topic"
    )


class ImpComRecommendationViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = ImpComRecommendation.objects.all().prefetch_related(
        'reporting_period'
    )
    serializer_class = ImpComRecommendationSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
    )
    filterset_class = ImpComRecommendationFilterSet


class ImpComBodyViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = ImpComBody.objects.all()
    serializer_class = ImpComBodySerializer
    permission_classes = (IsAuthenticated,)


class ImpComTopicViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = ImpComTopic.objects.all()
    serializer_class = ImpComTopicSerializer
    permission_classes = (IsAuthenticated,)


class EssentialCriticalPaginator(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"


class EssentialCriticalFilterSet(SwitchableOrFilterset):
    or_fields = MultiValueCharFilter(
        "or_fields",
        help_text="Use OR instead of AND for the specified request params"
    )
    party = MultiValueNumberFilter(
        field_name="submission__party", help_text="Filter by party ID"
    )
    reporting_period = MultiValueNumberFilter(
        "submission__reporting_period",
        help_text="Filter by Reporting Period ID"
    )
    group = MultiValueNumberFilter(
        field_name="substance__group", help_text="Filter by Annex Group ID"
    )
    region = MultiValueNumberFilter(
        field_name="submission__party__subregion__region_id",
        help_text="Filter by party's region_id",
    )
    subregion = MultiValueNumberFilter(
        field_name="submission__party__subregion_id",
        help_text="Filter by party's subregion_id",
    )
    is_article5 = filters.BooleanFilter(
        field_name="is_article5",
        help_text="Filter by party_history.is_article5",
    )
    is_eu_member = filters.BooleanFilter(
        field_name="is_eu_member",
        help_text="Filter by party_history.is_eu_member",
    )


def populate_essencrit_aggregation(aggregation, to_add, odp_tons):
    """
    Helper function to populate an aggregation's fields based on a list
    of dictionaries containing key-value pairs for those fields.
    """
    if odp_tons:
        # ODP tons values should be rounded
        rounding_method = partial(round_decimal_half_up, decimals=2)
    else:
        # Do not round metric tons values when populating MT aggregations
        rounding_method = lambda x: x

    essential_use_quantities = [
        (a['quantity'] or Decimal(0)) * (a['substance__odp'] if odp_tons else Decimal(1))
        for a in to_add
        if not a['substance__has_critical_uses']
    ]
    aggregation['quantity_essential'] = rounding_method(
        sum(essential_use_quantities)
    ) if essential_use_quantities else None

    critical_use_quantities = [
        (a['quantity'] or Decimal(0)) * (a['substance__odp'] if odp_tons else Decimal(1))
        for a in to_add
        if a['substance__has_critical_uses']
    ]
    aggregation['quantity_critical'] = rounding_method(
        sum(critical_use_quantities)
    ) if critical_use_quantities else None


class EssentialCriticalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExemptionApproved.objects.all().prefetch_related(
        'submission__party', 'submission__reporting_period',
        'substance__group', 'submission__party__subregion',
    )
    serializer_class = EssentialCriticalSerializer

    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    )
    filterset_class = EssentialCriticalFilterSet
    search_fields = (
        "submission__party__name", "submission__reporting_period__name"
    )
    ordering = (
        "-submission__reporting_period__start_date",
        "submission__party",
        "substance__group"
    )
    pagination_class = EssentialCriticalPaginator

    # Custom class attributes needed for list() to properly work
    odp_tons = True
    allowed_aggregates = ('party', 'group', 'substance', )

    def get_queryset(self):
        return ExemptionApproved.objects.all().prefetch_related(
            'submission__party', 'submission__reporting_period',
            'submission__party__subregion__region',
            'substance__group',
        )

    @action(methods=["get",], detail=False)
    def last_updated(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.exclude(submission__submitted_at=None)
        updated = None if not queryset else queryset.latest(
            'submission__submitted_at'
        ).submission.submitted_at

        return Response({'last_updated': updated})

    def list(self, request, *args, **kwargs):
        # First filter queryset according to params
        queryset = self.filter_queryset(self.get_queryset())

        aggregates = request.query_params.get('aggregation', None)
        aggregates = aggregates.split(',') if aggregates else []
        aggregates = [
            agg for agg in aggregates if agg in self.allowed_aggregates
        ]
        groupings = request.query_params.get('group_by', None)
        groupings = groupings.split(',') if groupings else []

        # If there are no aggregations to perform, behave like a normal
        # ModelViewSet.
        if not aggregates:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        # Maps grouping param value to field names to be retrieved
        # Keys are possible values for the 'group_by' parameter.
        # Values are corresponding values of field_name
        grouping_mapping = {
            'is_article5': 'is_article5',
            'is_eu_member': 'is_eu_member',
            'region': 'submission__party__subregion__region'
        }
        # Field names that will be used for grouping, based on the 'group_by'
        # parameter
        grouping_fields = [
            value for key, value in grouping_mapping.items() if key in groupings
        ]

        # Otherwise, need to perform the aggregations
        values_list = queryset.values_list(
            'submission__reporting_period',
            'submission__party',
            'substance__group',
        )
        reporting_periods = set(value[0] for value in values_list)
        parties = set(value[1] for value in values_list)
        groups = set(value[2] for value in values_list)

        all_values = queryset.values(
            'id',
            'quantity', 'submission__party', 'submission__reporting_period',
            'substance_id', 'substance__odp', 'substance__group',
            'substance__has_critical_uses',
            *grouping_mapping.values()
        )
        values_dict = {period: [] for period in reporting_periods}
        for value in all_values:
            values_dict[value['submission__reporting_period']].append(value)

        # List of values that will be returned
        data = []
        for reporting_period in reporting_periods:
            # Create in-memory list of dictionaries for each exemption approved
            # for this reporting_period
            values_for_period = values_dict.get(reporting_period, [])
            if not values_for_period:
                continue

            # Take grouping fields into account to possibly generate several
            # objects for the same reporting period
            filtered_values = filter_aggregated_data_by_grouping(
                grouping_fields, values_for_period
            )
            for key in filtered_values.keys():
                # We must construct an aggregation for each key-value item
                # in the filtered_values dictionary
                to_add = filtered_values[key]
                grouping_fields_values = dict(zip(grouping_fields, key))
                params_dict = {
                    key: grouping_fields_values.get(value, None)
                    for key, value in grouping_mapping.items()
                }

                # Now aggregate
                if 'party' in aggregates and 'group' in aggregates:
                    ret = dict({
                        'reporting_period': reporting_period,
                        'party': None,
                        'group': None,
                        **params_dict
                    })
                    populate_essencrit_aggregation(ret, to_add, self.odp_tons)
                    data.append(ret)
                elif 'group' in aggregates:
                    for party in parties:
                        # Do in-memory filtering to avoid yet another DB hit
                        entries = [
                            entry for entry in to_add
                            if entry['submission__party'] == party
                        ]
                        if entries:
                            ret = dict({
                                'reporting_period': reporting_period,
                                'party': party,
                                'group': None,
                                **params_dict
                            })
                            populate_essencrit_aggregation(
                                ret, entries, self.odp_tons
                            )
                            data.append(ret)
                elif 'party' in aggregates:
                    for group in groups:
                        # Do in-memory filtering to avoid yet another DB hit
                        entries = [
                            entry for entry in to_add
                            if entry['substance__group'] == group
                        ]
                        if entries:
                            ret = dict({
                                'reporting_period': reporting_period,
                                'party': None,
                                'group': group,
                                **params_dict
                            })
                            populate_essencrit_aggregation(
                                ret, entries, self.odp_tons
                            )
                            data.append(ret)
                elif 'substance' in aggregates:
                    for party in parties:
                        for group in groups:
                            # Do initial filtering by party & group
                            entries = [
                                entry for entry in to_add
                                if entry['substance__group'] == group and
                                    entry['submission__party'] == party
                            ]
                            # Now create individual entries for each substance
                            entries_by_substance = {}
                            for entry in entries:
                                substance = entry['substance_id']
                                if substance in entries_by_substance:
                                    entries_by_substance[substance].append(
                                        entry
                                    )
                                else:
                                    entries_by_substance[substance] = [entry, ]
                            for sub, entries in entries_by_substance.items():
                                ret = dict({
                                    'reporting_period': reporting_period,
                                    'party': party,
                                    'group': group,
                                    'substance': sub,
                                    **params_dict
                                })
                                populate_essencrit_aggregation(
                                    ret, entries, self.odp_tons
                                )
                                data.append(ret)

        return Response(data)


class EssentialCriticalMTViewSet(EssentialCriticalViewSet):
    """
    The same information as in the EssentialCriticalViewSet, but given in
    metric tons.
    """
    serializer_class = EssentialCriticalMTSerializer

    # Custom class attribute needed for list() to properly work
    odp_tons = False


class GetCurrentTimeView(ReadOnlyMixin, views.APIView):
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def get(self, request, *args, **kwargs):
        return Response(datetime.now().strftime('%d %B %Y %H:%M:%S'))
