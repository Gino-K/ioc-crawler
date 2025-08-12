import datetime
import threading

import customtkinter
from settings.user_settings import UserSettings
from db.ui_db_handler import UiDBHandler
from ui.controllers.history_controller import ArticleHistoryController
from ui.controllers.settings_controller import SettingsController
from ui.controllers.search_controller import SearchController
from ui.controllers.dashboard_controller import DashboardController
from ui.views.history.article_history_view import ArticleHistoryView
from ui.views.settings.settings_main_view import SettingsMainView
from ui.views.dashboard.dashboard_main_view import DashboardView
from ui.views.search.search_main_view import SearchView


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.user_settings = UserSettings()
        self.db_handler = UiDBHandler()

        self.settings_controller = SettingsController(self.user_settings)
        self.dashboard_controller = DashboardController(self.db_handler)
        self.search_controller = SearchController(self.db_handler, self.user_settings)
        self.article_history_controller = ArticleHistoryController(self.db_handler)


        self.settings_controller.post_init_connect(self)


        self.title("IOC Webcrawler")
        self.geometry("1200x800")

        self.tabview = customtkinter.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        self.tabview.add("Dashboard")
        self.tabview.add("Suche")
        self.tabview.add("Einstellungen")
        self.tabview.add("Artikel Links")


        views = {}

        views['dashboard'] = DashboardView(self.tabview.tab("Dashboard"), self.dashboard_controller)
        self.dashboard_controller.set_view(views['dashboard'])
        views['dashboard'].pack(fill="both", expand=True)

        views['search'] = SearchView(self.tabview.tab("Suche"), self.search_controller)
        self.search_controller.set_view(views['search'])
        views['search'].pack(fill="both", expand=True)

        self.settings_view = SettingsMainView(self.tabview.tab("Einstellungen"), controller=self.settings_controller)
        self.settings_controller.set_view(self.settings_view)
        self.settings_view.pack(fill="both", expand=True)

        self.history_view = ArticleHistoryView(self.tabview.tab("Artikel Links"), self.article_history_controller)
        self.article_history_controller.set_view(self.history_view)
        self.history_view.pack(fill="both", expand=True)

        self.settings_controller.load_settings_into_view()

        self.dashboard_controller.update_ioc_sighting_chart_data('ioc')
        self.dashboard_controller.update_ioc_type_apt_chart_data('ioc_type')
        self.dashboard_controller.update_sighting_details_chart_data('source')
        self.search_controller.perform_search()
        self.article_history_controller.load_initial_data()
        self.article_history_controller.perform_search()

        self.start_initial_preload()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def refresh_data_views(self):
        """Aktualisiert alle datenabhängigen Ansichten (Dashboard, Suche)."""
        print("[App] Aktualisiere Dashboard- und Such-Ansichten nach Crawler-Lauf...")
        self.dashboard_controller.update_ioc_sighting_chart_data('ioc')
        self.dashboard_controller.update_ioc_type_apt_chart_data('ioc_type')
        self.dashboard_controller.update_sighting_details_chart_data('source')
        self.search_controller.perform_search()
        print("[App] Ansichten erfolgreich aktualisiert.")

    def start_initial_preload(self):
        """
        Startet den Preload-Prozess im Hintergrund, aber nur, wenn die Daten
        fehlen oder älter als 7 Tage sind.
        """
        PRELOAD_THRESHOLD_DAYS = 7

        last_run_str = self.user_settings.last_preload_timestamp

        needs_preload = False
        if not last_run_str:
            print("[App] Entscheidung: Preload wird ausgeführt (kein Zeitstempel gefunden).")
            needs_preload = True
        else:
            try:
                last_run_time = datetime.datetime.fromisoformat(last_run_str).astimezone(datetime.timezone.utc)
                current_time = datetime.datetime.now(datetime.timezone.utc)
                threshold = datetime.timedelta(days=PRELOAD_THRESHOLD_DAYS)
                time_difference = current_time - last_run_time

                if time_difference > threshold:
                    print(
                        f"[App] Entscheidung: Preload wird ausgeführt (Daten sind älter als {PRELOAD_THRESHOLD_DAYS} Tage).")
                    needs_preload = True
                else:
                    print("[App] Entscheidung: Preload wird übersprungen (Daten sind aktuell).")
            except Exception as e:
                print(f"[App] FEHLER beim Verarbeiten des Zeitstempels: {e}. Führe Preload vorsichtshalber aus.")
                needs_preload = True

        if needs_preload:
            print("[App] Starte initialen Preload-Prozess im Hintergrund...")
            preload_thread = threading.Thread(
                target=self.settings_controller.preloader_manager.run_all,
                daemon=True
            )
            preload_thread.start()

    def on_closing(self):
        print("Anwendung wird geschlossen...")
        self.quit()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()