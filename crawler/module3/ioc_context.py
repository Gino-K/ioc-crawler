import re

from db.database_handler import DatabaseHandler
from db.database_models import APT, Country

IOC_REGEXES = {
    "ipv4": re.compile(r'\b(?:[0-9]{1,3}(?:\[\.\]|\(\.\)|[\s.])){3}[0-9]{1,3}\b'),
    "domain": re.compile(
        r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\[\.\]|\(\.\)|\.)){1,}[a-zA-Z]{2,24}\b'),
    "md5": re.compile(r'\b[a-fA-F0-9]{32}\b'),
    "sha1": re.compile(r'\b[a-fA-F0-9]{40}\b'),
    "sha256": re.compile(r'\b[a-fA-F0-9]{64}\b'),
    "sha512": re.compile(r'\b[a-fA-F0-9]{128}\b'),
    "cve": re.compile(r'\bCVE-(?:1999|2\d{3})-(?:0\d{2}[1-9]|[1-9]\d{3,})\b', re.IGNORECASE),
    "ipv6": re.compile(r'\b(?:[0-9a-fA-F]{1,4}(?:\[:\]|:)){2,7}[0-9a-fA-F]{1,4}\b', re.IGNORECASE),
    "email": re.compile(r'\b[a-zA-Z0-9._%+-]+(?:@|\[@\])[a-zA-Z0-9.-]+(?:\[\.\]|\.)[a-zA-Z]{2,24}\b', re.IGNORECASE),
    "file": re.compile(
        r'\b[a-zA-Z0-9_~@#$\%\^\&\'\(\)\.\-]+'  # Erlaubt mehr Zeichen im Dateinamensteil
        r'\.(?:exe|dll|bat|sh|ps1|vbs|js|jar|py|docm|xlsm|pptm|pdf|zip|rar|tar|gz|dat|tmp|log|ini|conf|config|xml|json|doc|docx|xls|xlsx|ppt|pptx|pem|key|cer|txt|rtf|lnk|scr|com)\b',
        re.IGNORECASE
    )
}

# Liste von Dateiendungen, die oft fälschlicherweise als Domains erkannt werden könnten
COMMON_FILE_EXTENSIONS = (
    ".exe", ".dll", ".sys", ".bat", ".ps1", ".sh", ".py", ".js",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".svg",
    ".pdf", ".txt", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".iso", ".img",
    ".cer", ".pem", ".key", ".csr",
    ".html", ".htm", ".css", ".json", ".xml", ".yaml", ".yml",
    ".log", ".bak", ".tmp", ".temp", ".cfg", ".ini", ".conf"
)

COMPILED_APT_REGEX = None
APT_NAME_MAP = {}

COMPILED_COUNTRY_REGEX = None


def load_and_compile_apt_regex(db_handler: DatabaseHandler):
    """
    Lädt alle APT-Gruppen und ihre Aliase aus der Datenbank.
    Erstellt daraus einen Regex, der auch gängige Schreibvarianten (z.B. mit Leerzeichen)
    automatisch berücksichtigt.
    """
    global COMPILED_APT_REGEX, APT_NAME_MAP

    print("[Module 3] Lade APT-Liste aus der Datenbank für Regex-Erstellung...")
    with db_handler.Session() as session:
        apts = session.query(APT).all()
        if not apts:
            print("[Module 3] WARNUNG: Keine APTs in der DB. APT-Erkennung wird nicht funktionieren.")
            COMPILED_APT_REGEX = re.compile(r'a^')
            return

        all_names_to_search = set()
        temp_name_map = {}

        for apt in apts:
            main_name = apt.name
            if not main_name:
                continue

            all_names_to_search.add(main_name)
            temp_name_map[main_name.lower()] = main_name

            # Erstelle automatisch Variationen
            # Wenn der Name wie "APT28" oder "FIN10" aussieht
            match = re.match(r'([a-zA-Z]+)(\d+)', main_name)
            if match:
                # ...erstelle eine Version mit Leerzeichen, z.B. "APT 28"
                variation_with_space = f"{match.group(1)} {match.group(2)}"
                all_names_to_search.add(variation_with_space)
                # Mappe auch die Variation auf den Hauptnamen
                temp_name_map[variation_with_space.lower()] = main_name

            # Verarbeite die offiziellen Aliase aus der Datenbank
            if apt.aliases:
                aliases = [alias.strip() for alias in apt.aliases.split(',')]
                for alias in aliases:
                    if alias:
                        all_names_to_search.add(alias)
                        temp_name_map[alias.lower()] = main_name

        # Sortiere die finale Liste nach Länge für eine robuste Regex
        sorted_unique_names = sorted(list(all_names_to_search), key=len, reverse=True)

        apt_pattern = r'\b(?:' + '|'.join(re.escape(name) for name in sorted_unique_names) + r')\b'

        COMPILED_APT_REGEX = re.compile(apt_pattern, re.IGNORECASE)
        APT_NAME_MAP = {key.lower(): value for key, value in temp_name_map.items()}

        print(f"[Module 3] Regex für {len(sorted_unique_names)} APT-Namen/Aliase/Variationen erfolgreich erstellt.")


