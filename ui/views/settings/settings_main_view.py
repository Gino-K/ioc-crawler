import customtkinter

from ui.controllers.settings_controller import SettingsController
from ui.views.settings.blacklist_view import BlacklistView
from ui.views.settings.schedular_view import SchedulerView
from ui.views.settings.source_url_view import SourceURLView


class SettingsMainView(customtkinter.CTkFrame):
    def __init__(self, master, model):
        super().__init__(master, fg_color="transparent")

        self.controller = SettingsController(model)
        self.controller.set_view(self)

        self.source_view = SourceURLView(self, self.controller)
        self.source_view.pack(fill="x", padx=20, pady=(10, 0))

        self.blacklist_view = BlacklistView(self, self.controller)
        self.blacklist_view.pack(fill="x", padx=20, pady=20)

        self.scheduler_view = SchedulerView(self, self.controller)
        self.scheduler_view.pack(fill="x", padx=20, pady=10)