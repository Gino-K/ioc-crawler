import unittest
from unittest.mock import patch, MagicMock
import datetime
from crawler.module4 import enrichment

FIXED_TIMESTAMP = datetime.datetime.fromisoformat("2025-06-01T12:00:00+00:00")


class TestEnrichmentNormalizeIOCValue(unittest.TestCase):
    """Testfälle für die _normalize_ioc_value Hilfsfunktion."""

    def test_normalize_domain_lowercase(self):
        self.assertEqual(enrichment._normalize_ioc_value("EXAMPLE.COM", "domain"), "example.com")

    def test_normalize_email_lowercase(self):
        self.assertEqual(enrichment._normalize_ioc_value("USER@EXAMPLE.COM", "email"), "user@example.com")

    def test_normalize_other_types_unchanged(self):
        self.assertEqual(enrichment._normalize_ioc_value("192.168.1.1", "ipv4"), "192.168.1.1")


class TestEnrichmentAddUniqueMention(unittest.TestCase):
    """Testfälle für die _add_unique_mention Hilfsfunktion."""

    def test_add_new_mention(self):
        target_list, seen_set = [], set()
        mention = {"ioc_value": "CVE-2023-1234"}
        enrichment._add_unique_mention(target_list, seen_set, mention, ('ioc_value',))
        self.assertEqual(len(target_list), 1)
        self.assertIn(("CVE-2023-1234",), seen_set)

    def test_add_duplicate_mention_value(self):
        mention1 = {"ioc_value": "CVE-2023-1234", "context_snippet": "Context A"}
        target_list, seen_set = [mention1.copy()], {("CVE-2023-1234",)}
        mention2 = {"ioc_value": "CVE-2023-1234", "context_snippet": "Context B"}
        enrichment._add_unique_mention(target_list, seen_set, mention2, ('ioc_value',))
        self.assertEqual(len(target_list), 1)


@patch('crawler.module4.enrichment.datetime')
class TestEnrichmentProcessAndStructureIOCs(unittest.TestCase):
    """Testfälle für die Hauptfunktion process_and_structure_iocs."""

    def setUp(self):
        """Bereitet die Testdaten und Mocks vor."""
        self.mock_db_handler = MagicMock()

        mock_session = MagicMock()
        self.mock_db_handler.Session.return_value.__enter__.return_value = mock_session
        self.mock_db_handler.find_country.return_value = None
        self.mock_db_handler.find_or_create_apt.side_effect = lambda session, apt_info: apt_info

        self.article_data_map = {
            'urls': ["http://example.com/article0", "http://example.com/article1"],
            'texts': {
                0: "Text for article 0 contains 1.1.1.1 and evil.com",
                1: "Text for article 1 contains MiXeDcAsE.CoM and also 1.1.1.1 with CVE-002"
            }
        }

    def test_empty_input_list(self, mock_datetime):
        print("\n[TEST] test_empty_input_list")
        mock_datetime.datetime.now.return_value.replace.return_value = FIXED_TIMESTAMP
        self.assertEqual(enrichment.process_and_structure_iocs([], {}, self.mock_db_handler), [])

    def test_single_ioc_entry_no_mentions(self, mock_datetime):
        print("\n[TEST] test_single_ioc_entry_no_mentions")
        mock_datetime.datetime.now.return_value.replace.return_value = FIXED_TIMESTAMP
        module3_output = [{
            "ioc_value": "EVIL.EXE", "ioc_type": "file", "source_article_index": 0,
            "context_snippet": "Found EVIL.EXE here."
        }]

        expected_output = [{
            "ioc_value": "EVIL.EXE", "ioc_type": "file",
            "discovery_timestamp": FIXED_TIMESTAMP,
            "source_article_urls": [self.article_data_map['urls'][0]],
            "first_seen_context_snippet": "Found EVIL.EXE here.",
            "occurrence_count": 1
        }]

        actual_output = enrichment.process_and_structure_iocs(module3_output, self.article_data_map,
                                                              self.mock_db_handler)
        self.assertEqual(actual_output, expected_output)

    def test_deduplication_and_merge(self, mock_datetime):
        print("\n[TEST] test_deduplication_and_merge")
        mock_datetime.datetime.now.return_value.replace.return_value = FIXED_TIMESTAMP
        module3_output = [
            # Erster Fund von 1.1.1.1
            {"ioc_value": "1.1.1.1", "ioc_type": "ipv4", "source_article_index": 0,
             "context_snippet": "IP 1.1.1.1 in article 0."},
            {"ioc_value": "CVE-001", "ioc_type": "cve", "source_article_index": 0},
            {"ioc_value": "CountryA", "ioc_type": "country_mention", "source_article_index": 0},
            # Zweiter Fund von 1.1.1.1
            {"ioc_value": "1.1.1.1", "ioc_type": "ipv4", "source_article_index": 1,
             "context_snippet": "IP 1.1.1.1 again."},
            {"ioc_value": "CVE-002", "ioc_type": "cve", "source_article_index": 1},
        ]

        # Simuliere, dass die Proximity-Analyse die Mentions findet
        with patch('crawler.module4.enrichment._proximity_search') as mock_proximity:
            def proximity_side_effect(text, p_ioc_val, mentions):
                if p_ioc_val == "1.1.1.1" and "article 0" in text:
                    return [m for m in mentions if m['ioc_value'] in ['CVE-001', 'CountryA']]
                if p_ioc_val == "1.1.1.1" and "article 1" in text:
                    return [m for m in mentions if m['ioc_value'] == 'CVE-002']
                return []

            mock_proximity.side_effect = proximity_side_effect

            actual_output = enrichment.process_and_structure_iocs(module3_output, self.article_data_map,
                                                                  self.mock_db_handler)

        self.assertEqual(len(actual_output), 1)
        ioc = actual_output[0]
        self.assertEqual(ioc['ioc_value'], "1.1.1.1")
        self.assertEqual(ioc['occurrence_count'], 2)
        self.assertCountEqual(ioc['source_article_urls'],
                              [self.article_data_map['urls'][0], self.article_data_map['urls'][1]])
        self.assertEqual(len(ioc['associated_cves']), 2)  # Beide CVEs wurden gemerged
        self.assertEqual(len(ioc['associated_countries']), 1)  # Nur ein Land


if __name__ == '__main__':
    unittest.main()