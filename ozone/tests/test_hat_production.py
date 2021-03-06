from django.urls import reverse
from django.contrib.auth.hashers import Argon2PasswordHasher

from ozone.core.models import HighAmbientTemperatureProduction, Submission

from .base import BaseTests
from .factories import (
    PartyFactory,
    RegionFactory,
    LanguageEnFactory,
    ReportingChannelFactory,
    SecretariatUserFactory,
    SubmissionFactory,
    SubregionFactory,
    SubstanceFactory,
    AnotherSubstanceFactory,
    AnotherPartyFactory,
    HighAmbientTemperatureProductionFactory,
    ObligationFactory,
)


class BaseHATProductionTest(BaseTests):
    def setUp(self):
        super().setUp()
        self.workflow_class = "default"

        self.obligation = ObligationFactory(_obligation_type="hat")
        self.region = RegionFactory.create()
        self.subregion = SubregionFactory.create(region=self.region)
        self.party = PartyFactory(subregion=self.subregion)
        self.another_party = AnotherPartyFactory(subregion=self.subregion)
        self.language = LanguageEnFactory()

        hash_alg = Argon2PasswordHasher()
        self.secretariat_user = SecretariatUserFactory(
            language=self.language,
            password=hash_alg.encode(password="qwe123qwe", salt="123salt123")
        )
        self.client.login(username=self.secretariat_user.username, password='qwe123qwe')

        self.substance = SubstanceFactory()
        self.another_substance = AnotherSubstanceFactory()
        ReportingChannelFactory()

    def create_submission(self, **kwargs):
        if "obligation" not in kwargs:
            kwargs["obligation"] = self.obligation

        submission = SubmissionFactory(
            party=self.party, created_by=self.secretariat_user,
            last_edited_by=self.secretariat_user, **kwargs
        )
        return submission


HAT_PROD_DATA = {
    'quantity_msac': 100,
    'quantity_sdac': 101,
    'quantity_dcpac': 102,
    'remarks_os': 'nothing to remark OS',
    'remarks_party': 'nothing to remark'
}


