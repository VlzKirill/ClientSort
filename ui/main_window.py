import customtkinter as ctk
from datetime import datetime
from ui.settings_window import SettingsWindow
from ui.staff_window import StaffWindow
from core.config_manager import ConfigManager
from ui.help_window import HelpWindow

class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.DEFAULT_DATE_TEXT = "Выберите дату"

        self.geometry("1000x600")
        self.title("Client Sorter")

        self.config = ConfigManager.load()

        self.help_window = None
        self.settings_window = None
        self.staff_window = None
        self.selected_date = None
        self.date_menu = None

        self.create_ui()
        self.update_dates()

    def create_ui(self):

        # верхняя панель
        top_frame = ctk.CTkFrame(self, height=50)
        top_frame.pack(fill="x", padx=10, pady=10)

        # кнопка настроек
        settings_button = ctk.CTkButton(
            top_frame,
            text="⚙ Настройки",
            width=40,
            height=40,
            font=("Arial", 20),
            command=self.open_settings
        )
        settings_button.pack(side="left", padx=5, pady=5)

        #кнопка Персонала
        staff_button = ctk.CTkButton(
            top_frame,
            text="👥 Персонал",
            width=40,
            height=40,
            font=("Arial", 20),
            command=self.open_staff
        )
        staff_button.pack(side="left", padx=5, pady=5)

        # Выбор даты
        self.selected_date = ctk.StringVar(value=self.DEFAULT_DATE_TEXT)

        saved_dates = list(self.config.staff_state.keys())

        self.date_menu = ctk.CTkOptionMenu(
            top_frame,
            width=40,
            height=40,
            font=("Arial", 18),
            variable=self.selected_date,
            values=[self.DEFAULT_DATE_TEXT] + saved_dates
        )

        self.date_menu.pack(side="left", padx=10)

        # Кнопка справки
        help_button = ctk.CTkButton(
            top_frame,
            text="?",
            width=40,
            height=40,
            font=("Arial", 20),
            command=self.open_help
        )
        help_button.pack(side="right", padx=10)

    def open_settings(self):

        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self, self.config)
        else:
            self.settings_window.focus()

    def open_staff(self):

        if self.staff_window is None or not self.staff_window.winfo_exists():
            self.staff_window = StaffWindow(self, self.config)
        else:
            self.staff_window.focus()

    def open_help(self):
        if self.help_window is None or not self.help_window.winfo_exists():
            self.help_window = HelpWindow(self)
        else:
            self.help_window.focus()

    def sort_dates(self, date_list):
        return sorted(date_list, key=lambda d: datetime.strptime(d, "%d.%m"))

    def update_dates(self):
        saved_dates = list(self.config.staff_state.keys())
        saved_dates = self.sort_dates(saved_dates)

        if self.date_menu:
            self.date_menu.configure(values=[self.DEFAULT_DATE_TEXT] + saved_dates)

        current = self.selected_date.get()

        if current not in saved_dates or current == self.DEFAULT_DATE_TEXT:
            self.selected_date.set(self.DEFAULT_DATE_TEXT)