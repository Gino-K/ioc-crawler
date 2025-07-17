from scheduler import task_manager


class SettingsController:
    def __init__(self, model):
        self.model = model
        self.view = None

    def set_view(self, view):
        """Verknüpft den Controller mit seiner Haupt-View."""
        self.view = view

    def save_sources(self):
        """Holt die URLs von der View und speichert sie im Model."""
        urls = self.view.source_view.get_urls()
        self.model.source_urls = urls
        self.model.save()
        print("[SettingsController] Quell-URLs gespeichert.")

    def save_blacklist(self):
        """Holt die Blacklist von der View und speichert sie im Model."""
        keywords = self.view.blacklist_view.get_keywords()
        self.model.blacklist_keywords = keywords
        self.model.save()
        print("[SettingsController] Blacklist gespeichert.")

    def save_schedule(self):
        """Holt die Zeitplan-Daten von der View, speichert sie und wendet sie an."""
        schedule_data = self.view.scheduler_view.get_schedule_data()
        self.model.schedule = schedule_data
        self.model.save()

        task_manager.manage_schedule(
            schedule_data['day'],
            schedule_data['time'],
            schedule_data['enabled']
        )
        print("[SettingsController] Zeitplan gespeichert und angewendet.")

    def load_settings_into_view(self):
        """Lädt alle Einstellungen aus dem Model und übergibt sie an die View-Komponenten."""
        if not self.view:
            return

        print("[SettingsController] Lade Einstellungen in die GUI-Ansichten.")
        self.view.source_view.set_urls(self.model.source_urls)
        self.view.blacklist_view.set_keywords(self.model.blacklist_keywords)
        self.view.scheduler_view.set_schedule_data(self.model.schedule)
