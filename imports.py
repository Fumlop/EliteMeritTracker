from report import Report
from history import PowerPlayHistory
from power import PledgedPower

# Singleton-Config (wird überall importiert, immer gleiches Objekt)
pledgedPower = PledgedPower()
report = Report()
history = PowerPlayHistory()
systems = {}  # leeres Dict
