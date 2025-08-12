import json
import os
import re
import csv
from urllib.parse import urlparse
import stix2

def _sanitize_filename(name_part, max_length=100):
    """
    Bereinigt einen String, um ihn als Teil eines Dateinamens verwenden zu koennen.
    Ersetzt problematische Zeichen und kaerzt ihn bei Bedarf.
    """
    if not isinstance(name_part, str):
        name_part = str(name_part)

    name_part = name_part.replace("://", "_protocol_")
    name_part = name_part.replace(":", "_colon_")
    name_part = name_part.replace("/", "_slash_")
    name_part = name_part.replace("\\", "_backslash_")
    name_part = name_part.replace("*", "_star_")
    name_part = name_part.replace("?", "_question_")
    name_part = name_part.replace("<", "_lt_")
    name_part = name_part.replace(">", "_gt_")
    name_part = name_part.replace("|", "_pipe_")
    name_part = name_part.replace("\"", "_quote_")


    name_part = re.sub(r'[^\w.-]', '_', name_part)

    name_part = re.sub(r'_+', '_', name_part)

    name_part = name_part.strip('._')

    if len(name_part) > max_length:

        name_part = name_part[:max_length]
        name_part = name_part.strip(
            '._')

    if not name_part:
        return "default_ioc_name"

    return name_part


def save_iocs_to_json_files(structured_iocs_list, output_directory):
    """
    Speichert jeden strukturierten IOC-Datensatz aus der Liste in eine eigene JSON-Datei.

    Args:
        structured_iocs_list (list): Liste der einzigartigen, strukturierten und angereicherten
                                     IOC-Datensaetze von Modul 4.
        output_directory (str): Das Verzeichnis, in dem die JSON-Dateien gespeichert werden sollen.
    """
    if not structured_iocs_list:
        print("[Module 5] Keine strukturierten IOCs zum Speichern erhalten.")
        return 0

    try:
        os.makedirs(output_directory, exist_ok=True)
        print(f"[Module 5] JSON-Dateien werden im Verzeichnis gespeichert: {os.path.abspath(output_directory)}")
    except OSError as e:
        print(
            f"[Module 5] Fehler: Konnte das Ausgabeverzeichnis '{output_directory}' nicht erstellen oder darauf zugreifen: {e}")
        return 0

    files_saved_count = 0
    for ioc_record in structured_iocs_list:
        ioc_type = ioc_record.get('ioc_type', 'unknown_type')
        ioc_value = ioc_record.get('ioc_value', 'unknown_value')

        sanitized_value_for_filename = _sanitize_filename(ioc_value)

        json_filename = f"{ioc_type}_{sanitized_value_for_filename}.json"
        full_filepath = os.path.join(output_directory, json_filename)

        try:
            with open(full_filepath, 'w', encoding='utf-8') as f:
                json.dump(ioc_record, f, indent=4, ensure_ascii=False, default=str)
            files_saved_count += 1
        except IOError as e:
            print(f"[Module 5] Fehler beim Schreiben der Datei '{full_filepath}': {e}")
        except TypeError as e:
            print(
                f"[Module 5] Fehler: Daten faer IOC '{ioc_value}' (Typ: {ioc_type}) sind nicht JSON-serialisierbar: {e}")
        except Exception as e:
            print(f"[Module 5] Ein unerwarteter Fehler ist beim Speichern von IOC '{ioc_value}' aufgetreten: {e}")

    print(
        f"[Module 5] Speicherung abgeschlossen. {files_saved_count} IOC(s) in separate JSON-Dateien im Verzeichnis '{os.path.abspath(output_directory)}' gespeichert.")
    return files_saved_count


def save_iocs_to_csv(structured_iocs_list, output_directory, filename="iocs_summary.csv"):
    """
    Speichert eine Zusammenfassung der strukturierten IOC-Datensaetze in einer einzigen CSV-Datei.
    Listen-artige Felder werden durch ein Trennzeichen getrennt.

    """
    if not structured_iocs_list:
        print("[Module 5] CSV: Keine strukturierten IOCs zum Speichern erhalten.")
        return 0

    try:
        os.makedirs(output_directory, exist_ok=True)
    except OSError as e:
        print(f"[Module 5] CSV-Fehler: Konnte das Ausgabeverzeichnis '{output_directory}' nicht erstellen: {e}")
        return 0

    filepath = os.path.join(output_directory, filename)
    print(f"[Module 5] CSV-Datei wird erstellt: {os.path.abspath(filepath)}")

    headers = [
        "ioc_value", "ioc_type", "discovery_timestamp", "occurrence_count",
        "source_article_urls", "first_seen_context_snippet", "associated_cves",
        "associated_countries", "associated_apts", "normalized_apts"
    ]

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            for ioc_record in structured_iocs_list:
                source_urls_str = "|".join(ioc_record.get("source_article_urls", []))

                context_str = ioc_record.get("first_seen_context_snippet", "").replace('\n', ' ').replace('\r', '')

                cves_str = ";".join([cve['value'] for cve in ioc_record.get("associated_cves", [])])
                countries_str = ";".join([country['value'] for country in ioc_record.get("associated_countries", [])])
                apts_str = ";".join([apt['value'] for apt in ioc_record.get("associated_apts", [])])

                normalized_apts_str = ";".join(
                    [apt.get('normalized_value', apt['value']) for apt in ioc_record.get("associated_apts", [])]
                )

                row = {
                    "ioc_value": ioc_record.get("ioc_value"),
                    "ioc_type": ioc_record.get("ioc_type"),
                    "discovery_timestamp": str(ioc_record.get("discovery_timestamp")),
                    "occurrence_count": ioc_record.get("occurrence_count"),
                    "source_article_urls": source_urls_str,
                    "first_seen_context_snippet": context_str,
                    "associated_cves": cves_str,
                    "associated_countries": countries_str,
                    "associated_apts": apts_str,
                    "normalized_apts": normalized_apts_str
                }
                writer.writerow(row)

        print(
            f"[Module 5] CSV-Speicherung abgeschlossen. {len(structured_iocs_list)} IOCs in '{filepath}' geschrieben.")
        return len(structured_iocs_list)
    except IOError as e:
        print(f"[Module 5] CSV-Fehler: Konnte nicht in Datei schreiben '{filepath}': {e}")
        return 0
    except Exception as e:
        print(f"[Module 5] Ein unerwarteter Fehler ist beim Erstellen der CSV-Datei aufgetreten: {e}")
        return 0


