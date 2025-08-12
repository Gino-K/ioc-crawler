import customtkinter
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ChartFrame(customtkinter.CTkFrame):
    """
    Eine wiederverwendbare Widget-Klasse, die einen Frame mit Buttons
    und einem Matplotlib-Diagramm-Canvas kapselt.
    """

    def __init__(self, master, title, button_configs):
        super().__init__(master)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")

        for i, config in enumerate(button_configs):
            button = customtkinter.CTkButton(button_frame, text=config["text"], command=config["command"])
            button.pack(side="left", padx=(0, 10) if i < len(button_configs) - 1 else 0)

        canvas_frame = customtkinter.CTkFrame(self)
        canvas_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.fig = Figure(dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    def update_chart(self, plot_function, labels, data, title):
        """
        Aktualisiert das Diagramm, indem eine übergebene Zeichenfunktion aufgerufen wird.
        """
        self.ax.clear()
        theme = customtkinter.get_appearance_mode()
        bg_color = "#2b2b2b" if theme == "Dark" else "#f0f0f0"
        text_color = "white" if theme == "Dark" else "black"

        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)

        plot_function(self.ax, labels, data, text_color)

        self.ax.set_title(title, color=text_color, fontsize=14, weight='bold')
        for spine in self.ax.spines.values():
            spine.set_edgecolor(text_color)

        try:
            self.fig.tight_layout()
        except Exception:
            pass

        self.canvas.draw()