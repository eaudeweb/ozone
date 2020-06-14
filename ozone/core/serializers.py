from datetime import datetime
import mimetypes

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework_extensions.serializers import PartialUpdateSerializerMixin

from .models import (
    Region,
    Subregion,
    Party,
    PartyRatification,
    PartyDeclaration,
    PartyHistory,
    ReportingPeriod,
    Obligation,
    Substance,
    Group,
    BlendComponent,
    Blend,
    Submission,
    HistoricalSubmission,
    SubmissionInfo,
    Treaty,
    Article7Questionnaire,
    Article7Destruction,
    Article7Production,
    Article7Export,
    Article7Import,
    Article7NonPartyTrade,
    Article7Emission,
    HighAmbientTemperatureProduction,
    Transfer,
    ProcessAgentUsesReported,
    DataOther,
    SubmissionFile,
    UploadToken,
    HighAmbientTemperatureImport,
    ReportingChannel,
    Language,
    Nomination,
    ExemptionApproved,
    ApprovedCriticalUse,
    RAFReport,
    RAFReportUseCategory,
    RAFImport,
    SubmissionFormat,
    ProdCons,
    ProdConsMT,
    Limit,
    Email,
    EmailTemplate,
    EmailTemplateAttachment,
    CriticalUseCategory,
    DeviationType,
    DeviationSource,
    PlanOfActionDecision,
    PlanOfAction,
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
    ImpComRecommendation,
    ImpComTopic,
    ImpComBody,
)
from ozone.core.api.export_pdf import reports

User = get_user_model()


class BaseBulkUpdateSerializer(serializers.ListSerializer):
    """
    This is a base class for serializers that allow bulk updates (PUT requests
    containing a list of objects to create under a specific resource)
    """
    class ConfigurationError(Exception):
        pass

    # These need to be set properly by each class that extends this
    # Fields in substance_blend_fields list are mutually exclusive (one DB entry
    # cannot have more that one of them not null (e.g. substance or blend))
    # `unique_with` can be None, a list or a tuple.
    substance_blend_fields = None
    unique_with = None

    def __init__(self, *args, **kwargs):
        if not isinstance(self.substance_blend_fields, list):
            raise self.ConfigurationError(
                'Class attribute `substance_blend_fields` needs to be a list'
            )

        super().__init__(*args, **kwargs)

    def construct_data_dictionary(self, validated_data):
        """
        Constructs a dictionary with (substance, party) keys starting from
        validated_data (which is a list of data entries).
        This is later used to easily lookup existing entries and see if they
        need to be deleted or updated.
        This approach does not generate key collisions because
        `entry.get(field)` returns either a `Blend` or a `Substance` object,
        instead of integer id's.
        """
        data_dictionary = {}
        for entry in validated_data:
            for field in self.substance_blend_fields:
                if self.unique_with is None:
                    field_value = entry.get(field, None)
                else:
                    field_value = (
                        entry.get(field),
                        *[entry.get(f) for f in self.unique_with]
                    )

                if entry.get(field, None) is None:
                    continue
                if field_value in data_dictionary:
                    raise ValidationError(_(f"Duplicate value for {field_value}"))
                data_dictionary[field_value] = entry

        return data_dictionary

    def construct_key(self, existing_entry):
        # These fields are mutually exclusive, so this works
        for field in self.substance_blend_fields:
            field_value = getattr(existing_entry, field)
            if field_value:
                # Construct key to find existing_entry in validated_data
                key = field_value
                if self.unique_with is not None:
                    key = (
                        key,
                        *[getattr(existing_entry, f) for f in self.unique_with]
                    )
                return key
        # Should never get here
        return None

    def update_single(self, existing_entry, entry):
        """Updates a single entry"""
        changed = False
        for field, value in entry.items():
            if getattr(existing_entry, field, None) != value:
                setattr(existing_entry, field, value)
                changed = True
        return changed

    def create_single(self, data, instance, submission):
        """Creates a single entry"""
        obj = instance.create(
            submission=submission,
            **data
        )
        return obj

    def update(self, instance, validated_data):
        """
        Updating data reports in a submission will work as follows:
        - all substances in queryset that do not appear in `validated_data`
          will be deleted.
        - substances in queryset that do appear in `validated_data` will be
          updated.
        - substances in `validated_data` that do not appear in queryset will
          have entries created for them

        The update method will *only permit lists* to be passed as parameters.
        The `instance` parameter is, in this case, a queryset!
        """
        submission = instance.first().submission
        # List of updated/created items to be returned
        ret = []

        data_dictionary = self.construct_data_dictionary(validated_data)

        if not data_dictionary:
            # If the data dictionary is not populated (e.g. there are no fields
            # to do lookups on), we simply delete all existing data
            instance.delete()
            data_dictionary = dict(enumerate(validated_data))
        else:
            # Hitting the database (one query) to iterate over the list of
            # existing data is a small price to pay for potentially avoiding
            # a lot of unnecessary updates afterwards (e.g. when a single record
            # changes for an existing submission with a lot of records).
            for existing_entry in instance:
                # Construct the key to lookup the existing entry in data_dict
                key = self.construct_key(existing_entry)

                # If existing entry needs to be deleted, delete it
                if key not in data_dictionary:
                    existing_entry.delete()
                # If it needs to be updated, update it and remove the
                # corresponding entry from validated_data
                else:
                    # Check if it needs to be updated to avoid database hit
                    entry = data_dictionary.pop(key)
                    if self.update_single(existing_entry, entry):
                        ret.append(existing_entry)

        for existing_entry in ret:
            existing_entry.save()

        # After all that is done, just create the entries that still need to be
        # created (have not been popped out of data_dictionary)
        for key, data in data_dictionary.items():
            obj = self.create_single(data, instance, submission)
            ret.append(obj)

        return ret

    def create(self, validated_data):
        # Call this method to check for duplicates in validated_data
        self.construct_data_dictionary(validated_data)
        return super().create(validated_data)


class CurrentUserSerializer(serializers.ModelSerializer):
    """
    Used to get basic info for current user
    """
    impersonated_by = serializers.SerializerMethodField()
    language = serializers.SlugRelatedField(
        read_only=False,
        queryset=Language.objects.all(),
        many=False,
        slug_field='iso'
    )
    party_name = serializers.StringRelatedField(source='party', read_only=True)
    related_parties = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username',
            'is_secretariat', 'is_read_only', 'is_cap', 'is_mobile_app',
            'party', 'party_name', 'related_parties',
            'first_name', 'last_name', 'email', 'language', 'role',
            'impersonated_by'
        )
        read_only_fields = (
            'id', 'username',
            'is_secretariat', 'is_read_only', 'is_cap', 'is_mobile_app',
            'party', 'role',
            'related_parties',
        )

    def get_impersonated_by(self, obj):
        session = self.context['request'].session
        if '_impersonate' not in session:
            return None
        return User.objects.get(pk=session['_auth_user_id']).username

    def get_related_parties(self, obj):
        if obj.is_secretariat:
            return [party.pk for party in Party.get_main_parties()]
        elif obj.party_group:
            return [party.pk for party in obj.party_group.parties.all()]
        elif obj.party:
            return [obj.party.pk]
        return []


