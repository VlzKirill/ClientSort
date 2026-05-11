import customtkinter as ctk
import pandas as pd
from core.config_manager import ConfigManager

class StaffWindow(ctk.CTkToplevel):

    def __init__(self, parent, config):
        super().__init__(parent)

        self.config = config

        self.title("Персонал")
        self.geometry("900x600")

        self.transient(parent)

        self.df = None
        self.date_columns = []
        self.check_vars = {}  # (fio -> BooleanVar)

        self.create_ui()
        self.load_staff()

    # ---------------- UI ----------------
    def create_ui(self):

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # заголовок
        self.title_label = ctk.CTkLabel(self, text="Выберите дату")
        self.title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        # dropdown дат
        self.date_var = ctk.StringVar()
        self.date_menu = ctk.CTkOptionMenu(
            self,
            variable=self.date_var,
            values=[],
            command=self.on_date_selected
        )
        self.date_menu.grid(row=1, column=0, sticky="w", padx=10)

        # таблица (скролл)
        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        # ---------------- RESET BUTTON ----------------

        self.reset_button = ctk.CTkButton(
            self,
            text="Сброс настроек",
            fg_color="gray",
            command=self.reset_staff_settings
        )

        self.reset_button.grid(
            row=3,
            column=0,
            sticky="sw",
            padx=20,
            pady=20
        )

        # ---------------- APPLY BUTTON ----------------
        self.apply_btn = ctk.CTkButton(
            self,
            text="Применить",
            command=self.save_state
        )
        self.apply_btn.grid(row=3, column=1, sticky="se", padx=20, pady=20)

        # ---------------- EXIT BUTTON ----------------
        self.exit_btn = ctk.CTkButton(
            self,
            text="Выход",
            command=self.exit_staff_settings
        )

        self.exit_btn.grid(
            row=3,
            column=2,
            sticky="se",
            padx=20,
            pady=20
        )

    # ---------------- DATA LOAD ----------------
    def load_staff(self):

        url = self.config.schedule_url
        if not url:
            print("Нет ссылки")
            return

        try:
            self.df = pd.read_csv(self.convert_to_csv_url(url))

            # берём колонки-даты
            self.date_columns = [
                col for col in self.df.columns
                if col not in ["ФИО", "График", "Дежурства"]
            ]

            self.date_menu.configure(values=self.date_columns)

            if self.date_columns:
                self.date_var.set(self.date_columns[0])
                self.render_table(self.date_columns[0])

        except Exception as e:
            print("Ошибка загрузки:", e)

    # ---------------- DATE CHANGE ----------------
    def on_date_selected(self, value):
        self.render_table(value)

    # ---------------- TABLE RENDER ----------------
    def render_table(self, date):

        for widget in self.table_frame.winfo_children():
            widget.destroy()

        self.check_vars.clear()

        saved_state = self.config.staff_state.get(date, {})

        # header
        header = ctk.CTkFrame(self.table_frame)
        header.pack(fill="x", pady=2)

        ctk.CTkLabel(header, text="Active", width=80).pack(side="left")
        ctk.CTkLabel(header, text="ФИО", width=300).pack(side="left")
        ctk.CTkLabel(header, text="Расписание").pack(side="left")

        for _, row in self.df.iterrows():

            fio = row.get("ФИО")
            if pd.isna(fio):
                continue

            frame = ctk.CTkFrame(self.table_frame)
            frame.pack(fill="x", pady=1)

            # 🔥 вот тут restore состояния
            is_active = saved_state.get(fio, True)

            var = ctk.BooleanVar(value=is_active)
            self.check_vars[fio] = var

            cb = ctk.CTkCheckBox(frame, text="", variable=var, width=50)
            cb.pack(side="left", padx=10)

            ctk.CTkLabel(frame, text=str(fio), width=300).pack(side="left")

            value = row.get(date, "")
            if pd.isna(value):
                value = ""

            ctk.CTkLabel(frame, text=str(value)).pack(side="left")


    # ---------------- SAVE STATE ----------------
    def save_state(self):

        selected_date = self.date_var.get()

        if not hasattr(self.config, "staff_state"):
            self.config.staff_state = {}

        self.config.staff_state[selected_date] = {
            fio: var.get()
            for fio, var in self.check_vars.items()
        }

        ConfigManager.save(self.config)
        print("Сохранена конфигурация персонала")

    # ---------------- CSV FIX ----------------
    def convert_to_csv_url(self, url: str) -> str:

        import re

        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if not match:
            return url

        sheet_id = match.group(1)

        gid_match = re.search(r"gid=(\d+)", url)
        gid = gid_match.group(1) if gid_match else "0"

        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    def reset_staff_settings(self):

        self.config.reset_staff_settings()
        ConfigManager.save(self.config)
        current_date = self.date_var.get()
        if current_date:
            self.render_table(current_date)

        print("Настройки персонала сброшены")

    def exit_staff_settings(self):
        self.destroy()