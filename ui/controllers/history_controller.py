class ArticleHistoryController:
    def __init__(self, model):
        self.model = model
        self.view = None
        self.current_results = []
        self.sort_column = 'last_scanned'
        self.sort_reverse = True

    def set_view(self, view):
        self.view = view

    def load_initial_data(self):
        """Lädt die Domains für das Filter-Dropdown."""
        if not self.view: return
        domains = self.model.get_all_scanned_domains()
        self.view.set_domains(domains)

    def perform_search(self):
        """Führt eine neue Suche durch und setzt die Sortierung zurück."""
        if not self.view: return
        domain = self.view.get_domain_filter()
        keyword = self.view.get_keyword_filter()

        self.current_results = self.model.search_scan_history(domain, keyword)

        self.sort_column = None
        self.sort_reverse = False
        self.view.display_results(self.current_results)

    def sort_results(self, column_name):
        """Sortiert die Ergebnisse mit 3-Zustands-Logik (auf, ab, unsortiert)."""
        if not self.current_results: return

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
            if column_name == 'url':
                sort_key = lambda item: item.url.lower()
            else:
                sort_key = lambda item: item.last_scanned

            self.current_results.sort(key=sort_key, reverse=self.sort_reverse)
        else:
            self.current_results.sort(key=lambda item: item.last_scanned, reverse=True)

        self.view.display_results(self.current_results)