class BaseBlendCompositionSerializer(serializers.ModelSerializer):
    """
    This will be used as a base for all reporting serializers that accept
    both substances and blends.
    """

    derived_substance_data = serializers.SerializerMethodField()

    def get_derived_substance_data(self, obj):
        derived_substances = []
        if obj.blend:
            for component in obj.components.all():
                component_details = dict()
                component_details['substance'] = component.substance.name
                for quantity in obj.QUANTITY_FIELDS:
                    component_details[quantity] = getattr(component, quantity)
                derived_substances.append(component_details)
        return derived_substances


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ('id', 'name', 'abbr')


class SubregionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subregion
        fields = ('id', 'name', 'abbr', 'region')


class TreatySerializer(serializers.ModelSerializer):
    class Meta:
        model = Treaty
        fields = ('treaty_id', 'name')


class RatificationSerializer(serializers.ModelSerializer):
    treaty = TreatySerializer(
        many=False, read_only=True
    )

    class Meta:
        model = PartyRatification
        fields = (
            'treaty', 'ratification_type', 'ratification_date',
            'entry_into_force_date'
        )


class PartySerializer(serializers.ModelSerializer):
    region_id = serializers.PrimaryKeyRelatedField(
        source="subregion.region_id",
        many=False,
        read_only=True,
    )

    class Meta:
        model = Party
        fields = (
            'id', 'name', 'abbr', 'region_id', 'subregion_id', 'parent_party', 'iso_alpha3_code'
        )


class PartyRatificationSerializer(serializers.ModelSerializer):
    subregion = serializers.StringRelatedField(many=False)
    ratifications = RatificationSerializer(
        many=True, read_only=True
    )
    flags = serializers.SerializerMethodField()
    ratification_notes = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(PartyRatificationSerializer, self).__init__(*args, **kwargs)
        self._current_period = ReportingPeriod.get_current_period()

    def get_flags(self, obj):
        try:
            current_history_entry = obj.history.get(
                reporting_period=self._current_period
            )
            return dict({
                field: getattr(current_history_entry, field)
                for field in (
                    'is_eu_member', 'is_high_ambient_temperature', 'is_article5'
                )
            }, **{
                'is_group2': current_history_entry.is_group2()
            })
        except PartyHistory.DoesNotExist:
            return {
                'is_eu_member':  False,
                'is_high_ambient_temperature':  False,
                'is_article5':  False,
                'is_group2':  False,
            }

    def get_ratification_notes(self, obj):
        try:
            declaration = obj.declarations.all().get()
            return declaration.declaration
        except PartyDeclaration.DoesNotExist:
            return None

    class Meta:
        model = Party
        fields = (
            'id', 'name', 'abbr', 'subregion',
            'sign_date_vc', 'sign_date_mp', 'ratifications', 'flags',
            'ratification_notes',
        )


class SubstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Substance
        fields = (
            'id', 'name', 'description', 'sort_order',
            'odp', 'gwp', 'formula', 'number_of_isomers',
            'is_qps', 'is_contained_in_polyols', 'is_captured',
            'has_critical_uses',
        )


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'


class GroupSubstanceSerializer(serializers.ModelSerializer):
    substances = SubstanceSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = Group
        fields = ('id', 'group_id', 'name', 'description', 'substances')


class BlendComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlendComponent
        fields = ('substance', 'component_name', 'percentage')


class BlendSerializer(serializers.ModelSerializer):
    components = BlendComponentSerializer(many=True)

    class Meta:
        model = Blend
        fields = (
            'id', 'blend_id', 'custom', 'is_qps', 'party', 'type',
            'other_names', 'composition', 'components', 'sort_order',
            'trade_name', 'odp', 'gwp',
        )
        read_only_fields = ('custom', 'is_qps',)


class CreateBlendSerializer(BlendSerializer):
    components = BlendComponentSerializer(many=True)

    class Meta(BlendSerializer.Meta):
        pass

    def create(self, validated_data):
        components_data = validated_data.pop('components')
        # Enforce Custom type for new blends.
        validated_data['type'] = 'Custom'
        blend = Blend.objects.create(**validated_data)
        for component_data in components_data:
            BlendComponent.objects.create(blend=blend, **component_data)
        return blend

    def update(self, instance, validated_data):
        components_data = validated_data.pop('components')
        blend = super().update(instance, validated_data)

        validated_mapping = {}
        for c in components_data:
            # Substance, if present always takes precedence over component_name,
            # as we may want to change the component_name for a specific subst
            if c.get('substance', None) is not None:
                validated_mapping[c.get('substance')] = c
            elif c.get('component_name', "") != "":
                validated_mapping[c.get('component_name')] = c

        # Delete all components that do not correspond to the new data
        # and update the modified ones
        for c in BlendComponent.objects.filter(blend=instance):
            if c.substance not in validated_mapping.keys():
                if c.component_name not in validated_mapping.keys():
                    c.delete()
                else:
                    # No substance, but component name in validated_data
                    component_data = validated_mapping.pop(c.component_name)
                    c.percentage = component_data.get('percentage')
                    c.save()
            else:
                # Substance in validated_data
                component_data = validated_mapping.pop(c.substance)
                c.component_name = component_data.get('component_name', "")
                c.percentage = component_data.get('percentage')
                c.save()

        # And now create the new ones
        for key, component in validated_mapping.items():
            BlendComponent.objects.create(blend=instance, **component)

        return blend


class ReportingPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportingPeriod
        fields = (
            'id', 'name', 'start_date', 'end_date',
            'description',
            'is_reporting_allowed', 'is_reporting_open'
        )


class ObligationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Obligation
        fields = ('id', 'name', 'obligation_type', 'sort_order', 'is_active')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class Article7QuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article7Questionnaire
        exclude = ('submission',)


class DataCheckRemarksMixInBase(object):
    """Base class for checking remarks permissions for data entry."""

    def check_remarks(self, remark_party_changed, remark_os_changed):
        """Check if the party/secretariat remark are being incorrectly changed.

        Raises a ValidationError.
        """
        user = self.context['request'].user
        submission = self.context['submission']

        # XXX Logic duplicated in Submission.check_remarks
        if not submission.filled_by_secretariat and user.is_secretariat and remark_party_changed:
            # Secretariat users cannot modify any of the party fields, if the
            # submission was filled by a party.
            raise ValidationError({
                "remarks_party": [_('User is not allowed to change this remark')]
            })
        elif not user.is_secretariat and remark_os_changed:
            # Party users cannot modify any of the secretariat remark fields
            raise ValidationError({
                "remarks_os": [_('User is not allowed to change this remark')]
            })


class DataCheckRemarksMixIn(DataCheckRemarksMixInBase):
    """
    Check create and update permissions on remarks for adding/updating a single
    data entry.
    """

    def create(self, validated_data):
        if not isinstance(validated_data, list):
            self.check_remarks(
                bool(validated_data.get("remarks_party")),
                bool(validated_data.get("remarks_os"))
            )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if not isinstance(validated_data, list):
            self.check_remarks(
                "remarks_party" in validated_data and validated_data["remarks_party"] != instance.remarks_party,
                "remarks_os" in validated_data and validated_data["remarks_os"] != instance.remarks_os
            )
        return super().update(instance, validated_data)


class DataCheckRemarksBulkUpdateMixIn(DataCheckRemarksMixIn):
    """
    Check create and update permissions on remarks for adding/updating bulk
    data entries.
    """

    def update_single(self, existing_entry, entry):
        self.check_remarks(
            "remarks_party" in entry and entry["remarks_party"] != existing_entry.remarks_party,
            "remarks_os" in entry and entry["remarks_os"] != existing_entry.remarks_os
        )
        return super().update_single(existing_entry, entry)

    def create_single(self, data, instance, submission):
        self.check_remarks(
            bool(data.get("remarks_party")),
            bool(data.get("remarks_os"))
        )
        return super().create_single(data, instance, submission)


