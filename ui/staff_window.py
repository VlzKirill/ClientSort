import customtkinter as ctk
import pandas as pd
from core.config_manager import ConfigManager
import re
import unicodedata

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

    # =========================================================
    # UI
    # =========================================================
    def create_ui(self):

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.title_label = ctk.CTkLabel(
            self,
            text="Выберите дату"
        )
        self.title_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=(10, 5)
        )

        self.date_var = ctk.StringVar()

        self.date_menu = ctk.CTkOptionMenu(
            self,
            variable=self.date_var,
            values=[],
            command=self.on_date_selected
        )
        self.date_menu.grid(
            row=1,
            column=0,
            sticky="w",
            padx=10
        )

        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10
        )

        # ---------------- BOTTOM FRAME ----------------

        self.bottom_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.bottom_frame.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=20,
            pady=20
        )

        self.bottom_frame.grid_columnconfigure(0, weight=1)

        self.right_buttons = ctk.CTkFrame(
            self.bottom_frame,
            fg_color="transparent"
        )

        self.right_buttons.grid(
            row=0,
            column=1,
            sticky="e"
        )

        self.apply_btn = ctk.CTkButton(
            self.right_buttons,
            text="Применить",
            command=self.save_state
        )
        self.apply_btn.pack(
            side="left",
            padx=(0, 10)
        )

        self.exit_btn = ctk.CTkButton(
            self.right_buttons,
            text="Выход",
            command=self.destroy
        )
        self.exit_btn.pack(side="left")

    # =========================================================
    # НОРМАЛИЗАЦИЯ ФИО
    # =========================================================
    def normalize_fio(self, value):
        """
        Нормализация ФИО для сравнения.

        Примеры:

        "Иванов Иван Иванович"
        "Иванов Иван Иванович *"
        "Иванов  Иван   Иванович"
        "Иванов Иван Иванович."

        будут считаться одним человеком.

        Также:
            ё == е
            й == и

        Регистр не учитывается.
        """

        if value is None or pd.isna(value):
            return ""

        value = str(value)

        # Unicode-нормализация
        value = unicodedata.normalize("NFKC", value)

        # Удаляем всё, кроме букв и пробельных символов.
        # Например:
        # * . , ! ? ( ) - _ / и т.д.
        # будут удалены.
        value = "".join(
            ch for ch in value
            if ch.isalpha() or ch.isspace()
        )

        # Убираем пробелы по краям
        value = value.strip()

        # Несколько пробелов подряд -> один
        value = re.sub(r"\s+", " ", value)

        # Не различаем:
        # ё / е
        # й / и
        value = value.lower()
        value = value.replace("ё", "е")
        value = value.replace("й", "и")

        return value

    # =========================================================
    # DATA LOAD
    # =========================================================
    def load_staff(self):

        url = self.config.schedule_url

        if not url:
            print("Нет ссылки")
            return

        self.df = pd.read_csv(
            self.convert_to_csv_url(url)
        )

        self.lunch_data = self.load_lunch_data()

        # Берём колонки-даты
        self.date_columns = [
            col
            for col in self.df.columns
            if col not in ["ФИО", "График", "Дежурства"]
        ]

        self.date_menu.configure(
            values=self.date_columns
        )

        if self.date_columns:
            self.date_var.set(self.date_columns[0])
            self.render_table(self.date_columns[0])

    # =========================================================
    # LOAD LUNCH DATA
    # =========================================================
    def load_lunch_data(self):

        url = self.config.lunch_url

        if not url:
            return {}

        try:

            df = pd.read_csv(
                self.convert_to_csv_url(url)
            )

            lunch_map = {}

            for _, row in df.iterrows():

                # Колонка A
                window_number = (
                    row.iloc[0]
                    if len(row) > 0
                    else None
                )

                try:
                    int(window_number)
                except:
                    continue

                # Колонка B
                fio = (
                    row.iloc[1]
                    if len(row) > 1
                    else None
                )

                # Колонка C
                lunch = (
                    row.iloc[2]
                    if len(row) > 2
                    else ""
                )

                if pd.notna(fio):

                    original_fio = str(fio).strip()

                    normalized_fio = self.normalize_fio(
                        original_fio
                    )

                    if not normalized_fio:
                        continue

                    lunch_map[normalized_fio] = {
                        "fio": original_fio,
                        "window": int(window_number),
                        "lunch": (
                            ""
                            if pd.isna(lunch)
                            else str(lunch).strip()
                        )
                    }

            return lunch_map

        except Exception as e:
            print("Ошибка загрузки обедов:", e)
            return {}

    # =========================================================
    # DATE CHANGE
    # =========================================================
    def on_date_selected(self, value):
        self.render_table(value)

    # =========================================================
    # TABLE RENDER
    # =========================================================
    def render_table(self, date):

        # Очистка таблицы
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        self.check_vars.clear()
        self.schedule_entries.clear()
        self.lunch_entries.clear()

        # Сохранённые данные
        saved_state = self.config.staff_state.get(
            date,
            {}
        )

        # =====================================================
        # HEADER
        # =====================================================

        header = ctk.CTkFrame(self.table_frame)
        header.pack(
            fill="x",
            pady=2
        )

        header.grid_columnconfigure(
            0,
            minsize=80
        )

        header.grid_columnconfigure(
            1,
            weight=1,
            minsize=300
        )

        header.grid_columnconfigure(
            2,
            weight=1,
            minsize=150
        )

        header.grid_columnconfigure(
            3,
            weight=1,
            minsize=150
        )

        ctk.CTkLabel(
            header,
            text="Active",
            width=80
        ).grid(
            row=0,
            column=0,
            padx=5,
            sticky="w"
        )

        ctk.CTkLabel(
            header,
            text="ФИО"
        ).grid(
            row=0,
            column=1,
            padx=5,
            sticky="w"
        )

        ctk.CTkLabel(
            header,
            text="Расписание"
        ).grid(
            row=0,
            column=2,
            padx=5,
            sticky="w"
        )

        ctk.CTkLabel(
            header,
            text="Обед"
        ).grid(
            row=0,
            column=3,
            padx=5,
            sticky="w"
        )

        # =====================================================
        # ROWS
        # =====================================================

        for _, row in self.df.iterrows():

            fio_raw = row.get("ФИО")

            if pd.isna(fio_raw):
                continue

            # ФИО из основной таблицы
            # очищаем от спецсимволов
            fio = self.clean_display_fio(fio_raw)

            if not fio:
                continue

            # Нормализованное ФИО для поиска обеда
            normalized_fio = self.normalize_fio(
                fio_raw
            )

            # =================================================
            # СТАРЫЕ НАСТРОЙКИ
            # =================================================

            person_state = saved_state.get(
                fio,
                {}
            )

            # =================================================
            # РАСПИСАНИЕ
            # =================================================

            schedule_value = person_state.get(
                "schedule",
                row.get(date, "")
            )

            if pd.isna(schedule_value):
                schedule_value = ""

            schedule_value = str(
                schedule_value
            ).strip()

            schedule_valid = self.is_schedule_active(
                schedule_value
            )

            # =================================================
            # ОБЕД
            # =================================================

            # Сначала пытаемся взять ранее сохранённый
            # пользователем обед.
            saved_lunch = person_state.get(
                "lunch",
                None
            )

            if saved_lunch is not None:
                lunch_value = (
                    ""
                    if pd.isna(saved_lunch)
                    else str(saved_lunch).strip()
                )

            else:
                # Если ранее ничего не сохраняли,
                # ищем сотрудника в таблице обедов.
                lunch_info = self.lunch_data.get(
                    normalized_fio
                )

                if lunch_info:
                    lunch_value = lunch_info.get(
                        "lunch",
                        ""
                    )
                else:
                    lunch_value = ""

            lunch_value = str(
                lunch_value
            ).strip()

            # =================================================
            # ACTIVE
            # =================================================

            saved_active = person_state.get(
                "active",
                None
            )

            if saved_active is not None:

                is_active = bool(saved_active)

            else:

                # По умолчанию сотрудник активен
                # только если:
                #
                # 1. есть корректное расписание
                # 2. есть обед
                #
                is_active = (
                        schedule_valid
                        and bool(lunch_value)
                )

            # Нельзя сделать активным сотрудника,
            # если нет расписания или обеда.
            if not schedule_valid or not lunch_value:
                is_active = False

            # =================================================
            # ROW
            # =================================================

            frame = ctk.CTkFrame(
                self.table_frame
            )

            frame.pack(
                fill="x",
                pady=1
            )

            frame.grid_columnconfigure(
                0,
                minsize=80
            )

            frame.grid_columnconfigure(
                1,
                weight=1,
                minsize=300
            )

            frame.grid_columnconfigure(
                2,
                weight=1,
                minsize=150
            )

            frame.grid_columnconfigure(
                3,
                weight=1,
                minsize=150
            )

            # =================================================
            # ACTIVE CHECKBOX
            # =================================================

            var = ctk.BooleanVar(
                value=is_active
            )

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

            # Если нет расписания или обеда,
            # чекбокс вообще отключаем.
            if not schedule_valid or not lunch_value:
                cb.configure(
                    state="disabled"
                )

            # =================================================
            # FIO
            # =================================================

            ctk.CTkLabel(
                frame,
                text=fio
            ).grid(
                row=0,
                column=1,
                padx=5,
                sticky="w"
            )

            # =================================================
            # SCHEDULE
            # =================================================

            schedule_entry = ctk.CTkEntry(
                frame
            )

            schedule_entry.insert(
                0,
                schedule_value
            )

            schedule_entry.grid(
                row=0,
                column=2,
                padx=5,
                pady=2,
                sticky="ew"
            )

            self.schedule_entries[fio] = (
                schedule_entry
            )

            # =================================================
            # LUNCH
            # =================================================

            lunch_entry = ctk.CTkEntry(
                frame
            )

            lunch_entry.insert(
                0,
                lunch_value
            )

            lunch_entry.grid(
                row=0,
                column=3,
                padx=5,
                pady=2,
                sticky="ew"
            )

            self.lunch_entries[fio] = (
                lunch_entry
            )

    # =========================================================
    # CLEAN DISPLAY FIO
    # =========================================================
    def clean_display_fio(self, value):

        if value is None or pd.isna(value):
            return ""

        value = unicodedata.normalize(
            "NFKC",
            str(value)
        )

        # Оставляем только буквы и пробелы.
        value = "".join(
            ch
            for ch in value
            if ch.isalpha() or ch.isspace()
        )

        value = value.strip()

        # Убираем двойные/тройные пробелы
        value = re.sub(
            r"\s+",
            " ",
            value
        )

        return value

    # =========================================================
    # SAVE STATE
    # =========================================================
    def save_state(self):

        selected_date = self.date_var.get()

        new_state = {}

        # =====================================================
        # СНАЧАЛА ПРОВЕРЯЕМ ВСЕХ СОТРУДНИКОВ
        # =====================================================

        for fio, var in self.check_vars.items():

            # Если чекбокс не активен — он не может быть
            # установлен пользователем.
            is_active = var.get()

            schedule = self.schedule_entries[
                fio
            ].get().strip()

            lunch = self.lunch_entries[
                fio
            ].get().strip()

            # -------------------------------------------------
            # Проверка: активный сотрудник обязан иметь обед
            # -------------------------------------------------

            if is_active and not lunch:
                from tkinter import messagebox

                messagebox.showerror(
                    "Ошибка",
                    f"Не прописан обед для сотрудника {fio}"
                )

                return

            # -------------------------------------------------
            # Проверка расписания
            # -------------------------------------------------

            if is_active and not self.is_schedule_active(
                    schedule
            ):
                from tkinter import messagebox

                messagebox.showerror(
                    "Ошибка",
                    f"Не указано корректное расписание "
                    f"для сотрудника {fio}"
                )

                return

            new_state[fio] = {
                "active": is_active,
                "schedule": schedule,
                "lunch": lunch
            }

        # =====================================================
        # СОХРАНЕНИЕ
        # =====================================================

        self.config.staff_state[
            selected_date
        ] = new_state

        ConfigManager.save(
            self.config
        )

        self.master.update_dates()

    # =========================================================
    # CSV FIX
    # =========================================================
    def convert_to_csv_url(
            self,
            url: str
    ) -> str:

        match = re.search(
            r"/d/([a-zA-Z0-9-_]+)",
            url
        )

        if not match:
            return url

        sheet_id = match.group(1)

        gid_match = re.search(
            r"gid=(\d+)",
            url
        )

        gid = (
            gid_match.group(1)
            if gid_match
            else "0"
        )

        return (
            f"https://docs.google.com/spreadsheets/d/"
            f"{sheet_id}/export?format=csv&gid={gid}"
        )

    # =========================================================
    # CHECK SCHEDULE
    # =========================================================
    def is_schedule_active(self, value):

        if not value:
            return False

        value = str(value).strip()

        pattern = (
            r"^\d{1,2}:\d{2}\s*-\s*"
            r"\d{1,2}:\d{2}$"
        )

        return bool(
            re.match(
                pattern,
                value
            )
        )