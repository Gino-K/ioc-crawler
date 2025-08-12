import customtkinter

from ui.views.settings.blacklist_view import BlacklistView
from ui.views.settings.crawler_control_view import CrawlerControlView
from ui.views.settings.export_view import ExportSettingsView
from ui.views.settings.preloader_view import PreloaderView
from ui.views.settings.schedular_view import SchedulerView
from ui.views.settings.source_url_view import SourceURLView


class SettingsMainView(customtkinter.CTkScrollableFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="transparent")

        self.controller = controller

        self.crawler_control_view = CrawlerControlView(self, self.controller)
        self.crawler_control_view.pack(fill="x", padx=20, pady=20)

        self.source_view = SourceURLView(self, self.controller)
        self.source_view.pack(fill="x", padx=20, pady=(10, 0))

        self.blacklist_view = BlacklistView(self, self.controller)
        self.blacklist_view.pack(fill="x", padx=20, pady=20)

        self.export_view = ExportSettingsView(self, self.controller)
        self.export_view.pack(fill="x", padx=20, pady=(0, 20))

        self.preloader_view = PreloaderView(self, self.controller)
        self.preloader_view.pack(fill="x", padx=20, pady=(0, 20))

        self.scheduler_view = SchedulerView(self, self.controller)
        self.scheduler_view.pack(fill="x", padx=20, pady=10)