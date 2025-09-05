import unittest
from unittest.mock import patch, MagicMock

from crawler.crawler_orch import CrawlerOrchestrator


class TestCrawlerOrchestrator(unittest.TestCase):
    """
    Integrationstests für den CrawlerOrchestrator.
    Testet das Zusammenspiel der Prozessoren, indem die Prozessoren selbst gemockt werden.
    """

    @patch('crawler.crawler_orch.OutputProcessor')
    @patch('crawler.crawler_orch.EnrichmentProcessor')
    @patch('crawler.crawler_orch.IocExtractorProcessor')
    @patch('crawler.crawler_orch.ContentExtractor')
    @patch('crawler.crawler_orch.LinkFinder')
    @patch('crawler.crawler_orch.UserSettings')
    @patch('crawler.crawler_orch.CrawlerDBHandler')
    def test_run_happy_path(self, MockDBHandler, MockUserSettings, MockLinkFinder,
                            MockContentExtractor, MockIocExtractor, MockEnrichment, MockOutput):
        """Testet den idealen Durchlauf, bei dem jeder Schritt Daten zurückgibt."""
        print("\n[TEST] Orchestrator: Happy Path")

        mock_link_finder_instance = MockLinkFinder.return_value
        mock_link_finder_instance.process.return_value = ['http://example.com/article1']

        mock_content_extractor_instance = MockContentExtractor.return_value
        mock_content_extractor_instance.process.return_value = {'urls': [...], 'texts': {...}}

        mock_ioc_extractor_instance = MockIocExtractor.return_value
        mock_ioc_extractor_instance.process.return_value = [{'ioc_value': '1.1.1.1'}]

        mock_enrichment_instance = MockEnrichment.return_value
        mock_enrichment_instance.process.return_value = [{'structured_ioc': 'data'}]

        mock_output_instance = MockOutput.return_value
        mock_db_handler_instance = MockDBHandler.return_value

        orchestrator = CrawlerOrchestrator()
        orchestrator.run()

        mock_link_finder_instance.process.assert_called_once()
        mock_content_extractor_instance.process.assert_called_once()
        mock_ioc_extractor_instance.process.assert_called_once()
        mock_enrichment_instance.process.assert_called_once()
        mock_output_instance.process.assert_called_once()

        mock_db_handler_instance.update_article_scan_history.assert_called_once()

    @patch('crawler.crawler_orch.LinkFinder')
    @patch('crawler.crawler_orch.ContentExtractor')
    @patch('crawler.crawler_orch.UserSettings')
    @patch('crawler.crawler_orch.CrawlerDBHandler')
    def test_run_stops_if_no_links_found(self, MockDBHandler, MockUserSettings, MockContentExtractor, MockLinkFinder):
        """Testet, dass der Workflow korrekt abbricht, wenn keine Links gefunden werden."""
        print("\n[TEST] Orchestrator: Stoppt bei keinen Links")

        mock_link_finder_instance = MockLinkFinder.return_value
        mock_link_finder_instance.process.return_value = []  # Keine Links gefunden

        mock_content_extractor_instance = MockContentExtractor.return_value

        orchestrator = CrawlerOrchestrator()
        orchestrator.run()

        mock_link_finder_instance.process.assert_called_once()
        mock_content_extractor_instance.process.assert_not_called()


if __name__ == '__main__':
    unittest.main()