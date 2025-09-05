import unittest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database_models import Base, IOC, Sighting, APT, Country, CVE
from db.crawler_db_handler import CrawlerDBHandler


class TestDatabaseHandler(unittest.TestCase):
    """Testfälle für den DatabaseHandler und die Datenbankinteraktion."""

    def setUp(self):
        """
        Wird vor jeder Testmethode ausgeführt.
        Erstellt eine saubere In-Memory-SQLite-Datenbank für jeden Test.
        """
        print(f"\n--- Setting up for {self._testMethodName} ---")
        self.engine = create_engine('sqlite:///:memory:')

        Base.metadata.create_all(self.engine)

        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        self.db_handler = CrawlerDBHandler(db_name=":memory:")
        self.db_handler.Session = self.TestingSessionLocal

        self.sample_ioc_data_1 = {
            "ioc_value": "evil.com", "ioc_type": "domain",
            "discovery_timestamp": datetime.datetime.fromisoformat("2025-06-08T12:00:00+00:00"),
            "source_article_urls": ["http://test.com/article1"],
            "first_seen_context_snippet": "evil.com context",
            "associated_apts": [{"ioc_value": "APT-TEST", "normalized_value": "APT-TEST", "context_snippet": "..."}],
            "associated_cves": [{"ioc_value": "CVE-2025-9999", "context_snippet": "..."}],
            "occurrence_count": 1
        }
        self.sample_ioc_data_2 = {
            "ioc_value": "1.2.3.4", "ioc_type": "ipv4",
            "discovery_timestamp": datetime.datetime.fromisoformat("2025-06-08T13:00:00+00:00"),
            "source_article_urls": ["http://test.com/article2"],
            "first_seen_context_snippet": "1.2.3.4 context",
            "associated_cves": [{"ioc_value": "CVE-2025-9999", "context_snippet": "..."}],
            "associated_countries": [{"ioc_value": "Testland", "context_snippet": "..."}],
            "occurrence_count": 1
        }
        self.sample_ioc_data_1_duplicate = {
            "ioc_value": "evil.com", "ioc_type": "domain",
            "discovery_timestamp": datetime.datetime.fromisoformat("2025-06-08T14:00:00+00:00"),
            "source_article_urls": ["http://test.com/article3"],
            "first_seen_context_snippet": "evil.com context 2",
            "associated_countries": [{"ioc_value": "Testland", "context_snippet": "..."}],
            "occurrence_count": 1
        }

    def tearDown(self):
        """Wird nach jeder Testmethode ausgeführt."""
        print(f"--- Tearing down for {self._testMethodName} ---")
        pass

    def test_get_or_create_functionality(self):
        """Testet die _get_or_create Hilfsfunktion des Handlers."""
        print("[TEST] test_get_or_create_functionality")
        with self.db_handler.Session() as session:
            country1 = self.db_handler._get_or_create(session, Country, name="Testland", defaults={'iso2_code': 'DE'})
            session.commit()
            self.assertIsNotNone(country1.id)
            country2 = self.db_handler._get_or_create(session, Country, name="Testland", defaults={'iso2_code': 'DE'})
            self.assertEqual(country1.id, country2.id)
            country_count_after = session.query(Country).count()
            self.assertEqual(country_count_after, 1)

    def test_add_single_ioc_with_all_relations(self):
        """Testet das Hinzufügen eines einzelnen IOCs mit allen Beziehungstypen."""
        print("[TEST] test_add_single_ioc_with_all_relations")
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_1)

        with self.db_handler.Session() as session:
            ioc_db = session.query(IOC).filter_by(value="evil.com", type="domain").one_or_none()
            self.assertIsNotNone(ioc_db)
            self.assertEqual(len(ioc_db.sightings), 1)
            sighting_db = ioc_db.sightings[0]
            self.assertEqual(sighting_db.source_article_url, "http://test.com/article1")
            self.assertEqual(len(sighting_db.apts), 1)
            self.assertEqual(sighting_db.apts[0].name, "APT-TEST")
            self.assertEqual(len(sighting_db.cves), 1)
            self.assertEqual(sighting_db.cves[0].name, "CVE-2025-9999")
            self.assertEqual(len(sighting_db.countries), 0)

    def test_add_duplicate_primary_ioc(self):
        """Testet, dass für denselben primären IOC keine neue IOC-Zeile, aber ein neues Sighting erstellt wird."""
        print("[TEST] test_add_duplicate_primary_ioc")
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_1)
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_1_duplicate)

        with self.db_handler.Session() as session:
            ioc_count = session.query(IOC).filter_by(value="evil.com").count()
            self.assertEqual(ioc_count, 1)

            ioc_db = session.query(IOC).filter_by(value="evil.com").one()
            self.assertEqual(len(ioc_db.sightings), 2)

            sighting_urls = {s.source_article_url for s in ioc_db.sightings}
            self.assertEqual(sighting_urls, {"http://test.com/article1", "http://test.com/article3"})

    def test_reuse_of_mention_objects(self):
        """Testet, dass Entitäten wie CVEs und Länder wiederverwendet und nicht dupliziert werden."""
        print("[TEST] test_reuse_of_mention_objects")
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_1)
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_2)
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_1_duplicate)

        with self.db_handler.Session() as session:
            cve_count = session.query(CVE).filter_by(name="CVE-2025-9999").count()
            self.assertEqual(cve_count, 1)

            cve_db = session.query(CVE).one()
            self.assertEqual(len(cve_db.sightings), 2)

    def test_get_existing_sightings(self):
        """Testet die Abfrage existierender Sightings mit einem URL-Präfix."""
        print("[TEST] test_get_existing_sightings")
        with self.db_handler.Session() as session:
            now = datetime.datetime.now(datetime.UTC)
            t_old = now - datetime.timedelta(days=10)
            t_new = now - datetime.timedelta(days=1)

            parent_ioc = IOC(value="dummy.ioc", type="domain")
            session.add(parent_ioc)
            session.commit()

            sightings_to_add = [
                Sighting(ioc_id=parent_ioc.id, source_article_url="https://test.com/article1", sighting_timestamp=t_old),
                Sighting(ioc_id=parent_ioc.id, source_article_url="https://test.com/article1", sighting_timestamp=t_new),
                Sighting(ioc_id=parent_ioc.id, source_article_url="https://test.com/article2", sighting_timestamp=t_old),
                Sighting(ioc_id=parent_ioc.id, source_article_url="https://other.com/article3", sighting_timestamp=t_old)
            ]
            session.add_all(sightings_to_add)
            session.commit()

        result_map = self.db_handler.get_existing_sightings("https://test.com")
        self.assertEqual(len(result_map), 2)

        self.assertEqual(result_map.get("https://test.com/article1").replace(tzinfo=None), t_new.replace(tzinfo=None))
        self.assertEqual(result_map.get("https://test.com/article2").replace(tzinfo=None), t_old.replace(tzinfo=None))

        empty_result_map = self.db_handler.get_existing_sightings("https://nonexistent.com")
        self.assertEqual(len(empty_result_map), 0)

    def test_find_or_create_apt_logic(self):
        """Testet die find_or_create_apt Methode auf verschiedene Szenarien."""
        print("[TEST] test_find_or_create_apt_logic")
        with self.db_handler.Session() as session:
            preloaded_apt = APT(name="APT28", mitre_id="G0007", aliases="Fancy Bear, Strontium")
            session.add(preloaded_apt)
            session.commit()
            preloaded_apt_id = preloaded_apt.id

            print("  Szenario 1: Finde über primären Namen 'APT28'")
            apt_info1 = {"ioc_value": "APT28", "normalized_value": "APT28"}
            found_apt1 = self.db_handler.find_or_create_apt(session, apt_info1)
            self.assertEqual(found_apt1.id, preloaded_apt_id)
            self.assertEqual(session.query(APT).count(), 1)

            print("  Szenario 2: Finde über Alias 'Fancy Bear'")
            apt_info2 = {"ioc_value": "Fancy Bear", "normalized_value": "APT28"}
            found_apt2 = self.db_handler.find_or_create_apt(session, apt_info2)
            self.assertEqual(found_apt2.id, preloaded_apt_id)
            self.assertEqual(session.query(APT).count(), 1)

            print("  Szenario 3: Erstelle neue APT 'New Group'")
            apt_info3 = {"ioc_value": "New Group", "normalized_value": "New Group"}
            found_apt3 = self.db_handler.find_or_create_apt(session, apt_info3)
            self.assertNotEqual(found_apt3.id, preloaded_apt_id)
            self.assertEqual(found_apt3.name, "New Group")
            self.assertEqual(session.query(APT).count(), 2)

if __name__ == '__main__':
    unittest.main()