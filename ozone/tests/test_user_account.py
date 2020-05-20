from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import Argon2PasswordHasher

from .base import BaseTests
from .factories import (
    PartyFactory,
    AnotherPartyFactory,
    ReporterUserFactory,
    SubregionFactory,
    RegionFactory,
    ReportingChannelFactory,
    LanguageEnFactory,
    LanguageFrFactory,
    SecretariatUserFactory,
    ReporterUserSamePartyFactory,
    ReporterUserAnotherPartyFactory,
)

User = get_user_model()


REPORTER_ACCOUNT_DATA = {
    'email': 'reporter@example.com',
    'first_name': 'Test',
    'last_name': 'Test',
    'role': 'Party Reporter',
    'is_secretariat': False,
    'is_read_only': False
}


class UserAccountTests(BaseTests):

    def setUp(self):
        super().setUp()
        hash_alg = Argon2PasswordHasher()
        region = RegionFactory.create()
        subregion = SubregionFactory.create(region=region)
        party = PartyFactory.create(subregion=subregion)
        another_party = AnotherPartyFactory(subregion=subregion)
        self.language_en = LanguageEnFactory()
        self.language_fr = LanguageFrFactory()
        self.reporter = ReporterUserFactory.create(
            first_name='Test',
            last_name='Test',
            email='reporter@example.com',
            language=self.language_en,
            party=party,
            password=hash_alg.encode(password='qwe123qwe', salt='123salt123'),
        )
        self.reporter_same_party = ReporterUserSamePartyFactory(
            language=self.language_en,
            party=party,
            password=hash_alg.encode(password='qwe123qwe', salt='123salt123')
        )
        self.reporter_another_party = ReporterUserAnotherPartyFactory(
            language=self.language_en,
            party=another_party,
            password=hash_alg.encode(password='qwe123qwe', salt='123salt123')
        )
        self.secretariat_user = SecretariatUserFactory(
            language=self.language_en,
            password=hash_alg.encode(password='qwe123qwe', salt='123salt123')
        )

        self.client.login(username=self.reporter.username, password='qwe123qwe')
        ReportingChannelFactory()

    def test_get_user_account_owner(self):
        """
        Test viewing my account details.
        """
        result = self.client.get(
            reverse(
                "core:current_user-detail",
                kwargs={"pk": self.reporter.pk}
            )
        )
        self.assertEqual(result.status_code, 200)
        expected_data = dict(REPORTER_ACCOUNT_DATA)
        expected_data['id'] = self.reporter.pk
        expected_data['username'] = self.reporter.username
        expected_data['party'] = self.reporter.party.pk
        expected_data['party_name'] = self.reporter.party.name
        expected_data['language'] = self.reporter.language.iso
        expected_data['impersonated_by'] = None
        expected_data['related_parties'] = [self.reporter.party.pk]
        expected_data['is_cap'] = False
        expected_data['is_mobile_app'] = False
        self.assertEqual(result.json(), expected_data)

    def test_get_user_account_secretariat(self):
        """
        Test viewing account details of a secretariat user using a party reporter.
        We will test only the permissions in this case, so it is not necessary
        to fill all the details. Just `username` will do in this case.
        """
        result = self.client.get(
            reverse(
                "core:current_user-detail",
                kwargs={"pk": self.secretariat_user.pk}
            )
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['username'], self.secretariat_user.username)

    def test_get_user_account_same_party(self):
        """
        Test viewing account details of a party reporter from the same party.
        We will test only the permissions, just we did before.
        """
        result = self.client.get(
            reverse(
                "core:current_user-detail",
                kwargs={"pk": self.reporter_same_party.pk}
            )
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['username'], self.reporter_same_party.username)

    def test_get_user_account_another_party(self):
        """
        Test viewing account details of a party reporter from the another party.
        We will test only the permissions, just we did before.
        """
        result = self.client.get(
            reverse(
                "core:current_user-detail",
                kwargs={"pk": self.reporter_another_party.pk}
            )
        )
        self.assertEqual(result.status_code, 403)

    def test_update_user_account_owner(self):
        data = dict(REPORTER_ACCOUNT_DATA)
        data['email'] = 'reporter_edited@example.com'
        data['first_name'] = 'Test Edited'
        data['last_name'] = 'Test Edited'
        data['language'] = self.language_fr.iso

        result = self.client.put(
            reverse(
                "core:current_user-detail",
                kwargs={"pk": self.reporter.pk}
            ),
            data
        )
        self.assertEqual(result.status_code, 200)
        user = User.objects.get(pk=self.reporter.pk)
        self.assertEqual(user.email, 'reporter_edited@example.com')
        self.assertEqual(user.first_name, 'Test Edited')
        self.assertEqual(user.last_name, 'Test Edited')
        self.assertEqual(user.language, self.language_fr)

    def test_update_user_account_secretariat(self):
        result = self.client.put(
            reverse(
                "core:current_user-detail",
                kwargs={"pk": self.secretariat_user.pk}
            ),
            dict()
        )
        self.assertEqual(result.status_code, 403)

    def test_update_user_account_same_party(self):
        result = self.client.put(
            reverse(
                "core:current_user-detail",
                kwargs={"pk": self.reporter_same_party.pk}
            ),
            dict()
        )
        self.assertEqual(result.status_code, 403)

    def test_update_user_account_another_party(self):
        result = self.client.put(
            reverse(
                "core:current_user-detail",
                kwargs={"pk": self.reporter_another_party.pk}
            ),
            dict()
        )
        self.assertEqual(result.status_code, 403)