def load_and_compile_country_regex(db_handler: DatabaseHandler):
    """
    Lädt alle Ländernamen aus der Datenbank und erstellt daraus einen einzigen,
    kompilierten Regex-Pattern für die schnelle Suche.
    """
    global COMPILED_COUNTRY_REGEX

    print("[Module 3] Lade Länderliste aus der Datenbank für Regex-Erstellung...")
    with db_handler.Session() as session:
        countries = session.query(Country).all()
        if not countries:
            print(
                "[Module 3] WARNUNG: Keine Länder in der Datenbank gefunden. Ländererkennung wird nicht funktionieren.")
            COMPILED_COUNTRY_REGEX = re.compile(r'a^')
            return

        country_names = [country.name for country in countries]
        print(f"[Module 3] {len(country_names)} Länder aus der DB geladen.")

        sorted_names = sorted(country_names, key=len, reverse=True)

        country_pattern = r'\b(?:' + '|'.join(re.escape(name) for name in sorted_names) + r')\b'

        COMPILED_COUNTRY_REGEX = re.compile(country_pattern, re.IGNORECASE)
        print("[Module 3] Regex für Ländererkennung erfolgreich erstellt.")


def refang_ioc(ioc_value, ioc_type):
    """
    Konvertiert "defangte" IOCs in ihr Standardformat.
    """
    refanged = ioc_value
    refanged = refanged.replace("[.]", ".").replace("(.)", ".")
    refanged = refanged.replace("[:]", ":")

    if ioc_type == "email":
        refanged = refanged.replace("[@]", "@")

    if ioc_type in ["domain", "url", "email"]:  # Domain-Teil von E-Mails auch behandeln
        if refanged.lower().startswith("hxxp://"):
            refanged = "http://" + refanged[len("hxxp://"):]
        elif refanged.lower().startswith("hxxps://"):
            refanged = "https://" + refanged[len("hxxps://"):]

        if not ioc_type == "email":  # Für reine Domains/URLs, nicht für den Hostteil einer E-Mail-Adresse
            if refanged.endswith('.') and not refanged.endswith('..'):
                parts = refanged[:-1].split('.')
                if len(parts) > 1 and 2 <= len(parts[-1]) <= 24:
                    refanged = refanged[:-1]

    elif ioc_type == "ipv4":
        refanged = refanged.replace(" ", ".")

    return refanged.strip()


