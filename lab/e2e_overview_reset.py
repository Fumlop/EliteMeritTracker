r"""Overview Reset / Reset all, end to end, into a throwaway database.

Premise and failure list: lab/e2e_overview_reset.md.

    python lab/e2e_overview_reset.py

Prints one PASS/FAIL line per check and exits 1 on any FAIL. The commander's
own database is never opened: database.PATH is pointed at a temp file before
anything that could write is imported, as lab/replay_journals.py does.
"""
import os
import sys
import tempfile
from unittest.mock import MagicMock

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)

import emt_tests.mocks  # noqa: E402,F401  the EDMC and tkinter stubs

sys.modules.setdefault("requests", MagicMock())
import tkinter as _tk  # noqa: E402
for _name in ("ttk", "filedialog", "messagebox", "font", "simpledialog"):
    setattr(_tk, _name, MagicMock())
    sys.modules.setdefault("tkinter." + _name, getattr(_tk, _name))

from emt_core import database  # noqa: E402

SANDBOX = tempfile.mkdtemp(prefix="emt-reset-")
database.ROOT = SANDBOX
database.DIR = os.path.join(SANDBOX, "db")
database.PATH = os.path.join(SANDBOX, "db", "merittracker.db")

from emt_core.duplicate import merit_ledger  # noqa: E402
from emt_models.power import pledgedPower  # noqa: E402
from emt_models.system import StarSystem, systems, dumpSystems, loadSystems  # noqa: E402
from emt_ui import details  # noqa: E402

failures = 0


def check(label, ok, got):
    global failures
    print(f"{'PASS' if ok else 'FAIL'}  {label}  (got {got})")
    failures += 0 if ok else 1


def seed():
    """Three systems holding merits, credited in the ledger, written to disk."""
    systems.clear()
    merit_ledger.reset()
    merit_ledger.baseline = 5000
    merit_ledger.power = "Felicia Winters"
    merit_ledger.pending = [[400, 5400, "Sol"]]
    for name, merits in (("Eme", 1200), ("Sol", 800), ("HIP 44291", 300)):
        system = StarSystem()
        system.StarSystem = name
        system.Merits = merits
        systems[name] = system
        merit_ledger.record(name, merits)
    dumpSystems()
    database.save_meta("ledger", merit_ledger.export_state())
    pledgedPower.MeritsSession = 2300


def reload():
    """What a restart after an EDMC kill would see: memory dropped, disk read."""
    systems.clear()
    loadSystems()
    return {name: data.Merits for name, data in systems.items()}


LEDGER = {"baseline": 5000, "power": "Felicia Winters", "pending": [[400, 5400, "Sol"]]}


def saved_ledger():
    """The ledger a restart would import: baseline, power, parked awards. The
    per-system credits are RAM only by design (MeritLedger.export_state)."""
    return database.load_meta("ledger", {})


print("sandbox  : " + os.path.join("%TEMP%", os.path.relpath(database.PATH, tempfile.gettempdir())))

# 1. Reset one system.
seed()
details._reset("Eme")
after = reload()
check("reset: the system is 0 after a reload", after.get("Eme") == 0, after.get("Eme"))
check("reset: the other systems keep their merits",
      after.get("Sol") == 800 and after.get("HIP 44291") == 300, after)
check("reset: the saved ledger keeps baseline and parked awards",
      saved_ledger() == LEDGER, saved_ledger())
check("reset: session merits untouched", pledgedPower.MeritsSession == 2300,
      pledgedPower.MeritsSession)
check("reset: status says reset", details._state["status"] == "Reset Eme",
      details._state["status"])

# 2. Reset all, the confirmation answered yes.
seed()
details.messagebox.askyesno = lambda *a, **k: True
details._reset_all()
after = reload()
check("reset all: every system is 0 after a reload",
      after and all(v == 0 for v in after.values()), after)
check("reset all: the rows are kept, not deleted", len(after) == 3, len(after))
check("reset all: the saved ledger keeps baseline and parked awards",
      saved_ledger() == LEDGER, saved_ledger())
check("reset all: session merits untouched", pledgedPower.MeritsSession == 2300,
      pledgedPower.MeritsSession)

# 3. Reset all, the confirmation answered no: nothing moves.
seed()
details.messagebox.askyesno = lambda *a, **k: False
details._reset_all()
after = reload()
check("reset all declined: merits unchanged on disk",
      after == {"Eme": 1200, "Sol": 800, "HIP 44291": 300}, after)

# 4. The write fails: the status line must say so.
seed()
real_save = database.save_progress
database.save_progress = lambda rows, ledger_state, db=None: False
details._reset("Sol")
status = details._state["status"]
check("failed write: reset reports the failure", "failed" in status, status)
seed()
details.messagebox.askyesno = lambda *a, **k: True
details._reset_all()
status = details._state["status"]
check("failed write: reset all reports the failure", "failed" in status, status)
database.save_progress = real_save

print(f"{'FAIL' if failures else 'PASS'}  {failures} check(s) failed")
sys.exit(1 if failures else 0)
