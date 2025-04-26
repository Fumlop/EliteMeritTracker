from imports import *
from datetime import datetime

class PowerPlayHistory:
    def __init__(self, date=None, merits=0):
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.merits = merits
