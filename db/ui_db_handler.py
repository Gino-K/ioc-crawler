import datetime
from collections import defaultdict
from urllib.parse import urlparse
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from .database_handler_base import DatabaseHandlerBase
from .database_models import IOC, Sighting, APT, Country, ArticleScanHistory


class UiDBHandler(DatabaseHandlerBase):
    """
    Ein spezialisierter Datenbank-Handler fuer alle Lese-Operationen,
    die von der grafischen Benutzeroberflaeche (GUI) benoetigt werden.
    """

    def get_monthly_stats(self, months=12):
        """
        Holt die Anzahl der neuen IOCs und Sightings fuer die letzten X Monate.
        """
        print("[DB Handler] Lade monatliche Statistiken...")

        now = datetime.datetime.now(datetime.timezone.utc)
        labels = []
        ioc_counts = defaultdict(int)
        sighting_counts = defaultdict(int)

        for i in range(months - 1, -1, -1):
            year = now.year
            month = now.month - i
            while month <= 0:
                month += 12
                year -= 1

            date_in_month = datetime.datetime(year, month, 1)
            date_in_month.strftime('%Y-%m')
            month_label = date_in_month.strftime('%b %y')
            if month_label not in labels:
                labels.append(month_label)

        with self.Session() as session:
            try:
                ioc_results = session.query(
                    func.strftime('%Y-%m', Sighting.sighting_timestamp),
                    func.count(Sighting.ioc_id.distinct())
                ).group_by(func.strftime('%Y-%m', Sighting.sighting_timestamp)).all()

                for month, count in ioc_results:
                    ioc_counts[month] = count

                sighting_results = session.query(
                    func.strftime('%Y-%m', Sighting.sighting_timestamp),
                    func.count(Sighting.id)
                ).group_by(func.strftime('%Y-%m', Sighting.sighting_timestamp)).all()

                for month, count in sighting_results:
                    sighting_counts[month] = count
            except Exception as e:
                print(f"[DB Handler] Fehler bei der Abfrage der Monatsstatistiken: {e}")

        final_ioc_counts = [ioc_counts.get(datetime.datetime.strptime(label, '%b %y').strftime('%Y-%m'), 0) for label in
                            labels]
        final_sighting_counts = [sighting_counts.get(datetime.datetime.strptime(label, '%b %y').strftime('%Y-%m'), 0)
                                 for label in labels]

        return {
            "labels": labels,
            "ioc_counts": final_ioc_counts,
            "sighting_counts": final_sighting_counts
        }

    def get_top_ioc_types(self, limit=7):
        """
        Zaehlt die Vorkommen jedes primaeren IOC-Typs und gibt die haeufigsten zurueck.
        """
        print("[DB Handler] Lade Statistiken zu IOC-Typen...")
        with self.Session() as session:
            try:
                results = session.query(
                    IOC.type,
                    func.count(IOC.id)
                ).group_by(IOC.type).order_by(
                    func.count(IOC.id).desc()
                ).limit(limit).all()
                return results
            except Exception as e:
                print(f"[DB Handler] Fehler beim Abrufen der IOC-Typ-Statistiken: {e}")
                return []

    def get_top_apt_groups(self, limit=5):
        """
        Zaehlt, wie oft jede APT-Gruppe in einem Sighting erwaehnt wird und gibt die Top 5 zurueck.
        """
        print("[DB Handler] Lade Statistiken zu Top-APT-Gruppen...")
        with self.Session() as session:
            try:
                results = session.query(
                    APT.name,
                    func.count(Sighting.id)
                ).join(Sighting.apts).group_by(
                    APT.name
                ).order_by(
                    func.count(Sighting.id).desc()
                ).limit(limit).all()
                return results
            except Exception as e:
                print(f"[DB Handler] Fehler beim Abrufen der APT-Statistiken: {e}")
                return []

    def get_top_sighting_sources(self, limit=5):
        """
        Ermittelt die Top-Quell-Domains basierend auf der Anzahl der Sightings.
        """
        print("[DB Handler] Lade Statistiken zu Top-Sighting-Quellen...")
        with self.Session() as session:
            try:
                all_urls = session.query(Sighting.source_article_url).all()
                domain_counts = defaultdict(int)

                for url_tuple in all_urls:
                    try:
                        domain = urlparse(url_tuple[0]).netloc
                        if domain:
                            domain_counts[domain] += 1
                    except Exception:
                        continue

                sorted_domains = sorted(domain_counts.items(), key=lambda item: item[1], reverse=True)
                return sorted_domains[:limit]

            except Exception as e:
                print(f"[DB Handler] Fehler beim Abrufen der Sighting-Quellen-Statistiken: {e}")
                return []

    def get_top_mentioned_countries(self, limit=5):
        """
        Zaehlt, wie oft jedes Land in einem Sighting erwaehnt wird und gibt die Top 5 zurueck.
        """
        print("[DB Handler] Lade Statistiken zu Top-Laendern...")
        with self.Session() as session:
            try:
                results = session.query(
                    Country.name,
                    func.count(Sighting.id)
                ).join(Sighting.countries).group_by(
                    Country.name
                ).order_by(
                    func.count(Sighting.id).desc()
                ).limit(limit).all()
                return results
            except Exception as e:
                print(f"[DB Handler] Fehler beim Abrufen der Laender-Statistiken: {e}")
                return []

    def search_iocs(self, ioc_type_filter=None, value_filter=None):
        """
        Durchsucht die Datenbank nach IOCs, die den Filterkriterien entsprechen.
        """
        print(f"[DB Handler] Suche IOCs mit Typ='{ioc_type_filter}' und Wert='{value_filter}'")
        with self.Session() as session:
            try:
                query = session.query(IOC)

                if ioc_type_filter and ioc_type_filter != "Alle":
                    query = query.filter(IOC.type == ioc_type_filter.lower())

                if value_filter:
                    query = query.filter(IOC.value.like(f"%{value_filter}%"))

                query = query.options(joinedload(IOC.sightings))

                return query.order_by(IOC.id.desc()).all()

            except Exception as e:
                print(f"[DB Handler] Fehler bei der IOC-Suche: {e}")
                return []

    def get_ioc_details(self, ioc_id: int):
        """
        Holt alle detaillierten Informationen fuer einen einzelnen IOC,
        inklusive aller verknuepften Sightings und deren Relationen.
        """
        print(f"[DB Handler] Lade Details fuer IOC mit ID: {ioc_id}")
        with self.Session() as session:
            try:
                ioc = session.query(IOC).options(
                    joinedload(IOC.sightings).joinedload(Sighting.apts),
                    joinedload(IOC.sightings).joinedload(Sighting.countries),
                    joinedload(IOC.sightings).joinedload(Sighting.cves)
                ).filter(IOC.id == ioc_id).one_or_none()

                return ioc
            except Exception as e:
                print(f"[DB Handler] Fehler beim Laden der IOC-Details: {e}")
                return None

    def delete_ioc(self, ioc_id: int) -> bool:
        """
        Loescht einen IOC und alle zugehoerigen Sightings aus der Datenbank.
        Diese Funktion wird aufgerufen, nachdem ein IOC als Falsch-Positiv markiert wurde.
        """
        print(f"[DB Handler] Loesche IOC mit ID: {ioc_id}")
        with self.Session() as session:
            try:
                ioc_to_delete = session.query(IOC).filter(IOC.id == ioc_id).one_or_none()

                if ioc_to_delete:
                    session.delete(ioc_to_delete)
                    session.commit()
                    print(f"[DB Handler] IOC {ioc_id} und zugehoerige Daten erfolgreich geloescht.")
                    return True
                else:
                    print(f"[DB Handler] WARNUNG: IOC {ioc_id} zum Loeschen nicht gefunden.")
                    return False
            except Exception as e:
                print(f"[DB Handler] FEHLER beim Loeschen von IOC {ioc_id}: {e}")
                session.rollback()
                return False

    def get_all_scanned_domains(self) -> list[str]:
        """Holt alle einzigartigen Domains aus der Scan-Historie fuer den Filter."""
        print("[DB Handler] Lade einzigartige Domains aus der Scan-Historie...")
        with self.Session() as session:
            try:
                all_urls = session.query(ArticleScanHistory.url).all()
                unique_domains = sorted(list({urlparse(url[0]).netloc for url in all_urls if url[0]}))
                return ["Alle"] + unique_domains
            except Exception as e:
                print(f"[DB Handler] Fehler beim Laden der Domains aus der Scan-Historie: {e}")
                return ["Alle"]

    def search_scan_history(self, domain_filter: str, url_keyword_filter: str) -> list:
        """Durchsucht die Scan-Historie basierend auf Filtern."""
        print(f"[DB Handler] Durchsuche Scan-Historie mit Domain='{domain_filter}' und Keyword='{url_keyword_filter}'")
        with self.Session() as session:
            try:
                query = session.query(ArticleScanHistory)

                if domain_filter and domain_filter != "Alle":
                    query = query.filter(ArticleScanHistory.url.like(f"%{domain_filter}%"))

                if url_keyword_filter:
                    query = query.filter(ArticleScanHistory.url.like(f"%{url_keyword_filter}%"))

                return query.order_by(ArticleScanHistory.last_scanned.desc()).all()
            except Exception as e:
                print(f"[DB Handler] Fehler bei der Suche in der Scan-Historie: {e}")
                return []
