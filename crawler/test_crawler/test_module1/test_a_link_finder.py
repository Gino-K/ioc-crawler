import unittest
from unittest.mock import patch, MagicMock
import datetime
from bs4 import BeautifulSoup

from settings.user_settings import UserSettings
from db.crawler_db_handler import CrawlerDBHandler
from crawler.processors.a_link_finder import LinkFinder


class TestLinkFinder(unittest.TestCase):
    """
    Testfälle für die LinkFinder-Prozessorklasse.
    """

    def setUp(self):
        """Erstellt eine saubere LinkFinder-Instanz mit gemockten Abhängigkeiten vor jedem Test."""
        self.mock_settings = MagicMock(spec=UserSettings)
        self.mock_settings.blacklist_keywords = ["/ignore-this/"]  # Beispiel-Blacklist

        self.mock_db_handler = MagicMock(spec=CrawlerDBHandler)
        self.mock_db_handler.get_article_scan_history.return_value = {}

        self.link_finder = LinkFinder(self.mock_settings, self.mock_db_handler)

    @patch('crawler.processors.a_link_finder.feedparser.parse')
    def test_process_source_rss_success(self, mock_feedparser_parse):
        """Testet die erfolgreiche Extraktion von Links aus einem RSS-Feed."""
        print("\n[TEST] test_process_source_rss_success")
        mock_entry1 = MagicMock()
        mock_entry1.link = "https://example.com/rss-article1"
        mock_entry2 = MagicMock()
        mock_entry2.link = "https://example.com/rss-article2"
        mock_parsed_feed = MagicMock()
        mock_parsed_feed.entries = [mock_entry1, mock_entry2]
        mock_feedparser_parse.return_value = mock_parsed_feed

        source_url = "https://example.com/feed.rss"
        expected_links = ["https://example.com/rss-article1", "https://example.com/rss-article2"]

        actual_links = self.link_finder._process_source(source_url)

        self.assertEqual(sorted(actual_links), sorted(expected_links))
        mock_feedparser_parse.assert_called_once()  # Die genauen Argumente sind hier weniger wichtig

    @patch('crawler.processors.a_link_finder.HttpClient')
    @patch('crawler.processors.a_link_finder.feedparser.parse')
    def test_process_source_html_fallback_success(self, mock_feedparser_parse, MockHttpClient):
        """Testet den Fallback auf HTML-Extraktion, wenn der RSS-Feed leer ist."""
        print("\n[TEST] test_process_source_html_fallback_success")
        # RSS ist leer
        mock_parsed_feed = MagicMock()
        mock_parsed_feed.entries = []
        mock_feedparser_parse.return_value = mock_parsed_feed

        mock_http_instance = MockHttpClient.return_value

        html_content = """
        <html><body>
            <article>
                <a href="/news/article-1.html">Ein toller Artikel mit genug Wörtern</a>
                <a href="/news/article-2.html">Noch ein super Artikel über Cybersecurity</a>
                <a href="/ignore-this/bad-link.html">Dieser Link steht auf der Blacklist</a>
            </article>
        </body></html>
        """
        mock_http_instance.get_soup.return_value = BeautifulSoup(html_content, 'html.parser')

        source_url = "https://example.com/"
        expected_links = [
            "https://example.com/news/article-1.html",
            "https://example.com/news/article-2.html"
        ]

        self.link_finder = LinkFinder(self.mock_settings, self.mock_db_handler)
        actual_links = self.link_finder._process_source(source_url)

        self.assertEqual(sorted(actual_links), sorted(expected_links))
        mock_http_instance.get_soup.assert_called_once_with(source_url)

    @patch('crawler.processors.a_link_finder.LinkFinder._process_source')
    def test_process_with_scan_history_filter(self, mock_process_source):
        """Testet die Logik der `process`-Methode, die Links gegen die DB-Historie filtert."""
        print("\n[TEST] test_process_with_scan_history_filter")

        all_found_links = [
            "https://site.com/new-article",
            "https://site.com/old-article",
            "https://site.com/recent-article"
        ]
        mock_process_source.side_effect = [[l] for l in all_found_links]

        now = datetime.datetime.now(datetime.timezone.utc)
        scan_history = {
            "https://site.com/old-article": now - datetime.timedelta(days=10),  # Alt genug
            "https://site.com/recent-article": now - datetime.timedelta(days=1)  # Zu neu
        }
        self.mock_db_handler.get_article_scan_history.return_value = scan_history

        expected_links_to_process = [
            "https://site.com/new-article",
            "https://site.com/old-article"
        ]

        actual_links = self.link_finder.process(all_found_links)

        self.assertCountEqual(actual_links, expected_links_to_process)
        self.mock_db_handler.get_article_scan_history.assert_called_once()


if __name__ == '__main__':
    unittest.main()