class TestHATProduction(BaseHATProductionTest):

    def test_create(self):
        submission = self.create_submission()

        data = dict(HAT_PROD_DATA)
        data["substance"] = self.substance.id

        result = self.client.post(
            reverse(
                "core:submission-hat-productions-list",
                kwargs={"submission_pk": submission.pk},
            ),
            [data],
        )
        self.assertEqual(result.status_code, 201, result.json())

    def test_create_wrong_obligation(self):
        obligation = ObligationFactory.create(_obligation_type="art7", name="Much obliged")
        submission = self.create_submission(obligation=obligation)

        data = dict(HAT_PROD_DATA)
        data["substance"] = self.substance.id

        result = self.client.post(
            reverse(
                "core:submission-hat-productions-list",
                kwargs={"submission_pk": submission.pk},
            ),
            [data],
        )
        self.assertEqual(result.status_code, 403, result.json())

    def test_create_multiple(self):
        submission = self.create_submission()

        data1 = dict(HAT_PROD_DATA)
        data1["substance"] = self.substance.id

        data2 = dict(HAT_PROD_DATA)
        data2["substance"] = self.another_substance.id

        result = self.client.post(
            reverse(
                "core:submission-hat-productions-list",
                kwargs={"submission_pk": submission.pk},
            ),
            [data1, data2],
        )
        self.assertEqual(result.status_code, 201, result.json())

    def test_create_multiple_duplicate(self):
        submission = self.create_submission()

        data1 = dict(HAT_PROD_DATA)
        data1["substance"] = self.substance.id

        data2 = dict(HAT_PROD_DATA)
        data2["substance"] = self.substance.id

        result = self.client.post(
            reverse(
                "core:submission-hat-productions-list",
                kwargs={"submission_pk": submission.pk},
            ),
            [data1, data2],
        )
        self.assertEqual(result.status_code, 422, result.json())

    def test_get(self):
        submission = self.create_submission()

        hat_prod = HighAmbientTemperatureProductionFactory(
            submission=submission, substance=self.substance,
            **HAT_PROD_DATA
        )

        result = self.client.get(
            reverse(
                "core:submission-hat-productions-list",
                kwargs={"submission_pk": submission.pk},
            ),
        )
        self.assertEqual(result.status_code, 200, result.json())

        expected_data = dict(HAT_PROD_DATA)
        expected_data["substance"] = self.substance.id
        expected_data["id"] = hat_prod.id
        expected_data["ordering_id"] = 0
        expected_data["group"] = ''

        self.assertEqual(result.json(), [expected_data])

    def test_update(self):
        submission = self.create_submission()

        hat_prod = HighAmbientTemperatureProductionFactory(
            submission=submission, substance=self.substance,
            **HAT_PROD_DATA
        )

        data = dict(HAT_PROD_DATA)
        data["substance"] = self.substance.id
        data["quantity_msac"] = 42

        result = self.client.put(
            reverse(
                "core:submission-hat-productions-list",
                kwargs={"submission_pk": submission.pk},
            ),
            [data],
        )
        self.assertEqual(result.status_code, 200, result.json())

        hat_prod = HighAmbientTemperatureProduction.objects.get(pk=hat_prod.id)
        self.assertEqual(hat_prod.quantity_msac, 42)

    def test_update_multiple(self):
        submission = self.create_submission()

        hat_prod = HighAmbientTemperatureProductionFactory(
            submission=submission, substance=self.substance,
            **HAT_PROD_DATA
        )

        data1 = dict(HAT_PROD_DATA)
        data1["substance"] = self.substance.id
        data1["quantity_msac"] = 42

        data2 = dict(HAT_PROD_DATA)
        data2["substance"] = self.another_substance.id
        data2["quantity_msac"] = 42

        result = self.client.put(
            reverse(
                "core:submission-hat-productions-list",
                kwargs={"submission_pk": submission.pk},
            ),
            [data1, data2],
        )
        self.assertEqual(result.status_code, 200, result.json())

        hat_prod1 = submission.highambienttemperatureproductions.get(
            substance_id=self.substance.id
        )
        hat_prod2 = submission.highambienttemperatureproductions.get(
            substance_id=self.another_substance.id
        )
        self.assertEqual(hat_prod1.quantity_msac, 42)
        self.assertEqual(hat_prod2.quantity_msac, 42)

    def test_update_multiple_duplicate(self):
        submission = self.create_submission()

        hat_prod = HighAmbientTemperatureProductionFactory(
            submission=submission, substance=self.substance,
            **HAT_PROD_DATA
        )

        data1 = dict(HAT_PROD_DATA)
        data1["substance"] = self.substance.id
        data1["quantity_msac"] = 42

        data2 = dict(HAT_PROD_DATA)
        data2["substance"] = self.substance.id
        data2["quantity_msac"] = 42

        result = self.client.put(
            reverse(
                "core:submission-hat-productions-list",
                kwargs={"submission_pk": submission.pk},
            ),
            [data1, data2],
        )
        self.assertEqual(result.status_code, 422, result.json())

    def test_update_immutable(self):
        submission = self.create_submission()
        hat_prod = HighAmbientTemperatureProductionFactory(
            submission=submission, substance=self.substance,
            **HAT_PROD_DATA
        )
        submission._current_state = "finalized"
        submission.save()

        data = dict(HAT_PROD_DATA)
        data["substance"] = self.substance.id
        data["quantity_msac"] = 42

        result = self.client.put(
            reverse(
                "core:submission-hat-productions-list",
                kwargs={"submission_pk": submission.pk},
            ),
            [data],
        )
        self.assertEqual(result.status_code, 422, result.json())

    def test_clone(self):
        submission = self.create_submission()

        hat_prod = HighAmbientTemperatureProductionFactory(
            submission=submission, substance=self.substance,
            **HAT_PROD_DATA
        )
        submission._current_state = "finalized"
        submission.save()

        result = self.client.post(
            reverse(
                "core:submission-clone",
                kwargs={"pk": submission.pk},
            ),
        )
        self.assertEqual(result.status_code, 200, result.json())
        new_id = result.json()['url'].split("/")[-2]

        new_hat = Submission.objects.get(pk=new_id).highambienttemperatureproductions.first()
        self.assertEqual({
            'quantity_msac': new_hat.quantity_msac,
            'quantity_sdac': new_hat.quantity_sdac,
            'quantity_dcpac': new_hat.quantity_dcpac,
            'remarks_os': new_hat.remarks_os,
            'remarks_party': new_hat.remarks_party,
        }, HAT_PROD_DATA)