def _extract_iocs_with_regex(text, ioc_type, regex, article_index, context_window=35):
    """
    Hilfsfunktion zur Extraktion von IOCs mit einem gegebenen Regex.
    """
    found_iocs_list = []
    for match in regex.finditer(text):
        raw_ioc = match.group(0)

        # Spezifische Filterung für Domains, um False Positives zu reduzieren
        if ioc_type == "domain":
            # Überspringe, wenn es wahrscheinlich eine Dateiendung ist
            if raw_ioc.lower().endswith(COMMON_FILE_EXTENSIONS):
                continue
            # Überspringe, wenn es nicht mindestens einen Punkt enthält oder zu kurz ist
            if '.' not in raw_ioc or len(raw_ioc) < 4:  # z.B. "a.b" ist zu kurz
                continue
            # Überspringe, wenn es mit "http" oder "https" beginnt (dies sollte idealerweise als URL klassifiziert werden,
            # aber unsere Domain-Regex ist gierig. Hier eine einfache Korrektur)
            if raw_ioc.lower().startswith(("http://", "https://", "hxxp://", "hxxps://")):
                # Versuche, nur den Hostnamen zu extrahieren, wenn möglich
                try:
                    parsed_hostname = re.match(r'^(?:hxxps?|https?)://([^/\s]+)', raw_ioc.lower(), re.IGNORECASE)
                    if parsed_hostname:
                        raw_ioc = parsed_hostname.group(1)
                    else:  # Wenn es nicht dem URL-Muster mit Host entspricht, überspringen
                        continue
                except Exception:  # Bei Fehlern im Parsing überspringen
                    continue

        refanged_ioc = refang_ioc(raw_ioc, ioc_type)

        # Zusätzliche Validierung nach dem Refanging (Beispiel für IPv4)
        if ioc_type == "ipv4":
            octets = refanged_ioc.split('.')
            if len(octets) == 4:
                valid_octets = True
                for octet in octets:
                    if not (octet.isdigit() and 0 <= int(octet) <= 255):
                        valid_octets = False
                        break
                if not valid_octets:
                    continue  # Ungültige IP-Adresse (z.B. 999.1.1.1)
            else:  # Nicht das Format x.x.x.x
                continue

        # Kontext-Snippet erstellen
        start_index = max(0, match.start() - context_window)
        end_index = min(len(text), match.end() + context_window)
        snippet = text[start_index:end_index].replace("\n", " ")  # Newlines im Snippet ersetzen

        ioc_entry = {
            "ioc_value": refanged_ioc,
            "ioc_type": ioc_type,
            "source_article_index": article_index,  # Index des Artikels in der Ursprungsliste
            "context_snippet": f"...{snippet}..."
        }
        found_iocs_list.append(ioc_entry)
    return found_iocs_list


def extract_iocs_from_text(text_content, article_idx):
    """
    Extrahiert alle definierten IOC-Typen aus einem einzelnen Textstück.
    """
    if not text_content or not isinstance(text_content, str):
        return []

    collected_iocs = []

    # 1. Standard-IOCs basierend auf IOC_REGEXES
    for ioc_type_key, regex_pattern in IOC_REGEXES.items():
        collected_iocs.extend(
            _extract_iocs_with_regex(text_content, ioc_type_key, regex_pattern, article_idx)
        )

    # 2. APT-Gruppen-Erwähnungen
    for match in COMPILED_APT_REGEX.finditer(text_content):
        # Der im Text gefundene Name/Alias (z.B. "Fancy Bear")
        matched_text = match.group(0)
        normalized_name = APT_NAME_MAP.get(matched_text.lower(), matched_text)

        start_idx = max(0, match.start() - 35)
        end_idx = min(len(text_content), match.end() + 35)
        snippet = text_content[start_idx:end_idx].replace("\n", " ")

        ioc_entry = {
            "ioc_value": matched_text,
            "ioc_type": "apt_group_mention",
            "normalized_value": normalized_name,
            "source_article_index": article_idx,
            "context_snippet": f"...{snippet}..."
        }
        collected_iocs.append(ioc_entry)

    # 3. Länder-Erwähnungen
    for match in COMPILED_COUNTRY_REGEX.finditer(text_content):
        country_name_found = match.group(0)
        start_idx = max(0, match.start() - 35)
        end_idx = min(len(text_content), match.end() + 35)
        snippet = text_content[start_idx:end_idx].replace("\n", " ")

        ioc_entry = {
            "ioc_value": country_name_found,  # Das gefundene Land
            "ioc_type": "country_mention",
            "source_article_index": article_idx,
            "context_snippet": f"...{snippet}..."
        }
        collected_iocs.append(ioc_entry)

    return collected_iocs


