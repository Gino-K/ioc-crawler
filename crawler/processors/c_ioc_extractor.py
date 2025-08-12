from .base_processor import BaseProcessor
from ..module3.ioc_context import IOCExtractor
from db.crawler_db_handler import CrawlerDBHandler


class IocExtractorProcessor(BaseProcessor):
    def __init__(self, db_handler: CrawlerDBHandler):
        self.ioc_extractor = IOCExtractor(db_handler)

    def process(self, article_data_map: dict) -> list:
        """
        Nimmt die Textdaten entgegen und verwendet die IOCExtractor-Klasse,
        um alle annotierten IOCs zu finden.
        """
        print(f"\n[Prozessor 3] Übergebe {len(article_data_map.get('texts', {}))} Textinhalte zur IOC-Extraktion...")

        article_contents_list = [article_data_map['texts'].get(i) for i in range(len(article_data_map['urls']))]

        annotated_iocs = self.ioc_extractor.process_text_contents(article_contents_list)

        print(f"[Prozessor 3] {len(annotated_iocs)} annotierte primäre IOCs extrahiert.")
        return annotated_iocs