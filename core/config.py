class AppConfig:
    SCHEDULE_URL = ""
    LUNCH_URL = ""
    EXCEL_FILE = ""

    def __init__(self):
        self.set_defaults()

    def set_defaults(self):
        self.schedule_url = self.SCHEDULE_URL
        self.lunch_url = self.LUNCH_URL
        self.excel_file = self.EXCEL_FILE

        # временные данные, не сохраняются на диск
        self.staff_state = {}
        self.clients_data = []

    def reset_main_settings(self):
        self.schedule_url = self.SCHEDULE_URL
        self.lunch_url = self.LUNCH_URL
        self.excel_file = self.EXCEL_FILE

    def reset_staff_settings(self):
        self.staff_state = {}