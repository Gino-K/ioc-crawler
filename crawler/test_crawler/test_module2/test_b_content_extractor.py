import unittest
from unittest.mock import patch, call
from bs4 import BeautifulSoup

from crawler.processors.b_content_extractor import ContentExtractor


class TestContentExtractor(unittest.TestCase):
    """
    Testfälle für die ContentExtractor-Prozessorklasse.
    """

    def setUp(self):
        """Erstellt eine saubere ContentExtractor-Instanz vor jedem Test."""
        # Diese Instanz wird in den Tests, die HttpClient mocken, neu erstellt.
        self.extractor = ContentExtractor()

    @patch('crawler.processors.b_content_extractor.HttpClient')
    def test_extract_worker_success(self, MockHttpClient):
        """Testet den erfolgreichen Extraktions-Workflow im _extract_worker."""
        print("\n[TEST] test_extract_worker_success")

        # Konfiguriere den Mock
        mock_http_instance = MockHttpClient.return_value
        url = "https://example.com/article1"
        html_content = """
        <html><body>
            <div class="articlebody">
                <h1>Test Title</h1>
                <p>This is the main article content that should be long enough.</p>
                <script>irrelevant script</script>
            </div>
        </body></html>
        """
        mock_http_instance.get_soup.return_value = BeautifulSoup(html_content, 'html.parser')

        extractor = ContentExtractor()
        expected_content = "Test Title\nThis is the main article content that should be long enough."

        result_url, actual_content = extractor._extract_worker(url)

        self.assertEqual(result_url, url)
        self.assertEqual(actual_content, expected_content)
        mock_http_instance.get_soup.assert_called_once_with(url)

    @patch('crawler.processors.b_content_extractor.HttpClient')
    def test_extract_worker_network_error(self, MockHttpClient):
        """Testet, dass der Worker bei einem Netzwerkfehler None zurückgibt."""
        print("\n[TEST] test_extract_worker_network_error")

        mock_http_instance = MockHttpClient.return_value
        mock_http_instance.get_soup.return_value = None  # Simuliere einen permanenten Fehler

        extractor = ContentExtractor()
        url = "https://example.com/network-error"

        result_url, actual_content = extractor._extract_worker(url)

        self.assertEqual(result_url, url)
        self.assertIsNone(actual_content)
        self.assertEqual(mock_http_instance.get_soup.call_count, 3)

    @patch('crawler.processors.b_content_extractor.HttpClient')
    def test_extract_worker_no_content_found(self, MockHttpClient):
        """Testet den Fall, dass die HTML-Seite keine extrahierbaren Textelemente enthält."""
        print("\n[TEST] test_extract_worker_no_content_found")

        mock_http_instance = MockHttpClient.return_value
        html_content = "<html><body><article></article></body></html>"
        mock_http_instance.get_soup.return_value = BeautifulSoup(html_content, 'html.parser')

        extractor = ContentExtractor()
        url = "https://example.com/no-content"

        result_url, actual_content = extractor._extract_worker(url)

        self.assertEqual(result_url, url)
        self.assertIsNone(actual_content)

    @patch('crawler.processors.b_content_extractor.ContentExtractor._extract_worker')
    def test_process_method_parallel_execution(self, mock_extract_worker):
        """
        Testet die `process`-Methode, die den ThreadPoolExecutor verwendet, um Worker aufzurufen.
        """
        print("\n[TEST] test_process_method_parallel_execution")
        urls = [
            "https://example.com/article1",
            "https://example.com/article2-error",
            "https://example.com/article3"
        ]

        mock_extract_worker.side_effect = [
            ("https://example.com/article1", "Content for article 1"),
            ("https://example.com/article2-error", None),
            ("https://example.com/article3", "Content for article 3"),
        ]

        expected_map = {
            'urls': urls,
            'texts': {
                0: "Content for article 1",
                2: "Content for article 3"
            }
        }

        actual_map = self.extractor.process(urls)

        self.assertEqual(actual_map, expected_map)

        expected_calls = [call(urls[0]), call(urls[1]), call(urls[2])]
        mock_extract_worker.assert_has_calls(expected_calls, any_order=True)


if __name__ == '__main__':
    unittest.main()