# main_table.py
import pandas as pd
import customtkinter as ctk
from datetime import datetime, timedelta
import random

class MainTable:
    def __init__(self, config, date):
        self.config = config
        self.date = date

        self.table_frame = None
        self.scrollable_frame = None

