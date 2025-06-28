import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database_models import Base, APT
from db.database_handler import DatabaseHandler

from extraScripts.loaddb import preload_mitre_apts

SAMPLE_HTML = """
<html><body>
    <table>
        <tbody>
            <tr>
                <td><a href="/groups/G0018"> G0018 </a></td>
                <td><a href="/groups/G0018"> admin@338 </a></td>
                <td></td>
                <td><p>admin@338 is a China-based cyber threat group.</p></td>
            </tr>
            <tr>
                <td><a href="/groups/G0130"> G0130 </a></td>
                <td><a href="/groups/G0130"> Ajax Security Team </a></td>
                <td>Rocket Kitten, Flying Kitten</td>
                <td><p>Ajax Security Team is a group active since 2010.</p></td>
            </tr>
        </tbody>
    </table>
</body></html>
"""

# HTML für einen Update-Test
SAMPLE_HTML_UPDATE = """
<html><body>
    <table>
        <tbody>
            <tr>
                <td><a href="/groups/G0130"> G0130 </a></td>
                <td><a href="/groups/G0130"> Ajax Security Team </a></td>
                <td>Rocket Kitten, Flying Kitten, Operation Saffron Rose</td>
                <td><p>This is an updated description.</p></td>
            </tr>
        </tbody>
    </table>
</body></html>
"""


class TestPreloadMitreApts(unittest.TestCase):

    def setUp(self):
        """Erstellt eine saubere In-Memory-DB für jeden Test."""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.TestingSessionLocal = sessionmaker(bind=self.engine)

    def tearDown(self):
        """Räumt nach jedem Test auf."""
        Base.metadata.drop_all(self.engine)

    @patch('extraScripts.loaddb.preload_mitre_apts.DatabaseHandler')
    @patch('extraScripts.loaddb.preload_mitre_apts.requests.get')
    def test_scrape_and_load_apts(self, mock_requests_get, mock_db_handler):
        """Testet das erfolgreiche Scrapen und Speichern der APT-Gruppen."""
        print("\n[TEST] test_scrape_and_load_apts")

        # Mock für den Web-Request
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = SAMPLE_HTML.encode('utf-8')
        mock_requests_get.return_value = mock_response

        test_db_handler_instance = DatabaseHandler(db_name=":memory:")
        test_db_handler_instance.Session = self.TestingSessionLocal
        mock_db_handler.return_value = test_db_handler_instance

        preload_mitre_apts.scrape_and_load_apts()

        # Überprüfe den Inhalt der Test-DB
        session = self.TestingSessionLocal()
        apt_count = session.query(APT).count()
        self.assertEqual(apt_count, 2)

        # Überprüfe einen Eintrag im Detail
        apt_ajax = session.query(APT).filter_by(mitre_id="G0130").one()
        self.assertEqual(apt_ajax.name, "Ajax Security Team")
        self.assertEqual(apt_ajax.aliases, "Rocket Kitten, Flying Kitten")
        self.assertEqual(apt_ajax.description, "Ajax Security Team is a group active since 2010.")

        session.close()

        # ----- Teste das Update-Szenario -----
        print("[TEST] test_scrape_and_load_apts (Update-Szenario)")
        # Konfiguriere den Web-Request-Mock neu, um die Update-HTML zurückzugeben
        mock_response.content = SAMPLE_HTML_UPDATE.encode('utf-8')
        mock_requests_get.return_value = mock_response

        preload_mitre_apts.scrape_and_load_apts()

        # Überprüfe erneut die DB
        session = self.TestingSessionLocal()
        # Es sollten immer noch nur 2 Einträge sein (keine Duplikate)
        apt_count_after_update = session.query(APT).count()
        self.assertEqual(apt_count_after_update, 2)

        # Überprüfe, ob der Eintrag für G0130 aktualisiert wurde
        apt_ajax_updated = session.query(APT).filter_by(mitre_id="G0130").one()
        self.assertEqual(apt_ajax_updated.aliases, "Rocket Kitten, Flying Kitten, Operation Saffron Rose")
        self.assertEqual(apt_ajax_updated.description, "This is an updated description.")
        session.close()
