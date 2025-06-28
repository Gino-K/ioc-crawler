import unittest
from unittest.mock import patch
from crawler import main


class TestMainWorkflow(unittest.TestCase):

    @patch('crawler.main.load_and_compile_country_regex')
    @patch('crawler.main.load_and_compile_apt_regex')
    @patch('crawler.main.DatabaseHandler')
    @patch('crawler.main.load_data_sources')
    @patch('crawler.main.article.get_article_links_from_source')
    @patch('crawler.main.text.process_article_links')
    @patch('crawler.main.ioc_context.process_text_contents')
    @patch('crawler.main.enrichment.process_and_structure_iocs')
    @patch('crawler.main.write_files.save_iocs_to_json_files')
    @patch('crawler.main.write_files.save_iocs_to_csv')
    @patch('crawler.main.write_files.save_iocs_to_stix')
    def test_happy_path_full_run(self, mock_save_stix, mock_save_csv, mock_save_json,
                                 mock_structure_iocs_m4, mock_process_iocs_m3,
                                 mock_process_text, mock_get_links, mock_load_sources,
                                 mock_db_handler_class, mock_load_apts, mock_load_countries):
        """Testet den idealen Durchlauf, bei dem alle Schritte erfolgreich sind."""
        print("\n[Integrationstest] Szenario 1: Happy Path (Alles funktioniert)")

        mock_load_sources.return_value = ['https://test-source.com']
        mock_get_links.return_value = ['https://test-source.com/article1']

        db_instance = mock_db_handler_class.return_value
        db_instance.get_existing_sightings.return_value = {}

        mock_process_text.return_value = ["Text mit IOCs"]

        mock_annotated_iocs = [{
            "ioc_value": "1.1.1.1", "ioc_type": "ipv4", "source_article_index": 0,
            "context_snippet": "...",
            "associated_apts": [{"value": "APT28", "normalized_value": "APT28"}]
        }]
        mock_process_iocs_m3.return_value = mock_annotated_iocs

        structured_iocs = [{
            "ioc_value": "1.1.1.1", "ioc_type": "ipv4", "discovery_timestamp": "2025-06-26T18:00:00Z",
            "source_article_urls": ["https://test-source.com/article1"],
            "occurrence_count": 1,
            "associated_apts": [{"value": "APT28", "normalized_value": "APT28"}]
        }]
        mock_structure_iocs_m4.return_value = structured_iocs

        main.CREATE_JSON_PER_IOC = main.CREATE_CSV_SUMMARY = main.CREATE_STIX_BUNDLE = True

        main.main()

        db_instance.add_structured_ioc_data.assert_called_with(structured_iocs[0])
        mock_save_json.assert_called_once_with(structured_iocs, main.JSON_OUTPUT_DIR)

    @patch('crawler.main.load_data_sources')
    @patch('crawler.main.article.get_article_links_from_source')
    def test_no_sources_found(self, mock_get_links, mock_load_sources):
        """Testet das Szenario, bei dem die sources.txt leer ist."""
        print("\n[Integrationstest] Szenario 2: Keine Datenquellen gefunden")
        mock_load_sources.return_value = []

        main.main()

        mock_get_links.assert_not_called()

    @patch('crawler.main.load_data_sources')
    @patch('crawler.main.article.get_article_links_from_source')
    @patch('crawler.main.text.process_article_links')
    def test_no_new_articles_found(self, mock_process_text, mock_get_links, mock_load_sources):
        """Testet das Szenario, bei dem die Quellen keine neuen Artikel-Links liefern."""
        print("\n[Integrationstest] Szenario 3: Keine neuen Artikel gefunden")
        mock_load_sources.return_value = ['https://test-source.com']
        mock_get_links.return_value = []

        main.main()

        mock_process_text.assert_not_called()

    @patch('crawler.main.DatabaseHandler')
    @patch('crawler.main.load_data_sources')
    @patch('crawler.main.article.get_article_links_from_source')
    @patch('crawler.main.text.process_article_links')
    @patch('crawler.main.ioc_context.process_text_contents')
    @patch('crawler.main.enrichment.process_and_structure_iocs')
    def test_mixed_articles_with_and_without_iocs(self, mock_structure_iocs_m4, mock_process_iocs_m3, mock_process_text,
                                                  mock_get_links, mock_load_sources, mock_db_handler_class):
        """Testet das Szenario mit gemischten Artikeln: einer mit IOCs, einer ohne."""
        print("\n[Integrationstest] Szenario 4: Gemischte Artikel (mit & ohne IOCs)")

        mock_load_sources.return_value = ['https://test-source.com']
        mock_get_links.return_value = ['https://site.com/article-with-iocs', 'https://site.com/article-without-iocs']
        mock_process_text.return_value = ["Text mit 1.1.1.1", "Text ohne alles."]

        mock_process_iocs_m3.return_value = [{"ioc_value": "1.1.1.1", "ioc_type": "ipv4", "source_article_index": 0}]

        structured_iocs = [{"ioc_value": "1.1.1.1", "ioc_type": "ipv4", "occurrence_count": 1,
                            "discovery_timestamp": "2025-06-26T18:00:00Z",
                            "source_article_urls": ['https://site.com/article-with-iocs']}]
        mock_structure_iocs_m4.return_value = structured_iocs

        db_instance = mock_db_handler_class.return_value
        db_instance.get_existing_sightings.return_value = {}

        main.main()

        db_instance.add_structured_ioc_data.assert_called_once_with(structured_iocs[0])

    @patch('crawler.main.DatabaseHandler')
    @patch('crawler.main.load_data_sources')
    @patch('crawler.main.article.get_article_links_from_source')
    @patch('crawler.main.text.process_article_links')
    @patch('crawler.main.ioc_context.process_text_contents')
    def test_content_extraction_fails_for_one_article(self, mock_process_iocs_m3, mock_process_text, mock_get_links,
                                                      mock_load_sources, mock_db_handler_class):
        """Testet das Szenario, bei dem Modul 2 für einen Artikel keinen Inhalt extrahieren kann."""
        print("\n[Integrationstest] Szenario 5: Fehler bei der Inhaltsextraktion")

        mock_load_sources.return_value = ['https://test-source.com']
        mock_get_links.return_value = ['https://site.com/article-ok', 'https://site.com/article-fail']
        mock_process_text.return_value = ["Gültiger Text mit 8.8.8.8", None]

        db_instance = mock_db_handler_class.return_value
        db_instance.get_existing_sightings.return_value = {}

        main.main()

        mock_process_iocs_m3.assert_called_once_with(["Gültiger Text mit 8.8.8.8", None])


if __name__ == '__main__':
    unittest.main()