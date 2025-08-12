import ipaddress
import json
import re
from pathlib import Path
from typing import Dict, Set
from urllib.parse import urlparse

from crawler.module3.ioc_normalization import refang_ioc
from db.crawler_db_handler import CrawlerDBHandler
from db.database_models import APT, Country


def _normalize_apt_name(name: str) -> str:
    """Eine zentrale Funktion zur Normalisierung von APT-Namen und Aliasen."""
    if not name:
        return ""
    return name.lower().replace('-', '').replace(' ', '')


def _find_project_root():
    """Findet das Projekt-Hauptverzeichnis, indem es nach der .gitignore-Datei sucht."""
    current_path = Path(__file__).resolve()
    while not (current_path / '.gitignore').exists():
        if current_path.parent == current_path:
            return Path.cwd()
        current_path = current_path.parent
    return current_path

def _normalize_text_for_regex(text: str) -> str:
    """Bereinigt einen Text aggressiv fuer die Regex-Verarbeitung."""
    if not text:
        return ""
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


class IOCExtractor:
    """
    Eine in sich geschlossene Klasse, die die gesamte Logik zur IOC-Extraktion handhabt.
    Sie laedt alle notwendigen Referenzdaten bei der Initialisierung.
    """

    COMMON_FILE_EXTENSIONS = (
        ".exe", ".dll", ".sys", ".bat", ".ps1", ".sh", ".py", ".js", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff",
        ".svg", ".pdf", ".txt", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar", ".7z", ".tar", ".gz", ".iso",
        ".img",".cer", ".pem", ".key", ".csr", ".html", ".htm", ".css", ".json", ".xml", ".yaml", ".yml", ".query",
        ".log", ".bak", ".tmp", ".temp", ".cfg", ".ini", ".conf"
    )

    def __init__(self, db_handler: CrawlerDBHandler):
        """Initialisiert den Extraktor und laedt alle Referenzdaten nur einmal."""
        print("[IOCExtractor] Initialisiere und lade Referenzdaten...")
        self.db_handler = db_handler

        extensions_pattern = '|'.join([ext.lstrip('.') for ext in self.COMMON_FILE_EXTENSIONS])
        file_regex_pattern = (
            r'([^\s"]+?)\.'
            rf'(?:{extensions_pattern})'
            r'(?=[\s,;]|\Z|$)'
        )

        self.IOC_REGEXES = {
            "url": re.compile(r'\b(?:hxxps?|https?|ftps?)://[^\s/$.?#].\S*\b', re.IGNORECASE),
            "ipv4": re.compile(r'\b((?:(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(?:\[\.\]|\.|\s)){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9]))\b'),
            "domain": re.compile(
                r'(?<!@)\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\[\.]|\(\.\)|\.))+[a-zA-Z]{2,24}\b'),
            "md5": re.compile(r'\b[a-fA-F0-9]{32}\b'),
            "sha1": re.compile(r'\b[a-fA-F0-9]{40}\b'),
            "sha256": re.compile(r'\b[a-fA-F0-9]{64}\b'),
            "cve": re.compile(r'\bCVE-(?:1999|2\d{3})-(?:0\d{2}[1-9]|[1-9]\d{3,})\b', re.IGNORECASE),
            "email": re.compile(r'\b[a-zA-Z0-9._%+-]+(?:@|\[@])[a-zA-Z0-9.-]+(?:\[\.]|\.)[a-zA-Z]{2,24}\b',
                                re.IGNORECASE),
            "file": re.compile(file_regex_pattern, re.IGNORECASE)
        }

        self.whitelist = {"domains": [], "ips": []}

        self.whitelist: Dict[str, Set[str]] = {
            'domains': set(),
            'ips': set(),
            'files': set(),
            'emails': set(),
            'cves': set(),
            'md5': set(),
            'sha1': set(),
            'sha256': set()
        }

        self.context_blacklist = {"negative_keywords": []}
        self.valid_tlds = set()
        self.compiled_apt_regex = None
        self.apt_name_map = {}
        self.compiled_country_regex = None

        self.project_root = _find_project_root()


        self._load_all_reference_data()

    def _classify_and_validate(self, raw_ioc, snippet):
        """
        Zentrale Klassifizierungs-Pipeline NUR fuer URL, Domain und Datei.
        Prueft intern auch gegen die jeweilige Whitelist.
        """
        # HIERARCHIE: URL > Domain > Datei

        if self.IOC_REGEXES['url'].fullmatch(raw_ioc):
            refanged = refang_ioc(raw_ioc, 'url')
            try:
                domain = urlparse(refanged).netloc
                if domain.lower() in self.whitelist.get('domains', set()):
                    return None
            except Exception:
                pass
            if self._is_context_suspicious(snippet): return None
            return {"value": refanged, "type": "url"}

        if self.IOC_REGEXES['domain'].fullmatch(raw_ioc):
            refanged = refang_ioc(raw_ioc, 'domain')
            parts = refanged.split('.')
            if self.valid_tlds and len(parts) >= 2 and parts[-1].lower() in self.valid_tlds:
                if refanged.lower() in self.whitelist.get('domains', set()):
                    return None
                if self._is_context_suspicious(snippet): return None
                return {"value": refanged, "type": "domain"}

        if self.IOC_REGEXES['file'].fullmatch(raw_ioc):
            refanged = refang_ioc(raw_ioc, 'file')
            if refanged.lower() in self.whitelist.get('files', set()):
                return None
            if self._is_context_suspicious(snippet): return None
            return {"value": refanged, "type": "file"}

        return None

    def _load_whitelist(self):
        filepath = self.project_root / "settings" / "whitelist.json"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.whitelist['domains'] = {d.strip().lower() for d in data.get('domains', [])}
                self.whitelist['ips'] = {ip.strip() for ip in data.get('ips', [])}
                self.whitelist['files'] = {f.strip().lower() for f in data.get('files', [])}
                self.whitelist['emails'] = {e.strip().lower() for e in data.get('emails', [])}
                self.whitelist['md5'] = {h.strip().lower() for h in data.get('md5', [])}
                self.whitelist['sha1'] = {h.strip().lower() for h in data.get('sha1', [])}
                self.whitelist['sha256'] = {h.strip().lower() for h in data.get('sha256', [])}

            print(f"[IOCExtractor] Whitelist geladen: "
                  f"{len(self.whitelist['domains'])} Domains, "
                  f"{len(self.whitelist['ips'])} IPs, "
                  f"{len(self.whitelist['files'])} Dateien, "
                  f"{len(self.whitelist['emails'])} E-Mails, "
                  f"{len(self.whitelist.get('md5', [])) + len(self.whitelist.get('sha1', [])) + len(self.whitelist.get('sha256', []))} Hashes.")
        except Exception as e:
            print(f"[IOCExtractor] WARNUNG: Whitelist konnte nicht von '{filepath}' geladen werden: {e}")



    def _load_context_blacklist(self):
        filepath = self.project_root / "settings" / "context_blacklist.json"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.context_blacklist = json.load(f)
        except Exception as e:
            print(f"[IOCExtractor] WARNUNG: Kontext-Blacklist konnte nicht geladen werden: {e}")

    def _load_valid_tlds(self):
        """Laedt die Liste der gueltigen TLDs aus der JSON-Datei."""
        filepath = self.project_root / "settings" / "tlds.json"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.valid_tlds = set(t.lower() for t in data.get('tlds', []))
            print(f"[IOCExtractor] {len(self.valid_tlds)} gueltige TLDs geladen.")
        except FileNotFoundError:
            print(f"[IOCExtractor] WARNUNG: TLD-Datei nicht gefunden unter '{filepath}'. Domain-Validierung wird ungenauer sein.")
        except Exception as e:
            print(f"[IOCExtractor] WARNUNG: TLD-Liste konnte nicht geladen werden: {e}")


    def _load_and_compile_apt_regex(self):
        with self.db_handler.Session() as session:
            apts = session.query(APT).all()
            if not apts:
                self.compiled_apt_regex = re.compile(r'a^')
                return

            all_names = set()
            temp_map = {}
            for apt in apts:
                main_name = apt.name
                if not main_name: continue

                all_names.add(main_name)
                temp_map[main_name.lower()] = main_name

                match = re.match(r'([a-zA-Z]+)(\d+)', main_name)
                if match:
                    variation = f"{match.group(1)} {match.group(2)}"
                    all_names.add(variation)
                    temp_map[variation.lower()] = main_name

                if apt.aliases:
                    for alias in apt.aliases.split(','):
                        alias = alias.strip()
                        if alias:
                            all_names.add(alias)
                            temp_map[alias.lower()] = main_name

            sorted_names = sorted(list(all_names), key=len, reverse=True)
            pattern = r'\b(?:' + '|'.join(re.escape(name) for name in sorted_names) + r')\b'
            self.compiled_apt_regex = re.compile(pattern, re.IGNORECASE)
            self.apt_name_map = {k.lower(): v for k, v in temp_map.items()}

    def _load_and_compile_country_regex(self):
        with self.db_handler.Session() as session:
            countries = session.query(Country).all()
            if not countries:
                self.compiled_country_regex = re.compile(r'a^')  # Matcht niemals
                return

            country_names = [c.name for c in countries]
            sorted_names = sorted(country_names, key=len, reverse=True)
            pattern = r'\b(?:' + '|'.join(re.escape(name) for name in sorted_names) + r')\b'
            self.compiled_country_regex = re.compile(pattern, re.IGNORECASE)

    def _load_all_reference_data(self):
        """Laedt alle Referenzdaten in die Instanz-Variablen."""
        self._load_whitelist()
        self._load_context_blacklist()
        self._load_valid_tlds()
        self._load_and_compile_country_regex()
        self._load_and_compile_apt_regex()
        print("[IOCExtractor] Initialisierung abgeschlossen.")

    def _is_context_suspicious(self, snippet: str) -> bool:
        """Prueft, ob ein Kontext-Snippet auf einen harmlosen Fund hindeutet."""
        for keyword in self.context_blacklist.get('negative_keywords', []):
            if re.search(r'\b' + re.escape(keyword) + r'\b', snippet, re.IGNORECASE):
                return True
        return False

    def extract_iocs_from_text(self, text_content, article_idx):
        if not text_content: return []

        text_content = _normalize_text_for_regex(text_content)

        all_regexes = {
            "url": self.IOC_REGEXES['url'],
            "email": self.IOC_REGEXES['email'],
            "file": self.IOC_REGEXES['file'],
            "domain": self.IOC_REGEXES['domain'],
            "cve": self.IOC_REGEXES['cve'],
            "ipv4": self.IOC_REGEXES['ipv4'],
            "md5": self.IOC_REGEXES['md5'],
            "sha1": self.IOC_REGEXES['sha1'],
            "sha256": self.IOC_REGEXES['sha256'],
            "apt_group_mention": self.compiled_apt_regex,
            "country_mention": self.compiled_country_regex
        }

        potential_matches = []
        for ioc_type, regex in all_regexes.items():
            if not regex: continue
            for match in regex.finditer(text_content):
                potential_matches.append({
                    'span': match.span(),
                    'text': match.group(0),
                    'type': ioc_type
                })

        potential_matches.sort(key=lambda x: (x['span'][0], -(x['span'][1] - x['span'][0])))

        collected_iocs = []
        found_spans = set()

        for match_info in potential_matches:
            start, end = match_info['span']
            if any(max(start, s) < min(end, e) for s, e in found_spans):
                continue

            raw_ioc = match_info['text']
            ioc_type = match_info['type']
            snippet = text_content[max(0, start - 50):min(len(text_content), end + 50)].replace("\n", " ")

            if ioc_type in ["url", "domain", "file"]:
                validated_ioc = self._classify_and_validate(raw_ioc, snippet)
                if validated_ioc:
                    ioc_entry = {
                        "ioc_value": validated_ioc['value'], "ioc_type": validated_ioc['type'],
                        "source_article_index": article_idx, "context_snippet": f"...{snippet}..."
                    }
                    collected_iocs.append(ioc_entry)
                    found_spans.add((start, end))
                continue
            refanged_ioc = refang_ioc(raw_ioc, ioc_type)

            whitelisted = False
            if ioc_type in ['ipv4', 'ipv6'] and refanged_ioc in self.whitelist.get('ips', set()):
                whitelisted = True
            elif ioc_type == 'email' and refanged_ioc.lower() in self.whitelist.get('emails', set()):
                whitelisted = True
            elif ioc_type in ['md5', 'sha1', 'sha256'] and refanged_ioc.lower() in self.whitelist.get(ioc_type, set()):
                whitelisted = True

            if whitelisted:
                continue

            if ioc_type in ["ipv4"]:
                try:
                    ip_obj = ipaddress.ip_address(refanged_ioc)
                    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_unspecified or ip_obj.is_reserved:
                        continue
                except ValueError:
                    continue

            if ioc_type in ["ipv4", "email"] and self._is_context_suspicious(snippet):
                continue

            ioc_entry = {
                "ioc_value": refanged_ioc, "ioc_type": ioc_type,
                "source_article_index": article_idx, "context_snippet": f"...{snippet}..."
            }
            if ioc_type == "apt_group_mention":
                ioc_entry["normalized_value"] = self.apt_name_map.get(refanged_ioc.lower(), raw_ioc)

            collected_iocs.append(ioc_entry)
            found_spans.add((start, end))

        return collected_iocs

    def process_text_contents(self, article_contents: list):
        """Verarbeitet eine Liste von Texten und extrahiert alle IOCs."""
        all_iocs = []
        for i, text in enumerate(article_contents):
            if text:
                all_iocs.extend(self.extract_iocs_from_text(text, i))
        return all_iocs
