import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database_models import Base, APT
from db.crawler_db_handler import CrawlerDBHandler

from extraScripts import preload_manager as preload_mitre_apts

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

    @patch('requests.get')
    def test_scrape_and_load_apts(self, mock_requests_get):
        """Testet das erfolgreiche Scrapen und Speichern der APT-Gruppen."""
        print("\n[TEST] test_scrape_and_load_apts")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = SAMPLE_HTML.encode('utf-8')
        mock_requests_get.return_value = mock_response

        test_db_handler_instance = CrawlerDBHandler(db_name=":memory:")
        test_db_handler_instance.Session = self.TestingSessionLocal

        mitre_preloader = preload_mitre_apts.MitreAptPreloader(test_db_handler_instance)

        mitre_preloader.run()

        with self.TestingSessionLocal() as session:
            apt_count = session.query(APT).count()
            self.assertEqual(apt_count, 2)

            apt_ajax = session.query(APT).filter_by(mitre_id="G0130").one()
            self.assertEqual(apt_ajax.name, "Ajax Security Team")
            self.assertEqual(apt_ajax.aliases, "Rocket Kitten, Flying Kitten")
            self.assertEqual(apt_ajax.description, "Ajax Security Team is a group active since 2010.")

        print("[TEST] test_scrape_and_load_apts (Update-Szenario)")
        mock_response.content = SAMPLE_HTML_UPDATE.encode('utf-8')
        mock_requests_get.return_value = mock_response

        mitre_preloader.run()

        with self.TestingSessionLocal() as session:
            apt_count_after_update = session.query(APT).count()
            self.assertEqual(apt_count_after_update, 2)  # Darf nicht mehr werden

            apt_ajax_updated = session.query(APT).filter_by(mitre_id="G0130").one()
            self.assertEqual(apt_ajax_updated.aliases, "Rocket Kitten, Flying Kitten, Operation Saffron Rose")
            self.assertEqual(apt_ajax_updated.description, "This is an updated description.")


if __name__ == '__main__':
    unittest.main()

