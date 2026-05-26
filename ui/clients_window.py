# clients_window.py
import pandas as pd
import customtkinter as ctk
from core.config_manager import ConfigManager
import re


class ClientsWindow(ctk.CTkToplevel):
    TIME_SRC_COL = "Назначенная дата и время"
    TIME_COL = "Время"

    BASE_COLS = [
        TIME_SRC_COL,
        "Гражданин",
        "Цель взаимодействия",
        "Куда назначено",
    ]

    def __init__(self, parent, config):
        super().__init__(parent)

        self.parent = parent
        self.config = config

        self.title("Клиенты")
        self.geometry("1100x600")
        self.transient(parent)

        self.df = pd.DataFrame()
        self.check_vars = {}
        self.column_widths = []

        self._build_ui()
        self.load_clients()

    # ---------------- UI ----------------
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Список клиентов").grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 5)
        )

        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        bottom.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(bottom, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            right,
            text="Применить",
            command=self.apply_changes
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            right,
            text="Выход",
            command=self.destroy
        ).pack(side="left")

    # ---------------- LOAD ----------------
    def load_clients(self):
        try:
            df = pd.read_excel(self.config.excel_file, engine="openpyxl")

            # оставляем только нужные колонки
            cols = [c for c in self.BASE_COLS if c in df.columns]
            df = df[cols].copy()

            # ---- приводим "Куда назначено" ----
            if "Куда назначено" in df.columns:
                df["Куда назначено"] = df["Куда назначено"].apply(self._extract_name)

            # ---- нормализуем время ----
            if self.TIME_SRC_COL in df.columns:
                df[self.TIME_SRC_COL] = df[self.TIME_SRC_COL].apply(self._to_time)

                df.rename(columns={self.TIME_SRC_COL: self.TIME_COL}, inplace=True)

            self.df = df

            self._compute_column_widths()
            self._render_table()

        except Exception as e:
            print("Ошибка загрузки Excel:", e)
            self.df = pd.DataFrame(columns=[self.TIME_COL, "Гражданин", "Цель взаимодействия", "Куда назначено"])

    # ---------------- HELPERS ----------------
    def _extract_name(self, cell):
        if pd.isna(cell):
            return ""
        match = re.search(r"\((.*?)\)", str(cell))
        return match.group(1) if match else str(cell)

    def _to_time(self, val):
        if pd.isna(val):
            return ""
        try:
            return pd.to_datetime(val, dayfirst=True, errors="coerce").strftime("%H:%M")
        except Exception:
            return str(val)

    # ---------------- WIDTHS ----------------
    def _compute_column_widths(self):
        headers = ["Не менять"] + list(self.df.columns)
        widths = []

        for i, col in enumerate(headers):
            max_len = len(col)

            if i > 0:
                for v in self.df.iloc[:, i - 1]:
                    max_len = max(max_len, len(str(v)))

            widths.append(max_len * 10)

        self.column_widths = widths

    # ---------------- RENDER ----------------
    def _render_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        saved = getattr(self.config, "clients_data", [])

        # header
        header = ctk.CTkFrame(self.table_frame)
        header.pack(fill="x", pady=2)

        headers = ["Не менять"] + list(self.df.columns)

        for i, text in enumerate(headers):
            header.grid_columnconfigure(i, minsize=self.column_widths[i])
            ctk.CTkLabel(
                header,
                text=text,
                width=self.column_widths[i],
                anchor="w"
            ).grid(row=0, column=i, padx=5, sticky="w")

        # rows
        self.check_vars.clear()

        for idx, row in self.df.iterrows():
            frame = ctk.CTkFrame(self.table_frame)
            frame.pack(fill="x", pady=1)

            for i in range(len(headers)):
                frame.grid_columnconfigure(i, minsize=self.column_widths[i])

            keep = False
            if saved and idx < len(saved):
                keep = saved[idx].get("keep", False)

            var = ctk.BooleanVar(value=keep)
            self.check_vars[idx] = var

            ctk.CTkCheckBox(frame, variable=var, text="").grid(
                row=0, column=0, padx=5, sticky="w"
            )

            values = [
                row.get(self.TIME_COL, ""),
                row.get("Гражданин", ""),
                row.get("Цель взаимодействия", ""),
                row.get("Куда назначено", ""),
            ]

            for i, val in enumerate(values, start=1):
                ctk.CTkLabel(
                    frame,
                    text=val,
                    width=self.column_widths[i],
                    anchor="w"
                ).grid(row=0, column=i, padx=5, sticky="w")

    # ---------------- APPLY ----------------
    def apply_changes(self):
        clients_data = []

        for idx, row in self.df.iterrows():
            clients_data.append({
                "keep": self.check_vars[idx].get(),
                "time": row.get(self.TIME_COL, ""),
                "citizen": row.get("Гражданин", ""),
                "service": row.get("Цель взаимодействия", ""),
                "assigned": row.get("Куда назначено", "")
            })

        self.config.clients_data = clients_data
        ConfigManager.save(self.config)