def process_text_contents(article_texts_list):
    """
    Verarbeitet eine Liste von Textinhalten, extrahiert IOCs und Erwähnungen
    und assoziiert Erwähnungen (CVEs, Länder, APTs) mit den primären IOCs
    aus demselben Artikel.
    """
    master_annotated_ioc_list = []
    if not article_texts_list:
        print("[Module 3] Keine Textinhalte zur Verarbeitung erhalten.")
        return master_annotated_ioc_list

    print(f"\n[Module 3] Starte IOC-Extraktion und -Assoziierung für {len(article_texts_list)} Textinhalte...")

    primary_ioc_types = ["ipv4", "ipv6", "domain", "md5", "sha1", "sha256", "sha512", "email", "file"]
    mention_type_to_key_map = {
        "cve": "associated_cves",
        "country_mention": "associated_countries",
        "apt_group_mention": "associated_apts"
    }

    for current_article_index, text_item in enumerate(article_texts_list):
        if not (text_item and isinstance(text_item, str)):
            print(
                f"[Module 3] Überspringe Artikel #{current_article_index}, da kein gültiger Textinhalt vorhanden ist.")
            continue

        print(f"[Module 3] --- Verarbeite Artikel #{current_article_index} ---")

        # Schritt 1: Extrahiere ALLE Items (primäre IOCs und Erwähnungen) aus dem aktuellen Artikel
        all_items_in_article = extract_iocs_from_text(text_item, current_article_index)

        if not all_items_in_article:
            print(
                f"[Module 3] Keine primären IOCs oder relevanten Erwähnungen in Artikel #{current_article_index} gefunden.")
            continue

        # Schritt 2: Trenne primäre IOCs von Erwähnungen für diesen Artikel
        current_primary_iocs = []
        current_mentions_by_type = {
            "associated_cves": [],
            "associated_countries": [],
            "associated_apts": []
        }

        for item in all_items_in_article:
            item_type = item['ioc_type']
            if item_type in primary_ioc_types:
                current_primary_iocs.append(item)
            elif item_type in mention_type_to_key_map:
                association_key = mention_type_to_key_map[item_type]

                # Speichere die relevanten Details der Erwähnung
                mention_detail = {"value": item["ioc_value"]}
                if "context_snippet" in item:
                    mention_detail["context_snippet"] = item["context_snippet"]
                if item_type == "apt_group_mention" and "normalized_value" in item:
                    mention_detail["normalized_value"] = item["normalized_value"]

                current_mentions_by_type[association_key].append(mention_detail)

        # Schritt 3: Wenn primäre IOCs gefunden wurden, annotiere jeden mit allen Erwähnungen aus diesem Artikel
        if current_primary_iocs:
            for p_ioc in current_primary_iocs:
                annotated_ioc = p_ioc.copy()  # Beginne mit den Details des primären IOCs

                # Füge assoziierte Erwähnungen hinzu, falls vorhanden
                for key, mentions_list in current_mentions_by_type.items():
                    if mentions_list:  # Nur hinzufügen, wenn die Liste nicht leer ist
                        annotated_ioc[key] = mentions_list

                master_annotated_ioc_list.append(annotated_ioc)
            print(
                f"[Module 3] {len(current_primary_iocs)} primäre IOCs für Artikel #{current_article_index} mit {sum(len(v) for v in current_mentions_by_type.values())} Erwähnungen assoziiert.")

        # Fall: Es gibt Erwähnungen, aber KEINE primären IOCs im Artikel
        elif any(current_mentions_by_type.values()):
            print(
                f"[Module 3] Artikel #{current_article_index} enthält {sum(len(v) for v in current_mentions_by_type.values())} Erwähnungen, aber keine primären IOCs. "
                "Diese Erwähnungen werden in der aktuellen Ausgabestruktur nicht separat aufgeführt, da sie nicht mit einem primären IOC verknüpft werden können.")
    print(
        f"[Module 3] IOC-Extraktion und -Assoziierung abgeschlossen. Insgesamt {len(master_annotated_ioc_list)} annotierte primäre IOCs gefunden.")
    return master_annotated_ioc_list