class Article7DestructionListSerializer(
    DataCheckRemarksBulkUpdateMixIn, BaseBulkUpdateSerializer
):
    substance_blend_fields = ['substance', 'blend']
    unique_with = None


class Article7DestructionSerializer(
    DataCheckRemarksMixIn, serializers.ModelSerializer
):
    group = serializers.CharField(
        source='substance.group.group_id', default='', read_only=True
    )

    class Meta:
        list_serializer_class = Article7DestructionListSerializer
        model = Article7Destruction
        exclude = ('submission', 'blend_item',)


class Article7ProductionListSerializer(
    DataCheckRemarksBulkUpdateMixIn, BaseBulkUpdateSerializer
):
    substance_blend_fields = ['substance', ]
    unique_with = None


class Article7ProductionSerializer(
    DataCheckRemarksMixIn, serializers.ModelSerializer
):
    group = serializers.CharField(
        source='substance.group.group_id', default='', read_only=True
    )

    class Meta:
        list_serializer_class = Article7ProductionListSerializer
        model = Article7Production
        exclude = ('submission',)


class Article7ExportListSerializer(
    DataCheckRemarksBulkUpdateMixIn, BaseBulkUpdateSerializer
):
    substance_blend_fields = ['substance', 'blend']
    unique_with = ('destination_party',)


class Article7ExportSerializer(
    DataCheckRemarksMixIn, BaseBlendCompositionSerializer
):
    group = serializers.CharField(
        source='substance.group.group_id', default='', read_only=True
    )

    class Meta:
        list_serializer_class = Article7ExportListSerializer
        model = Article7Export
        exclude = ('submission', 'blend_item',)


class Article7ImportListSerializer(
    DataCheckRemarksBulkUpdateMixIn, BaseBulkUpdateSerializer
):
    substance_blend_fields = ['substance', 'blend']
    unique_with = ('source_party',)


class Article7ImportSerializer(
    DataCheckRemarksMixIn, BaseBlendCompositionSerializer
):
    group = serializers.CharField(
        source='substance.group.group_id', default='', read_only=True
    )

    class Meta:
        list_serializer_class = Article7ImportListSerializer
        model = Article7Import
        exclude = ('submission', 'blend_item',)


class Article7NonPartyTradeListSerializer(
    DataCheckRemarksBulkUpdateMixIn, BaseBulkUpdateSerializer
):
    substance_blend_fields = ['substance', 'blend']
    unique_with = ('trade_party',)


class Article7NonPartyTradeSerializer(
    DataCheckRemarksMixIn, BaseBlendCompositionSerializer
):
    group = serializers.CharField(
        source='substance.group.group_id', default='', read_only=True
    )

    class Meta:
        list_serializer_class = Article7NonPartyTradeListSerializer
        model = Article7NonPartyTrade
        exclude = ('submission', 'blend_item',)


class Article7EmissionListSerializer(
    DataCheckRemarksBulkUpdateMixIn, BaseBulkUpdateSerializer
):
    """
    The list serializer for emissions needs to delete everything
    there was and create all data fresh, as there is no field to filter on.

    This is accomplished easily by setting substance_blend_fields = []
    """
    substance_blend_fields = []


class Article7EmissionSerializer(
    DataCheckRemarksMixIn, serializers.ModelSerializer
):
    class Meta:
        list_serializer_class = Article7EmissionListSerializer
        model = Article7Emission
        exclude = ('submission',)


class HighAmbientTemperatureProductionListSerializer(
    DataCheckRemarksBulkUpdateMixIn, BaseBulkUpdateSerializer
):
    substance_blend_fields = ['substance', ]
    unique_with = None


class HighAmbientTemperatureProductionSerializer(
    DataCheckRemarksMixIn, serializers.ModelSerializer
):
    group = serializers.CharField(
        source='substance.group.group_id', default='', read_only=True
    )

    class Meta:
        list_serializer_class = HighAmbientTemperatureProductionListSerializer
        model = HighAmbientTemperatureProduction
        exclude = ('submission',)


class HighAmbientTemperatureImportListSerializer(
    DataCheckRemarksBulkUpdateMixIn, BaseBulkUpdateSerializer
):
    substance_blend_fields = ['substance', 'blend']
    unique_with = None


class HighAmbientTemperatureImportSerializer(
    DataCheckRemarksMixIn, BaseBlendCompositionSerializer
):
    group = serializers.CharField(
        source='substance.group.group_id', default='', read_only=True
    )

    class Meta:
        list_serializer_class = HighAmbientTemperatureImportListSerializer
        model = HighAmbientTemperatureImport
        exclude = ('submission', 'blend_item',)


class DataOtherSerializer(DataCheckRemarksMixIn, serializers.ModelSerializer):
    class Meta:
        model = DataOther
        exclude = ('submission',)


class ExemptionNominationListSerializer(
    DataCheckRemarksBulkUpdateMixIn, BaseBulkUpdateSerializer
):
    substance_blend_fields = ['substance', ]
    unique_with = ('is_emergency',)


class ExemptionNominationSerializer(
    DataCheckRemarksMixIn, serializers.ModelSerializer
):
    group = serializers.CharField(
        source='substance.group.group_id', default='', read_only=True
    )

    class Meta:
        list_serializer_class = ExemptionNominationListSerializer
        model = Nomination
        exclude = ('submission',)


class ApprovedCriticalUseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovedCriticalUse
        exclude = ('exemption',)


class ExemptionApprovedListSerializer(
    DataCheckRemarksBulkUpdateMixIn, BaseBulkUpdateSerializer
):
    substance_blend_fields = ['substance', ]
    unique_with = ('is_emergency', 'decision_approved',)

    approved_uses = ApprovedCriticalUseSerializer(many=True, required=False)

    def create_single(self, data, instance, submission):
        """
        Creates a single entry taking into account the special case of approved
        critical uses.
        """
        approved_uses = data.pop('approved_uses', [])
        res = super().create_single(data, instance, submission)

        for value_entry in approved_uses:
            ApprovedCriticalUse.objects.create(exemption=res, **value_entry)

        return res

    def update_single(self, existing_entry, entry):
        """
        Updates a single entry taking into account the special case of approved
        critical uses.
        """
        changed = False
        for field, value in entry.items():
            if field == 'approved_uses':
                # Delete all existing approved critical uses and recreate them,
                # using the related manager.
                existing_entry.approved_uses.all().delete()
                for value_entry in value:
                    ApprovedCriticalUse.objects.create(
                        exemption=existing_entry, **value_entry
                    )
                changed = True
            elif getattr(existing_entry, field, None) != value:
                setattr(existing_entry, field, value)
                changed = True
        return changed


class ExemptionApprovedSerializer(
    DataCheckRemarksMixIn, serializers.ModelSerializer
):
    group = serializers.CharField(
        source='substance.group.group_id', default='', read_only=True
    )
    approved_uses = ApprovedCriticalUseSerializer(many=True, required=False)

    def create(self, validated_data):
        """
        Overriding create() to make sure critical_uses are properly treated.
        """
        approved_uses_data = validated_data.pop("approved_uses", [])

        instance = ExemptionApproved.objects.create(
            submission=self.context['submission'], **validated_data
        )
        for data in approved_uses_data:
            ApprovedCriticalUse.objects.create(exemption=instance, **data)

        return instance

    class Meta:
        list_serializer_class = ExemptionApprovedListSerializer
        model = ExemptionApproved
        exclude = ('submission',)


