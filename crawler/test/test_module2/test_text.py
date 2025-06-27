import unittest
from unittest.mock import patch, MagicMock, call
from crawler.module2 import text

TEST_HEADERS = text.HEADERS

class TestModule2CleanText(unittest.TestCase):
    """
    Testfälle für die interne Funktion _clean_text.
    """

    def test_clean_text_multiple_spaces_and_tabs(self):
        print("\n[Test _clean_text] Führe test_clean_text_multiple_spaces_and_tabs aus...")
        body_text = "Hello   World\tTest  \t  String."
        expected = "Hello World Test String."
        self.assertEqual(text._clean_text(body_text), expected)

    def test_clean_text_multiple_newlines(self):
        print("\n[Test _clean_text] Führe test_clean_text_multiple_newlines aus...")
        body_text = "Line1\n\n\nLine2\n  \nLine3\n \n"
        expected = "Line1\nLine2\nLine3"
        self.assertEqual(text._clean_text(body_text), expected)

    def test_clean_text_leading_trailing_whitespace(self):
        print("\n[Test _clean_text] Führe test_clean_text_leading_trailing_whitespace aus...")
        body_text = "  \n  Line1 has spaces  \n  \tLine2 also \n  "
        expected = "Line1 has spaces\nLine2 also"
        self.assertEqual(text._clean_text(body_text), expected)

    def test_clean_text_empty_string(self):
        print("\n[Test _clean_text] Führe test_clean_text_empty_string aus...")
        body_text = ""
        expected = ""
        self.assertEqual(text._clean_text(body_text), expected)

    def test_clean_text_already_clean(self):
        print("\n[Test _clean_text] Führe test_clean_text_already_clean aus...")
        body_text = "This is a\nperfectly clean string."
        expected = "This is a\nperfectly clean string."
        self.assertEqual(text._clean_text(body_text), expected)

    def test_clean_text_only_whitespace(self):
        print("\n[Test _clean_text] Führe test_clean_text_only_whitespace aus...")
        body_text = "   \n\t  \n  \t "
        expected = ""
        self.assertEqual(text._clean_text(body_text), expected)


