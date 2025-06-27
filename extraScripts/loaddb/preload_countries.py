import requests
from bs4 import BeautifulSoup
from db.database_handler import DatabaseHandler

SOURCE_URL = "https://country-code.cl/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}


def scrape_country_data(url: str) -> list[dict]:
    """
    Scrapt die Webseite country-code.cl und extrahiert relevante Daten zu Ländern.
    """
    print(f"[Scraper] Rufe Daten von {url} ab...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[Scraper] Fehler beim Abrufen der Webseite: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    table_body = soup.find('tbody')
    if not table_body:
        print("[Scraper] Fehler: Konnte den 'tbody' der Tabelle nicht finden.")
        return []

    countries_data = []
    rows = table_body.find_all('tr')
    print(f"[Scraper] {len(rows)} Zeilen in der Tabelle gefunden. Extrahiere Daten...")

    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 8:
            try:
                continent_code = cols[0].text.strip()
                country_name = cols[2].get_text(strip=True)
                iso2_code = cols[3].get_text(strip=True)
                iso3_code = cols[4].text.strip()
                tld = cols[7].text.strip()
                if country_name and iso2_code:
                    countries_data.append({
                        "name": country_name, "continent_code": continent_code,
                        "iso2_code": iso2_code, "iso3_code": iso3_code, "tld": tld
                    })
            except IndexError:
                print(f"[Scraper] Warnung: Eine Zeile hatte eine unerwartete Struktur und wurde übersprungen.")
                continue

    print(f"[Scraper] {len(countries_data)} Länder erfolgreich extrahiert.")
    return countries_data


if __name__ == "__main__":
    print("Starte Pre-Loading-Skript für Länderdaten...")

    db_handler = DatabaseHandler()
    scraped_data = scrape_country_data(SOURCE_URL)

    if scraped_data:
        db_handler.preload_countries(scraped_data)
    else:
        print("Programm beendet, da keine Daten gescrapt werden konnten.")