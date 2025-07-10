import unittest
from unittest.mock import patch
import datetime
from crawler.module4 import enrichment

FIXED_TIMESTAMP_STR = "2025-06-01T12:00:00+00:00"
FIXED_DATETIME_NOW = datetime.datetime.fromisoformat(FIXED_TIMESTAMP_STR)


class TestenrichmentNormalizeIOCValue(unittest.TestCase):
    """Testfälle für die _normalize_ioc_value Hilfsfunktion."""

    def test_normalize_domain_lowercase(self):
        print("\n[Test _normalize_ioc_value] test_normalize_domain_lowercase")
        self.assertEqual(enrichment._normalize_ioc_value("EXAMPLE.COM", "domain"), "example.com")

    def test_normalize_email_lowercase(self):
        print("\n[Test _normalize_ioc_value] test_normalize_email_lowercase")
        self.assertEqual(enrichment._normalize_ioc_value("USER@EXAMPLE.COM", "email"), "user@example.com")

    def test_normalize_other_types_unchanged(self):
        print("\n[Test _normalize_ioc_value] test_normalize_other_types_unchanged")
        self.assertEqual(enrichment._normalize_ioc_value("192.168.1.1", "ipv4"), "192.168.1.1")
        self.assertEqual(enrichment._normalize_ioc_value("Malware.EXE", "file"),
                         "Malware.EXE")
        self.assertEqual(enrichment._normalize_ioc_value("CVE-2023-1234", "cve"), "CVE-2023-1234")


class TestenrichmentAddUniqueMention(unittest.TestCase):
    """Testfälle für die _add_unique_mention Hilfsfunktion."""

    def test_add_new_mention(self):
        print("\n[Test _add_unique_mention] test_add_new_mention")
        target_list = []
        seen_set = set()
        mention = {"value": "CVE-2023-1234", "context_snippet": "..."}
        enrichment._add_unique_mention(target_list, seen_set, mention, ('value',))
        self.assertEqual(len(target_list), 1)
        self.assertEqual(target_list[0], mention)
        self.assertIn(("CVE-2023-1234",), seen_set)

    def test_add_duplicate_mention_value(self):
        print("\n[Test _add_unique_mention] test_add_duplicate_mention_value")
        mention1 = {"value": "CVE-2023-1234", "context_snippet": "Context A"}
        target_list = [mention1.copy()]
        seen_set = {("CVE-2023-1234",)}
        mention2 = {"value": "CVE-2023-1234", "context_snippet": "Context B"}
        enrichment._add_unique_mention(target_list, seen_set, mention2, ('value',))
        self.assertEqual(len(target_list), 1)
        self.assertEqual(target_list[0]["context_snippet"], "Context A")

    def test_add_different_mentions(self):
        print("\n[Test _add_unique_mention] test_add_different_mentions")
        target_list = []
        seen_set = set()
        mention1 = {"value": "CVE-2023-1234"}
        mention2 = {"value": "CVE-2023-5678"}
        enrichment._add_unique_mention(target_list, seen_set, mention1, ('value',))
        enrichment._add_unique_mention(target_list, seen_set, mention2, ('value',))
        self.assertEqual(len(target_list), 2)
        self.assertIn(("CVE-2023-1234",), seen_set)
        self.assertIn(("CVE-2023-5678",), seen_set)

    def test_add_apt_mentions_uniqueness(self):
        print("\n[Test _add_unique_mention] test_add_apt_mentions_uniqueness")
        target_list = []
        seen_set = set()
        apt1 = {"value": "Fancy Bear", "normalized_value": "APT28", "context_snippet": "c1"}
        apt2 = {"value": "APT 28", "normalized_value": "APT28",
                "context_snippet": "c2"}
        apt3 = {"value": "Fancy Bear", "normalized_value": "APT28",
                "context_snippet": "c3"}

        enrichment._add_unique_mention(target_list, seen_set, apt1, ('value', 'normalized_value'))
        enrichment._add_unique_mention(target_list, seen_set, apt2, ('value', 'normalized_value'))
        enrichment._add_unique_mention(target_list, seen_set, apt3, ('value', 'normalized_value'))

        self.assertEqual(len(target_list), 2)
        self.assertIn(apt1, target_list)
        self.assertIn(apt2, target_list)
        self.assertIn(("Fancy Bear", "APT28"), seen_set)
        self.assertIn(("APT 28", "APT28"), seen_set)


