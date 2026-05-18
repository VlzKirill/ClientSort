import customtkinter as ctk
from tkinter import filedialog
from core.config_manager import ConfigManager

class SettingsWindow(ctk.CTkToplevel):

    def __init__(self, parent, config):
        super().__init__(parent)

        self.config = config

        self.title("Настройки")
        self.geometry("800x500")

        self.transient(parent)

        self.create_ui()
        self.load_settings()

    def create_ui(self):
        # ---------------- COLUMNS ----------------
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # ---------------- TITLE ----------------
        title = ctk.CTkLabel(
            self,
            text="Настройки",
            font=("Arial", 22)
        )
        title.grid(row=0, column=0, columnspan=3, pady=20)

        # ---------------- SCHEDULE ----------------
        self.schedule_label = ctk.CTkLabel(
            self,
            text="Ссылка на Google Таблицу с графиком:"
        )
        self.schedule_label.grid(row=1, column=0, columnspan=3, sticky="w", padx=20)

        self.schedule_entry = ctk.CTkEntry(self)
        self.schedule_entry.grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=(0, 15))

        # ---------------- LUNCH ----------------
        self.lunch_label = ctk.CTkLabel(
            self,
            text="Ссылка на Google Таблицу с обедами:"
        )
        self.lunch_label.grid(row=3, column=0, columnspan=3, sticky="w", padx=20)

        self.lunch_entry = ctk.CTkEntry(self)
        self.lunch_entry.grid(row=4, column=0, columnspan=3, sticky="ew", padx=20, pady=(0, 20))

        # ---------------- FILE ----------------
        self.file_label = ctk.CTkLabel(
            self,
            text="Excel файл с записанными клиентами:"
        )
        self.file_label.grid(row=5, column=0, columnspan=3, sticky="w", padx=20)

        self.browse_button = ctk.CTkButton(
            self,
            text="Обзор",
            width=120,
            command=self.select_excel_file
        )
        self.browse_button.grid(row=6, column=0, padx=(20, 10), pady=(5, 10), sticky="w")

        self.file_path_entry = ctk.CTkEntry(self)
        self.file_path_entry.grid(row=6, column=1, columnspan=2, padx=(0, 20), pady=(5, 10), sticky="ew")

        self.grid_rowconfigure(7, weight=1)

        # ---------------- INFO  ----------------
        hint_label = ctk.CTkLabel(
            self,
            text="Для вставки текста смените раскладку клавиатуры на английскую",
            font=("Arial", 12, "italic"),
            text_color="gray"
        )
        hint_label.grid(row=7, column=0, columnspan=3, pady=(0, 10))

        # ---------------- BOTTOM BUTTONS FRAME ----------------
        bottom_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_buttons_frame.grid(row=8, column=0, columnspan=3, sticky="ew", padx=20, pady=20)
        bottom_buttons_frame.grid_columnconfigure(0, weight=1)
        bottom_buttons_frame.grid_columnconfigure(1, weight=0)
        bottom_buttons_frame.grid_columnconfigure(2, weight=0)

        # ---------------- RESET BUTTON ----------------
        self.reset_button = ctk.CTkButton(
            bottom_buttons_frame,
            text="Сброс настроек",
            fg_color="gray",
            command=self.reset_settings
        )
        self.reset_button.grid(row=0, column=0, sticky="w")

        # ---------------- APPLY BUTTON ----------------
        self.apply_button = ctk.CTkButton(
            bottom_buttons_frame,
            text="Применить",
            command=self.save_settings
        )
        self.apply_button.grid(row=0, column=1, sticky="e", padx=(10, 10))

        # ---------------- EXIT BUTTON ----------------
        self.exit_button = ctk.CTkButton(
            bottom_buttons_frame,
            text="Выход",
            command=self.destroy
        )
        self.exit_button.grid(row=0, column=2, sticky="e")

    def select_excel_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите Excel файл",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.file_path_entry.delete(0, "end")
            self.file_path_entry.insert(0, file_path)

    def save_settings(self):
        self.config.schedule_url = self.schedule_entry.get()
        self.config.lunch_url = self.lunch_entry.get()
        self.config.excel_file = self.file_path_entry.get()

        ConfigManager.save(self.config)
        print("Настройки сохранены")

    def load_settings(self):
        self.schedule_entry.delete(0, "end")
        self.lunch_entry.delete(0, "end")
        self.file_path_entry.delete(0, "end")

        self.schedule_entry.insert(0, self.config.schedule_url)
        self.lunch_entry.insert(0, self.config.lunch_url)
        self.file_path_entry.insert(0, self.config.excel_file)

    def reset_settings(self):
        self.config.reset_main_settings()
        ConfigManager.save(self.config)
        self.load_settings()
        print("Настройки сброшены")