# Helper function for handling unknown/other parties in RAF imports and use
# categories.
def _handle_party_other_out(entry):
    """
    When the party is None on the model instance, frontend will get special
    country id 9999 instead of null.
    """
    if 'party' in entry:
        entry["party"] = 9999 if entry["party"] is None else entry["party"]
    return entry


class RAFImportSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        """
        Handle the special case of the party with id 9999.
        """
        ret = super().to_representation(instance)
        return _handle_party_other_out(ret)

    class Meta:
        model = RAFImport
        exclude = ('report',)


class RAFReportUseCategorySerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        """
        Handle the special case of the party with id 9999.
        """
        ret = super().to_representation(instance)
        return _handle_party_other_out(ret)

    class Meta:
        model = RAFReportUseCategory
        exclude = ('report',)


class RAFListSerializer(
    DataCheckRemarksBulkUpdateMixIn, BaseBulkUpdateSerializer
):
    substance_blend_fields = ['substance', ]
    unique_with = ('is_emergency',)

    imports = RAFImportSerializer(many=True)
    use_categories = RAFReportUseCategorySerializer(many=True)

    def is_valid(self, raise_exception=False):
        """
        Overriding is_valid to treat special case of party 9999 - which actually
        translates into None in the DB. If all occurrences of 9999 in
        self.initial_data are not replaced, field validation will fail since
        9999 is not an actual pk.
        """
        for data in self.initial_data:
            for imp in data.get('imports', []):
                if imp['party'] == 9999:
                    imp['party'] = None

        return super().is_valid(raise_exception)

    def create_single(self, data, instance, submission):
        """
        Creates a single entry taking into account the special "imports" and
        "use_categories" cases.
        """
        imports = data.pop('imports', [])
        use_categories = data.pop('use_categories', [])
        res = super().create_single(data, instance, submission)

        for value_entry in imports:
            RAFImport.objects.create(
                report=res, **value_entry
            )

        for value_entry in use_categories:
            RAFReportUseCategory.objects.create(
                report=res, **value_entry
            )

        return res

    def update_single(self, existing_entry, entry):
        """
        Updates a single entry taking into account the special "imports" case
        """
        changed = False
        for field, value in entry.items():
            if field == 'imports':
                # Delete all existing imports and recreate them, using the
                # related manager.
                existing_entry.imports.all().delete()
                for value_entry in value:
                    RAFImport.objects.create(
                        report=existing_entry, **value_entry
                    )
                changed = True
            elif field == 'use_categories':
                # Delete all existing use categories and recreate them, using
                # the related manager.
                existing_entry.use_categories.all().delete()
                for value_entry in value:
                    RAFReportUseCategory.objects.create(
                        report=existing_entry, **value_entry
                    )
                changed = True
            elif getattr(existing_entry, field, None) != value:
                setattr(existing_entry, field, value)
                changed = True
        return changed


class RAFSerializer(
    DataCheckRemarksMixIn, serializers.ModelSerializer
):
    group = serializers.CharField(
        source='substance.group.group_id', default='', read_only=True
    )

    imports = RAFImportSerializer(many=True)
    use_categories = RAFReportUseCategorySerializer(many=True)

    def is_valid(self, raise_exception=False):
        """
        Overriding is_valid to treat special case of party 9999 - which actually
        translates into None in the DB. If all occurrences of 9999 in
        self.initial_data are not replaced, field validation will fail since
        9999 is not an actual pk.
        """
        for imp in self.initial_data.get('imports', []):
            if imp['party'] == 9999:
                imp['party'] = None
        return super().is_valid(raise_exception)

    def create(self, validated_data):
        """
        Overriding create() to make sure imports and use_categories are
        properly treated.
        """
        imports_data = validated_data.pop("imports", [])
        use_categories_data = validated_data.pop("use_categories", [])

        instance = RAFReport.objects.create(
            submission=self.context['submission'], **validated_data
        )
        for data in imports_data:
            RAFImport.objects.create(report=instance, **data)
        for data in use_categories_data:
            RAFReportUseCategory.objects.create(report=instance, **data)

        return instance

    class Meta:
        list_serializer_class = RAFListSerializer
        model = RAFReport
        exclude = ('submission',)


class CriticalUseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CriticalUseCategory
        fields = '__all__'


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        exclude = ('source_party_submission', 'destination_party_submission')


class ProcessAgentUsesReportedSerializer(serializers.ModelSerializer):
    application_substance = serializers.CharField(
        source='application.substance', default=''
    )
    application = serializers.CharField(
        source='application.application', default=''
    )
    decision = serializers.CharField(default='')
    contain_technologies = serializers.CharField(default='')

    class Meta:
        model = ProcessAgentUsesReported
        fields = (
            'application_substance', 'application', 'decision',
            'makeup_quantity', 'emissions', 'units', 'contain_technologies',
            'remark'
        )


class DeviationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviationType
        fields = '__all__'


class DeviationSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviationSource
        fields = '__all__'


class PlanOfActionDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanOfActionDecision
        fields = '__all__'


class PlanOfActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanOfAction
        fields = '__all__'


class UpdateSubmissionInfoSerializer(serializers.ModelSerializer):
    reporting_channel = serializers.SerializerMethodField()
    submitted_at = serializers.SerializerMethodField()
    submission_format = serializers.SerializerMethodField()

    class Meta:
        model = SubmissionInfo
        exclude = ('submission',)

    def get_reporting_channel(self, obj):
        return getattr(obj.submission.reporting_channel, 'name', '')

    def get_submitted_at(self, obj):
        submitted_at = getattr(obj.submission, 'submitted_at', None)
        if submitted_at:
            return submitted_at.strftime('%Y-%m-%d')

    def get_submission_format(self, obj):
        return getattr(obj.submission_format, 'name', '')

    def check_reporting_channel(self, instance, user):
        if (
            instance.submission.check_reporting_channel_modified()
            and not instance.submission.can_change_reporting_channel(user)
        ):
            raise ValidationError({
                "reporting_channel": [
                    _('User is not allowed to change the reporting channel')
                ]
            })

    def check_submitted_at(self, instance, user):
        if (
            instance.submission.check_submitted_at_modified()
            and not instance.submission.can_change_submitted_at(user)
        ):
            raise ValidationError({
                "submitted_at": [
                    _('User is not allowed to change date of submission.')
                ]
            })

    def update(self, instance, validated_data):
        user = self.context['request'].user
        # Quick fix for staging error. Reporting channel info has been lost for
        # some submissions, otherwise this check wouldn't be necessary.
        to_update_fields = []
        if self.context.get('reporting_channel', None):
            instance.submission.reporting_channel = ReportingChannel.objects.get(
                name=self.context['reporting_channel']
            )
            self.check_reporting_channel(instance, user)
            to_update_fields.append('reporting_channel')
        if self.context.get('submitted_at', None):
            instance.submission.submitted_at = datetime.strptime(
                self.context['submitted_at'],
                '%Y-%m-%d'
            ).date()
            self.check_submitted_at(instance, user)
            to_update_fields.append('submitted_at')
        if to_update_fields:
            instance.submission.save(update_fields=to_update_fields)

        if self.context.get('submission_format', None):
            instance.submission_format = SubmissionFormat.objects.get(
                name=self.context['submission_format']
            )

        return super().update(instance, validated_data)


