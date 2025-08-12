import customtkinter
from .chart_frame import ChartFrame


class DashboardView(customtkinter.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="transparent")
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=2)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.monthly_chart = ChartFrame(self, "Monatliche Aktivitaet", [
            {"text": "IOCs pro Monat", "command": lambda: self.controller.update_ioc_sighting_chart_data('ioc')},
            {"text": "Sightings pro Monat",
             "command": lambda: self.controller.update_ioc_sighting_chart_data('sighting')}
        ])
        self.monthly_chart.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="nsew")

        self.type_apt_chart = ChartFrame(self, "Top-Statistiken", [
            {"text": "IOC-Typen", "command": lambda: self.controller.update_ioc_type_apt_chart_data('ioc_type')},
            {"text": "Top 5 APTs", "command": lambda: self.controller.update_ioc_type_apt_chart_data('apt')}
        ])
        self.type_apt_chart.grid(row=1, column=0, padx=(10, 5), pady=(5, 10), sticky="nsew")

        self.sighting_details_chart = ChartFrame(self, "Sighting-Details", [
            {"text": "Top Quellen", "command": lambda: self.controller.update_sighting_details_chart_data('source')},
            {"text": "Top Laender", "command": lambda: self.controller.update_sighting_details_chart_data('country')}
        ])
        self.sighting_details_chart.grid(row=1, column=1, padx=(5, 10), pady=(5, 10), sticky="nsew")

    def update_ioc_sighting_chart(self, labels, data, title):
        self.monthly_chart.update_chart(self._plot_vertical_bar, labels, data, title)

    def update_type_apt_chart(self, labels, data, title):
        self.type_apt_chart.update_chart(self._plot_horizontal_bar, labels, data, title)

    def update_sighting_details_chart(self, labels, data, title):
        self.sighting_details_chart.update_chart(self._plot_horizontal_bar, labels, data, title)

    def _plot_vertical_bar(self, ax, labels, data, text_color):
        if not data:
            ax.text(0.5, 0.5, 'Keine Daten verfuegbar', ha='center', va='center', color=text_color)
            ax.set_xticks([])
            ax.set_yticks([])
            return

        ax.bar(labels, data, color="#1f6aa5")
        ax.set_ylabel("Anzahl", color=text_color)
        ax.tick_params(axis='x', colors=text_color, rotation=45)
        ax.tick_params(axis='y', colors=text_color)

    def _plot_horizontal_bar(self, ax, labels, data, text_color):
        if not data:
            ax.text(0.5, 0.5, 'Keine Daten verfuegbar', ha='center', va='center', color=text_color)
            ax.set_xticks([])
            ax.set_yticks([])
            return

        y_pos = range(len(labels))
        ax.barh(y_pos, data, align='center', color="#4a75ff")
        ax.set_yticks(y_pos, labels=labels)
        ax.invert_yaxis()
        ax.set_xlabel('Anzahl', color=text_color)
        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        for index, value in enumerate(data):
            ax.text(value, index, f' {value}', va='center', color=text_color)