def save_iocs_to_stix(structured_iocs_list, output_directory, filename="threat_intel_bundle.json"):
    """
    Erstellt ein STIX 2.1 Bundle aus den strukturierten IOCs und speichert es als JSON-Datei.

    Args:
        structured_iocs_list (list): Liste der einzigartigen, strukturierten IOCs von Modul 4.
        output_directory (str): Das Verzeichnis, in dem die STIX-Datei gespeichert wird.
        filename (str): Der Dateiname faer das STIX Bundle.
    """
    if not structured_iocs_list:
        print("[Module 5] STIX: Keine strukturierten IOCs zum Speichern erhalten.")
        return 0

    try:
        os.makedirs(output_directory, exist_ok=True)
    except OSError as e:
        print(f"[Module 5] STIX-Fehler: Konnte das Ausgabeverzeichnis '{output_directory}' nicht erstellen: {e}")
        return 0

    filepath = os.path.join(output_directory, filename)
    print(f"[Module 5] STIX Bundle wird erstellt: {os.path.abspath(filepath)}")

    created_reports = {}
    created_apts = {}
    created_locations = {}
    created_vulnerabilities = {}
    all_stix_objects = []

    for ioc_record in structured_iocs_list:
        primary_sco = None
        ioc_type = ioc_record["ioc_type"]
        ioc_value = ioc_record["ioc_value"]

        if ioc_type == "ipv4":
            primary_sco = stix2.IPv4Address(value=ioc_value)
        elif ioc_type == "domain":
            primary_sco = stix2.DomainName(value=ioc_value)
        elif ioc_type == "email":
            primary_sco = stix2.EmailAddress(value=ioc_value)
        elif ioc_type in ["md5", "sha1", "sha256", "sha512"]:
            primary_sco = stix2.File(hashes={ioc_type.upper(): ioc_value})
        elif ioc_type == "file":
            primary_sco = stix2.File(name=ioc_value)

        if not primary_sco:
            continue

        all_stix_objects.append(primary_sco)

        apts = []
        for apt_info in ioc_record.get("associated_apts", []):
            norm_name = apt_info["normalized_value"]
            if norm_name not in created_apts:
                created_apts[norm_name] = stix2.IntrusionSet(name=norm_name, aliases=[apt_info["value"]])
                all_stix_objects.append(created_apts[norm_name])
            apts.append(created_apts[norm_name])

        vulnerabilities = []
        for cve_info in ioc_record.get("associated_cves", []):
            cve_name = cve_info["value"].upper()
            if cve_name not in created_vulnerabilities:
                created_vulnerabilities[cve_name] = stix2.Vulnerability(name=cve_name)
                all_stix_objects.append(created_vulnerabilities[cve_name])
            vulnerabilities.append(created_vulnerabilities[cve_name])

        locations = []
        for country_info in ioc_record.get("associated_countries", []):
            iso_code = country_info.get("iso2_code")
            country_name = country_info["value"]

            if iso_code and iso_code not in created_locations:
                created_locations[iso_code] = stix2.Location(country=iso_code, name=country_name.title())
                all_stix_objects.append(created_locations[iso_code])
            if iso_code:
                locations.append(created_locations[iso_code])

        for apt_sdo in apts:
            rel = stix2.Relationship(apt_sdo, "uses", primary_sco)
            all_stix_objects.append(rel)
            for vuln_sdo in vulnerabilities:
                rel_vuln = stix2.Relationship(apt_sdo, "targets", vuln_sdo)
                all_stix_objects.append(rel_vuln)
            for loc_sdo in locations:
                rel_loc = stix2.Relationship(apt_sdo, "originates-from", loc_sdo)
                all_stix_objects.append(rel_loc)

        for url in ioc_record.get("source_article_urls", []):
            if url not in created_reports:
                report_desc = f"Threat intelligence report sourced from the article at {url}."
                report_name = f"Report from {urlparse(url).netloc}" if "urlparse" in globals() else f"Report from {url}"
                created_reports[url] = stix2.Report(
                    name=report_name,
                    description=report_desc,
                    published=ioc_record["discovery_timestamp"],
                    report_types=['threat-report'],
                    object_refs=[primary_sco.id]
                )
                all_stix_objects.append(created_reports[url])
            else:
                if primary_sco.id not in created_reports[url].object_refs:
                    created_reports[url].object_refs.append(primary_sco.id)

    try:
        bundle = stix2.Bundle(all_stix_objects, spec_version="2.1", allow_custom=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(bundle.serialize(indent=4))

        print(
            f"[Module 5] STIX-Speicherung abgeschlossen. {len(all_stix_objects)} STIX-Objekte in '{filepath}' geschrieben.")
        return len(all_stix_objects)
    except Exception as e:
        print(f"[Module 5] STIX-Fehler: Konnte das Bundle nicht erstellen oder speichern: {e}")
        return 0

