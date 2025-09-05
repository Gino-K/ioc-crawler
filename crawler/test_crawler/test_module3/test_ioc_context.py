import unittest
from unittest.mock import patch, MagicMock
import re

from crawler.module3.ioc_context import IOCExtractor
from crawler.module3.ioc_normalization import refang_ioc
from db.crawler_db_handler import CrawlerDBHandler


class TestRefangIOC(unittest.TestCase):
    """Testfälle für die refang_ioc Hilfsfunktion."""

    def test_refang_ip_defanged_brackets(self):
        self.assertEqual(refang_ioc("192[.]168[.]1[.]1", "ipv4"), "192.168.1.1")

    def test_refang_domain_hxxp(self):
        self.assertEqual(refang_ioc("hxxp://example[.]com/path", "domain"), "http://example.com/path")

    def test_refang_email_defanged_at_and_dot(self):
        self.assertEqual(refang_ioc("user[@]example[.]com", "email"), "user@example.com")


class TestIOCExtractor(unittest.TestCase):
    """Testfälle für die IOCExtractor Klasse."""

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

    @patch('crawler.module3.ioc_context.IOCExtractor._load_all_reference_data')
    def test_extract_iocs_from_text_simple(self, mock_load_data):
        """Testet die grundlegende Extraktion verschiedener IOC-Typen."""
        print("\n[TEST] test_extract_iocs_from_text_simple")

        mock_db_handler = MagicMock(spec=CrawlerDBHandler)
        extractor = IOCExtractor(mock_db_handler)

        extractor.compiled_apt_regex = re.compile(r'a^')  # Matcht nie
        extractor.compiled_country_regex = re.compile(r'a^')  # Matcht nie

        extractor.valid_tlds = {"com"}

        text = "A malicious IP is 1.2.3.4, a domain is bad-site.com, and a hash is d41d8cd98f00b204e9800998ecf8427e."
        iocs = extractor.extract_iocs_from_text(text, article_idx=0)

        self.assertEqual(len(iocs), 3)
        self.assertIOCOccurs(iocs, "1.2.3.4", "ipv4")
        self.assertIOCOccurs(iocs, "bad-site.com", "domain")
        self.assertIOCOccurs(iocs, "d41d8cd98f00b204e9800998ecf8427e", "md5")

    @patch('crawler.module3.ioc_context.IOCExtractor._load_all_reference_data')
    def test_extract_with_apts_and_countries(self, mock_load_data):
        """Testet die Extraktion von IOCs zusammen mit APT- und Länder-Erwähnungen."""
        print("\n[TEST] test_extract_with_apts_and_countries")

        mock_db_handler = MagicMock(spec=CrawlerDBHandler)
        extractor = IOCExtractor(mock_db_handler)

        apt_pattern = r'\b(?:APT28|Fancy Bear|Lazarus Group)\b'
        extractor.compiled_apt_regex = re.compile(apt_pattern, re.IGNORECASE)
        extractor.apt_name_map = {
            'apt28': 'APT28',
            'fancy bear': 'APT28',
            'lazarus group': 'Lazarus Group'
        }
        country_pattern = r'\b(?:North Korea|Russia)\b'
        extractor.compiled_country_regex = re.compile(country_pattern, re.IGNORECASE)

        text = ("Attribution points to APT28, also known as Fancy Bear. "
                "Lazarus Group is active in North Korea. IP: 8.8.8.8")

        iocs = extractor.extract_iocs_from_text(text, article_idx=0)

        self.assertNormalizedAPT(iocs, "APT28", "APT28")
        self.assertNormalizedAPT(iocs, "Fancy Bear", "APT28")
        self.assertNormalizedAPT(iocs, "Lazarus Group", "Lazarus Group")
        self.assertIOCOccurs(iocs, "North Korea", "country_mention")
        self.assertIOCOccurs(iocs, "8.8.8.8", "ipv4")

    @patch('crawler.module3.ioc_context.IOCExtractor._load_all_reference_data')
    @patch('crawler.module3.ioc_context.IOCExtractor.extract_iocs_from_text')
    def test_process_text_contents_calls_extractor(self, mock_extract_iocs, mock_load_data):
        """Testet, ob process_text_contents die Extraktionsmethode für jeden Text aufruft."""
        print("\n[TEST] test_process_text_contents_calls_extractor")

        extractor = IOCExtractor(MagicMock(spec=CrawlerDBHandler))

        texts = ["Text 1 mit ioc1", "Text 2 mit ioc2", ""]

        # Simuliere die Rückgabewerte für jeden Aufruf
        mock_extract_iocs.side_effect = [
            [{"ioc_value": "ioc1"}],  # Erster Aufruf
            [{"ioc_value": "ioc2"}],  # Zweiter Aufruf
        ]

        results = extractor.process_text_contents(texts)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['ioc_value'], 'ioc1')
        self.assertEqual(results[1]['ioc_value'], 'ioc2')

        self.assertEqual(mock_extract_iocs.call_count, 2)


if __name__ == '__main__':
    unittest.main()