@patch('crawler.module4.enrichment.datetime')
class TestenrichmentProcessAndStructureIOCs(unittest.TestCase):
    """Testfälle für die Hauptfunktion process_and_structure_iocs."""

    def setUp(self):
        self.article_urls = [
            "http://example.com/article0",
            "http://example.com/article1",
            "http://example.com/article2"
        ]

    def test_empty_input_list(self, mock_datetime):
        print("\n[Test process_and_structure_iocs] test_empty_input_list")
        mock_datetime.datetime.now.return_value = FIXED_DATETIME_NOW
        self.assertEqual(enrichment.process_and_structure_iocs([], self.article_urls), [])

    def test_single_ioc_entry_no_mentions(self, mock_datetime):
        print("\n[Test process_and_structure_iocs] test_single_ioc_entry_no_mentions")
        mock_datetime.datetime.now.return_value = FIXED_DATETIME_NOW
        module3_output = [{
            "ioc_value": "EVIL.EXE", "ioc_type": "file", "source_article_index": 0,
            "context_snippet": "Found EVIL.EXE here."
        }]

        expected_output = [{
            "ioc_value": "EVIL.EXE", "ioc_type": "file",
            "discovery_timestamp": FIXED_TIMESTAMP_STR,
            "source_article_urls": [self.article_urls[0]],
            "first_seen_context_snippet": "Found EVIL.EXE here.",
            "occurrence_count": 1
            # Keine associated_xxx Schlüssel, da sie leer wären und entfernt werden
        }]

        actual_output = enrichment.process_and_structure_iocs(module3_output, self.article_urls)
        self.assertEqual(actual_output, expected_output)

    def test_domain_normalization_and_enrichment(self, mock_datetime):
        print("\n[Test process_and_structure_iocs] test_domain_normalization_and_enrichment")
        mock_datetime.datetime.now.return_value = FIXED_DATETIME_NOW
        module3_output = [{
            "ioc_value": "MiXeDcAsE.CoM", "ioc_type": "domain", "source_article_index": 1,
            "context_snippet": "Domain MiXeDcAsE.CoM found.",
            "associated_cves": [{"value": "CVE-2023-0001", "context_snippet": "cve context"}]
        }]

        expected_output = [{
            "ioc_value": "mixedcase.com", "ioc_type": "domain",
            "discovery_timestamp": FIXED_TIMESTAMP_STR,
            "source_article_urls": [self.article_urls[1]],
            "first_seen_context_snippet": "Domain MiXeDcAsE.CoM found.",
            "associated_cves": [{"value": "CVE-2023-0001", "context_snippet": "cve context"}],
            "occurrence_count": 1
        }]
        actual_output = enrichment.process_and_structure_iocs(module3_output, self.article_urls)
        self.assertEqual(actual_output, expected_output)

    def test_deduplication_of_primary_ioc_merge_mentions(self, mock_datetime):
        print("\n[Test process_and_structure_iocs] test_deduplication_of_primary_ioc_merge_mentions")
        mock_datetime.datetime.now.return_value = FIXED_DATETIME_NOW
        module3_output = [
            {  # Erster Fund von 1.1.1.1
                "ioc_value": "1.1.1.1", "ioc_type": "ipv4", "source_article_index": 0,
                "context_snippet": "IP 1.1.1.1 in article 0.",
                "associated_cves": [{"value": "CVE-001", "context_snippet": "cve1..."}],
                "associated_countries": [{"value": "CountryA", "context_snippet": "cA..."}]
            },
            {  # Zweiter Fund von 1.1.1.1 (aus anderem Artikel, mit anderen/überlappenden Mentions)
                "ioc_value": "1.1.1.1", "ioc_type": "ipv4", "source_article_index": 1,
                "context_snippet": "IP 1.1.1.1 again in article 1.",  # Dieser Kontext wird ignoriert
                "associated_cves": [{"value": "CVE-002", "context_snippet": "cve2..."}],
                "associated_countries": [{"value": "CountryA", "context_snippet": "cA updated..."}]
                # Gleiches Land, anderer Kontext
            },
            {  # Ein anderer IOC
                "ioc_value": "evil.com", "ioc_type": "domain", "source_article_index": 0,  # Normalisiert zu evil.com
                "context_snippet": "evil.com here",
                "associated_apts": [{"value": "APT1", "normalized_value": "APT1", "context_snippet": "apt1..."}]
            }
        ]

        actual_output = enrichment.process_and_structure_iocs(module3_output, self.article_urls)
        self.assertEqual(len(actual_output), 2)  # Sollte zu 2 einzigartigen IOCs führen

        ioc_1_1_1_1 = next(item for item in actual_output if item["ioc_value"] == "1.1.1.1")
        ioc_evil_com = next(item for item in actual_output if item["ioc_value"] == "evil.com")

        # Prüfe 1.1.1.1
        self.assertEqual(ioc_1_1_1_1["occurrence_count"], 2)
        self.assertEqual(sorted(ioc_1_1_1_1["source_article_urls"]),
                         sorted([self.article_urls[0], self.article_urls[1]]))
        self.assertEqual(ioc_1_1_1_1["first_seen_context_snippet"], "IP 1.1.1.1 in article 0.")
        self.assertEqual(len(ioc_1_1_1_1["associated_cves"]), 2)  # CVE-001 und CVE-002
        self.assertTrue(any(cve["value"] == "CVE-001" for cve in ioc_1_1_1_1["associated_cves"]))
        self.assertTrue(any(cve["value"] == "CVE-002" for cve in ioc_1_1_1_1["associated_cves"]))
        self.assertEqual(len(ioc_1_1_1_1["associated_countries"]), 1)  # CountryA ist dedupliziert
        self.assertEqual(ioc_1_1_1_1["associated_countries"][0]["value"], "CountryA")
        # Der Kontext von CountryA wird vom ersten Mal sein, als CountryA für 1.1.1.1 hinzugefügt wurde
        self.assertEqual(ioc_1_1_1_1["associated_countries"][0]["context_snippet"], "cA...")

        # Prüfe evil.com
        self.assertEqual(ioc_evil_com["occurrence_count"], 1)
        self.assertEqual(ioc_evil_com["source_article_urls"], [self.article_urls[0]])
        self.assertEqual(len(ioc_evil_com["associated_apts"]), 1)
        self.assertEqual(ioc_evil_com["associated_apts"][0]["value"], "APT1")

    def test_invalid_source_article_index(self, mock_datetime):
        print("\n[Test process_and_structure_iocs] test_invalid_source_article_index")
        mock_datetime.datetime.now.return_value = FIXED_DATETIME_NOW
        module3_output = [{
            "ioc_value": "test.file", "ioc_type": "file", "source_article_index": 99,  # Ungültiger Index
            "context_snippet": "File context"
        }]

        expected_output = [{
            "ioc_value": "test.file", "ioc_type": "file",
            "discovery_timestamp": FIXED_TIMESTAMP_STR,
            "source_article_urls": ["URL_NOT_FOUND"],  # Erwartetes Verhalten
            "first_seen_context_snippet": "File context",
            "occurrence_count": 1
        }]
        actual_output = enrichment.process_and_structure_iocs(module3_output, self.article_urls)
        self.assertEqual(actual_output, expected_output)

    def test_empty_associated_lists_are_popped(self, mock_datetime):
        print("\n[Test process_and_structure_iocs] test_empty_associated_lists_are_popped")
        mock_datetime.datetime.now.return_value = FIXED_DATETIME_NOW
        module3_output = [{
            "ioc_value": "clean.com", "ioc_type": "domain", "source_article_index": 0,
            "context_snippet": "Clean domain",
            "associated_cves": [],
        }]

        actual_output = enrichment.process_and_structure_iocs(module3_output, self.article_urls)
        self.assertEqual(len(actual_output), 1)
        processed_ioc = actual_output[0]

        self.assertEqual(processed_ioc["ioc_value"], "clean.com")
        self.assertNotIn("associated_cves", processed_ioc)
        self.assertNotIn("associated_countries", processed_ioc)
        self.assertNotIn("associated_apts", processed_ioc)


if __name__ == '__main__':
    unittest.main()