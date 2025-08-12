import datetime

from sqlalchemy import func
from .database_handler_base import DatabaseHandlerBase, _normalize_name
from .database_models import IOC, Sighting, APT, Country, CVE, ArticleScanHistory


class CrawlerDBHandler(DatabaseHandlerBase):
    """
    Ein spezialisierter Datenbank-Handler fuer alle Operationen,
    die vom Crawler und den Pre-Loading-Skripten benoetigt werden.
    """

    def get_existing_sightings(self, url_prefix):
        session = self.Session()
        sightings_map = {}
        try:
            query_results = session.query(
                Sighting.source_article_url,
                func.max(Sighting.sighting_timestamp)
            ).filter(
                Sighting.source_article_url.like(f"{url_prefix}%")
            ).group_by(
                Sighting.source_article_url
            ).all()
            for url, last_timestamp in query_results:
                sightings_map[url] = last_timestamp
        except Exception as e:
            print(f"DB-Fehler beim Abrufen existierender Sightings fuer '{url_prefix}': {e}")
        finally:
            session.close()
        print(f"DB-Abfrage: {len(sightings_map)} existierende Links fuer das Praefix '{url_prefix}' gefunden.")
        return sightings_map

    def preload_countries(self, countries_data: list[dict]):
        """
        Fuegt eine Liste von Laendern in die Datenbank ein.
        Diese Methode wird vom Pre-Loading-Skript aufgerufen.
        """
        if not countries_data:
            print("[DB Handler] Keine Laenderdaten zum Einfuegen erhalten.")
            return

        print(f"[DB Handler] Pre-Loading von {len(countries_data)} Laendern gestartet...")
        with self.Session() as session:
            for country_info in countries_data:
                self._get_or_create(
                    session,
                    model=Country,
                    iso2_code=country_info['iso2_code'],
                    defaults={
                        'name': country_info['name'],
                        'continent_code': country_info['continent_code'],
                        'iso3_code': country_info['iso3_code'],
                        'tld': country_info['tld']
                    }
                )
            session.commit()
            print("[DB Handler] Pre-Loading der Laender erfolgreich abgeschlossen.")

    def find_or_create_apt(self, session, apt_info):
        mention_name = apt_info["value"]
        search_key = _normalize_name(mention_name)
        if not search_key: return None

        all_apts_from_db = session.query(APT).all()
        for apt_db in all_apts_from_db:
            if _normalize_name(apt_db.name) == search_key:
                return apt_db
            if apt_db.aliases:
                for alias in apt_db.aliases.split(','):
                    if _normalize_name(alias.strip()) == search_key:
                        return apt_db

        print(f"WARNUNG: APT '{mention_name}' nicht in DB gefunden. Erstelle minimalen neuen Eintrag.")
        normalized_name = apt_info.get("normalized_value", mention_name)
        return self._get_or_create(session, APT, name=normalized_name, defaults={'aliases': mention_name})

    def find_country(self, session, country_name: str) -> Country | None:
        return session.query(Country).filter(Country.name.ilike(country_name)).first()

    def add_structured_ioc_data(self, ioc_data):
        with self.Session() as session:
            try:
                ioc_db = self._get_or_create(session, IOC, value=ioc_data["ioc_value"], type=ioc_data["ioc_type"])

                apt_db_objects = [self.find_or_create_apt(session, apt_info) for apt_info in
                                  ioc_data.get("associated_apts", [])]
                country_db_objects = [self.find_country(session, c['value']) for c in
                                      ioc_data.get("associated_countries", [])]
                cve_db_objects = [self._get_or_create(session, CVE, name=cve['value']) for cve in
                                  ioc_data.get("associated_cves", [])]

                for url in ioc_data.get("source_article_urls", []):
                    if session.query(Sighting).filter_by(ioc_id=ioc_db.id, source_article_url=url).first():
                        continue

                    timestamp_obj = ioc_data["discovery_timestamp"]
                    new_sighting = Sighting(
                        ioc_id=ioc_db.id, source_article_url=url,
                        sighting_timestamp=timestamp_obj,
                        context_snippet=ioc_data.get("first_seen_context_snippet")
                    )
                    new_sighting.apts.extend(filter(None, apt_db_objects))
                    new_sighting.countries.extend(filter(None, country_db_objects))
                    new_sighting.cves.extend(filter(None, cve_db_objects))
                    session.add(new_sighting)

                session.commit()
            except Exception as e:
                print(f"  [DB] FEHLER beim Verarbeiten von IOC {ioc_data.get('ioc_value')}: {e}")
                session.rollback()

    def get_article_scan_history(self, url_prefix: str) -> dict:
        """
        Holt die letzten Scan-Zeitstempel fuer alle Artikel von einer bestimmten Quelle.
        """
        print(f"[DB Handler] Lade Scan-Verlauf fuer URLs mit Praefix: {url_prefix}")
        with self.Session() as session:
            try:
                history_entries = session.query(ArticleScanHistory).filter(
                    ArticleScanHistory.url.like(f"{url_prefix}%")
                ).all()
                return {entry.url: entry.last_scanned for entry in history_entries}
            except Exception as e:
                print(f"[DB Handler] Fehler beim Laden des Scan-Verlaufs: {e}")
                return {}

    def update_article_scan_history(self, processed_urls: list):
        """
        Aktualisiert den Scan-Zeitstempel fuer eine Liste von URLs.
        Fuegt neue URLs hinzu, falls sie noch nicht existieren.
        """
        if not processed_urls:
            return

        print(f"[DB Handler] Aktualisiere Scan-Verlauf fuer {len(processed_urls)} URLs...")
        with self.Session() as session:
            try:
                existing_urls = {
                    entry[0] for entry in
                    session.query(ArticleScanHistory.url).filter(ArticleScanHistory.url.in_(processed_urls))
                }

                urls_to_add = [url for url in processed_urls if url not in existing_urls]

                if existing_urls:
                    session.query(ArticleScanHistory).filter(
                        ArticleScanHistory.url.in_(existing_urls)
                    ).update(
                        {ArticleScanHistory.last_scanned: datetime.datetime.now(datetime.timezone.utc)},
                        synchronize_session=False
                    )

                if urls_to_add:
                    new_entries = [ArticleScanHistory(url=url) for url in urls_to_add]
                    session.bulk_save_objects(new_entries)

                session.commit()
            except Exception as e:
                print(f"[DB Handler] FEHLER beim Aktualisieren des Scan-Verlaufs: {e}")
                session.rollback()
