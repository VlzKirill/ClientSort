import customtkinter as ctk
import pandas as pd
from core.config_manager import ConfigManager
import re

class StaffWindow(ctk.CTkToplevel):

    def __init__(self, parent, config):
        super().__init__(parent)

        self.config = config

        self.title("Персонал")
        self.geometry("900x600")

        self.transient(parent)

        self.df = None
        self.date_columns = []
        self.check_vars = {}
        self.schedule_entries = {}
        self.lunch_entries = {}

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

        # ---------------- BOTTOM FRAME ----------------

        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=20,
            pady=20
        )

        self.bottom_frame.grid_columnconfigure(0, weight=1)

        # ---------------- RESET BUTTON ----------------

        self.reset_button = ctk.CTkButton(
            self.bottom_frame,
            text="Сброс настроек",
            fg_color="gray",
            command=self.reset_staff_settings
        )

        self.reset_button.grid(
            row=0,
            column=0,
            sticky="w"
        )

        # ---------------- RIGHT BUTTONS FRAME ----------------

        self.right_buttons = ctk.CTkFrame(
            self.bottom_frame,
            fg_color="transparent"
        )

        self.right_buttons.grid(
            row=0,
            column=1,
            sticky="e"
        )

        # ---------------- APPLY BUTTON ----------------

        self.apply_btn = ctk.CTkButton(
            self.right_buttons,
            text="Применить",
            command=self.save_state
        )

        self.apply_btn.pack(side="left", padx=(0, 10))

        # ---------------- EXIT BUTTON ----------------

        self.exit_btn = ctk.CTkButton(
            self.right_buttons,
            text="Выход",
            command=self.destroy
        )

        self.exit_btn.pack(side="left")

    # ---------------- DATA LOAD ----------------
    def load_staff(self):

        url = self.config.schedule_url
        if not url:
            print("Нет ссылки")
            return

        try:
            self.df = pd.read_csv(self.convert_to_csv_url(url))
            self.lunch_data = self.load_lunch_data()

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

    def load_lunch_data(self):

        url = self.config.lunch_url
        if not url:
            return {}

        try:
            df = pd.read_csv(self.convert_to_csv_url(url))
            lunch_map = {}

            for _, row in df.iterrows():
                # колонка A
                window_number = row.iloc[0] if len(row) > 0 else None
                try:
                    int(window_number)
                except:
                    continue

                # колонка B
                fio = row.iloc[1] if len(row) > 1 else None

                # колонка C
                lunch = row.iloc[2] if len(row) > 2 else ""

                if pd.notna(fio):
                    fio = str(fio).strip()

                    lunch_map[fio] = {
                        "window": int(window_number),
                        "lunch": str(lunch)
                    }

            return lunch_map

        except Exception as e:

            print("Ошибка загрузки обедов:", e)
            return {}

    # ---------------- DATE CHANGE ----------------
    def on_date_selected(self, value):
        self.render_table(value)

    # ---------------- TABLE RENDER ----------------
    def render_table(self, date):

        # очистка таблицы
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        self.check_vars.clear()
        self.schedule_entries.clear()
        self.lunch_entries.clear()

        # сохранённые данные
        saved_state = self.config.staff_state.get(date, {})

        # ---------------- HEADER ----------------

        header = ctk.CTkFrame(self.table_frame)
        header.pack(fill="x", pady=2)

        header.grid_columnconfigure(0, minsize=80)
        header.grid_columnconfigure(1, weight=1, minsize=300)
        header.grid_columnconfigure(2, weight=1, minsize=150)
        header.grid_columnconfigure(3, weight=1, minsize=150)

        ctk.CTkLabel(
            header,
            text="Active",
            width=80
        ).grid(row=0, column=0, padx=5, sticky="w")

        ctk.CTkLabel(
            header,
            text="ФИО"
        ).grid(row=0, column=1, padx=5, sticky="w")

        ctk.CTkLabel(
            header,
            text="Расписание"
        ).grid(row=0, column=2, padx=5, sticky="w")

        ctk.CTkLabel(
            header,
            text="Обед"
        ).grid(row=0, column=3, padx=5, sticky="w")

        # ---------------- ROWS ----------------

        for _, row in self.df.iterrows():

            fio = row.get("ФИО")

            if pd.isna(fio):
                continue

            fio = str(fio).strip()
            if fio not in self.lunch_data:
                continue

            # сохранённые значения
            person_state = saved_state.get(fio, {})

            schedule_value = person_state.get(
                "schedule",
                row.get(date, "")
            )

            default_active = self.is_schedule_active(schedule_value)

            is_active = person_state.get(
                "active",
                default_active
            )

            lunch_value = person_state.get(
                "lunch",
                self.lunch_data[fio]["lunch"]
            )

            if pd.isna(schedule_value):
                schedule_value = ""

            if pd.isna(lunch_value):
                lunch_value = ""

            # строка
            frame = ctk.CTkFrame(self.table_frame)
            frame.pack(fill="x", pady=1)

            frame.grid_columnconfigure(0, minsize=80)
            frame.grid_columnconfigure(1, weight=1, minsize=300)
            frame.grid_columnconfigure(2, weight=1, minsize=150)
            frame.grid_columnconfigure(3, weight=1, minsize=150)

            # ---------------- ACTIVE ----------------

            var = ctk.BooleanVar(value=is_active)

            self.check_vars[fio] = var

            cb = ctk.CTkCheckBox(
                frame,
                text="",
                variable=var,
                width=50
            )

            cb.grid(
                row=0,
                column=0,
                padx=5,
                sticky="w"
            )

            # ---------------- FIO ----------------

            ctk.CTkLabel(
                frame,
                text=fio
            ).grid(
                row=0,
                column=1,
                padx=5,
                sticky="w"
            )

            # ---------------- SCHEDULE ----------------

            schedule_entry = ctk.CTkEntry(frame)

            schedule_entry.insert(0, str(schedule_value))

            schedule_entry.grid(
                row=0,
                column=2,
                padx=5,
                pady=2,
                sticky="ew"
            )

            self.schedule_entries[fio] = schedule_entry

            # ---------------- LUNCH ----------------

            lunch_entry = ctk.CTkEntry(frame)

            lunch_entry.insert(0, str(lunch_value))

            lunch_entry.grid(
                row=0,
                column=3,
                padx=5,
                pady=2,
                sticky="ew"
            )

            self.lunch_entries[fio] = lunch_entry


    # ---------------- SAVE STATE ----------------
    def save_state(self):

        selected_date = self.date_var.get()

        self.config.staff_state[selected_date] = {}

        for fio, var in self.check_vars.items():
            self.config.staff_state[selected_date][fio] = {
                "active": var.get(),
                "schedule": self.schedule_entries[fio].get(),
                "lunch": self.lunch_entries[fio].get()
            }

        ConfigManager.save(self.config)
        self.master.update_dates()
        print("Сохранено")

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
        self.master.update_dates()
        print("Настройки персонала сброшены")

    def is_schedule_active(self, value):

        if not value:
            return False

        value = str(value).strip()
        pattern = r"^\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}$"

        return bool(re.match(pattern, value))