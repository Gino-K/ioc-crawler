import datetime
from db.database_handler import DatabaseHandler

def _normalize_ioc_value(ioc_value, ioc_type):
    """Normalisiert den IOC-Wert (z.B. Kleinschreibung für Domains/E-Mails)."""
    if ioc_type in ["domain", "email"]:
        return ioc_value.lower()
    return ioc_value


def _add_unique_mention(target_mention_list, seen_mention_values_set, new_mention_item, unique_key_fields):
    """
    Fügt ein Erwähnungselement zur Zielliste hinzu, falls es neu ist.
    Die Einzigartigkeit wird durch die Werte der `unique_key_fields` im `new_mention_item` bestimmt.

    Args:
        target_mention_list (list): Die Liste, zu der das Element hinzugefügt werden soll.
        seen_mention_values_set (set): Ein Set zum Speichern der bereits gesehenen einzigartigen Schlüssel-Tupel.
        new_mention_item (dict): Das hinzuzufügende Erwähnungselement (z.B. {"value": "CVE-...", "context_snippet": "..."}).
        unique_key_fields (tuple): Ein Tupel von Feldnamen, die die Einzigartigkeit definieren
                                   (z.B. ('value',) für CVEs, ('value', 'normalized_value') für APTs).
    """
    key_parts = []
    for field in unique_key_fields:
        key_parts.append(new_mention_item.get(field))

    unique_tuple = tuple(key_parts)

    if unique_tuple not in seen_mention_values_set:
        target_mention_list.append(new_mention_item.copy())
        seen_mention_values_set.add(unique_tuple)


def process_and_structure_iocs(annotated_iocs_from_module3: list,
                               article_urls_list_from_main: list,
                               db_handler: 'DatabaseHandler') -> list:
    """
    Normalisiert, dedupliziert und reichert IOCs aus der Ausgabe von Modul 3 an,
    indem es Daten aus der Datenbank abruft.
    """
    unique_processed_iocs = {}
    current_discovery_timestamp = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)

    print(
        f"\n[Module 4] Starte Strukturierung und Anreicherung für {len(annotated_iocs_from_module3)} Roh-IOC-Einträge von Modul 3...")

    with db_handler.Session() as session:
        for raw_annotated_ioc in annotated_iocs_from_module3:
            original_ioc_value = raw_annotated_ioc['ioc_value']
            ioc_type = raw_annotated_ioc['ioc_type']
            source_article_idx = raw_annotated_ioc['source_article_index']
            primary_ioc_context = raw_annotated_ioc.get('context_snippet', '')

            normalized_ioc_value = _normalize_ioc_value(original_ioc_value, ioc_type)
            ioc_key_tuple = (normalized_ioc_value, ioc_type)

            try:
                current_article_url = article_urls_list_from_main[source_article_idx]
            except IndexError:
                print(f"[Module 4] Warnung: Ungültiger source_article_index ({source_article_idx}).")
                continue

            if ioc_key_tuple not in unique_processed_iocs:
                unique_processed_iocs[ioc_key_tuple] = {
                    "ioc_value": normalized_ioc_value,
                    "ioc_type": ioc_type,
                    "discovery_timestamp": current_discovery_timestamp,
                    "source_article_urls": {current_article_url},
                    "first_seen_context_snippet": primary_ioc_context,
                    "associated_cves": [],
                    "_seen_cve_values_for_ioc": set(),
                    "associated_countries": [],
                    "_seen_country_values_for_ioc": set(),
                    "associated_apts": [],
                    "_seen_apt_values_for_ioc": set(),
                    "occurrence_count": 1
                }
            else:
                unique_processed_iocs[ioc_key_tuple]["occurrence_count"] += 1
                unique_processed_iocs[ioc_key_tuple]["source_article_urls"].add(current_article_url)

            current_unique_ioc_entry = unique_processed_iocs[ioc_key_tuple]

            for country_mention in raw_annotated_ioc.get("associated_countries", []):
                country_db = db_handler.find_country(session, country_mention['value'])
                if country_db:
                    country_mention['iso2_code'] = country_db.iso2_code
                    country_mention['iso3_code'] = country_db.iso3_code
                    country_mention['tld'] = country_db.tld

                _add_unique_mention(
                    current_unique_ioc_entry["associated_countries"],
                    current_unique_ioc_entry["_seen_country_values_for_ioc"],
                    country_mention, ('value',)
                )

            for apt_mention in raw_annotated_ioc.get("associated_apts", []):
                apt_db = db_handler._find_or_create_apt(session, apt_mention)
                if apt_db:
                    apt_mention['description'] = apt_db.description
                    apt_mention['aliases'] = apt_db.aliases

                _add_unique_mention(
                    current_unique_ioc_entry["associated_apts"],
                    current_unique_ioc_entry["_seen_apt_values_for_ioc"],
                    apt_mention, ('value', 'normalized_value')
                )

            for cve_mention in raw_annotated_ioc.get("associated_cves", []):
                _add_unique_mention(
                    current_unique_ioc_entry["associated_cves"],
                    current_unique_ioc_entry["_seen_cve_values_for_ioc"],
                    cve_mention, ('value',)
                )

    final_list_of_iocs = []
    for ioc_data_dict in unique_processed_iocs.values():
        ioc_data_dict["source_article_urls"] = sorted(list(ioc_data_dict["source_article_urls"]))
        ioc_data_dict.pop("_seen_cve_values_for_ioc", None)
        ioc_data_dict.pop("_seen_country_values_for_ioc", None)
        ioc_data_dict.pop("_seen_apt_values_for_ioc", None)

        if not ioc_data_dict.get("associated_cves"): ioc_data_dict.pop("associated_cves", None)
        if not ioc_data_dict.get("associated_countries"): ioc_data_dict.pop("associated_countries", None)
        if not ioc_data_dict.get("associated_apts"): ioc_data_dict.pop("associated_apts", None)

        final_list_of_iocs.append(ioc_data_dict)

    print(
        f"[Module 4] Strukturierung und Anreicherung abgeschlossen. {len(final_list_of_iocs)} einzigartige, strukturierte IOC-Datensätze erstellt.")
    return final_list_of_iocs