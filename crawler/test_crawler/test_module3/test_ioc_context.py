import unittest
from unittest.mock import patch
from crawler.module3 import ioc_context
import re


class MockAPT:
    def __init__(self, name, aliases):
        self.name = name
        self.aliases = aliases


class MockCountry:
    def __init__(self, name):
        self.name = name

class Testioc_contextExtractIOCsFromText(unittest.TestCase):
    """Testfälle für die extract_iocs_from_text Funktion."""

    def setUp(self):
        """Wird vor jedem Test aufgerufen, um globale Variablen sauber zurückzusetzen."""
        ioc_context.COMPILED_APT_REGEX = None
        ioc_context.APT_NAME_MAP = {}
        ioc_context.COMPILED_COUNTRY_REGEX = None

    def tearDown(self):
        """Wird nach jedem Test aufgerufen, um aufzuräumen."""
        self.setUp()

    def assertIOCOccurs(self, ioc_list, expected_value, expected_type):
        """Hilfsmethode, um zu prüfen, ob ein bestimmter IOC gefunden wurde."""
        for ioc in ioc_list:
            if ioc['ioc_value'] == expected_value and ioc['ioc_type'] == expected_type:
                return True
        self.fail(f"IOC {expected_value} (Typ: {expected_type}) nicht in der Ergebnisliste gefunden.")

    def assertNormalizedAPT(self, ioc_list, expected_value, expected_normalized):
        for ioc in ioc_list:
            if ioc['ioc_value'] == expected_value and \
               ioc['ioc_type'] == "apt_group_mention" and \
               ioc['normalized_value'] == expected_normalized:
                return True
        self.fail(f"APT {expected_value} (Norm: {expected_normalized}) nicht in der Ergebnisliste gefunden.")

class Testioc_contextRefangIOC(unittest.TestCase):
    def test_refang_ip_defanged_brackets(self):
        self.assertEqual(ioc_context.refang_ioc("192[.]168[.]1[.]1", "ipv4"), "192.168.1.1")

    def test_refang_ip_defanged_parentheses(self):
        self.assertEqual(ioc_context.refang_ioc("10(.)0(.)0(.)1", "ipv4"), "10.0.0.1")

    def test_refang_ip_defanged_spaces(self):
        self.assertEqual(ioc_context.refang_ioc("172 16 0 1", "ipv4"), "172.16.0.1")

    def test_refang_domain_defanged_brackets(self):
        self.assertEqual(ioc_context.refang_ioc("example[.]com", "domain"), "example.com")

    def test_refang_domain_hxxp(self):
        self.assertEqual(ioc_context.refang_ioc("hxxp://example[.]com/path", "domain"), "http://example.com/path")

    def test_refang_domain_hxxps(self):
        self.assertEqual(ioc_context.refang_ioc("hxxps://sub[.]example(.)org", "domain"), "https://sub.example.org")

    def test_refang_domain_trailing_dot(self):
        self.assertEqual(ioc_context.refang_ioc("example.com.", "domain"), "example.com")

    def test_refang_already_refanged(self):
        self.assertEqual(ioc_context.refang_ioc("10.20.30.40", "ipv4"), "10.20.30.40")

    def test_refang_ipv6_defanged_brackets(self):
        self.assertEqual(ioc_context.refang_ioc("2001[:]0db8[:]85a3[:]0000[:]0000[:]8a2e[:]0370[:]7334", "ipv6"),
                         "2001:0db8:85a3:0000:0000:8a2e:0370:7334")

    def test_refang_email_defanged_at_and_dot(self):
        self.assertEqual(ioc_context.refang_ioc("user[@]example[.]com", "email"), "user@example.com")


