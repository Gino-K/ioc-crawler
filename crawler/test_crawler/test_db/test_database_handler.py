import unittest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database_models import Base, IOC, Sighting, APT, Country, CVE
from db.database_handler import DatabaseHandler


class TestDatabaseHandler(unittest.TestCase):
    """Testfälle für den DatabaseHandler und die Datenbankinteraktion."""

    def setUp(self):
        """
        Wird vor jeder Testmethode ausgeführt.
        Erstellt eine saubere In-Memory-SQLite-Datenbank für jeden Test.
        """
        print(f"\n--- Setting up for {self._testMethodName} ---")
        # 1. Erstelle eine In-Memory-Datenbank (`:memory:`)
        self.engine = create_engine('sqlite:///:memory:')

        # 2. Erstelle alle Tabellen im Schema in dieser In-Memory-Datenbank
        Base.metadata.create_all(self.engine)

        # 3. Erstelle eine Session-Klasse, die an unsere Test-Engine gebunden ist
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # 4. Erstelle eine Instanz unseres Handlers speziell für diesen Test
        self.db_handler = DatabaseHandler(db_name=":memory:")
        # Überschreibe die Session des Handlers mit unserer Test-Session
        self.db_handler.Session = self.TestingSessionLocal

        # 5. Erstelle Beispieldaten (simuliert den Output von Modul 4)
        self.sample_ioc_data_1 = {
            "ioc_value": "evil.com", "ioc_type": "domain",
            "discovery_timestamp": "2025-06-08T12:00:00Z",
            "source_article_urls": ["http://test.com/article1"],
            "first_seen_context_snippet": "evil.com context",
            "associated_apts": [{"value": "APT-TEST", "normalized_value": "APT-TEST", "context_snippet": "..."}],
            "associated_cves": [{"value": "CVE-2025-9999", "context_snippet": "..."}],
            "occurrence_count": 1
        }
        self.sample_ioc_data_2 = {
            "ioc_value": "1.2.3.4", "ioc_type": "ipv4",
            "discovery_timestamp": "2025-06-08T13:00:00Z",
            "source_article_urls": ["http://test.com/article2"],
            "first_seen_context_snippet": "1.2.3.4 context",
            "associated_cves": [{"value": "CVE-2025-9999", "context_snippet": "..."}],  # Gleiches CVE wie oben
            "associated_countries": [{"value": "Testland", "context_snippet": "..."}],
            "occurrence_count": 1
        }
        self.sample_ioc_data_1_duplicate = {  # Gleicher primärer IOC wie 1, aber aus anderem Artikel
            "ioc_value": "evil.com", "ioc_type": "domain",
            "discovery_timestamp": "2025-06-08T14:00:00Z",
            "source_article_urls": ["http://test.com/article3"],
            "first_seen_context_snippet": "evil.com context 2",
            "associated_countries": [{"value": "Testland", "context_snippet": "..."}],  # Gleiches Land wie bei 2
            "occurrence_count": 1
        }

    def tearDown(self):
        """Wird nach jeder Testmethode ausgeführt."""
        print(f"--- Tearing down for {self._testMethodName} ---")
        # Bei einer In-Memory-Datenbank ist kein Aufräumen nötig, sie wird verworfen.
        pass

    def test_get_or_create_functionality(self):
        """Testet die _get_or_create Hilfsfunktion des Handlers."""
        print("[TEST] test_get_or_create_functionality")
        session = self.db_handler.Session()

        # Erster Aufruf: Sollte ein neues Country-Objekt erstellen
        country1 = self.db_handler._get_or_create(session, Country, name="Testland",  iso2_code="xx", iso3_code="xxx", tld="xxx")
        self.assertIsNotNone(country1.id)  # Muss eine ID nach dem Commit haben

        # Zähle die Länder in der DB
        country_count = session.query(Country).count()
        self.assertEqual(country_count, 1)

        # Zweiter Aufruf mit denselben Daten: Sollte dasselbe Objekt zurückgeben
        country2 = self.db_handler._get_or_create(session, Country, name="Testland")
        self.assertEqual(country1.id, country2.id)

        # Zähle erneut, es sollte immer noch nur ein Land geben
        country_count_after = session.query(Country).count()
        self.assertEqual(country_count_after, 1)

        session.close()

    def test_add_single_ioc_with_all_relations(self):
        """Testet das Hinzufügen eines einzelnen IOCs mit allen Beziehungstypen."""
        print("[TEST] test_add_single_ioc_with_all_relations")
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_1)

        # Überprüfe die Datenbank direkt
        session = self.db_handler.Session()
        # 1. Prüfe, ob der IOC erstellt wurde
        ioc_db = session.query(IOC).filter_by(value="evil.com", type="domain").one_or_none()
        self.assertIsNotNone(ioc_db)

        # 2. Prüfe, ob ein Sighting erstellt wurde
        self.assertEqual(len(ioc_db.sightings), 1)
        sighting_db = ioc_db.sightings[0]
        self.assertEqual(sighting_db.source_article_url, "http://test.com/article1")

        # 3. Prüfe, ob die n-zu-n-Beziehungen korrekt sind
        self.assertEqual(len(sighting_db.apts), 1)
        self.assertEqual(sighting_db.apts[0].name, "APT-TEST")
        self.assertEqual(len(sighting_db.cves), 1)
        self.assertEqual(sighting_db.cves[0].name, "CVE-2025-9999")
        self.assertEqual(len(sighting_db.countries), 0)  # Keine Länder in diesen Testdaten

        session.close()

    def test_add_duplicate_primary_ioc(self):
        """Testet, dass für denselben primären IOC keine neue IOC-Zeile, aber ein neues Sighting erstellt wird."""
        print("[TEST] test_add_duplicate_primary_ioc")
        # Füge den ersten Fund hinzu
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_1)
        # Füge den zweiten Fund desselben IOCs hinzu
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_1_duplicate)

        session = self.db_handler.Session()
        # Es sollte nur EINEN IOC-Eintrag für "evil.com" geben
        ioc_count = session.query(IOC).filter_by(value="evil.com").count()
        self.assertEqual(ioc_count, 1)

        # Aber es sollte ZWEI Sightings für diesen einen IOC geben
        ioc_db = session.query(IOC).filter_by(value="evil.com").one()
        self.assertEqual(len(ioc_db.sightings), 2)

        # Prüfe, ob die Sighting-URLs korrekt sind
        sighting_urls = {s.source_article_url for s in ioc_db.sightings}
        self.assertEqual(sighting_urls, {"http://test.com/article1", "http://test.com/article3"})

        session.close()

    def test_reuse_of_mention_objects(self):
        """Testet, dass Entitäten wie CVEs und Länder wiederverwendet und nicht dupliziert werden."""
        print("[TEST] test_reuse_of_mention_objects")
        # Füge beide IOC-Datensätze hinzu, die sich ein CVE und ein Land teilen
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_1)
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_2)
        self.db_handler.add_structured_ioc_data(self.sample_ioc_data_1_duplicate)

        session = self.db_handler.Session()

        # Es sollte nur EINEN Eintrag für "CVE-2025-9999" geben
        cve_count = session.query(CVE).filter_by(name="CVE-2025-9999").count()
        self.assertEqual(cve_count, 1)

        # Es sollte nur EINEN Eintrag für "Testland" geben
        country_count = session.query(Country).filter_by(name="Testland").count()
        self.assertEqual(country_count, 1)

        # Prüfe, ob die Beziehungen korrekt sind
        cve_db = session.query(CVE).one()
        # Das CVE sollte mit 2 Sightings verknüpft sein (von ioc_data_1 und ioc_data_2)
        self.assertEqual(len(cve_db.sightings), 2)

        country_db = session.query(Country).one()
        # Das Land sollte mit 2 Sightings verknüpft sein (von ioc_data_2 und ioc_data_1_duplicate)
        self.assertEqual(len(country_db.sightings), 2)

        session.close()

    def test_get_existing_sightings(self):
        """Testet die Abfrage existierender Sightings mit einem URL-Präfix."""
        print("[TEST] test_get_existing_sightings")

        # 1. Arrange: Befülle die Datenbank mit Test-Sightings
        session = self.db_handler.Session()

        # Wichtig: Wir erstellen hier absichtlich naive UTC-Zeitstempel,
        # um das Verhalten im Fehlerprotokoll exakt nachzubilden.
        # datetime.utcnow() erstellt einen naiven Zeitstempel, der aber auf UTC basiert.
        now_naive_utc = datetime.datetime.utcnow()
        t_old = now_naive_utc - datetime.timedelta(days=10)
        t_new = now_naive_utc - datetime.timedelta(days=1)

        parent_ioc = IOC(value="dummy.ioc", type="domain")
        session.add(parent_ioc)
        session.commit()

        # Füge die Sightings mit den naiven UTC-Zeitstempeln hinzu
        sightings_to_add = [
            Sighting(ioc_id=parent_ioc.id, source_article_url="https://test.com/article1", sighting_timestamp=t_old),
            Sighting(ioc_id=parent_ioc.id, source_article_url="https://test.com/article1", sighting_timestamp=t_new),
            Sighting(ioc_id=parent_ioc.id, source_article_url="https://test.com/article2", sighting_timestamp=t_old),
            Sighting(ioc_id=parent_ioc.id, source_article_url="https://other.com/article3", sighting_timestamp=t_old)
        ]
        session.add_all(sightings_to_add)
        session.commit()
        session.close()

        # 2. Act: Rufe die zu testende Methode auf
        url_prefix = "https://test.com"
        result_map = self.db_handler.get_existing_sightings(url_prefix)

        # 3. Assert: Überprüfe die Ergebnisse
        self.assertIsInstance(result_map, dict)
        self.assertEqual(len(result_map), 2)

        # --- KORREKTUR HIER ---
        # Hole den "informierten" Zeitstempel aus der Datenbank
        actual_aware_timestamp_art1 = result_map.get("https://test.com/article1")
        actual_aware_timestamp_art2 = result_map.get("https://test.com/article2")

        self.assertIsNotNone(actual_aware_timestamp_art1)
        self.assertIsNotNone(actual_aware_timestamp_art2)

        # Wandle den "informierten" Zeitstempel aus der DB in einen "naiven" um,
        # um ihn mit t_new und t_old vergleichen zu können.
        # .replace(tzinfo=None) entfernt die Zeitzonen-Information.
        actual_naive_timestamp_art1 = actual_aware_timestamp_art1.replace(tzinfo=None)
        actual_naive_timestamp_art2 = actual_aware_timestamp_art2.replace(tzinfo=None)

        # Vergleiche die beiden jetzt naiven Zeitstempel
        self.assertEqual(actual_naive_timestamp_art1, t_new)
        self.assertEqual(actual_naive_timestamp_art2, t_old)

        # Teste einen Fall, der keine Ergebnisse liefern sollte
        empty_result_map = self.db_handler.get_existing_sightings("https://nonexistent.com")
        self.assertEqual(len(empty_result_map), 0)

    def test_find_or_create_apt_logic(self):
        """Testet die _find_or_create_apt Methode auf verschiedene Szenarien."""
        print("[TEST] test_find_or_create_apt_logic")

        # 1. Arrange: Befülle die DB mit einer bekannten APT-Gruppe
        session = self.db_handler.Session()
        preloaded_apt = APT(
            name="APT28",
            mitre_id="G0007",
            aliases="Fancy Bear, Strontium"
        )
        session.add(preloaded_apt)
        session.commit()

        # Behalte die ID für den Vergleich
        preloaded_apt_id = preloaded_apt.id
        self.assertIsNotNone(preloaded_apt_id)

        # --- Szenario 1: Finde die APT über ihren primären Namen ---
        print("  Szenario 1: Finde über primären Namen 'APT28'")
        apt_info1 = {"value": "APT28", "normalized_value": "APT28"}
        found_apt1 = self.db_handler._find_or_create_apt(session, apt_info1)
        self.assertEqual(found_apt1.id, preloaded_apt_id)  # Muss dasselbe Objekt sein

        # Es darf kein neues Objekt erstellt worden sein
        self.assertEqual(session.query(APT).count(), 1)

        # --- Szenario 2: Finde die APT über einen ihrer Aliase ---
        print("  Szenario 2: Finde über Alias 'Fancy Bear'")
        apt_info2 = {"value": "Fancy Bear", "normalized_value": "APT28"}
        found_apt2 = self.db_handler._find_or_create_apt(session, apt_info2)
        self.assertEqual(found_apt2.id, preloaded_apt_id)  # Muss immer noch dasselbe Objekt sein

        # Die Anzahl der APTs in der DB muss immer noch 1 sein
        self.assertEqual(session.query(APT).count(), 1)

        # --- Szenario 3: Eine unbekannte APT wird gefunden ---
        print("  Szenario 3: Erstelle neue APT 'New Group'")
        apt_info3 = {"value": "New Group", "normalized_value": "New Group"}
        found_apt3 = self.db_handler._find_or_create_apt(session, apt_info3)
        self.assertNotEqual(found_apt3.id, preloaded_apt_id)  # Muss eine neue ID haben
        self.assertEqual(found_apt3.name, "New Group")

        # Jetzt sollten 2 APTs in der Datenbank sein
        self.assertEqual(session.query(APT).count(), 2)

        session.close()


if __name__ == '__main__':
    unittest.main()