class TestModule2ExtractAndCleanContent(unittest.TestCase):
    """
    Testfälle für extract_and_clean_content.
    """

    @patch('crawler.module2.text.requests.get')
    def test_extract_thn_success(self, mock_requests_get):
        print("\n[Test extract_and_clean_content] Führe test_extract_thn_success aus...")
        url = "https://thehackernews.com/some-article.html"
        html_content = """
        <html><body>
            <header>Header</header>
            <nav>Navigation</nav>
            <div class="articlebody">
                <h1>THN Title</h1>
                <p>First paragraph.  Extra   spaces. </p>
                <script>console.log('ignored');</script>
                <p>Second paragraph.</p>
            </div>
            <footer>Footer</footer>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        expected_text = "THN Title\nFirst paragraph. Extra spaces.\nSecond paragraph."
        actual_text = text.extract_and_clean_content(url)
        self.assertEqual(actual_text, expected_text)
        mock_requests_get.assert_called_once_with(url, headers=TEST_HEADERS, timeout=15)

    @patch('crawler.module2.text.requests.get')
    def test_extract_article_tag_success(self, mock_requests_get):
        print("\n[Test extract_and_clean_content] Führe test_extract_article_tag_success aus...")
        url = "https://example.com/article-tag-test"
        html_content = """
        <html><body>
            <article>
                <h2>Article Tag Title</h2>
                <p>Content here.</p>
                <style>.some{color:red;}</style>
                <p>More content here.</p>
            </article>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        expected_text = "Article Tag Title\nContent here.\nMore content here."
        actual_text = text.extract_and_clean_content(url)
        self.assertEqual(actual_text, expected_text)

    @patch('crawler.module2.text.requests.get')
    def test_extract_common_div_success(self, mock_requests_get):
        print("\n[Test extract_and_clean_content] Führe test_extract_common_div_success aus...")
        url = "https://example.com/common-div-test"
        html_content = """
        <html><body>
            <div id="main-content">
                <h3>Div Title</h3>
                <p>Text from a div with id 'main-content'.</p>
            </div>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        expected_text = "Div Title\nText from a div with id 'main-content'."
        actual_text = text.extract_and_clean_content(url)
        self.assertEqual(actual_text, expected_text)

    @patch('crawler.module2.text.requests.get')
    def test_extract_fallback_p_tags_success(self, mock_requests_get):
        print("\n[Test extract_and_clean_content] Führe test_extract_fallback_p_tags_success aus...")
        url = "https://example.com/p-tag-fallback"
        html_content = """
        <html><body>
            <p>First p tag.</p>
            <div><p>Nested p tag.</p></div>
            <p>Last p tag.</p>
        </body></html>
        """
        # Erwartetes Verhalten: findet keine spezifischen Container, nimmt <p>-Tags
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        expected_text = "First p tag.\nNested p tag.\nLast p tag."
        actual_text = text.extract_and_clean_content(url)
        self.assertEqual(actual_text, expected_text)

    @patch('crawler.module2.text.requests.get')
    def test_extract_no_content_found(self, mock_requests_get):
        print("\n[Test extract_and_clean_content] Führe test_extract_no_content_found aus...")
        url = "https://example.com/no-content"
        html_content = "<html><body><article></article></body></html>"  # Leerer Artikel
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        self.assertIsNone(text.extract_and_clean_content(url))

    @patch('crawler.module2.text.requests.get')
    def test_extract_network_error(self, mock_requests_get):
        print("\n[Test extract_and_clean_content] Führe test_extract_network_error aus...")
        url = "https://example.com/network-error"
        mock_requests_get.side_effect = text.requests.exceptions.RequestException("Test Network Error")

        self.assertIsNone(text.extract_and_clean_content(url))

    @patch('crawler.module2.text.requests.get')
    def test_extract_http_error(self, mock_requests_get):
        print("\n[Test extract_and_clean_content] Führe test_extract_http_error aus...")
        url = "https://example.com/http-error"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = text.requests.exceptions.HTTPError("404 Not Found")
        mock_requests_get.return_value = mock_response

        self.assertIsNone(text.extract_and_clean_content(url))

    @patch('crawler.module2.text.requests.get')
    def test_unwanted_tags_and_comments_removed(self, mock_requests_get):
        print("\n[Test extract_and_clean_content] Führe test_unwanted_tags_and_comments_removed aus...")
        url = "https://example.com/tags-comments-test"
        html_content = """
        <html><body>
            <header>Site Header</header>
            <nav>Menu items</nav>
            <article>
                <h1>Title</h1>
                <p>Main text.</p>
                <script>alert("This is a script");</script>
                <style>.hidden { display: none; }</style>
                <p>Another paragraph.</p>
                <aside>Sidebar content</aside>
            </article>
            <footer>Copyright info</footer>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        expected_text = "Title\nMain text.\nAnother paragraph."
        actual_text = text.extract_and_clean_content(url)
        self.assertEqual(actual_text, expected_text)


class TestModule2ProcessArticleLinks(unittest.TestCase):
    """
    Testfälle für process_article_links.
    """

    @patch('crawler.module2.text.extract_and_clean_content')  # Mocke die Kernfunktion von Modul 2
    def test_process_empty_list(self, mock_extract_content):
        print("\n[Test process_article_links] Führe test_process_empty_list aus...")
        urls = []
        expected_contents = []
        actual_contents = text.process_article_links(urls)
        self.assertEqual(actual_contents, expected_contents)
        mock_extract_content.assert_not_called()

    @patch('crawler.module2.text.extract_and_clean_content')
    def test_process_multiple_links_varied_results(self, mock_extract_content):
        print("\n[Test process_article_links] Führe test_process_multiple_links_varied_results aus...")
        urls = [
            "https://example.com/article1",
            "https://example.com/article2-error",
            "https://example.com/article3"
        ]
        # Simuliere unterschiedliche Rückgabewerte für extract_and_clean_content
        mock_extract_content.side_effect = [
            "Content for article 1",
            None,  # Simuliert einen Fehler oder keinen Inhalt für article2
            "Content for article 3"
        ]

        expected_contents = [
            "Content for article 1",
            None,
            "Content for article 3"
        ]

        actual_contents = text.process_article_links(urls)
        self.assertEqual(actual_contents, expected_contents)

        expected_calls = [call(urls[0]), call(urls[1]), call(urls[2])]
        mock_extract_content.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(mock_extract_content.call_count, len(urls))

    @patch('crawler.module2.text.extract_and_clean_content')
    def test_process_single_link_success(self, mock_extract_content):
        print("\n[Test process_article_links] Führe test_process_single_link_success aus...")
        urls = ["https://example.com/single"]
        mock_extract_content.return_value = "Single article content"

        expected_contents = ["Single article content"]
        actual_contents = text.process_article_links(urls)

        self.assertEqual(actual_contents, expected_contents)
        mock_extract_content.assert_called_once_with(urls[0])


if __name__ == '__main__':
    unittest.main()