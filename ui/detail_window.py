import customtkinter as ctk


class DetailWindow(ctk.CTkToplevel):

    def __init__(self, parent, df):
        super().__init__(parent)

        self.title("Детальная таблица")
        self.geometry("1100x650")
        self.transient(parent)

        self.df = df
        self.column_widths = []

        self.create_ui()
        self.build_table()

    # =========================================================
    def create_ui(self):
        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # =========================================================
    def build_table(self):

        headers = ["Время", "Гражданин", "Цель", "Кому назначено"]

        # =====================================================
        # ВЫЧИСЛЕНИЕ ШИРИН (как в MainTable)
        # =====================================================
        self.column_widths = []

        for i, col in enumerate(headers):

            max_len = len(col)

            for _, row in self.df.iterrows():

                if i == 0:
                    value = str(row["Время"])
                elif i == 1:
                    value = str(row["Гражданин"])
                elif i == 2:
                    value = str(row["Цель"])
                else:
                    value = str(row["Кому назначено"])

                max_len = max(max_len, len(value))

            # небольшой минимум, чтобы не схлопывалось
            self.column_widths.append(max(max_len, 12))

        # =====================================================
        # HEADER
        # =====================================================
        header = ctk.CTkFrame(self.table_frame)
        header.pack(fill="x", pady=(0, 2))

        for i, col in enumerate(headers):

            ctk.CTkLabel(
                header,
                text=col,
                font=("Arial", 14, "bold"),
                width=self.column_widths[i] * 10,
                anchor="w"
            ).grid(
                row=0,
                column=i,
                padx=5,
                pady=5,
                sticky="w"
            )

        # =====================================================
        # ROWS
        # =====================================================
        for _, row in self.df.iterrows():

            row_frame = ctk.CTkFrame(self.table_frame)
            row_frame.pack(fill="x", pady=1)

            values = [
                str(row["Время"]),
                str(row["Гражданин"]),
                str(row["Цель"]),
                str(row["Кому назначено"])
            ]

            for i, value in enumerate(values):

                ctk.CTkLabel(
                    row_frame,
                    text=value,
                    font=("Arial", 13),
                    width=self.column_widths[i] * 10,
                    anchor="w"
                ).grid(
                    row=0,
                    column=i,
                    padx=5,
                    pady=2,
                    sticky="w"
                )