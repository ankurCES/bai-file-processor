import os
import tempfile
import warnings
from unittest import TestCase

from bai_file_processor import bai_parser
from bai_file_processor.models import Bai2File

from .test_writers import Bai2FileWriterTestCase

_SAMPLE_BAI2 = (
    '01,CITIDIRECT,8888888,150716,0713,00131100,,,2/\n'
    '02,8888888,CITIGB00,1,150715,2340,GBP,2/\n'
    '03,77777777,GBP,010,10000,,,015,10000,,,/\n'
    '16,191,001,V,150715,,1234567890,RP12312312312312/\n'
    '88,FR:FP SIP INCOMING\n'
    '88,ENDT:20150715\n'
    '88,TRID:RP12312312312312\n'
    '88,PY:RP1231231231231200                 A1234BC 22/03/66\n'
    '88,BI:22222222\n'
    '88,OB:111111 BUCKINGHAM PALACE OB3:BARCLAYS BANK PLC\n'
    '88,BO:11111111 BO1:DOE JO\n'
    '49,20001,10/\n'
    '98,20001,1,12/\n'
    '99,20001,1,14/\n'
)


class ParseTestCase(TestCase):
    def test_parse_from_lines(self):
        lines = [
            '01,CITIDIRECT,8888888,150716,0713,00131100,,,2/',
            '02,8888888,CITIGB00,1,150715,2340,GBP,2/',
            '03,77777777,GBP,010,10000,,,015,10000,,,/',
            '16,191,001,V,150715,,1234567890,RP12312312312312/',
            '88,FR:FP SIP INCOMING',
            '88,ENDT:20150715',
            '88,TRID:RP12312312312312',
            '88,PY:RP1231231231231200                 A1234BC 22/03/66',
            '88,BI:22222222',
            '88,OB:111111 BUCKINGHAM PALACE OB3:BARCLAYS BANK PLC',
            '88,BO:11111111 BO1:DOE JO',
            '49,20001,10/',
            '98,20001,1,12/',
            '99,20001,1,14/',
        ]

        bai2_file = bai_parser.parse_from_lines(lines)
        self.assertTrue(isinstance(bai2_file, Bai2File))

    def test_parse_from_string(self):
        bai2_file = bai_parser.parse_from_string(_SAMPLE_BAI2)
        self.assertTrue(isinstance(bai2_file, Bai2File))

    def test_parse_from_file(self):
        file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'citi_example.bai2')
        if not os.path.exists(file_path):
            self.skipTest('citi_example.bai2 fixture not present')
        bai2_file = bai_parser.parse_from_file(file_path)
        self.assertTrue(isinstance(bai2_file, Bai2File))

    def test_parse_from_file_2(self):
        file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'nwb_example.bai2')
        if not os.path.exists(file_path):
            self.skipTest('nwb_example.bai2 fixture not present')
        bai2_file = bai_parser.parse_from_file(file_path)
        self.assertTrue(isinstance(bai2_file, Bai2File))

    def test_as_string(self):
        original = (
            '01,CITIDIRECT,8888888,150716,0713,00131100,,,2/\n'
            '02,8888888,CITIGB00,1,150715,2340,GBP,2/\n'
            '03,77777777,GBP,010,10000,,,015,10000,,,/\n'
            '16,191,001,V,150715,,1234567890,RP12312312312312/\n'
            '88,FR:FP SIP INCOMING\n'
            '88,ENDT:20150715\n'
            '88,TRID:RP12312312312312\n'
            '88,PY:RP1231231231231200                 A1234BC 22/03/66\n'
            '88,BI:22222222\n'
            '88,OB:111111 BUCKINGHAM PALACE OB3:BARCLAYS BANK PLC\n'
            '88,BO:11111111 BO1:DOE JO\n'
            '49,20001,10/\n'
            '98,20001,1,12/\n'
            '99,20001,1,14/'
        )

        bai2_file = bai_parser.parse_from_string(original)
        self.assertTrue(isinstance(bai2_file, Bai2File))

        from_model = bai2_file.as_string()
        self.assertEqual(original, from_model)

    def test_extract_bai_components_returns_four_tuples(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bai2', delete=False) as f:
            f.write(_SAMPLE_BAI2)
            tmp_path = f.name
        try:
            header, grp_header, transactions, summaries = bai_parser.extract_bai_components(tmp_path)
            self.assertIsInstance(header, dict)
            self.assertIsInstance(grp_header, dict)
            self.assertIsInstance(transactions, list)
            self.assertIsInstance(summaries, list)
            self.assertIn('Sender ID', header)
            self.assertIn('Originator ID', grp_header)
        finally:
            os.unlink(tmp_path)

    def test_create_csv_file_writes_files(self):
        transactions = [{'Customer Account Number': '123', 'Amount': 100}]
        summaries = [{'BAI Code': '010', 'Amount': 10000}]
        with tempfile.TemporaryDirectory() as tmp_dir:
            bai_parser.create_csv_file(tmp_dir, transactions, summaries)
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'transactions.csv')))
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, 'summary.csv')))


    def test_parse_type_code_158_ach_reversal_credit(self):
        bai2_with_158 = (
            '01,TESTBANK,8888888,150716,0713,00131100,,,2/\n'
            '02,8888888,TESTBANK,1,150715,2340,GBP,2/\n'
            '03,77777777,GBP,010,10000,,,015,10000,,,/\n'
            '16,158,5000,0,,,ACH REVERSAL/\n'
            '49,25000,3/\n'
            '98,25000,1,5/\n'
            '99,25000,1,7/\n'
        )
        bai2_file = bai_parser.parse_from_string(bai2_with_158, check_integrity=False)
        self.assertIsInstance(bai2_file, Bai2File)
        transaction = bai2_file.children[0].children[0].children[0]
        self.assertEqual(transaction.type_code.code, '158')
        self.assertEqual(transaction.type_code.description, 'ACH Reversal Credit')

    def test_parse_unknown_type_code_does_not_crash(self):
        bai2_with_unknown = (
            '01,TESTBANK,8888888,150716,0713,00131100,,,2/\n'
            '02,8888888,TESTBANK,1,150715,2340,GBP,2/\n'
            '03,77777777,GBP,010,10000,,,015,10000,,,/\n'
            '16,999,1000,0,,,UNKNOWN TXN/\n'
            '49,21000,3/\n'
            '98,21000,1,5/\n'
            '99,21000,1,7/\n'
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            bai2_file = bai_parser.parse_from_string(bai2_with_unknown, check_integrity=False)
        self.assertIsInstance(bai2_file, Bai2File)
        self.assertTrue(any('999' in str(w.message) for w in caught))


class WriteTestCase(TestCase):
    def test_write(self):
        bai2_file = Bai2FileWriterTestCase.create_bai2_file()

        output = bai_parser.write(bai2_file)
        self.assertEqual(
            output,
            (
                '01,CITIDIRECT,8888888,150715,2340,00131100,,,2/\n'
                '02,8888888,CITIGB00,1,150715,2340,GBP,2/\n'
                '03,77777777,GBP,010,10000,,,015,10000,,/\n'
                '16,399,2599,,,,BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS\n'
                '88, BILLS\n'
                '16,399,1000,0,,,OTHER\n'
                '49,23599,5/\n'
                '03,77777777,GBP,010,10000,,,015,10000,,/\n'
                '16,399,2599,,,,BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS\n'
                '88, BILLS\n'
                '16,399,1000,0,,,OTHER\n'
                '49,23599,5/\n'
                '98,47198,2,12/\n'
                '02,8888888,CITIGB00,1,150715,2340,GBP,2/\n'
                '03,77777777,GBP,010,10000,,,015,10000,,/\n'
                '16,399,2599,,,,BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS\n'
                '88, BILLS\n'
                '16,399,1000,0,,,OTHER\n'
                '49,23599,5/\n'
                '03,77777777,GBP,010,10000,,,015,10000,,/\n'
                '16,399,2599,,,,BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS BILLS\n'
                '88, BILLS\n'
                '16,399,1000,0,,,OTHER\n'
                '49,23599,5/\n'
                '98,47198,2,12/\n'
                '99,94396,2,26/'
            )
        )
