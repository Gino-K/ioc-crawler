from .base_processor import BaseProcessor
from ..module4 import enrichment
from db.crawler_db_handler import CrawlerDBHandler


class EnrichmentProcessor(BaseProcessor):
    def __init__(self, db_handler: CrawlerDBHandler):
        self.db_handler = db_handler

    def process(self, data: dict) -> list:
        """
        Nimmt die annotierten IOCs und die Artikel-Texte entgegen, um sie
        zu deduplizieren und mittels Proximity-Analyse anzureichern.
        """
        annotated_iocs = data['annotated_iocs']
        article_data_map = data['article_data_map']

        print(f"\n[Prozessor 4] Starte Strukturierung und Anreicherung...")

        structured_iocs = enrichment.process_and_structure_iocs(
            annotated_iocs,
            article_data_map,
            self.db_handler
        )

        print(f"[Prozessor 4] {len(structured_iocs)} einzigartige, strukturierte IOCs erstellt.")
        return structured_iocs