import time
from settings.user_settings import UserSettings
from db.crawler_db_handler import CrawlerDBHandler
from .processors.a_link_finder import LinkFinder
from .processors.b_content_extractor import ContentExtractor
from .processors.c_ioc_extractor import IocExtractorProcessor
from .processors.d_enrichment import EnrichmentProcessor
from .processors.e_output import OutputProcessor


class CrawlerOrchestrator:
    def __init__(self):
        print("[Orchestrator] Initialisiere Crawler-Workflow...")
        self.settings = UserSettings()
        self.db_handler = CrawlerDBHandler()

        self.link_finder = LinkFinder(self.settings, self.db_handler)
        self.content_extractor = ContentExtractor()
        self.ioc_extractor = IocExtractorProcessor(self.db_handler)
        self.enrichment_processor = EnrichmentProcessor(self.db_handler)
        self.output_processor = OutputProcessor(self.db_handler, self.settings)

    def run(self):
        print("Starte den Prozess der Datenerfassung...")
        print("=" * 40)
        start_time = time.perf_counter()

        # Module 1: Links finden und filtern
        links_to_process = self.link_finder.process(self.settings.source_urls)
        if not links_to_process:
            print("[Main] Keine neuen Artikel zum Verarbeiten gefunden.")
            return

        # Module 2: Inhalte extrahieren
        article_data_map = self.content_extractor.process(links_to_process)

        # Module 3: IOCs extrahieren
        annotated_iocs = self.ioc_extractor.process(article_data_map)
        if not annotated_iocs:
            print("[Main] Keine IOCs in den Artikeln gefunden.")
            return

        # Module 4: IOCs anreichern
        enrichment_input = {'annotated_iocs': annotated_iocs,'article_data_map': article_data_map}
        structured_iocs = self.enrichment_processor.process(enrichment_input)

        # Module 5: Ergebnisse speichern
        self.output_processor.process(structured_iocs)

        print("\n[Main] Aktualisiere den Scan-Verlauf in der Datenbank...")
        self.db_handler.update_article_scan_history(links_to_process)
        print("[Main] Scan-Verlauf erfolgreich aktualisiert.")

        duration = time.perf_counter() - start_time
        print("\n==================================================")
        print(f"[Main] Gesamter Prozess abgeschlossen in {duration:.2f} Sekunden.")
        print("==================================================")

if __name__ == "__main__":
    orchestrator = CrawlerOrchestrator()
    orchestrator.run()