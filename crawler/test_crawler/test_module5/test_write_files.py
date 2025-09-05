import unittest
import os
import shutil
import tempfile
import json
import csv
from crawler.module5 import write_files


class TestModule5OutputFunctions(unittest.TestCase):
    """
    Testfälle für die Dateiausgabe-Funktionen in Modul 5.
    Erstellt ein temporäres Verzeichnis für Testausgaben, das nach den Tests wieder gelöscht wird.
    """

    def setUp(self):
        """
        Wird vor jeder Testmethode ausgeführt.
        Erstellt ein temporäres Verzeichnis und Testdaten.
        """
        print(f"\n--- Setting up for {self._testMethodName} ---")
        self.test_dir = tempfile.mkdtemp()
        print(f"Temporäres Testverzeichnis erstellt: {self.test_dir}")

        self.json_output_dir = os.path.join(self.test_dir, "test_gefundene_iocs_json")
        self.csv_output_dir = os.path.join(self.test_dir, "test_gefundene_iocs_csv")
        self.stix_output_dir = os.path.join(self.test_dir, "test_gefundene_iocs_stix")

        self.sample_structured_iocs = [
            {
                "ioc_value": "evil.com",
                "ioc_type": "domain",
                "discovery_timestamp": "2025-06-08T10:18:19Z",
                "source_article_urls": ["http://example.com/article1"],
                "first_seen_context_snippet": "evil.com was used by APT-X",
                "associated_cves": [{"value": "CVE-2025-1111", "context_snippet": "..."}],
                "associated_apts": [{"value": "APT-X", "normalized_value": "APT-X", "context_snippet": "..."}],
                "occurrence_count": 1
            },
            {
                "ioc_value": "192.168.1.101",
                "ioc_type": "ipv4",
                "discovery_timestamp": "2025-06-08T10:18:19Z",
                "source_article_urls": ["http://example.com/article1", "http://example.com/article2"],
                "first_seen_context_snippet": "The IP 192.168.1.101 was a C2.",
                "associated_countries": [{"value": "Russia", "context_snippet": "..."}],
                "occurrence_count": 2
            },
            {
                "ioc_value": "d41d8cd98f00b204e9800998ecf8427e",
                "ioc_type": "md5",
                "discovery_timestamp": "2025-06-08T10:18:19Z",
                "source_article_urls": ["http://example.com/article2"],
                "first_seen_context_snippet": "An empty file with hash d41d...",
                "occurrence_count": 1
            }
        ]

    def tearDown(self):
        """
        Wird nach jeder Testmethode ausgeführt.
        Löscht das temporäre Verzeichnis und seinen gesamten Inhalt.
        """
        print(f"--- Tearing down for {self._testMethodName} ---")
        try:
            shutil.rmtree(self.test_dir)
            print(f"Temporäres Testverzeichnis gelöscht: {self.test_dir}")
        except OSError as e:
            print(f"Fehler beim Löschen des Testverzeichnisses {self.test_dir}: {e}")

    def test_save_iocs_to_json_files(self):
        """Testet die Erstellung von separaten JSON-Dateien für jeden IOC."""
        print("[TEST] test_save_iocs_to_json_files")

        files_saved = write_files.save_iocs_to_json_files(self.sample_structured_iocs, self.json_output_dir)

        self.assertEqual(files_saved, len(self.sample_structured_iocs))
        self.assertTrue(os.path.isdir(self.json_output_dir))

        expected_filename = "domain_evil.com.json"
        expected_filepath = os.path.join(self.json_output_dir, expected_filename)
        self.assertTrue(os.path.isfile(expected_filepath))

        with open(expected_filepath, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data, self.sample_structured_iocs[0])

    def test_save_iocs_to_csv(self):
        """Testet die Erstellung einer zusammenfassenden CSV-Datei."""
        print("[TEST] test_save_iocs_to_csv")
        csv_filename = "test_summary.csv"

        rows_saved = write_files.save_iocs_to_csv(self.sample_structured_iocs, self.csv_output_dir, filename=csv_filename)

        self.assertEqual(rows_saved, len(self.sample_structured_iocs))
        expected_filepath = os.path.join(self.csv_output_dir, csv_filename)
        self.assertTrue(os.path.isfile(expected_filepath))

        with open(expected_filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            self.assertEqual(len(rows), len(self.sample_structured_iocs))

            row_for_ip = next(row for row in rows if row["ioc_value"] == "192.168.1.101")
            self.assertIsNotNone(row_for_ip)
            self.assertEqual(row_for_ip["ioc_type"], "ipv4")
            self.assertEqual(row_for_ip["occurrence_count"], "2")
            self.assertEqual(row_for_ip["source_article_urls"],
                             "http://example.com/article1|http://example.com/article2")
            self.assertEqual(row_for_ip["associated_countries"], "Russia")
            self.assertEqual(row_for_ip["associated_cves"], "")  # Sollte leer sein

    def test_save_iocs_to_stix(self):
        """Testet die Erstellung eines STIX Bundles."""
        print("[TEST] test_save_iocs_to_stix")
        stix_filename = "test_bundle.json"

        objects_saved = write_files.save_iocs_to_stix(self.sample_structured_iocs, self.stix_output_dir,
                                                      filename=stix_filename)

        expected_filepath = os.path.join(self.stix_output_dir, stix_filename)
        self.assertTrue(os.path.isfile(expected_filepath))

        with open(expected_filepath, 'r', encoding='utf-8') as f:
            bundle_data = json.load(f)

        # Grundlegende Bundle-Struktur prüfen
        self.assertEqual(bundle_data.get("type"), "bundle")
        self.assertTrue(bundle_data.get("id", "").startswith("bundle--"))
        self.assertEqual(str(bundle_data.get("spec_version")), "2.1")
        self.assertIn("objects", bundle_data)

        stix_objects = bundle_data["objects"]
        object_types = [obj["type"] for obj in stix_objects]

        # Primäre SCOs: 1x domain-name, 1x ipv4-address, 1x file (für den MD5-Hash)
        self.assertEqual(object_types.count("domain-name"), 1)
        self.assertEqual(object_types.count("ipv4-addr"), 1)
        self.assertEqual(object_types.count("file"), 1)

        # Assoziierte SDOs: 1x vulnerability, 1x intrusion-set, 2x report
        self.assertEqual(object_types.count("vulnerability"), 1)
        self.assertEqual(object_types.count("intrusion-set"), 1)
        self.assertEqual(object_types.count("report"), 2)

        self.assertIn("relationship", object_types)

        # Finde ein spezifisches Objekt und prüfe seine Eigenschaften
        domain_obj = next((obj for obj in stix_objects if obj.get("type") == "domain-name"), None)
        self.assertIsNotNone(domain_obj)
        self.assertEqual(domain_obj.get("value"), "evil.com")


if __name__ == '__main__':
    unittest.main()