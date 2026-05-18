# clients_window.py
import pandas as pd
import customtkinter as ctk
from core.config_manager import ConfigManager
import re


class ClientsWindow(ctk.CTkToplevel):
    def __init__(self, parent, config):
        super().__init__(parent)

        self.parent = parent
        self.config = config

        self.title("Клиенты")
        self.geometry("1100x600")

        # Делаем окно поверх главного
        self.transient(parent)

        self.df = None
        self.check_vars = {}
        self.column_widths = []

        self.create_ui()
        self.load_clients()

    # ---------------- UI ----------------
    def create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # заголовок
        self.title_label = ctk.CTkLabel(self, text="Список клиентов")
        self.title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        # таблица
        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # ---------------- BOTTOM FRAME ----------------
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=20,
            pady=20
        )
        self.bottom_frame.grid_columnconfigure(0, weight=1)

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
            command=self.apply_changes
        )
        self.apply_btn.pack(side="left", padx=(0, 10))

        # ---------------- EXIT BUTTON ----------------
        self.exit_btn = ctk.CTkButton(
            self.right_buttons,
            text="Выход",
            command=self.destroy
        )
        self.exit_btn.pack(side="left", padx=(0, 10))

    # ---------------- LOAD CLIENTS ----------------
    def load_clients(self):
        try:
            df = pd.read_excel(self.config.excel_file, engine='openpyxl')
            cols = [c for c in df.columns if c in ["Время", "Гражданин", "Цель взаимодействия", "Куда назначено"]]
            self.df = df[cols]

            # чистим "Куда назначено" — оставляем только ФИО в скобках
            def extract_name(cell):
                if pd.isna(cell):
                    return ""
                m = re.search(r"\((.*?)\)", str(cell))
                return m.group(1) if m else str(cell)
            if "Куда назначено" in self.df.columns:
                self.df["Куда назначено"] = self.df["Куда назначено"].apply(extract_name)

            # Время оставляем только часы и минуты
            if "Время" in self.df.columns:
                def time_only(val):
                    if pd.isna(val):
                        return ""
                    try:
                        return pd.to_datetime(val).strftime("%H:%M")
                    except:
                        return str(val)
                self.df["Время"] = self.df["Время"].apply(time_only)

            self.compute_column_widths()
            self.render_table()

        except Exception as e:
            print("Ошибка загрузки Excel:", e)
            self.df = pd.DataFrame(columns=["Не менять", "Время", "Гражданин", "Цель взаимодействия", "Куда назначено"])

    # ---------------- COMPUTE COLUMN WIDTHS ----------------
    def compute_column_widths(self):
        # фиксируем ширину каждой колонки как max длина значения + заголовок
        headers = ["Не менять"] + list(self.df.columns)
        self.column_widths = []

        for i, col in enumerate(headers):
            max_len = len(col)
            if i > 0:
                for val in self.df.iloc[:, i - 1]:
                    if pd.notna(val):
                        max_len = max(max_len, len(str(val)))
            self.column_widths.append(max_len * 10)  # масштабируем для пикселей

    # ---------------- RENDER TABLE ----------------
    def render_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        saved_clients = getattr(self.config, "clients_data", [])

        # ---------------- HEADER ----------------
        header = ctk.CTkFrame(self.table_frame)
        header.pack(fill="x", pady=2)

        for i, text in enumerate(["Не менять", "Время", "Гражданин", "Цель взаимодействия", "Куда назначено"]):
            header.grid_columnconfigure(i, minsize=self.column_widths[i])
            ctk.CTkLabel(header, text=text, width=self.column_widths[i], anchor="w").grid(row=0, column=i, padx=5, sticky="w")

        # ---------------- ROWS ----------------
        for idx, row in self.df.iterrows():
            frame = ctk.CTkFrame(self.table_frame)
            frame.pack(fill="x", pady=1)

            # применяем те же ширины колонок, что и в header
            for i in range(5):
                frame.grid_columnconfigure(i, minsize=self.column_widths[i])

            # проверяем, есть ли сохранённые данные
            keep_default = False
            if saved_clients and idx < len(saved_clients):
                keep_default = saved_clients[idx].get("keep", False)

            var = ctk.BooleanVar(value=keep_default)
            self.check_vars[idx] = var

            cb = ctk.CTkCheckBox(frame, variable=var, text="", width=50)
            cb.grid(row=0, column=0, padx=5, sticky="w")

            ctk.CTkLabel(frame, text=row.get("Время", ""), width=self.column_widths[1], anchor="w").grid(row=0, column=1, padx=5, sticky="w")
            ctk.CTkLabel(frame, text=row.get("Гражданин", ""), width=self.column_widths[2], anchor="w").grid(row=0, column=2, padx=5, sticky="w")
            ctk.CTkLabel(frame, text=row.get("Цель взаимодействия", ""), width=self.column_widths[3], anchor="w").grid(row=0, column=3, padx=5, sticky="w")
            ctk.CTkLabel(frame, text=row.get("Куда назначено", ""), width=self.column_widths[4], anchor="w").grid(row=0, column=4, padx=5, sticky="w")

    # ---------------- APPLY CHANGES ----------------
    def apply_changes(self):
        clients_data = []
        for idx, row in self.df.iterrows():
            clients_data.append({
                "keep": self.check_vars[idx].get(),
                "time": row.get("Время", ""),
                "citizen": row.get("Гражданин", ""),
                "service": row.get("Цель взаимодействия", ""),
                "assigned": row.get("Куда назначено", "")
            })
        self.config.clients_data = clients_data
        ConfigManager.save(self.config)