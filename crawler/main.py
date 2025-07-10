
import datetime
import os
from urllib.parse import urlparse

from db.database_handler import DatabaseHandler
from module1 import article
from module2 import text
from module3 import ioc_context
from module3.ioc_context import load_and_compile_country_regex, load_and_compile_apt_regex
from module4 import enrichment
from module5 import write_files

SOURCES_FILE_PATH = os.path.join("../url", "sources.txt")

# --- Konfiguration der Ausgabeformate ---
CREATE_JSON_PER_IOC = False
CREATE_CSV_SUMMARY = False
CREATE_STIX_BUNDLE = False

# --- Konfiguration der Verzeichnisse ---
JSON_OUTPUT_DIR = "gefundene_iocs_json"
CSV_OUTPUT_DIR = "gefundene_iocs_csv"
STIX_OUTPUT_DIR = "gefundene_iocs_stix"


def filter_links_by_timestamp(all_links_from_source, existing_sightings_map, days_to_rescan=5):
    """
    Filtert eine Liste von URLs basierend darauf, ob sie neu sind oder ob die letzte
    Sichtung länger als `days_to_rescan` Tage zurückliegt.
    """
    links_to_process = []
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    rescan_threshold = now_utc - datetime.timedelta(days=days_to_rescan)

    for link in all_links_from_source:
        if link not in existing_sightings_map:
            # Fall 1: Link ist komplett neu und wird zur Verarbeitung hinzugefügt.
            links_to_process.append(link)
        else:
            # Fall 2: Link existiert. Prüfe den Zeitstempel.
            timestamp_from_db = existing_sightings_map[link]

            # Stelle sicher, dass der Zeitstempel aus der DB "aware" ist, um Vergleiche zu ermöglichen
            aware_last_seen = timestamp_from_db.replace(tzinfo=datetime.timezone.utc)

            if aware_last_seen < rescan_threshold:
                # Der letzte Fund ist älter als die Schwelle -> erneut verarbeiten
                print(f"[Filter] Link wird erneut verarbeitet (älter als {days_to_rescan} Tage): {link}")
                links_to_process.append(link)

    return links_to_process


