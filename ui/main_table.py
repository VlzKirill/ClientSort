import pandas as pd
import customtkinter as ctk

class MainTable:
    def __init__(self, config, date):
        self.config = config
        self.date = date
        self.df = None
        self.assigned = []
        self.load_clients_data()

    def load_clients_data(self):
        """
        Загружаем данные клиентов из настроек.
        Пропускаем первый столбец "Не менять".
        """
        if not hasattr(self.config, "clients_data") or not self.config.clients_data:
            print("Нет сохранённых клиентов")
            self.df = pd.DataFrame(columns=["Время", "Гражданин", "Цель"])
            return

        # Определяем данные со второго столбца
        processed_data = []
        for row in self.config.clients_data:
            # если строка это словарь, берём значения по ключам
            if isinstance(row, dict):
                # пропускаем первый ключ
                values = list(row.values())[1:4]  # берём 2,3,4
            else:
                # если список/кортеж
                values = row[1:4]
            processed_data.append(values)

        self.df = pd.DataFrame(processed_data, columns=["Время", "Гражданин", "Цель"])

    def show_table(self, parent):
        table_frame = ctk.CTkScrollableFrame(parent)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        headers = ["Время", "Гражданин", "Цель", "Кому назначено"]
        self.column_widths = []

        for i, col in enumerate(headers):
            max_len = len(col)
            if i < 3 and not self.df.empty:
                for val in self.df.iloc[:, i]:
                    if pd.notna(val):
                        max_len = max(max_len, len(str(val)))
            self.column_widths.append(max_len)

        header_row = ctk.CTkFrame(table_frame)
        header_row.pack(fill="x", pady=(0, 2))
        for i, col in enumerate(headers):
            lbl = ctk.CTkLabel(
                header_row,
                text=col,
                width=self.column_widths[i] * 10,
                anchor="w",
                font=("Arial", 14, "bold")
            )
            lbl.grid(row=0, column=i, padx=5, pady=5, sticky="w")

        if self.df.empty:
            return

        # Четвёртый столбец пока пустой
        self.assigned = [""] * len(self.df)

        for idx, row in self.df.iterrows():
            row_frame = ctk.CTkFrame(table_frame)
            row_frame.pack(fill="x", pady=1)
            for i in range(4):
                if i < 3:
                    val = row.iloc[i]
                    text = str(val) if pd.notna(val) else ""
                else:
                    text = self.assigned[idx]
                lbl = ctk.CTkLabel(
                    row_frame,
                    text=text,
                    width=self.column_widths[i] * 10,
                    anchor="w",
                    font=("Arial", 13)
                )
                lbl.grid(row=0, column=i, padx=5, pady=2, sticky="w")