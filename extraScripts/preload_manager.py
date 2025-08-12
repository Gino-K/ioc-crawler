import datetime
import json
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from db.crawler_db_handler import CrawlerDBHandler
from db.database_models import APT


class BasePreloader(ABC):
    """
    Eine abstrakte Basisklasse, die die gemeinsame Logik fuer alle Preloader kapselt.
    Definiert den Workflow: Fetch -> Extract -> Load.
    """
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    def __init__(self, name: str, source_url: str):
        self.name = name
        self.source_url = source_url
        print(f"[{self.name} Preloader] Initialisiert.")

    def _fetch_content(self) -> BeautifulSoup | None:
        """Laedt den Inhalt der Quell-URL herunter und gibt ein BeautifulSoup-Objekt zurueck."""
        print(f"[{self.name} Preloader] Rufe Daten von {self.source_url} ab...")
        try:
            response = requests.get(self.source_url, headers=self.HEADERS, timeout=20)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"[{self.name} Preloader] FEHLER beim Abrufen der Webseite: {e}")
            return None

    @abstractmethod
    def _extract_data(self, soup: BeautifulSoup) -> list[dict] | dict:
        """Extrahiert die relevanten Daten aus dem Soup-Objekt. Muss von Subklassen implementiert werden."""
        pass

    @abstractmethod
    def _load_data(self, data: list[dict] | dict):
        """Laedt die extrahierten Daten in das Ziel (DB oder JSON). Muss von Subklassen implementiert werden."""
        pass

    def run(self):
        """Fuehrt den gesamten Preload-Prozess aus."""
        print(f"\n--- Starte Preload fuer: {self.name} ---")
        soup = self._fetch_content()
        if soup:
            extracted_data = self._extract_data(soup)
            if extracted_data:
                self._load_data(extracted_data)
                print(f"--- Preload fuer {self.name} erfolgreich abgeschlossen. ---")
            else:
                print(f"--- Preload fuer {self.name} beendet: Keine Daten extrahiert. ---")
        else:
            print(f"--- Preload fuer {self.name} fehlgeschlagen: Konnte Inhalt nicht abrufen. ---")


class TldPreloader(BasePreloader):
    """Laedt Top-Level-Domains von IANA und speichert sie in einer JSON-Datei"""

    def __init__(self):
        super().__init__("TLDs", "https://www.iana.org/domains/root/db")
        self.output_file = self._find_project_root() / "settings" / "tlds.json"

    def _find_project_root(self) -> Path:
        current_path = Path(__file__).resolve()
        while not (current_path / '.gitignore').exists():
            if current_path.parent == current_path:
                raise FileNotFoundError("Projekt-Root mit .gitignore konnte nicht gefunden werden.")
            current_path = current_path.parent
        return current_path

    def _extract_data(self, soup: BeautifulSoup) -> dict:
        tld_table = soup.find('table', id='tld-table')
        if not tld_table:
            print(f"[{self.name} Preloader] FEHLER: Konnte die TLD-Tabelle nicht finden.")
            return {}

        domain_spans = tld_table.find_all('span', class_='domain')
        tld_list = [span.get_text(strip=True).lstrip('.') for span in domain_spans]
        print(f"[{self.name} Preloader] {len(tld_list)} TLDs extrahiert.")
        return {"tlds": tld_list}

    def _load_data(self, data: dict):
        try:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[{self.name} Preloader] TLD-Liste erfolgreich in '{self.output_file}' gespeichert.")
        except IOError as e:
            print(f"[{self.name} Preloader] FEHLER beim Schreiben der Datei: {e}")


