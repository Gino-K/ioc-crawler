from settings.user_settings import UserSettings
from .base_processor import BaseProcessor
from ..module5 import write_files
from db.crawler_db_handler import CrawlerDBHandler


class OutputProcessor(BaseProcessor):
    JSON_OUTPUT_DIR = "gefundene_iocs_json"
    CSV_OUTPUT_DIR = "gefundene_iocs_csv"
    STIX_OUTPUT_DIR = "gefundene_iocs_stix"

    def __init__(self, db_handler: CrawlerDBHandler, user_settings: UserSettings):
        self.db_handler = db_handler
        self.settings = user_settings

    def process(self, structured_iocs: list):
        """
        Nimmt die finalen, strukturierten IOCs entgegen und speichert sie
        in der Datenbank und in den konfigurierten Dateiformaten.
        """
        print("\n[Prozessor 5] Starte Speicherung und Export der Ergebnisse...")

        for ioc_record in structured_iocs:
            self.db_handler.add_structured_ioc_data(ioc_record)
        print("[Prozessor 5] Datenbank-Verarbeitung abgeschlossen.")

        export_formats = self.settings.export_formats
        create_json = export_formats.get("json", False)
        create_csv = export_formats.get("csv", False)
        create_stix = export_formats.get("stix", False)

        if any([create_json, create_csv, create_stix]):
            print(f"[Prozessor 5] Übergebe {len(structured_iocs)} IOCs an die Export-Funktionen...")
            if create_json:
                write_files.save_iocs_to_json_files(structured_iocs, self.JSON_OUTPUT_DIR)
            if create_csv:
                write_files.save_iocs_to_csv(structured_iocs, self.CSV_OUTPUT_DIR)
            if create_stix:
                write_files.save_iocs_to_stix(structured_iocs, self.STIX_OUTPUT_DIR)
        else:
            print("[Prozessor 5] Dateiexport ist in den Einstellungen deaktiviert.")

        return None