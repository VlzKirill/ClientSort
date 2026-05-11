import customtkinter as ctk
from ui.settings_window import SettingsWindow
from ui.staff_window import StaffWindow
from core.config_manager import ConfigManager
from ui.help_window import HelpWindow

class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.geometry("1000x600")
        self.title("Client Sorter")

        self.config = ConfigManager.load()

        self.help_window = None
        self.settings_window = None
        self.staff_window = None
        self.create_ui()

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

        # # Выбор даты
        # self.selected_date = ctk.StringVar()
        # saved_dates = list(self.config.staff_state.keys())
        #
        # date_menu = ctk.CTkOptionMenu(
        #     top_frame,
        #     variable=self.selected_date,
        #     values=saved_dates
        # )
        #
        # date_menu.pack(side="left", padx=10)
        #
        # if saved_dates:
        #     self.selected_date.set(saved_dates[0])

        # Кнопка справки
        help_button = ctk.CTkButton(
            top_frame,
            text="?",
            width=30,
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