class SubmissionInfoSerializer(serializers.ModelSerializer):
    reporting_channel = serializers.SerializerMethodField()
    submitted_at = serializers.CharField(
        source='submission.submitted_at',
        read_only=True
    )
    submission_format = serializers.SerializerMethodField()

    class Meta:
        model = SubmissionInfo
        exclude = ('submission',)

    def get_reporting_channel(self, obj):
        return getattr(obj.submission.reporting_channel, 'name', '')

    def get_submission_format(self, obj):
        return getattr(obj.submission_format, 'name', '')


class SubmissionFormatSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubmissionFormat
        fields = ('name', )


class ReportingChannelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportingChannel
        fields = '__all__'


class PerTypeFieldsMixIn(object):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed/updated

    See https://www.django-rest-framework.org/api-guide/serializers/#dynamically-modifying-fields
    """

    def __init__(self, instance=None, **kwargs):
        # Instantiate the superclass normally
        super().__init__(instance=instance, **kwargs)
        try:
            # Fields and remarks return a list of one.
            instance = instance[0]
        except IndexError:
            # Empty queryset.
            return
        except TypeError:
            # A detail view.
            pass
        fields = self.get_dynamic_fields(instance)
        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    @classmethod
    def get_dynamic_fields(cls, instance):
        """Get the corresponding fields"""
        if not instance:
            return
        try:
            return cls.Meta.per_type_fields[instance.obligation.obligation_type]
        except KeyError:
            return cls.Meta.base_fields


class SubmissionFlagsSerializer(
    PerTypeFieldsMixIn, PartialUpdateSerializerMixin,
    serializers.ModelSerializer,
):
    """
    Specific serializer used to present all submission flags as a nested
    object, since this is easily usable by the frontend.
    """

    class Meta:
        model = Submission
        base_fields = (
            'flag_provisional', 'flag_valid', 'flag_superseded',
        )
        per_type_fields = {
            'art7': base_fields + (
                'flag_checked_blanks', 'flag_has_blanks',
                'flag_confirmed_blanks',
                'flag_has_reported_a1', 'flag_has_reported_a2',
                'flag_has_reported_b1', 'flag_has_reported_b2',
                'flag_has_reported_b3', 'flag_has_reported_c1',
                'flag_has_reported_c2', 'flag_has_reported_c3',
                'flag_has_reported_e', 'flag_has_reported_f',
            ),
            'hat': base_fields + (
                'flag_checked_blanks', 'flag_has_blanks',
                'flag_confirmed_blanks',
                'flag_has_reported_a1', 'flag_has_reported_a2',
                'flag_has_reported_b1', 'flag_has_reported_b2',
                'flag_has_reported_b3', 'flag_has_reported_c1',
                'flag_has_reported_c2', 'flag_has_reported_c3',
                'flag_has_reported_e', 'flag_has_reported_f',
            ),
            'essencrit': base_fields,
            'other': base_fields,
            'exemption': ('flag_emergency',),
            'transfer': base_fields,
            'procagent': base_fields,
        }
        fields = list(set(sum(per_type_fields.values(), ())))

    def update(self, instance, validated_data):
        """
        Not really kosher to perform validations here, but we need to
        pass the user to the validation method in the model.
        Cannot override the serializer's validate() method either since it
        does not have access to the object instance.
        """
        # User should always be on the request due to our permission classes
        user = self.context['request'].user
        instance.check_flags(user, validated_data)
        # If checks were successful, also inject user into validated data
        validated_data['last_edited_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class SubmissionRemarksSerializer(
    PerTypeFieldsMixIn, PartialUpdateSerializerMixin,
    serializers.ModelSerializer
):
    """
    Specific serializer used to present all general submission remarks,
    since this is easily usable by the frontend.
    """

    class Meta:
        model = Submission
        base_fields = ()
        per_type_fields = {
            'art7': (
                'questionnaire_remarks_party',
                'questionnaire_remarks_secretariat',
                'imports_remarks_party', 'imports_remarks_secretariat',
                'exports_remarks_party', 'exports_remarks_secretariat',
                'production_remarks_party', 'production_remarks_secretariat',
                'destruction_remarks_party', 'destruction_remarks_secretariat',
                'nonparty_remarks_party', 'nonparty_remarks_secretariat',
                'emissions_remarks_party', 'emissions_remarks_secretariat',
            ),
            'hat': (
                'hat_imports_remarks_party',
                'hat_imports_remarks_secretariat',
                'hat_production_remarks_party',
                'hat_production_remarks_secretariat',
            ),
            'essencrit': ('raf_remarks_party', 'raf_remarks_secretariat',),
            'other': (),
            'exemption': (
                'exemption_nomination_remarks_secretariat',
                'exemption_approved_remarks_secretariat',
            ),
            'transfer': ('transfers_remarks_secretariat',),
            'procagent': ('pa_uses_reported_remarks_secretariat',),
        }
        fields = list(set(sum(per_type_fields.values(), ())))

    def update(self, instance, validated_data):
        """
        Not really kosher to perform validations here, but we need to
        pass the user to the validation method in the model.
        Cannot override the serializer's validate() method either since it
        does not have access to the object instance.
        """
        # User should always be on the request due to our permission classes
        user = self.context['request'].user
        instance.check_remarks(user, validated_data)
        # If checks were successful, also inject user into validated data
        validated_data['last_edited_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class SubmissionFileListSerializer(serializers.ListSerializer):
    """
    ListSerializer for SubmissionFile's
    """

    def update(self, instance, validated_data):
        """
        Implements bulk update functionality for files.
        File entries will be identified by id, not by name, to allow renames.
        """
        if not isinstance(validated_data, list):
            validated_data = [validated_data, ]

        ret = []

        for modified_entry in validated_data:
            modified_id = modified_entry.get('id', None)
            if modified_id is None:
                raise ValidationError({
                    "id": [_('File id must be specified at update')]
                })
            try:
                # `instance` is a queryset due to the `BulkCreateUpdateMixin`
                obj = instance.get(id=modified_id)
                changed = False
                # We only allow changing the name and description
                if 'name' in modified_entry:
                    obj.name = modified_entry.get('name')
                    changed = True
                if 'description' in modified_entry:
                    obj.description = modified_entry.get('description')
                    changed = True
                if changed:
                    obj.save()
                    ret.append(obj)
            except ObjectDoesNotExist:
                raise ValidationError({
                    "id": [_('Specified file id not found for this submission')]
                })

        return ret


class SubmissionFileSerializer(serializers.ModelSerializer):

    # This needs to be specified explicitly so it is allowed on updates
    id = serializers.IntegerField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = SubmissionFile
        list_serializer_class = SubmissionFileListSerializer
        exclude = ('submission', 'file',)
        read_only_fields = (
            'file_url', 'tus_id', 'upload_successful', 'created', 'updated',
            'original_name', 'suffix', 'uploader',
        )

    def get_file_url(self, obj):
        return self.context['request'].build_absolute_uri(
            reverse(
                "core:submission-files-download",
                kwargs={
                    "submission_pk": obj.submission.pk,
                    "pk": obj.pk
                }
            )
        )


class SubmissionTransitionsSerializer(serializers.ModelSerializer):

    available_transitions = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = ('available_transitions',)
        read_only_fields = ('available_transitions',)

    def get_available_transitions(self, obj):
        user = self.context['request'].user
        return obj.available_transitions(user)


class UploadTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadToken
        fields = '__all__'


class SubmissionSerializer(
    PerTypeFieldsMixIn,
    PartialUpdateSerializerMixin,
    serializers.HyperlinkedModelSerializer,

):
    """
    This also needs to nested-serialize all data related to the specific
    submission.
    """
    party = serializers.PrimaryKeyRelatedField(many=False, read_only=True)
    reporting_period = serializers.StringRelatedField(
        many=False, read_only=True
    )
    obligation = serializers.StringRelatedField(
        many=False, read_only=True
    )
    # Frontend needs obligation type, as well
    obligation_type = serializers.SerializerMethodField()

    revision = serializers.SerializerMethodField()

    # At most one questionnaire per submission, but multiple other data
    article7questionnaire_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-article7-questionnaire-list',
        lookup_url_kwarg='submission_pk'
    )
    article7questionnaire = Article7QuestionnaireSerializer(
        many=False, read_only=True
    )

    files = SubmissionFileSerializer(
        many=True, read_only=True
    )

    # We want to add a URL for the destructions list
    article7destructions_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-article7-destructions-list',
        lookup_url_kwarg='submission_pk'
    )

    article7productions_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-article7-productions-list',
        lookup_url_kwarg='submission_pk'
    )

    article7exports_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-article7-exports-list',
        lookup_url_kwarg='submission_pk'
    )

    article7imports_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-article7-imports-list',
        lookup_url_kwarg='submission_pk'
    )

    article7nonpartytrades_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-article7-nonpartytrades-list',
        lookup_url_kwarg='submission_pk'
    )

    article7emissions_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-article7-emissions-list',
        lookup_url_kwarg='submission_pk'
    )

    hat_productions_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-hat-productions-list',
        lookup_url_kwarg='submission_pk'
    )

    hat_imports_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-hat-imports-list',
        lookup_url_kwarg='submission_pk',
    )

    data_others_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-data-others-list',
        lookup_url_kwarg='submission_pk'
    )

    files_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-files-list',
        lookup_url_kwarg='submission_pk'
    )

    sub_info_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-submission-info-list',
        lookup_url_kwarg='submission_pk',
    )
    sub_info = SubmissionInfoSerializer(
        many=False, read_only=True, source='info'
    )

    submission_flags_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-submission-flags-list',
        lookup_url_kwarg='submission_pk',
    )

    submission_remarks = serializers.HyperlinkedIdentityField(
        view_name='core:submission-submission-remarks-list',
        lookup_url_kwarg='submission_pk',
    )

    exemption_nomination_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-exemption-nomination-list',
        lookup_url_kwarg='submission_pk',
    )
    exemption_approved_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-exemption-approved-list',
        lookup_url_kwarg='submission_pk',
    )

    raf_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-raf-list',
        lookup_url_kwarg='submission_pk',
    )

    transfers_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-transfers-list',
        lookup_url_kwarg='submission_pk',
    )

    pa_uses_reported_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-pa-uses-reported-list',
        lookup_url_kwarg='submission_pk',
    )

    # Frontend needs both reporting period name and id.
    reporting_period_id = serializers.SerializerMethodField()
    reporting_period_description = serializers.SerializerMethodField()

    in_initial_state = serializers.SerializerMethodField()

    # Permission-related fields
    available_transitions_url = serializers.HyperlinkedIdentityField(
        view_name='core:submission-submission-transitions-list',
        lookup_url_kwarg='submission_pk'
    )
    available_transitions = serializers.SerializerMethodField()

    is_cloneable = serializers.SerializerMethodField()

    permission_matrix = serializers.SerializerMethodField()

    changeable_flags = serializers.SerializerMethodField()

    can_change_remarks_party = serializers.SerializerMethodField()
    can_change_remarks_secretariat = serializers.SerializerMethodField()

    can_change_reporting_channel = serializers.SerializerMethodField()

    can_upload_files = serializers.SerializerMethodField()

    can_edit_data = serializers.SerializerMethodField()
    can_delete_data = serializers.SerializerMethodField()

    can_change_submitted_at = serializers.SerializerMethodField()
    is_submitted_at_visible = serializers.SerializerMethodField()
    is_submitted_at_mandatory = serializers.SerializerMethodField()

    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    created_by = serializers.StringRelatedField(read_only=True)
    last_edited_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Submission

        base_fields = (
            'id', 'party', 'reporting_period', 'obligation', 'obligation_type',
            'version', 'revision',
            'reporting_period_id', 'reporting_period_description',
            'files', 'files_url',
            'sub_info_url', 'sub_info',
            'submission_flags_url', 'submission_remarks',
            'created_at', 'updated_at', 'submitted_at',
            'created_by', 'last_edited_by',
            'filled_by_secretariat',
            'current_state', 'previous_state', 'in_initial_state',
            'data_changes_allowed', 'is_current',
            'flag_provisional', 'flag_valid',
            'flag_superseded',

            # Permission-related fields; value is dependent on user
            'available_transitions', 'available_transitions_url',
            'is_cloneable', 'is_versionable',
            'permission_matrix',
            'changeable_flags',
            'can_change_remarks_party',
            'can_change_remarks_secretariat',
            'can_change_reporting_channel',
            'can_upload_files',
            'can_edit_data',
            'can_delete_data',
            'can_change_submitted_at',
            'is_submitted_at_visible',
            'is_submitted_at_mandatory',
        )

        per_type_fields = {
            'art7': base_fields + (
                'article7questionnaire_url', 'article7questionnaire',
                'article7destructions_url', 'article7productions_url',
                'article7exports_url', 'article7imports_url',
                'article7nonpartytrades_url', 'article7emissions_url',
                'date_reported_f',
            ),
            'hat': base_fields + (
                'hat_productions_url', 'hat_imports_url',
            ),
            'essencrit': base_fields + ('raf_url',),
            'other': base_fields + (
                'data_others_url',
            ),
            'exemption': base_fields + (
                'exemption_nomination_url', 'exemption_approved_url',
            ),
            'transfer': base_fields + (
                'transfers_url',
            ),
            'procagent': base_fields + (
                'pa_uses_reported_url',
            ),
        }
        # All possible fields still need to be specified here.
        # Otherwise DRF won't load them.
        fields = list(set(sum(per_type_fields.values(), ())))

        read_only_fields = (
            'version', 'revision',
            'is_cloneable', 'is_versionable',
            'available_transitions', 'changeable_flags',
            'can_change_remarks_party', 'can_change_remarks_secretariat',
            'can_change_reporting_channel', 'can_upload_files',
            'can_edit_data', 'can_delete_data',
            'created_by', 'last_edited_by',
        )

    def get_reporting_period_id(self, obj):
        return obj.reporting_period.id

    def get_reporting_period_description(self, obj):
        return obj.reporting_period.description

    def get_obligation_type(self, obj):
        return obj.obligation.obligation_type

    def get_revision(self, obj):
        return '-' if obj.revision_major is None else \
            f'{obj.revision_major}.{obj.revision_minor}'

    def get_in_initial_state(self, obj):
        return obj.in_initial_state

    def get_available_transitions(self, obj):
        user = self.context['request'].user
        return obj.available_transitions(user)

    def get_is_cloneable(self, obj):
        user = self.context['request'].user
        return obj.is_cloneable(user)

    def get_permission_matrix(self, obj):
        user = self.context['request'].user
        return obj.permissions_matrix(user)

    def get_changeable_flags(self, obj):
        user = self.context['request'].user
        flags = set(SubmissionFlagsSerializer.get_dynamic_fields(obj))
        return flags.intersection(obj.get_changeable_flags(user))

    def get_can_change_remarks_party(self, obj):
        user = self.context['request'].user
        return obj.can_change_remark(user, 'remarks_party')

    def get_can_change_remarks_secretariat(self, obj):
        user = self.context['request'].user
        return obj.can_change_remark(user, 'remarks_secretariat')

    def get_can_change_reporting_channel(self, obj):
        user = self.context['request'].user
        return obj.can_change_reporting_channel(user)

    def get_can_upload_files(self, obj):
        user = self.context['request'].user
        return obj.can_upload_files(user)

    def get_can_edit_data(self, obj):
        user = self.context['request'].user
        return obj.can_edit_data(user)

    def get_can_delete_data(self, obj):
        user = self.context['request'].user
        return obj.can_delete_data(user)

    def get_can_change_submitted_at(self, obj):
        user = self.context['request'].user
        return obj.can_change_submitted_at(user)

    def get_is_submitted_at_visible(self, obj):
        user = self.context['request'].user
        return obj.is_submitted_at_visible(user)

    def get_is_submitted_at_mandatory(self, obj):
        user = self.context['request'].user
        return obj.is_submitted_at_mandatory(user)


class CreateSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = (
            'id', 'party', 'reporting_period', 'obligation',
        )

    def create(self, validated_data):
        if 'created_by' not in validated_data:
            validated_data['created_by'] = self.context['request'].user
        if 'last_edited_by' not in validated_data:
            validated_data['last_edited_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'last_edited_by' not in validated_data:
            validated_data['last_edited_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ListSubmissionSerializer(CreateSubmissionSerializer):
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    revision = serializers.SerializerMethodField()
    available_transitions = serializers.SerializerMethodField()
    is_cloneable = serializers.SerializerMethodField()
    can_edit_data = serializers.SerializerMethodField()
    can_delete_data = serializers.SerializerMethodField()

    class Meta(CreateSubmissionSerializer.Meta):
        fields = (
            ('url',)
            + CreateSubmissionSerializer.Meta.fields
            + (
                'created_at', 'updated_at', 'submitted_at',
                'created_by', 'last_edited_by', 'filled_by_secretariat',
                'version', 'revision',
                'current_state', 'previous_state',
                'data_changes_allowed', 'is_current',
                'flag_provisional', 'flag_valid', 'flag_superseded',
                # Permissions-related fields
                'available_transitions', 'is_cloneable', 'is_versionable',
                'can_edit_data', 'can_delete_data',
            )
        )
        extra_kwargs = {'url': {'view_name': 'core:submission-detail'}}

    def get_revision(self, obj):
        return '-' if obj.revision_major is None else \
            f'{obj.revision_major}.{obj.revision_minor}'

    def get_available_transitions(self, obj):
        user = self.context['request'].user
        return obj.available_transitions(user)

    def get_is_cloneable(self, obj):
        user = self.context['request'].user
        return obj.is_cloneable(user)

    def get_can_edit_data(self, obj):
        user = self.context['request'].user
        return obj.can_edit_data(user)

    def get_can_delete_data(self, obj):
        user = self.context['request'].user
        return obj.can_delete_data(user)


class SubmissionHistorySerializer(serializers.ModelSerializer):
    revision = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    current_state = serializers.SerializerMethodField()

    class Meta:
        model = HistoricalSubmission
        fields = (
            'party', 'reporting_period', 'obligation', 'version', 'revision',
            'user', 'date', 'current_state',
            'flag_provisional', 'flag_valid', 'flag_superseded',
            'flag_checked_blanks', 'flag_has_blanks', 'flag_confirmed_blanks',
            'flag_has_reported_a1', 'flag_has_reported_a2',
            'flag_has_reported_b1', 'flag_has_reported_b2',
            'flag_has_reported_b3', 'flag_has_reported_c1',
            'flag_has_reported_c2', 'flag_has_reported_c3',
            'flag_has_reported_e', 'flag_has_reported_f',
        )
        read_only_fields = fields

    def get_revision(self, obj):
        return '-' if obj.revision_major is None else \
            f'{obj.revision_major}.{obj.revision_minor}'

    def get_date(self, obj):
        return obj.history_date.strftime('%Y-%m-%d')

    def get_current_state(self, obj):
        return obj._current_state

    def get_user(self, obj):
        return obj.history_user.username if obj.history_user else None


class AuthTokenByValueSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()
    expires = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = ('token', 'created', 'expires')

    @staticmethod
    def get_token(obj):
        return obj.key

    @staticmethod
    def get_expires(obj):
        return obj.created + settings.TOKEN_EXPIRE_INTERVAL


class AggregationSerializer(serializers.ModelSerializer):
    region = serializers.PrimaryKeyRelatedField(
        source='party.subregion.region.id', read_only=True
    )

    class Meta:
        model = ProdCons
        exclude = ('destroyed', )


class AggregationDestructionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProdCons
        fields = ('id', 'party', 'reporting_period', 'destroyed')


class AggregationMTSerializer(serializers.ModelSerializer):
    region = serializers.PrimaryKeyRelatedField(
        source='party.subregion.region.id', read_only=True
    )
    group = serializers.PrimaryKeyRelatedField(
        source='substance.group', read_only=True
    )

    class Meta:
        model = ProdConsMT
        exclude = ('destroyed', )


class AggregationDestructionMTSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProdConsMT
        fields = ('id', 'party', 'reporting_period', 'destroyed')


class LimitSerializer(serializers.ModelSerializer):

    class Meta:
        model = Limit
        fields = "__all__"


def guess_mimetype(filename, default='application/octet-stream'):
    return mimetypes.guess_type(filename)[0] or default


def generate_report(report, submission):
    party = submission.party
    period = submission.reporting_period
    filename = f"{report}_{party.abbr}_{period.name}.pdf"

    if report == reports.Art7RawdataReport.name:
        cls = reports.Art7RawdataReport

    elif report == reports.ProdConsReport.name:
        cls = reports.ProdConsReport

    else:
        raise ValueError(f"Unknown report type {report!r}")

    report = cls.for_submission(submission)
    data = report.render()
    with open(f'/tmp/{filename}', 'wb') as f:
        f.write(data.getvalue())
    return {
        'title': cls.display_name,
        'filename': filename,
        'data': data.getvalue(),
        'mime_type': 'application/pdf',
    }


class EmailSerializer(serializers.ModelSerializer):

    attachments = serializers.ListField(child=serializers.JSONField())

    class Meta:
        model = Email
        exclude = ('submission',)

    def create(self, validated_data):
        submission = self.context['submission']

        attachments = []
        for attachment in validated_data['attachments']:
            source = attachment['source']

            if source == 'email_template_attachment':
                a = EmailTemplateAttachment.objects.get(pk=attachment['id'])
                with a.file.open('rb') as f:
                    data = f.read()
                mime_type = guess_mimetype(a.filename)
                attachments.append({
                    'title': a.title,
                    'filename': a.filename,
                    'data': data,
                    'mime_type': mime_type,
                })

            elif source == 'generate_report':
                report = generate_report(attachment['id'], submission)
                attachments.append(report)

            else:
                raise ValueError(f"Unknown email attachment source {source!r}")

        email = Email(
            subject=validated_data['subject'],
            body=validated_data['body'],
            to=validated_data['to'],
            from_email=validated_data['from_email'],
            cc=validated_data['cc'],
            submission=submission,
            attachments=[{
                'title': a['title'],
                'size': len(a['data']),
                'filename': a['filename'],
                'mime_type': a['mime_type'],
            } for a in attachments],
        )

        mime_attachments = [
            (a['filename'], a['data'], a['mime_type'])
            for a in attachments
        ]

        email.send_email(mime_attachments)
        email.save()
        return email


class EmailTemplateAttachmentSerializer(serializers.ModelSerializer):

    source = serializers.ReadOnlyField(default='email_template_attachment')

    class Meta:
        model = EmailTemplateAttachment
        fields = ['id', 'filename', 'title', 'source']


class EmailTemplateSerializer(serializers.ModelSerializer):

    attachments = EmailTemplateAttachmentSerializer(many=True, read_only=True)
    generated_attachments = serializers.ReadOnlyField(default=[
        {
            'id': reports.Art7RawdataReport.name,
            'filename': 'art7raw_{party}_{period}.pdf',
            'title': reports.Art7RawdataReport.display_name,
            'source': 'generate_report',
        },
        {
            'id': reports.ProdConsReport.name,
            'filename': 'prodcons_{party}_{period}.pdf',
            'title': reports.ProdConsReport.display_name,
            'source': 'generate_report',
        },
    ])

    class Meta:
        model = EmailTemplate
        fields = "__all__"


class FocalPointSerializer(serializers.ModelSerializer):
    party = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = FocalPoint
        exclude = ('submission',)


class LicensingSystemFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicensingSystemFile
        exclude = ('licensing_system', )


class LicensingSystemURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicensingSystemURL
        exclude = ('licensing_system', )


class LicensingSystemSerializer(serializers.ModelSerializer):
    party = serializers.StringRelatedField(read_only=True)
    iso_alpha3_code = serializers.StringRelatedField(
        source="party.iso_alpha3_code",
        read_only=True,
    )
    party_id = serializers.StringRelatedField(
        source="party.id",
        read_only=True
    )
    files = LicensingSystemFileSerializer(read_only=True, many=True)
    urls = LicensingSystemURLSerializer(read_only=True, many=True)
    date_kigali_ratification = serializers.SerializerMethodField()

    class Meta:
        model = LicensingSystem
        exclude = ('submission', )

    def get_date_kigali_ratification(self, obj):
        return obj.date_kigali_ratification


class WebsiteSerializer(serializers.ModelSerializer):
    party = serializers.StringRelatedField(read_only=True)
    iso_alpha3_code = serializers.StringRelatedField(
        source="party.iso_alpha3_code", read_only=True
    )

    class Meta:
        model = Website
        fields = "__all__"


class OtherCountryProfileDataSerializer(serializers.ModelSerializer):
    party = serializers.StringRelatedField(read_only=True)
    iso_alpha3_code = serializers.StringRelatedField(
        source="party.iso_alpha3_code", read_only=True
    )
    period = serializers.StringRelatedField(source='reporting_period', read_only=True)
    obligation = serializers.StringRelatedField(read_only=True)
    obligation_type = serializers.StringRelatedField(
        source='obligation._obligation_type', read_only=True
    )

    class Meta:
        model = OtherCountryProfileData
        exclude = ('submission', 'reporting_period')


class ReclamationFacilitySerializer(serializers.ModelSerializer):
    party = serializers.StringRelatedField(read_only=True)
    iso_alpha3_code = serializers.StringRelatedField(
        source="party.iso_alpha3_code", read_only=True
    )

    class Meta:
        model = ReclamationFacility
        fields = "__all__"


class IllegalTradeSerializer(serializers.ModelSerializer):
    party = serializers.StringRelatedField(read_only=True)
    iso_alpha3_code = serializers.StringRelatedField(
        source="party.iso_alpha3_code", read_only=True
    )

    class Meta:
        model = IllegalTrade
        fields = "__all__"


class ORMReportSerializer(serializers.ModelSerializer):
    party = serializers.StringRelatedField(read_only=True)
    iso_alpha3_code = serializers.StringRelatedField(
        source="party.iso_alpha3_code", read_only=True
    )
    period = serializers.StringRelatedField(
        source='reporting_period', read_only=True
    )

    class Meta:
        model = ORMReport
        fields = "__all__"


class MultilateralFundSerializer(serializers.ModelSerializer):
    party = serializers.StringRelatedField(read_only=True)
    iso_alpha3_code = serializers.StringRelatedField(
        source="party.iso_alpha3_code", read_only=True
    )

    class Meta:
        model = MultilateralFund
        fields = "__all__"


class TEAPReportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TEAPReportType
        fields = "__all__"


class TEAPIndicativeNumberOfReportsSerializer(serializers.ModelSerializer):
    reporting_period = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = TEAPIndicativeNumberOfReports
        fields = "__all__"


class TEAPReportSerializer(serializers.ModelSerializer):
    report_type = serializers.StringRelatedField(read_only=True)
    reporting_period = serializers.StringRelatedField(read_only=True)
    decision = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = TEAPReport
        fields = "__all__"


class ImpComRecommendationSerializer(serializers.ModelSerializer):
    reporting_period = serializers.StringRelatedField(read_only=True)

    bodies = serializers.StringRelatedField(many=True, read_only=True)
    topics = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = ImpComRecommendation
        fields = "__all__"


class ImpComTopicSerializer(serializers.ModelSerializer):

    class Meta:
        model = ImpComTopic
        fields = "__all__"


class ImpComBodySerializer(serializers.ModelSerializer):

    class Meta:
        model = ImpComBody
        fields = "__all__"


class EssentialCriticalSerializer(serializers.ModelSerializer):
    """
    Used for serializing more detailed information about approved exemptions
    (to be used when presenting them non-aggregated).
    The quantities are presented in ODP tons (as is also the case with
    aggregated data).
    """
    reporting_period = serializers.IntegerField(
        source='submission.reporting_period.id', read_only=True
    )
    party = serializers.IntegerField(
        source='submission.party.id', read_only=True
    )
    group = serializers.IntegerField(
        source='substance.group.id', read_only=True
    )
    region = serializers.IntegerField(
        source='submission.party.subregion.region.id', read_only=True
    )

    quantity_essential = serializers.SerializerMethodField()
    quantity_critical = serializers.SerializerMethodField()

    class Meta:
        model = ExemptionApproved
        fields = (
            'reporting_period', 'group', 'party', 'region',
            'is_article5', 'is_eu_member',
            'decision_approved',
            'substance', 'quantity_essential', 'quantity_critical'
        )

    def get_quantity_critical(self, obj):
        if (
            obj.substance.has_critical_uses
            and obj.quantity is not None
        ):
            odp_gwp = obj.substance.odp_or_gwp
            return obj.quantity * odp_gwp if odp_gwp else None
        return None

    def get_quantity_essential(self, obj):
        if (
            not obj.substance.has_critical_uses
            and obj.quantity is not None
        ):
            odp_gwp = obj.substance.odp_or_gwp
            return obj.quantity * odp_gwp if odp_gwp else None
        return None


class EssentialCriticalMTSerializer(EssentialCriticalSerializer):
    """
    The serializerReturns the essencrit quantities in metric tons.
    """
    def get_quantity_critical(self, obj):
        return obj.quantity if obj.substance.has_critical_uses else None

    def get_quantity_essential(self, obj):
        return obj.quantity if (not obj.substance.has_critical_uses) else None
