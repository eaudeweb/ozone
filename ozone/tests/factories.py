from datetime import datetime
from factory import SubFactory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

from ozone.core.models import (
    Annex,
    Blend,
    Group,
    Meeting,
    Obligation,
    Party,
    Region,
    ReportingPeriod,
    Submission,
    Subregion,
    Treaty,
)


User = get_user_model()


class RegionFactory(DjangoModelFactory):
    abbr = 'TR'
    name = 'Test Region'

    class Meta:
        model = Region


class SubregionFactory(DjangoModelFactory):
    abbr = 'TS'
    name = 'Test Subregion'
    region = SubFactory(RegionFactory)

    class Meta:
        model = Subregion


class PartyFactory(DjangoModelFactory):
    abbr = 'TP'
    name = 'Test Party'
    subregion = SubFactory(SubregionFactory)

    class Meta:
        model = Party


class AnotherPartyFactory(DjangoModelFactory):
    abbr = 'AP'
    name = 'Another Party'
    subregion = SubFactory(SubregionFactory)

    class Meta:
        model = Party


class SecretariatUserFactory(DjangoModelFactory):
    is_secretariat = True
    is_read_only = False
    username = 'secretariat'
    email = 'secretariat@example.com'

    class Meta:
        model = User


class SecretariatUserROFactory(DjangoModelFactory):
    is_secretariat = True
    is_read_only = True
    username = 'secretariat_ro'
    email = 'secretariat_ro@example.com'

    class Meta:
        model = User


class ReporterUserFactory(DjangoModelFactory):
    is_secretariat = False
    is_read_only = False
    username = 'reporter'
    email = 'reporter@example.com'

    class Meta:
        model = User


class ReporterUserSamePartyFactory(DjangoModelFactory):
    is_secretariat = False
    is_read_only = False
    username = 'reporter_same_party'
    email = 'reporter_same_party@example.com'

    class Meta:
        model = User


class ReporterUserAnotherPartyFactory(DjangoModelFactory):
    is_secretariat = False
    is_read_only = False
    username = 'reporter_another_party'
    email = 'reporter_another_party@example.com'

    class Meta:
        model = User


class ObligationFactory(DjangoModelFactory):
    name = 'Test Obligation'

    class Meta:
        model = Obligation


class ReportingPeriodFactory(DjangoModelFactory):
    name = '2018'
    start_date = datetime.strptime('2018-01-01', '%Y-%m-%d')
    end_date = datetime.strptime('2018-12-31', '%Y-%m-%d')

    class Meta:
        model = ReportingPeriod


class SubmissionFactory(DjangoModelFactory):
    obligation = SubFactory(ObligationFactory)
    reporting_period = SubFactory(ReportingPeriodFactory)

    class Meta:
        model = Submission


class MeetingFactory(DjangoModelFactory):
    meeting_id = 'TM'
    location = "Test"
    description = "Test"

    class Meta:
        model = Meeting


class TreatyFactory(DjangoModelFactory):
    treaty_id = 'TT'
    name = 'Test Treaty'
    meeting_id = SubFactory(MeetingFactory)
    date = datetime.strptime('2018-01-01', '%Y-%m-%d')
    entry_into_force_date = datetime.strptime('2020-01-01', '%Y-%m-%d')

    class Meta:
        model = Treaty


class AnnexFactory(DjangoModelFactory):
    annex_id = 'TA'
    name = 'Test Annex'

    class Meta:
        model = Annex


class GroupFactory(DjangoModelFactory):
    group_id = 'TG'
    annex = SubFactory(AnnexFactory)
    name = 'Test Group'

    class Meta:
        model = Group


class BlendFactory(DjangoModelFactory):
    blend_id = 'TB'
    type = 'Zeotrope'
    composition = 'TEST'

    class Meta:
        model = Blend