def load_data_sources(file_path):
    """
    Lädt Quell-URLs aus einer Textdatei.
    Ignoriert leere Zeilen und Zeilen, die mit '#' beginnen.

    Args:
        file_path (str): Der Pfad zur Textdatei.

    Returns:
        list: Eine Liste der URLs.
    """
    sources = []
    print(f"[Main] Lade Datenquellen aus der Datei: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Entferne führende/nachfolgende Leerzeichen (inkl. Zeilenumbruch)
                stripped_line = line.strip()
                # Überspringe die Zeile, wenn sie leer oder ein Kommentar ist
                if stripped_line and not stripped_line.startswith('#'):
                    sources.append(stripped_line)
        print(f"[Main] {len(sources)} aktive Datenquellen erfolgreich geladen.")
    except FileNotFoundError:
        print(f"[Main] Fehler: Die Quell-Datei '{file_path}' wurde nicht gefunden.")
        print("[Main] Bitte erstelle die Datei und das 'url'-Verzeichnis oder passe den Pfad an.")
    except Exception as e:
        print(f"[Main] Ein unerwarteter Fehler ist beim Lesen der Quell-Datei aufgetreten: {e}")

    return sources

def main():
    print("Starte den Prozess der Datenerfassung...")
    print("=" * 40)

    all_article_links_globally = []

    DATA_SOURCES = load_data_sources(SOURCES_FILE_PATH)

    if not DATA_SOURCES:
        print("[Main] Keine Datenquellen zum Verarbeiten vorhanden. Das Skript wird beendet.")
        return

    db_handler = DatabaseHandler()

    load_and_compile_country_regex(db_handler)
    load_and_compile_apt_regex(db_handler)

    for source_url in DATA_SOURCES:
        print(f"\n[Main] Verarbeite Hauptquelle: {source_url}")
        # 1. Sammle *alle* potenziellen Links von der Quelle
        try:
            all_links_from_source = article.get_article_links_from_source(source_url)
            if not all_links_from_source:
                print(f"[Main] Keine Artikel-Links von '{source_url}' gefunden.")
                print("-" * 40)
                continue
        except Exception as e:
            print(f"[Main] Ein unerwarteter Fehler ist bei der Verarbeitung von {source_url} aufgetreten: {e}")
            print("-" * 40)
            continue

        print(f"[Main] {len(all_links_from_source)} Links von '{source_url}' gesammelt. Beginne Filterung gegen DB...")

        # 2. Hole bereits bekannte Links aus der DB für diese Domain
        # Wir extrahieren das Schema und die Domain, um ein sauberes Präfix zu haben.
        parsed_uri = urlparse(source_url)
        url_prefix = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        existing_sightings_map = db_handler.get_existing_sightings(url_prefix)

        # 3. Filtere die gesammelten Links
        links_to_process = filter_links_by_timestamp(all_links_from_source, existing_sightings_map)

        skipped_count = len(all_links_from_source) - len(links_to_process)
        print(
            f"[Filter] {len(links_to_process)} Links zur Verarbeitung ausgewählt ({skipped_count} bekannte/aktuelle Links übersprungen).")

        # 4. Füge nur die gefilterten Links zur globalen Liste hinzu
        if links_to_process:
            all_article_links_globally.extend(links_to_process)

        print("-" * 40)

    print("\n==================================================")
    print(
        f"[Main] Modul 1 Zusammenfassung: Insgesamt {len(all_article_links_globally)} Artikel-Links von allen Quellen gesammelt.")

    unique_global_links = []
    if all_article_links_globally:
        unique_global_links = sorted(list(set(all_article_links_globally)))
        print(f"[Main] Nach Entfernung globaler Duplikate: {len(unique_global_links)} einzigartige Artikel-Links.")
    else:
        print("[Main] Keine Artikel-Links zum Weiterverarbeiten gefunden.")
    print("==================================================")

    # ----- Aufruf von Modul 2 -----
    article_contents = []
    if unique_global_links:
        print(f"\n[Main] Übergebe {len(unique_global_links)} einzigartige Links an Modul 2 zur Inhalts-Extraktion...")

        article_contents = text.process_article_links(unique_global_links)  # Aufruf von Modul 2

        print(
            f"\n[Main] Modul 2 Zusammenfassung: {len(article_contents)} Textinhalte/Platzhalter von Modul 2 erhalten.")
        successful_extractions = 0
        for i, content in enumerate(article_contents):
            url_for_content = unique_global_links[i]  # Der korrespondierende Link
            if content:
                successful_extractions += 1
                preview_text = content[:300].replace('\n', ' ')

                print(f"\n  --- Inhalt von Link #{i + 1} ({url_for_content}) ---")
                # Gib nur die ersten 300 Zeichen und die Gesamtlänge aus, um die Konsole nicht zu überfluten
                print(f"  Vorschau: {preview_text}...")
                print(f"  (Gesamtlänge: {len(content)} Zeichen)")
            else:
                print(f"\n  --- Kein Inhalt für Link #{i + 1} ({url_for_content}) extrahiert oder Fehler ---")
        print(
            f"\n[Main] {successful_extractions} von {len(article_contents)} Artikeln erfolgreich mit Inhalt extrahiert.")
    else:
        print("[Main] Keine Links an Modul 2 zu übergeben.")

    print("\n==================================================")
    print("[Main] Verarbeitung mit Modul 2 abgeschlossen.")

    # ----- Aufruf von Modul 3 -----
    annotated_primary_iocs = []
    if article_contents:
        print(
            f"\n[Main] Übergebe {len(article_contents)} Textinhalte (inkl. möglicher None-Einträge) an Modul 3 zur IOC-Extraktion und Assoziierung...")

        annotated_primary_iocs = ioc_context.process_text_contents(article_contents)

        print(f"\n[Main] Modul 3 Zusammenfassung: {len(annotated_primary_iocs)} annotierte primäre IOCs extrahiert.")
        print("\n[Main] Beispielhafte annotierte primäre IOCs (max. erste 20):")

        for i, annotated_ioc in enumerate(annotated_primary_iocs[:20]):
            print(f"  {i + 1}. Primärer IOC: \"{annotated_ioc['ioc_value']}\" (Typ: {annotated_ioc['ioc_type']})")
            print(f"     Artikel-Index: {annotated_ioc['source_article_index']}")


            if annotated_ioc.get("associated_cves"):  # Prüfe, ob der Schlüssel existiert und die Liste nicht leer ist
                print("     Zugehörige CVEs:")
                for cve_info in annotated_ioc["associated_cves"]:
                    print(f"       - {cve_info['value']}")

            if annotated_ioc.get("associated_countries"):
                print("     Zugehörige Länder:")
                for country_info in annotated_ioc["associated_countries"]:
                    print(f"       - {country_info['value']}")

            if annotated_ioc.get("associated_apts"):
                print("     Zugehörige APTs:")
                for apt_info in annotated_ioc["associated_apts"]:
                    apt_display = apt_info['value']
                    if "normalized_value" in apt_info and apt_info['normalized_value'] != apt_info['value']:
                        apt_display += f" (Normalisiert: {apt_info['normalized_value']})"
                    print(f"       - {apt_display}")
            print("     ----")

        if not annotated_primary_iocs:
            print("  Keine annotierten primären IOCs gefunden.")

    else:
        print("[Main] Keine Textinhalte von Modul 2 erhalten, um sie an Modul 3 zu übergeben.")

    print("\n==================================================")
    print("[Main] Verarbeitung mit Modul 3 abgeschlossen.")

    structured_iocs = []
    if annotated_primary_iocs:
        print(
            f"\n[Main] Übergebe {len(annotated_primary_iocs)} annotierte primäre IOCs an Modul 4 zur Strukturierung...")

        structured_iocs = enrichment.process_and_structure_iocs(
            annotated_primary_iocs,
            unique_global_links,
            db_handler
        )

        print(f"\n[Main] Modul 4 Zusammenfassung: {len(structured_iocs)} einzigartige, strukturierte IOCs erstellt.")
        print("\n[Main] Beispielhafte strukturierte IOCs (max. erste 5):")
        for i, ioc in enumerate(structured_iocs[:5]):
            print(f"  {i + 1}. IOC: \"{ioc['ioc_value']}\" (Typ: {ioc['ioc_type']})")
            print(f"     Timestamp: {ioc['discovery_timestamp']}")
            print(f"     Quell-URLs: {ioc['source_article_urls']}")
            print(f"     Vorkommen (aus M3 Reports): {ioc['occurrence_count']}")
            if ioc.get("associated_cves"):
                print(f"     Zugehörige CVEs: {[cve['value'] for cve in ioc['associated_cves']]}")
            if ioc.get("associated_countries"):
                print(f"     Zugehörige Länder: {[country['value'] for country in ioc['associated_countries']]}")
            if ioc.get("associated_apts"):
                print(f"     Zugehörige APTs: {[apt['value'] for apt in ioc['associated_apts']]}")
            print("     ----")
    else:
        print("[Main] Keine Daten von Modul 3 für Modul 4 erhalten.")

    # ----- Aufruf von Modul 5: Datenspeicherung & Ausgabe -----
    if structured_iocs:
        print("\n==================================================")
        print("[Main] Starte Speicherung der Ergebnisse in die Datenbank...")

        # Initialisiere den Database Handler
        db_handler = DatabaseHandler()

        # Gehe durch jeden einzigartigen, strukturierten IOC von Modul 4
        # und füge ihn zur Datenbank hinzu.
        for ioc_record in structured_iocs:
            db_handler.add_structured_ioc_data(ioc_record)

        print("[Main] Datenbank-Verarbeitung abgeschlossen.")

        print(f"\n[Main] Übergebe {len(structured_iocs)} strukturierte IOCs an Modul 5 zur Ausgabe...")

        if CREATE_JSON_PER_IOC:
            write_files.save_iocs_to_json_files(structured_iocs, JSON_OUTPUT_DIR)

        if CREATE_CSV_SUMMARY:
            write_files.save_iocs_to_csv(structured_iocs, CSV_OUTPUT_DIR)

        if CREATE_STIX_BUNDLE:
            write_files.save_iocs_to_stix(structured_iocs, STIX_OUTPUT_DIR)

    else:
        print("[Main] Keine strukturierten IOCs zum Speichern in der Datenbank vorhanden.")
        print("[Main] Modul 5: Keine strukturierten IOCs zum Speichern vorhanden.")

    print("\n==================================================")
    print("[Main] Gesamter Prozess abgeschlossen.")
    print("==================================================")

if __name__ == "__main__":
    main()