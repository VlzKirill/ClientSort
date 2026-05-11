class AppConfig:
    SСHEDULE_URL = ""
    LUNCH_URL = ""
    EXCEL_FILE = ""

    def __init__(self):
        self.set_defaults()

    def set_defaults(self):
        self.schedule_url = self.SСHEDULE_URL
        self.lunch_url = self.LUNCH_URL
        self.excel_file = self.EXCEL_FILE

        self.staff_state = {}

    def reset_main_settings(self):
        self.schedule_url = self.SСHEDULE_URL
        self.lunch_url = self.LUNCH_URL
        self.excel_file = self.EXCEL_FILE

    def reset_staff_settings(self):
        self.staff_state = {}