import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func, or_
from .database_models import Base, IOC, Sighting, APT, Country, CVE


class DatabaseHandler:
    def __init__(self, db_name="threat_intelligence.sqlite"):
        """Initialisiert die Datenbankverbindung und erstellt die Session."""
        self.engine = create_engine(f'sqlite:///{db_name}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def _get_or_create(self, session, model, defaults=None, **kwargs):
        """
        Sucht ein Objekt anhand von Suchkriterien (**kwargs).
        Wenn es nicht existiert, wird es mit den Suchkriterien UND den
        optionalen 'defaults' erstellt.
        """
        instance = session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            params = {**kwargs, **(defaults or {})}
            instance = model(**params)
            session.add(instance)
            session.flush()
            return instance

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
            print(f"DB-Fehler beim Abrufen existierender Sightings für '{url_prefix}': {e}")
        finally:
            session.close()
        print(f"DB-Abfrage: {len(sightings_map)} existierende Links für das Präfix '{url_prefix}' gefunden.")
        return sightings_map

    def _find_or_create_apt(self, session, apt_info):
        mention_name = apt_info["value"]
        normalized_name = apt_info.get("normalized_value", mention_name)
        apt_db = session.query(APT).filter(
            or_(
                APT.name == normalized_name,
                APT.name == mention_name,
                APT.aliases.like(f"%{mention_name}%")
            )
        ).first()
        if apt_db:
            return apt_db
        else:
            print(f"WARNUNG: APT '{mention_name}' nicht in DB gefunden. Erstelle minimalen neuen Eintrag.")
            new_apt = self._get_or_create(session, APT, name=normalized_name, defaults={'aliases': mention_name})
            session.flush()
            return new_apt

    def preload_countries(self, countries_data: list[dict]):
        """
        Fügt eine Liste von Ländern in die Datenbank ein.
        Der Aufruf hier ist korrekt, die Implementierung von _get_or_create wurde angepasst.
        """
        if not countries_data:
            print("[DB Handler] Keine Länderdaten zum Einfügen erhalten.")
            return

        print(f"[DB Handler] Pre-Loading von {len(countries_data)} Ländern gestartet...")
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
            print("[DB Handler] Pre-Loading der Länder erfolgreich abgeschlossen.")

    def find_country(self, session, country_name: str) -> Country | None:
        country_db = session.query(Country).filter(
            Country.name.ilike(country_name)
        ).first()
        return country_db

    def add_structured_ioc_data(self, ioc_data):
        with self.Session() as session:
            try:
                # 1. Erstelle oder hole den einzigartigen IOC
                ioc_db = self._get_or_create(session, IOC,
                                             value=ioc_data["ioc_value"],
                                             type=ioc_data["ioc_type"])

                # 2. Hole assoziierte Entitäten
                apt_db_objects = [self._find_or_create_apt(session, apt_info) for apt_info in
                                  ioc_data.get("associated_apts", [])]
                country_db_objects = []
                for country_info in ioc_data.get("associated_countries", []):
                    country_db = self._get_or_create(session, Country,
                                                     name=country_info["value"],
                                                     defaults={'iso2_code': 'XX', 'iso3_code': 'XXX'})
                    country_db_objects.append(country_db)
                cve_db_objects = [self._get_or_create(session, CVE, name=cve_info["value"]) for cve_info in
                                  ioc_data.get("associated_cves", [])]

                # 3. Erstelle für jede Quell-URL einen "Sighting"-Eintrag
                for url in ioc_data.get("source_article_urls", []):
                    existing_sighting = session.query(Sighting).filter_by(ioc_id=ioc_db.id,
                                                                          source_article_url=url).first()
                    if existing_sighting:
                        print(f"Sighting für IOC {ioc_db.value} in {url} existiert bereits. Überspringe.")
                        continue

                    session.flush()

                    new_sighting = Sighting(
                        ioc_id=ioc_db.id,
                        source_article_url=url,
                        sighting_timestamp=datetime.datetime.fromisoformat(ioc_data["discovery_timestamp"]),
                        context_snippet=ioc_data.get("first_seen_context_snippet"),
                        saved_formats="json,csv,stix"
                    )

                    new_sighting.apts.extend(apt_db_objects)
                    new_sighting.countries.extend(country_db_objects)
                    new_sighting.cves.extend(cve_db_objects)

                    session.add(new_sighting)
                    print(f"Neuer Sighting für IOC {ioc_db.value} in {url} zur DB hinzugefügt.")

                session.commit()

            except Exception as e:
                print(f"DB-Fehler beim Verarbeiten von IOC {ioc_data.get('ioc_value')}: {e}")
                session.rollback()