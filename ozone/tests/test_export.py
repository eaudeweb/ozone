from decimal import Decimal as D
from pathlib import Path
from tempfile import TemporaryDirectory
from django.contrib.auth.hashers import Argon2PasswordHasher
from django.test import tag
from ozone.core.management.commands import import_submissions
from ozone.core.management.commands import export_submissions
from ozone.core.utils.spreadsheet import OzoneSpreadsheet
from .base import BaseTests
from . import factories
from .fixtures_for_importing import get_required_fixtures
from .fixtures_for_importing import create_fixtures

examples = Path(__file__).resolve().parent / 'examples'

NUMERIC_COLUMNS = [
    'Imported',
    'Exported',
    'Produced',
    'Destroyed',
    'NonPartyTrade',
    'Emitted',
    'SubstID',
    'ExpEssenUse',
    'ExpFeedstock',
    'ExpNew',
    'ExpPolyol',
    'ExpProcAgent',
    'ExpQuarAppl',
    'ExpRecov',
    'Export',
    'ImpEssenUse',
    'ImpFeedstock',
    'ImpLabUse',
    'ImpNew',
    'ImpPolyol',
    'ImpProcAgent',
    'ImpQuarAppl',
    'ImpRecov',
    'Import',
    'NPTExpNew',
    'NPTExpRecov',
    'NPTImpNew',
    'NPTImpRecov',
    'ProdAllNew',
    'ProdArt5',
    'ProdEssenUse',
    'ProdFeedstock',
    'ProdLabUse',
    'ProdProcAgent',
    'ProdQuarAppl',
]


def invoke_import_submissions(**kwargs):
    kwargs = dict({
        'recreate': False,
        'purge': False,
        'limit': None,
        'precision': 10,
        'use_cache': False,
        'dry_run': False,
        'single': False,
        'verbosity': 1,
    }, **kwargs)
    cmd = import_submissions.Command()
    cmd.handle(**kwargs)


def invoke_export_submissions(**kwargs):
    kwargs = dict({
        'verbosity': 1,
    }, **kwargs)
    cmd = export_submissions.Command()
    cmd.handle(**kwargs)


def normalize_for_test(spreadsheet):
    for sheet in spreadsheet.tables.values():
        for row in sheet.rows:
            for col in ['UserCreate', 'UserUpdate',
                        'DateCreate', 'DateUpdate', 'TS']:
                row[col] = None

            for col in NUMERIC_COLUMNS:
                if col in row and row[col] == 0:
                    row[col] = None

    for row in spreadsheet.tables['Overall'].rows:
        row['DateReported'] = row['DateReported'].date()
        for col in ['Blanks', 'Checked_Blanks', 'Confirm_Blanks']:
            row[col] = int(bool(row[col]))

    for name in ['Import', 'NonPartyTrade']:
        for row in spreadsheet.tables[name].rows:
            row['Remark'] = ''


def sorted_rows(sheet):
    def value(row, col):
        default = 0 if col in NUMERIC_COLUMNS else ''
        return row[col] or default

    def sort_key(row):
        return tuple(value(row, c) for c in sheet.header)
    return sorted(sheet.rows, key=sort_key)


def assert_spreadsheets_are_same(s1, s2):
    s1_sheets = list(s1.tables)
    s2_sheets = list(s2.tables)
    assert s1_sheets == s2_sheets, "Sheet names differ"
    for name in s1_sheets:
        t1 = s1.tables[name]
        t2 = s2.tables[name]
        assert t1.header == t2.header, f"Headers differ for sheet {name}"
        assert sorted_rows(t1) == sorted_rows(t2), f"Rows differ for sheet {name}\n{sorted_rows(t1)};\n{sorted_rows(t2)}"
        assert t1.rows == t2.rows, f"Row order differs for sheet {name}"


class ExportTest(BaseTests):

    def setUp(self):
        super().setUp()
        self.language = factories.LanguageEnFactory()
        hash_alg = Argon2PasswordHasher()
        self.secretariat_user = factories.SecretariatUserFactory(
            language=self.language,
            password=hash_alg.encode(password="qwe123qwe", salt="123salt123"),
        )
        self.subregion = factories.SubregionFactory()
        factories.ReportingChannelFactory(name="Legacy")
        factories.ObligationFactory(pk=1)

    @tag('export')
    def test_export_submissions_imports(self):
        in_path = examples / 'art7_submissions.xlsx'
        in_data = OzoneSpreadsheet.from_xlsx(in_path)
        blend_list = [
            (369, [
                (101, D('0.3')),
                (102, D('0.7')),
            ]),
        ]
        fixtures = get_required_fixtures(in_data, blend_list=blend_list)
        create_fixtures(self.subregion, **fixtures)
        invoke_import_submissions(file=in_path)

        with TemporaryDirectory() as tmp:
            out_path = Path(tmp) / 'out.xlsx'
            invoke_export_submissions(path=out_path)
            out_data = OzoneSpreadsheet.from_xlsx(out_path)

            normalize_for_test(in_data)
            normalize_for_test(out_data)
            assert_spreadsheets_are_same(in_data, out_data)
