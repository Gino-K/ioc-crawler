import customtkinter
from settings.user_settings import UserSettings
from db.database_handler import DatabaseHandler
from ui.views.dashboard.dashboard_main_view import DashboardView
from ui.views.search.search_main_view import SearchView
from ui.views.settings.settings_main_view import SettingsMainView


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.user_settings = UserSettings()
        self.db_handler = DatabaseHandler()

        self.title("IOC Webcrawler")
        self.geometry("800x650")

        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        self.tabview.add("Dashboard")
        self.tabview.add("Suche")
        self.tabview.add("Einstellungen")

        self.dashboard_view = DashboardView(self.tabview.tab("Dashboard"),
                                            controller=None)
        self.dashboard_view.pack(fill="both", expand=True)

        self.search_view = SearchView(self.tabview.tab("Suche"), controller=None)
        self.search_view.pack(fill="both", expand=True)

        self.settings_view = SettingsMainView(self.tabview.tab("Einstellungen"), model=self.user_settings)
        self.settings_view.pack(fill="both", expand=True)

        self.settings_view.controller.load_settings_into_view()


if __name__ == "__main__":
    app = App()
    app.mainloop()