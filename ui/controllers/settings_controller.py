import threading

from crawler.crawler_orch import CrawlerOrchestrator
from extraScripts.preload_manager import PreloaderManager
from scheduler import task_manager
from settings.user_settings import UserSettings
from ui.views.settings.settings_main_view import SettingsMainView


class SettingsController:
    model: UserSettings
    app: 'App'
    view: SettingsMainView | None
    preloader_manager: PreloaderManager

    def __init__(self, model: UserSettings):
        self.model = model
        self.app = None
        self.view = None
        self.preloader_manager = None

    def post_init_connect(self, app: 'App'):
        """Verbindet den Controller mit der Haupt-App und initialisiert abhaengige Komponenten."""
        self.app = app
        self.preloader_manager = PreloaderManager(user_settings=self.model, db_handler=self.app.db_handler)


    def set_view(self, view):
        """Verknuepft den Controller mit seiner Haupt-View."""
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

    def save_export_settings(self):
        """Holt die Export-Einstellungen von der View und speichert sie."""
        export_settings = self.view.export_view.get_settings()
        self.model.export_formats = export_settings
        self.model.save()
        print("[SettingsController] Export-Einstellungen gespeichert.")

    def load_settings_into_view(self):
        """Laedt alle Einstellungen aus dem Model und uebergibt sie an die View-Komponenten."""
        if not self.view:
            return

        print("[SettingsController] Lade Einstellungen in die GUI-Ansichten.")
        self.view.source_view.set_urls(self.model.source_urls)
        self.view.blacklist_view.set_keywords(self.model.blacklist_keywords)
        self.view.scheduler_view.set_schedule_data(self.model.schedule)
        self.view.export_view.set_settings(self.model.export_formats)

    def _run_task_in_thread(self, target_function, button, running_text="Wird ausgefuehrt...", on_complete=None):
        """Hilfsfunktion, um eine lange Aufgabe in einem Thread zu starten."""

        def worker():
            original_text = button.cget("text")
            self.view.after(0, lambda: button.configure(state="disabled", text=running_text))

            try:
                target_function()
                if on_complete:
                    self.app.after(100, on_complete)
            finally:
                self.view.after(100, lambda: button.configure(state="normal", text=original_text))

        threading.Thread(target=worker, daemon=True).start()

    def run_crawler_manually(self):
        """Erstellt eine Instanz des Crawlers und fuehrt ihn in einem Thread aus."""
        print("[SettingsController] Manueller Crawler-Start angefordert...")
        button = self.view.crawler_control_view.button_run_crawler

        def crawler_task():
            orchestrator = CrawlerOrchestrator()
            orchestrator.run()

        self._run_task_in_thread(
            crawler_task,
            button,
            running_text="Crawler laeuft...",
            on_complete=self.app.refresh_data_views
        )

    def run_all_preloaders(self):
        """Startet alle Preloads in einem separaten Thread."""
        print("[SettingsController] Starte alle Preloads...")
        button = self.view.preloader_view.button_all
        self._run_task_in_thread(self.preloader_manager.run_all, button)

    def run_tld_preloader(self):
        """Startet den TLD-Preload in einem separaten Thread."""
        print("[SettingsController] Starte TLD Preload...")
        button = self.view.preloader_view.button_tlds
        self._run_task_in_thread(lambda: self.preloader_manager.run_specific("tlds"), button)

    def run_country_preloader(self):
        """Startet den Laender-Preload in einem separaten Thread."""
        print("[SettingsController] Starte Country Preload...")
        button = self.view.preloader_view.button_countries
        self._run_task_in_thread(lambda: self.preloader_manager.run_specific("countries"), button)

    def run_apt_preloader(self):
        """Startet den APT-Preload in einem separaten Thread."""
        print("[SettingsController] Starte APT Preload...")
        button = self.view.preloader_view.button_apts
        self._run_task_in_thread(lambda: self.preloader_manager.run_specific("apts"), button)