class Testioc_contextExtractIOCsFromText(unittest.TestCase):
    def setUp(self):
        """Wird vor jedem Test aufgerufen, um die globalen Regex-Variablen zurückzusetzen."""
        ioc_context.COMPILED_APT_REGEX = None
        ioc_context.APT_NAME_MAP = {}
        ioc_context.COMPILED_COUNTRY_REGEX = None

    def assertIOCOccurs(self, ioc_list, expected_value, expected_type, expected_index=0):
        for ioc in ioc_list:
            if ioc['ioc_value'] == expected_value and ioc['ioc_type'] == expected_type and ioc[
                'source_article_index'] == expected_index:
                return True
        self.fail(f"IOC {expected_value} (Typ: {expected_type}) nicht in {ioc_list} gefunden.")

    def assertNormalizedAPT(self, ioc_list, expected_value, expected_normalized, expected_index=0):
        for ioc in ioc_list:
            if ioc['ioc_value'] == expected_value and \
                    ioc['ioc_type'] == "apt_group_mention" and \
                    ioc['normalized_value'] == expected_normalized and \
                    ioc['source_article_index'] == expected_index:
                return True
        self.fail(f"APT {expected_value} (Norm: {expected_normalized}) nicht in {ioc_list} gefunden.")

    @patch('crawler.module3.ioc_context.load_and_compile_apt_regex')
    @patch('crawler.module3.ioc_context.load_and_compile_country_regex')
    def test_extract_no_iocs(self, mock_load_countries, mock_load_apts):
        mock_load_apts.return_value = None
        mock_load_countries.return_value = None
        ioc_context.COMPILED_APT_REGEX = re.compile(r'a^')
        ioc_context.COMPILED_COUNTRY_REGEX = re.compile(r'a^')

        text = "This is a benign text with no indicators."
        iocs = ioc_context.extract_iocs_from_text(text, 0)
        self.assertEqual(len(iocs), 0)

    @patch('crawler.module3.ioc_context.DatabaseHandler')
    def test_extract_apts_and_countries_success(self, mock_db_handler_class):
        """
        Testet die erfolgreiche Erkennung von APTs und Ländern, wenn die DB Daten liefert.
        """
        print("\n[Test] Führe test_extract_apts_and_countries_success aus...")

        mock_apts = [
            MockAPT(name="APT28", aliases="Fancy Bear,Strontium"),
            MockAPT(name="Lazarus Group", aliases="")
        ]
        mock_countries = [MockCountry(name="North Korea"), MockCountry(name="Russia"), MockCountry(name="China")]

        mock_db_handler_instance = mock_db_handler_class.return_value
        mock_db_handler_instance.Session().__enter__().query().all.side_effect = [mock_apts, mock_countries]

        ioc_context.load_and_compile_apt_regex(mock_db_handler_instance)
        ioc_context.load_and_compile_country_regex(mock_db_handler_instance)

        text = ("Attribution points to APT 28, also known as Fancy Bear. "
                "Another group, Lazarus Group, is active in North Korea and Russia. China is also mentioned.")
        article_idx = 4
        iocs = ioc_context.extract_iocs_from_text(text, article_idx)

        self.assertNormalizedAPT(iocs, "APT 28", "APT28", article_idx)
        self.assertNormalizedAPT(iocs, "Fancy Bear", "APT28", article_idx)
        self.assertNormalizedAPT(iocs, "Lazarus Group", "Lazarus Group", article_idx)

        self.assertIOCOccurs(iocs, "North Korea", "country_mention", article_idx)
        self.assertIOCOccurs(iocs, "Russia", "country_mention", article_idx)
        self.assertIOCOccurs(iocs, "China", "country_mention", article_idx)

    def test_context_snippet(self):
        """
        Testet, ob der Kontext-Snippet korrekt extrahiert wird.
        Initialisiert die Regex-Variablen, damit der Test nicht fehlschlägt.
        """
        print("\n[Test] Führe test_context_snippet aus...")
        ioc_context.COMPILED_APT_REGEX = re.compile(r'a^')
        ioc_context.COMPILED_COUNTRY_REGEX = re.compile(r'a^')

        text = "The quick brown fox jumps over the lazy dog. An IP is 1.2.3.4 and then some more text."
        iocs = ioc_context.extract_iocs_from_text(text, 0)

        found_ip_ioc = next((ioc for ioc in iocs if ioc['ioc_value'] == "1.2.3.4"), None)
        self.assertIsNotNone(found_ip_ioc)
        self.assertTrue("An IP is 1.2.3.4 and then some" in found_ip_ioc['context_snippet'])

    @patch('crawler.module3.ioc_context.DatabaseHandler')
    def test_empty_db_leads_to_no_mentions(self, mock_db_handler_class):
        """
        Testet, dass keine Länder oder APTs gefunden werden, wenn die Datenbank leer ist.
        """
        print("\n[Test] Führe test_empty_db_leads_to_no_mentions aus...")

        mock_db_handler_instance = mock_db_handler_class.return_value
        mock_db_handler_instance.Session().__enter__().query().all.return_value = []

        ioc_context.load_and_compile_apt_regex(mock_db_handler_instance)
        ioc_context.load_and_compile_country_regex(mock_db_handler_instance)

        text = "This text mentions Russia and APT28 but the DB is empty, so nothing should be found."
        iocs = ioc_context.extract_iocs_from_text(text, 0)

        found_apts = [ioc for ioc in iocs if ioc['ioc_type'] == 'apt_group_mention']
        found_countries = [ioc for ioc in iocs if ioc['ioc_type'] == 'country_mention']

        self.assertEqual(len(found_apts), 0)
        self.assertEqual(len(found_countries), 0)


class Testioc_contextProcessTextContents(unittest.TestCase):
    @patch('crawler.module3.ioc_context.extract_iocs_from_text')
    def test_process_text_with_ioc_and_mentions_association(self, mock_extract_single):
        test_text = "File evil.exe and CVE-2023-1234 in China."
        article_idx = 0

        mock_extract_single.return_value = [
            {"ioc_value": "evil.exe", "ioc_type": "file", "source_article_index": article_idx,
             "context_snippet": "..."},
            {"ioc_value": "CVE-2023-1234", "ioc_type": "cve", "source_article_index": article_idx,
             "context_snippet": "..."},
            {"ioc_value": "China", "ioc_type": "country_mention", "source_article_index": article_idx,
             "context_snippet": "..."}
        ]

        expected_output = [{
            "ioc_value": "evil.exe", "ioc_type": "file", "source_article_index": article_idx,
            "context_snippet": "...",
            "associated_cves": [{"value": "CVE-2023-1234", "context_snippet": "..."}],
            "associated_countries": [{"value": "China", "context_snippet": "..."}]
        }]

        actual_output = ioc_context.process_text_contents([test_text])

        self.assertEqual(len(actual_output), 1)
        self.assertEqual(actual_output[0]['ioc_value'], expected_output[0]['ioc_value'])
        self.assertIn('associated_cves', actual_output[0])
        self.assertIn('associated_countries', actual_output[0])


if __name__ == '__main__':
    unittest.main()