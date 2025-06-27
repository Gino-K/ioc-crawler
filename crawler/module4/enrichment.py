import datetime


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


def process_and_structure_iocs(annotated_iocs_from_module3, article_urls_list_from_main):
    """
    Normalisiert, dedupliziert und reichert IOCs aus der Ausgabe von Modul 3 an.

    Args:
        annotated_iocs_from_module3 (list): Liste der annotierten IOCs von Modul 3.
            Jedes Element ist ein Dict, das einen primären IOC und optional
            assoziierte Erwähnungen ('associated_cves', 'associated_countries', 'associated_apts') enthält.
        article_urls_list_from_main (list): Liste der eindeutigen Artikel-URLs,
            wobei der Index dem `source_article_index` der IOCs entspricht.

    Returns:
        list: Eine Liste von einzigartigen, strukturierten und angereicherten IOC-Datensätzen.
    """
    unique_processed_iocs = {}

    current_discovery_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    print(
        f"\n[Module 4] Starte Strukturierung und Normalisierung für {len(annotated_iocs_from_module3)} Roh-IOC-Einträge von Modul 3...")

    for raw_annotated_ioc in annotated_iocs_from_module3:
        original_ioc_value = raw_annotated_ioc['ioc_value']
        ioc_type = raw_annotated_ioc['ioc_type']
        source_article_idx = raw_annotated_ioc['source_article_index']
        # Kontext des primären IOCs vom ersten Fund (Modul 3 liefert dies bereits so)
        primary_ioc_context = raw_annotated_ioc.get('context_snippet', '')

        # Schritt 1: Normalisiere den primären IOC-Wert
        normalized_ioc_value = _normalize_ioc_value(original_ioc_value, ioc_type)

        # Eindeutiger Schlüssel für diesen primären IOC
        ioc_key_tuple = (normalized_ioc_value, ioc_type)

        # Hole die Artikel-URL
        try:
            current_article_url = article_urls_list_from_main[source_article_idx]
        except IndexError:
            print(
                f"[Module 4] Warnung: Ungültiger source_article_index ({source_article_idx}) für IOC {normalized_ioc_value}. Verwende 'URL_NOT_FOUND'.")
            current_article_url = "URL_NOT_FOUND"

        # Schritt 2: Prüfe, ob dieser primäre IOC schon gesehen wurde
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

        # Schritt 3: Füge assoziierte Erwähnungen hinzu/merge sie (und dedupliziere sie dabei)
        # Hole den aktuellen Eintrag für diesen einzigartigen primären IOC
        current_unique_ioc_entry = unique_processed_iocs[ioc_key_tuple]

        # Verarbeite assoziierte CVEs
        for cve_mention in raw_annotated_ioc.get("associated_cves", []):
            _add_unique_mention(
                current_unique_ioc_entry["associated_cves"],
                current_unique_ioc_entry["_seen_cve_values_for_ioc"],
                cve_mention,
                ('value',)  # Einzigartigkeit für CVEs basiert auf ihrem 'value'
            )

        # Verarbeite assoziierte Länder
        for country_mention in raw_annotated_ioc.get("associated_countries", []):
            _add_unique_mention(
                current_unique_ioc_entry["associated_countries"],
                current_unique_ioc_entry["_seen_country_values_for_ioc"],
                country_mention,
                ('value',)  # Einzigartigkeit für Länder basiert auf ihrem 'value'
            )

        # Verarbeite assoziierte APTs
        for apt_mention in raw_annotated_ioc.get("associated_apts", []):
            # Einzigartigkeit für APTs basiert auf ('value', 'normalized_value'),
            # um z.B. "APT 28" (value) und "Fancy Bear" (value) als unterschiedliche Erwähnungen
            # desselben normalisierten "APT28" zu behandeln, wenn gewünscht.
            # Oder nur ('normalized_value',), wenn nur eine Erwähnung pro normalisierter APT gewünscht ist.
            # Die aktuelle Implementierung von _add_unique_mention mit ('value', 'normalized_value')
            # würde "APT 28 (APT28)" und "Fancy Bear (APT28)" als separate Einträge in associated_apts erlauben.
            _add_unique_mention(
                current_unique_ioc_entry["associated_apts"],
                current_unique_ioc_entry["_seen_apt_values_for_ioc"],
                apt_mention,
                ('value', 'normalized_value')
            )

    # Schritt 4: Finale Aufbereitung der Ergebnisliste
    final_list_of_iocs = []
    for ioc_data_dict in unique_processed_iocs.values():
        # Konvertiere das Set der Quell-URLs in eine sortierte Liste
        ioc_data_dict["source_article_urls"] = sorted(list(ioc_data_dict["source_article_urls"]))

        # Entferne die temporären "_seen_..." Sets
        ioc_data_dict.pop("_seen_cve_values_for_ioc", None)
        ioc_data_dict.pop("_seen_country_values_for_ioc", None)
        ioc_data_dict.pop("_seen_apt_values_for_ioc", None)

        # Entferne leere Assoziationslisten für eine sauberere Ausgabe
        if not ioc_data_dict["associated_cves"]: ioc_data_dict.pop("associated_cves", None)
        if not ioc_data_dict["associated_countries"]: ioc_data_dict.pop("associated_countries", None)
        if not ioc_data_dict["associated_apts"]: ioc_data_dict.pop("associated_apts", None)

        final_list_of_iocs.append(ioc_data_dict)

    print(
        f"[Module 4] Strukturierung abgeschlossen. {len(final_list_of_iocs)} einzigartige, strukturierte IOC-Datensätze erstellt.")
    return final_list_of_iocs