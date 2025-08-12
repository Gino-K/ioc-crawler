import datetime
import re

from db.crawler_db_handler import CrawlerDBHandler

def _normalize_ioc_value(ioc_value, ioc_type):
    """Normalisiert den IOC-Wert (z.B. Kleinschreibung fuer Domains/E-Mails)."""
    if ioc_type in ["domain", "email"]:
        return ioc_value.lower()
    return ioc_value


def _add_unique_mention(target_mention_list, seen_mention_values_set, new_mention_item, unique_key_fields):
    """
    Fuegt ein Erwaehnungselement zur Zielliste hinzu, falls es neu ist.
    Die Einzigartigkeit wird durch die Werte der `unique_key_fields` im `new_mention_item` bestimmt.
    """
    key_parts = []
    for field in unique_key_fields:
        key_parts.append(new_mention_item.get(field))

    unique_tuple = tuple(key_parts)

    if unique_tuple not in seen_mention_values_set:
        target_mention_list.append(new_mention_item.copy())
        seen_mention_values_set.add(unique_tuple)


def _proximity_search(text, primary_ioc_value, mentions_list, window=250):
    """
    Sucht, welche Erwaehnungen in der Naehe eines primaeren IOCs im Text vorkommen.
    """
    associated_mentions = []
    for match in re.finditer(r'\b' + re.escape(primary_ioc_value) + r'\b', text, re.IGNORECASE):
        start, end = match.span()
        search_start = max(0, start - window)
        search_end = min(len(text), end + window)
        search_area = text[search_start:search_end]

        for mention in mentions_list:
            mention_value = mention.get('ioc_value')
            if mention_value and re.search(r'\b' + re.escape(mention_value) + r'\b', search_area, re.IGNORECASE):
                associated_mentions.append(mention)

    return associated_mentions


def process_and_structure_iocs(annotated_iocs_from_module3: list,
                               article_texts_map: dict,
                               db_handler: 'CrawlerDBHandler') -> list:
    """
    Normalisiert, dedupliziert und reichert IOCs mittels Proximity-Analyse an,
    um sicherzustellen, dass nur relevante Entitaeten verknuepft werden.
    """
    unique_processed_iocs = {}
    current_discovery_timestamp = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)

    print(f"\n[Modul 4] Starte Strukturierung und Anreicherung mit Proximity-Analyse...")

    items_by_article = {}
    for item in annotated_iocs_from_module3:
        idx = item['source_article_index']
        items_by_article.setdefault(idx, []).append(item)

    with db_handler.Session() as session:
        for article_idx, items in items_by_article.items():
            full_text = article_texts_map['texts'].get(article_idx)
            current_article_url = article_texts_map['urls'][article_idx]
            if not full_text: continue

            primary_iocs = [i for i in items if i['ioc_type'] in ["ipv4", "domain", "md5", "sha256", "file", "email"]]
            cve_mentions = [i for i in items if i['ioc_type'] == 'cve']
            country_mentions = [i for i in items if i['ioc_type'] == 'country_mention']
            apt_mentions = [i for i in items if i['ioc_type'] == 'apt_group_mention']

            for p_ioc in primary_iocs:
                normalized_value = _normalize_ioc_value(p_ioc['ioc_value'], p_ioc['ioc_type'])
                ioc_key = (normalized_value, p_ioc['ioc_type'])

                nearby_cves = _proximity_search(full_text, p_ioc['ioc_value'], cve_mentions)
                nearby_countries = _proximity_search(full_text, p_ioc['ioc_value'], country_mentions)
                nearby_apts = _proximity_search(full_text, p_ioc['ioc_value'], apt_mentions)

                if ioc_key not in unique_processed_iocs:
                    unique_processed_iocs[ioc_key] = {
                        "ioc_value": normalized_value, "ioc_type": p_ioc['ioc_type'],
                        "discovery_timestamp": current_discovery_timestamp,
                        "source_article_urls": {current_article_url},
                        "first_seen_context_snippet": p_ioc.get('context_snippet', ''),
                        "associated_cves": [], "_seen_cve_values_for_ioc": set(),
                        "associated_countries": [], "_seen_country_values_for_ioc": set(),
                        "associated_apts": [], "_seen_apt_values_for_ioc": set(),
                        "occurrence_count": 1
                    }
                else:
                    unique_processed_iocs[ioc_key]["occurrence_count"] += 1
                    unique_processed_iocs[ioc_key]["source_article_urls"].add(current_article_url)

                entry = unique_processed_iocs[ioc_key]
                for cve in nearby_cves:
                    _add_unique_mention(entry['associated_cves'], entry['_seen_cve_values_for_ioc'], cve, ('value',))

                for country in nearby_countries:
                    country_db = db_handler.find_country(session, country['value'])
                    if country_db:
                        country['iso2_code'] = country_db.iso2_code
                    _add_unique_mention(entry['associated_countries'], entry['_seen_country_values_for_ioc'], country,
                                        ('value',))

                for apt in nearby_apts:
                    apt_db = db_handler.find_or_create_apt(session, apt)
                    if apt_db:
                        apt['description'] = apt_db.description
                    _add_unique_mention(entry['associated_apts'], entry['_seen_apt_values_for_ioc'], apt,
                                        ('value', 'normalized_value'))

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
        f"[Modul 4] Strukturierung und Anreicherung abgeschlossen. {len(final_list_of_iocs)} einzigartige IOC-Datensaetze erstellt.")
    return final_list_of_iocs