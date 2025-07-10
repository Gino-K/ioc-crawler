import unittest
from unittest.mock import patch, MagicMock
from crawler.module1 import article
from crawler.module1.article import HEADERS


class TestModule1(unittest.TestCase):
    """
    Testfälle für das Modul 1 um article.py und seine Funktion get_article_links_from_source.
    """

    # Test 1: Erfolgreiche Extraktion von Links aus einem RSS-Feed
    @patch('crawler.module1.article.feedparser.parse')
    def test_get_links_rss_success(self, mock_feedparser_parse):
        print("\n[Test] Führe test_get_links_rss_success aus...")
        mock_feed_entry1 = MagicMock()
        mock_feed_entry1.link = "https://example.com/rss-article1"
        mock_feed_entry2 = MagicMock()
        mock_feed_entry2.link = "https://example.com/rss-article2"

        mock_parsed_feed = MagicMock()
        mock_parsed_feed.entries = [mock_feed_entry1, mock_feed_entry2]
        mock_parsed_feed.bozo = 0
        mock_feedparser_parse.return_value = mock_parsed_feed

        source_url = "https://example.com/feed.rss"
        expected_links = ["https://example.com/rss-article1", "https://example.com/rss-article2"]

        actual_links = article.get_article_links_from_source(source_url)

        self.assertEqual(sorted(actual_links), sorted(expected_links))
        mock_feedparser_parse.assert_called_once_with(source_url, agent=HEADERS['User-Agent'])
        print("[Test] test_get_links_rss_success BEENDET.")

    # Test 2: RSS-Feed ist leer, es sollten keine Links zurückgegeben werden (und HTML wird versucht)
    @patch('crawler.module1.article.requests.get')
    @patch('crawler.module1.article.feedparser.parse')
    def test_get_links_rss_empty_fallback_to_html_empty(self, mock_feedparser_parse, mock_requests_get):
        print("\n[Test] Führe test_get_links_rss_empty_fallback_to_html_empty aus...")
        mock_parsed_feed = MagicMock()
        mock_parsed_feed.entries = []
        mock_feedparser_parse.return_value = mock_parsed_feed

        mock_response_html = MagicMock()
        mock_response_html.status_code = 200
        mock_response_html.content = "<html><body><p>Keine Links hier.</p></body></html>"
        mock_response_html.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response_html

        source_url = "https://example.com/empty-source"
        expected_links = []

        actual_links = article.get_article_links_from_source(source_url)

        self.assertEqual(actual_links, expected_links)
        mock_feedparser_parse.assert_called_once_with(source_url, agent=HEADERS['User-Agent'])
        mock_requests_get.assert_called_once_with(source_url, headers=article.HEADERS, timeout=10)
        print("[Test] test_get_links_rss_empty_fallback_to_html_empty BEENDET.")

    # Test 3: Erfolgreiche Extraktion von Links von thehackernews.com (HTML)
    @patch('crawler.module1.article.requests.get')
    @patch('crawler.module1.article.feedparser.parse')
    def test_get_links_thn_html_success(self, mock_feedparser_parse, mock_requests_get):
        print("\n[Test] Führe test_get_links_thn_html_success aus...")
        mock_empty_feed = MagicMock()
        mock_empty_feed.entries = []
        mock_feedparser_parse.return_value = mock_empty_feed

        thn_html_content = """
        <html><body>
            <a class="story-link" href="https://thehackernews.com/2025/05/article1.html">THN Article 1</a>
            <a class="story-link" href="https://thehackernews.com/2025/06/article2.html">THN Article 2</a>
            <a class="story-link" href="/search/label/Vulnerability">Search Link - Should be ignored by current logic</a>
            <a class="another-class" href="https://thehackernews.com/contact.html">Contact Page</a>
        </body></html>
        """
        mock_response_thn = MagicMock()
        mock_response_thn.status_code = 200
        mock_response_thn.content = thn_html_content.encode('utf-8')
        mock_response_thn.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response_thn

        source_url = "https://thehackernews.com/"
        # Erwartete Links basierend auf der Logik (ignoriert "/search/label/")
        expected_links = [
            "https://thehackernews.com/2025/05/article1.html",
            "https://thehackernews.com/2025/06/article2.html"
        ]

        actual_links = article.get_article_links_from_source(source_url)

        self.assertEqual(sorted(actual_links), sorted(expected_links))
        mock_feedparser_parse.assert_called_once_with(source_url, agent=HEADERS['User-Agent'])
        mock_requests_get.assert_called_once_with(source_url, headers=article.HEADERS, timeout=10)
        print("[Test] test_get_links_thn_html_success BEENDET.")

    # Test 4: Erfolgreiche Extraktion von Links von einer generischen HTML-Seite
    @patch('crawler.module1.article.requests.get')
    @patch('crawler.module1.article.feedparser.parse')
    def test_get_links_generic_html_success(self, mock_feedparser_parse, mock_requests_get):
        print("\n[Test] Führe test_get_links_generic_html_success aus...")
        # RSS-Versuch schlägt fehl oder ist leer
        mock_empty_feed = MagicMock()
        mock_empty_feed.entries = []
        mock_feedparser_parse.return_value = mock_empty_feed

        generic_html_content = """
        <html><body>
            <h1>Willkommen</h1>
            <a href="/artikel/detail/toller-artikel.html">Toller Artikel</a>
            <a href="https://example.com/news/another-article.htm">Anderer Artikel</a>
            <a href="https://external-site.com/page.html">Externer Link</a>
            <a href="/about-us">Über uns</a>
            <a href="mailto:info@example.com">Kontakt Mail</a>
        </body></html>
        """
        mock_response_generic = MagicMock()
        mock_response_generic.status_code = 200
        mock_response_generic.content = generic_html_content.encode('utf-8')
        mock_response_generic.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response_generic

        source_url = "https://example.com/mainpage"
        expected_links = [
            "https://example.com/artikel/detail/toller-artikel.html",
            "https://example.com/news/another-article.htm"
        ]

        actual_links = article.get_article_links_from_source(source_url)

        self.assertEqual(sorted(actual_links), sorted(expected_links))
        print("[Test] test_get_links_generic_html_success BEENDET.")

    # Test 5: HTML-Seite hat keine passenden Links
    @patch('crawler.module1.article.requests.get')
    @patch('crawler.module1.article.feedparser.parse')
    def test_get_links_html_no_links_found(self, mock_feedparser_parse, mock_requests_get):
        print("\n[Test] Führe test_get_links_html_no_links_found aus...")
        mock_empty_feed = MagicMock()
        mock_empty_feed.entries = []
        mock_feedparser_parse.return_value = mock_empty_feed

        html_no_links = "<html><body><p>Dies ist eine Seite ohne Links.</p><div></div></body></html>"
        mock_response_no_links = MagicMock()
        mock_response_no_links.status_code = 200
        mock_response_no_links.content = html_no_links.encode('utf-8')
        mock_response_no_links.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response_no_links

        source_url = "https://example.com/no-links-here"
        expected_links = []

        actual_links = article.get_article_links_from_source(source_url)

        self.assertEqual(actual_links, expected_links)
        print("[Test] test_get_links_html_no_links_found BEENDET.")

    # Test 6: Netzwerkfehler beim Abrufen von HTML
    @patch('crawler.module1.article.requests.get')
    @patch('crawler.module1.article.feedparser.parse')
    def test_get_links_network_error(self, mock_feedparser_parse, mock_requests_get):
        print("\n[Test] Führe test_get_links_network_error aus...")
        mock_empty_feed = MagicMock()
        mock_empty_feed.entries = []
        mock_feedparser_parse.return_value = mock_empty_feed

        mock_requests_get.side_effect = article.requests.exceptions.RequestException("Netzwerkproblem")

        source_url = "https://example.com/network-error-site"
        expected_links = []

        actual_links = article.get_article_links_from_source(source_url)

        self.assertEqual(actual_links, expected_links)
        print("[Test] test_get_links_network_error BEENDET.")

    # Test 7: HTTP-Fehlerstatus beim Abrufen von HTML (z.B. 404)
    @patch('crawler.module1.article.requests.get')
    @patch('crawler.module1.article.feedparser.parse')
    def test_get_links_http_error(self, mock_feedparser_parse, mock_requests_get):
        print("\n[Test] Führe test_get_links_http_error aus...")
        mock_empty_feed = MagicMock()
        mock_empty_feed.entries = []
        mock_feedparser_parse.return_value = mock_empty_feed

        mock_response_http_error = MagicMock()
        mock_response_http_error.status_code = 404
        mock_response_http_error.raise_for_status.side_effect = article.requests.exceptions.HTTPError("404 Not Found")
        mock_requests_get.return_value = mock_response_http_error

        source_url = "https://example.com/not-found-page"
        expected_links = []

        actual_links = article.get_article_links_from_source(source_url)

        self.assertEqual(actual_links, expected_links)
        print("[Test] test_get_links_http_error BEENDET.")

    # Test 8: RSS ist leer, aber HTML Fallback liefert erfolgreich Links
    @patch('crawler.module1.article.requests.get')
    @patch('crawler.module1.article.feedparser.parse')
    def test_get_links_rss_empty_html_fallback_success(self, mock_feedparser_parse, mock_requests_get):
        print("\n[Test] Führe test_get_links_rss_empty_html_fallback_success aus...")
        mock_parsed_feed = MagicMock()
        mock_parsed_feed.entries = []
        mock_feedparser_parse.return_value = mock_parsed_feed

        generic_html_content = """
        <html><body>
            <a href="/artikel/wichtig.html">Wichtiger Artikel</a>
        </body></html>
        """
        mock_response_html = MagicMock()
        mock_response_html.status_code = 200
        mock_response_html.content = generic_html_content.encode('utf-8')
        mock_response_html.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response_html

        source_url = "https://fallbackexample.com/"
        expected_links = ["https://fallbackexample.com/artikel/wichtig.html"]

        actual_links = article.get_article_links_from_source(source_url)

        self.assertEqual(sorted(actual_links), sorted(expected_links))
        mock_feedparser_parse.assert_called_once_with(source_url, agent=HEADERS['User-Agent'])
        mock_requests_get.assert_called_once_with(source_url, headers=article.HEADERS, timeout=10)
        print("[Test] test_get_links_rss_empty_html_fallback_success BEENDET.")

    @patch('crawler.module1.article.requests.get')
    def test_get_links_bleeping_computer_main_page_success(self, mock_requests_get):
        """
        Testet, ob Links von der Bleeping Computer Startseite korrekt extrahiert werden,
        indem der spezifische Container für Nachrichten gefunden wird.
        """
        source_url = "https://www.bleepingcomputer.com/"

        mock_html = """
        <html>
            <head><title>Bleeping Computer</title></head>
            <body>
                <header>
                    <a href="/nav-link">Navigation</a>
                </header>
                <div id="main-col">
                    <h1>Latest News</h1>
                    <div class="bc_latest_news_story">
                        <h2>
                            <a href="https://www.bleepingcomputer.com/news/technology/massive-heroku-outage-impacts-web-platforms-worldwide/">
                                Massive Heroku outage impacts web platforms worldwide
                            </a>
                        </h2>
                        <p>Some text here.</p>
                    </div>
                    <div class="bc_latest_news_story">
                        <h2>
                            <a href="https://www.bleepingcomputer.com/news/security/ai-is-a-data-breach-time-bomb-reveals-new-report/">
                                AI is a data breach time bomb, reveals new report
                            </a>
                        </h2>
                    </div>
                    <article>
                        <h3>
                             <a href="https://www.bleepingcomputer.com/news/security/ivanti-workspace-control-hardcoded-key-flaws-expose-sql-credentials/">
                                Ivanti Workspace Control hardcoded key flaws expose SQL credentials
                            </a>
                        </h3>
                    </article>
                    <a href="https://www.bleepingcomputer.com/news/security/">Security News</a>
                </div>
                <footer>
                    <a href="/about-us">About Us</a>
                </footer>
            </body>
        </html>
        """

        expected_links = [
            'https://www.bleepingcomputer.com/news/technology/massive-heroku-outage-impacts-web-platforms-worldwide/',
            'https://www.bleepingcomputer.com/news/security/ai-is-a-data-breach-time-bomb-reveals-new-report/',
            'https://www.bleepingcomputer.com/news/security/ivanti-workspace-control-hardcoded-key-flaws-expose-sql-credentials/'
        ]

        mock_requests_get.return_value.content = mock_html.encode('utf-8')
        mock_requests_get.return_value.raise_for_status.return_value = None

        actual_links = article.get_article_links_from_source(source_url)

        self.assertCountEqual(actual_links, expected_links)


if __name__ == '__main__':
    unittest.main()