class CountryPreloader(BasePreloader):
    """Laedt Laenderdaten und speichert sie in der Datenbank"""

    def __init__(self, db_handler: CrawlerDBHandler):
        super().__init__("Countries", "https://country-code.cl/")
        self.db_handler = db_handler

    def _extract_data(self, soup: BeautifulSoup) -> list[dict]:
        table_body = soup.find('tbody')
        if not table_body:
            print(f"[{self.name} Preloader] FEHLER: Konnte den 'tbody' der Tabelle nicht finden.")
            return []

        countries_data = []
        rows = table_body.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 8: continue

            country_name_span = cols[2].find('span', style="display:table")
            raw_country_name = country_name_span.get_text(strip=True) if country_name_span else cols[2].get_text(
                strip=True)

            normalized_name = raw_country_name.lower()
            if normalized_name == "congo, the democratic republic of the":
                country_name = "DR Congo"
            elif normalized_name == "congo, republic of the":
                country_name = "Republic of the Congo"
            elif normalized_name == "korea, republic of":
                country_name = "South Korea"
            elif normalized_name == "korea, democratic people's republic of":
                country_name = "North Korea"
            elif "virgin islands, british" in normalized_name:
                country_name = "British Virgin Islands"
            elif "virgin islands, u.s." in normalized_name:
                country_name = "U.S. Virgin Islands"
            elif ',' in raw_country_name:
                country_name = raw_country_name.split(',')[0].strip()
            else:
                country_name = raw_country_name

            countries_data.append({
                "name": country_name, "continent_code": cols[0].text.strip(),
                "iso2_code": cols[3].get_text(strip=True), "iso3_code": cols[4].text.strip(),
                "tld": cols[7].text.strip()
            })

        print(f"[{self.name} Preloader] {len(countries_data)} Laender extrahiert.")
        return countries_data

    def _load_data(self, data: list[dict]):
        self.db_handler.preload_countries(data)


class MitreAptPreloader(BasePreloader):
    """Laedt MITRE APT-Gruppen und speichert sie in der Datenbank"""

    def __init__(self, db_handler: CrawlerDBHandler):
        super().__init__("MITRE APTs", "https://attack.mitre.org/groups/")
        self.db_handler = db_handler

    def _extract_data(self, soup: BeautifulSoup) -> list[dict]:
        table_body = soup.find('tbody')
        if not table_body:
            print(f"[{self.name} Preloader] FEHLER: Konnte die Gruppen-Tabelle nicht finden.")
            return []

        apt_data = []
        for row in table_body.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) < 4: continue
            apt_data.append({
                "mitre_id": cols[0].get_text(strip=True),
                "name": cols[1].get_text(strip=True),
                "aliases": ", ".join(
                    [alias.strip() for alias in cols[2].get_text(strip=True).split(',') if alias.strip()]),
                "description": cols[3].get_text(strip=True)
            })
        print(f"[{self.name} Preloader] {len(apt_data)} APT-Gruppen extrahiert.")
        return apt_data

    def _load_data(self, data: list[dict]):
        print(f"[{self.name} Preloader] Speichere/Aktualisiere {len(data)} APTs in der DB...")
        with self.db_handler.Session() as session:
            for apt in data:
                try:
                    existing_apt = session.query(APT).filter_by(mitre_id=apt['mitre_id']).first()
                    if existing_apt:
                        existing_apt.name = apt['name']
                        existing_apt.aliases = apt['aliases']
                        existing_apt.description = apt['description']
                    else:
                        new_apt = APT(**apt)
                        session.add(new_apt)
                    session.commit()
                except Exception as e:
                    print(f"  -> FEHLER beim Speichern von {apt['mitre_id']}: {e}")
                    session.rollback()

class PreloaderManager:
    """Eine zentrale Klasse, um alle Preload-Prozesse zu steuern"""

    def __init__(self, user_settings, db_handler):
        print("Initialisiere Preloader Manager...")

        self.user_settings = user_settings
        self.db_handler = db_handler

        self.preloaders = {
            "tlds": TldPreloader(),
            "countries": CountryPreloader(self.db_handler),
            "apts": MitreAptPreloader(self.db_handler)
        }

    def run_all(self):
        """Fuehrt alle konfigurierten Preloads parallel aus"""
        print("\nStarte alle Preload-Prozesse parallel...")

        with ThreadPoolExecutor(max_workers=len(self.preloaders)) as executor:
            executor.map(lambda p: p.run(), self.preloaders.values())

        print("\nAlle Preload-Prozesse abgeschlossen.")

        self.user_settings.last_preload_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.user_settings.save()
        print("[PreloaderManager] Zeitstempel fuer letzten Preload aktualisiert.")

    def run_specific(self, name: str):
        """Fuehrt einen spezifischen Preload aus"""
        preloader = self.preloaders.get(name.lower())
        if preloader:
            preloader.run()
        else:
            print(f"FEHLER: Preloader '{name}' nicht gefunden. Verfuegbar: {list(self.preloaders.keys())}")
