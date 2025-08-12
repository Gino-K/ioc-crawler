from ui.views.search.search_detail_view import SearchDetailView


class SearchController:
    def __init__(self, model, settings):
        self.settings = settings
        self.model = model
        self.view = None
        self.detail_window = None

        self.current_results = []
        self.sort_column = None
        self.sort_reverse = False

    def set_view(self, view):
        self.view = view

    def perform_search(self):
        """Wird von der View aufgerufen, um eine neue Suche durchzuführen."""
        if not self.view:
            return

        ioc_type = self.view.get_type_filter()
        value_filter = self.view.get_value_filter()

        self.current_results = self.model.search_iocs(ioc_type_filter=ioc_type, value_filter=value_filter)

        self.sort_column = None
        self.sort_reverse = False
        self.view.display_results(self.current_results)

    def sort_results(self, column_name):
        """Sortiert die aktuell angezeigten Ergebnisse nach einer Spalte."""
        if not self.current_results:
            return

        # Bestimmt die Sortierreihenfolge (aufsteigend -> absteigend -> unsortiert)
        if self.sort_column == column_name:
            if not self.sort_reverse:
                self.sort_reverse = True
            else:
                self.sort_column = None
                self.sort_reverse = False
        else:
            self.sort_column = column_name
            self.sort_reverse = False

        if self.sort_column:
            if column_name == 'ioc_value':
                sort_key = lambda ioc: ioc.value
            elif column_name == 'type':
                sort_key = lambda ioc: ioc.type
            elif column_name == 'sources':
                sort_key = lambda ioc: len(ioc.sightings)
            elif column_name == 'last_sighting':
                sort_key = lambda ioc: max(s.sighting_timestamp for s in ioc.sightings) if ioc.sightings else 0
            else:
                sort_key = lambda ioc: ioc.id  # Fallback

            self.current_results.sort(key=sort_key, reverse=self.sort_reverse)
        else:
            self.current_results.sort(key=lambda ioc: ioc.id, reverse=True)

        self.view.display_results(self.current_results)

    def show_ioc_details(self, ioc_id):
        """Holt die Details für einen IOC und zeigt sie in einem neuen Fenster an."""
        if self.detail_window is not None and self.detail_window.winfo_exists():
            self.detail_window.destroy()

        ioc_details = self.model.get_ioc_details(ioc_id)

        if ioc_details:
            self.detail_window = SearchDetailView(
                master=self.view.winfo_toplevel(),
                ioc_data=ioc_details,
                controller=self
            )
            
    def mark_as_false_positive(self, ioc_data):
        """Wird von der Detail-View aufgerufen, um einen IOC als False Positive zu markieren."""
        print(f"Markiere {ioc_data.value} ({ioc_data.type}) als False Positive...")

        self.settings.add_to_whitelist(ioc_data.value, ioc_data.type)

        self.model.delete_ioc(ioc_data.id)

        if self.detail_window:
            self.detail_window.destroy()

        print("Aktualisiere Suchansicht...")
        self.perform_search()