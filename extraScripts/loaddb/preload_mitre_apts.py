import requests
from bs4 import BeautifulSoup
from db.database_handler import DatabaseHandler
from db.database_models import APT

MITRE_GROUPS_URL = "https://attack.mitre.org/groups/"

def scrape_and_load_apts():
    """
    Scrapt die MITRE ATT&CK Groups Seite und lädt die Informationen
    in die Datenbank.
    """
    print(f"Lade APT-Gruppen von: {MITRE_GROUPS_URL}")

    try:
        response = requests.get(MITRE_GROUPS_URL, timeout=20)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der MITRE-Seite: {e}")
        return

    print("Seite erfolgreich geladen. Starte Parsing...")
    soup = BeautifulSoup(response.content, 'html.parser')

    table_body = soup.find('tbody')
    if not table_body:
        print("Fehler: Konnte die Gruppen-Tabelle auf der Seite nicht finden.")
        return

    group_rows = table_body.find_all('tr')
    print(f"{len(group_rows)} Gruppen-Einträge gefunden. Verarbeite und speichere in DB...")

    db_handler = DatabaseHandler()

    for row in group_rows:
        cols = row.find_all('td')
        if len(cols) < 4:
            continue

        mitre_id = cols[0].get_text(strip=True)
        name = cols[1].get_text(strip=True)
        aliases = ", ".join([alias.strip() for alias in cols[2].get_text(strip=True).split(',') if alias.strip()])
        description = cols[3].get_text(strip=True)

        print(f"Verarbeite: {mitre_id} - {name}")

        session = db_handler.Session()
        try:
            existing_apt = session.query(APT).filter_by(mitre_id=mitre_id).first()

            if existing_apt:
                existing_apt.name = name
                existing_apt.aliases = aliases
                existing_apt.description = description
                print(f"  -> Eintrag für {mitre_id} aktualisiert.")
            else:
                new_apt = APT(
                    mitre_id=mitre_id,
                    name=name,
                    aliases=aliases,
                    description=description
                )
                session.add(new_apt)
                print(f"  -> Neuer Eintrag für {mitre_id} hinzugefügt.")

            session.commit()
        except Exception as e:
            print(f"  -> Fehler beim Speichern von {mitre_id}: {e}")
            session.rollback()
        finally:
            session.close()

    print("\nPre-Loading der MITRE ATT&CK Gruppen abgeschlossen.")


if __name__ == "__main__":
    scrape_and_load_apts()
