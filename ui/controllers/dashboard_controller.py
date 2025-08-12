class DashboardController:
    def __init__(self, model):
        self.model = model
        self.view = None

    def set_view(self, view):
        self.view = view

    def update_ioc_sighting_chart_data(self, data_type='ioc'):
        """Holt die monatlichen Statistikdaten und aktualisiert das obere Balkendiagramm."""
        if not self.view: return
        print(f"[DashboardController] Lade Daten für Balkendiagramm: {data_type}")

        stats = self.model.get_monthly_stats()

        if data_type == 'ioc':
            data_to_plot = stats.get('ioc_counts', [])
            title = "Neue primäre IOCs pro Monat"
        else:  # 'sighting'
            data_to_plot = stats.get('sighting_counts', [])
            title = "Neue Sichtungen (Sightings) pro Monat"

        labels = stats.get('labels', [])
        if not data_to_plot or sum(data_to_plot) == 0:
            self.view.update_ioc_sighting_chart(labels, [], title)
        else:
            self.view.update_ioc_sighting_chart(labels, data_to_plot, title)

    def update_ioc_type_apt_chart_data(self, chart_type='ioc_type'):
        """Holt die aggregierten Daten und aktualisiert das untere Diagramm (horizontale Balken)."""
        if not self.view: return
        print(f"[DashboardController] Lade Daten für unteres Diagramm: {chart_type}")

        if chart_type == 'ioc_type':
            data = self.model.get_top_ioc_types()
            title = "Top 7 häufigste IOC-Typen"
        else:  # 'apt'
            data = self.model.get_top_apt_groups()
            title = "Top 5 erwähnte APT-Gruppen"

        if not data:
            labels, sizes = [], []
        else:
            labels = [item[0] for item in data]
            sizes = [item[1] for item in data]

        self.view.update_type_apt_chart(labels, sizes, title)

    def update_sighting_details_chart_data(self, chart_type='source'):
        """Holt aggregierte Sighting-Daten und aktualisiert das untere Diagramm."""
        if not self.view: return
        print(f"[DashboardController] Lade Daten für Sighting-Detail-Diagramm: {chart_type}")

        if chart_type == 'source':
            data = self.model.get_top_sighting_sources()
            title = "Top 5 Quellen (nach Anzahl der Sightings)"
        else:  # 'country'
            data = self.model.get_top_mentioned_countries()
            title = "Top 5 erwähnte Länder in Sightings"

        labels, sizes = ([item[0] for item in data], [item[1] for item in data]) if data else ([], [])
        self.view.update_sighting_details_chart(labels, sizes, title)
