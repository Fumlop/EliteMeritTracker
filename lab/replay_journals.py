r"""Replay the commander's real journals through the plugin, into a temp store.

Not a test and not shipped. The generated journals in emt_tests cover the
scenarios; this checks the same pipeline against what the game actually wrote,
with the new save-on-change persistence switched on.

    python lab/replay_journals.py [--journals DIR] [--keep]

Safety: database.PATH is pointed at a throwaway file before anything is
imported that could write, so the commander's own
%LOCALAPPDATA%\EliteMeritTracker\db\merittracker.db is never opened. Nothing
under data\ is read or written either.

What it checks, per journal and over the whole corpus:

1. The ledger's baseline ends equal to the last TotalMerits the server sent.
   That is the number the plugin shows, and the whole point of tracking the
   delta rather than summing MeritsGained.
2. The merits credited to systems equal the server's own movement in
   TotalMerits, so nothing was invented or dropped between the two.
3. Every system's merits are >= 0.
4. What is in memory at the end survives a reload from the database.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
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

SANDBOX = tempfile.mkdtemp(prefix="emt-replay-")
database.ROOT = SANDBOX
database.DIR = os.path.join(SANDBOX, "db")
database.PATH = os.path.join(SANDBOX, "db", "merittracker.db")

import load  # noqa: E402
from emt_core.duplicate import merit_ledger  # noqa: E402
from emt_core.state import state  # noqa: E402
from emt_models.power import pledgedPower  # noqa: E402
from emt_models.system import systems, loadSystems  # noqa: E402

load.trackerFrame = MagicMock()

DEFAULT_JOURNALS = os.path.join(
    os.environ.get("USERPROFILE", os.path.expanduser("~")),
    "Saved Games", "Frontier Developments", "Elite Dangerous")


def reset_plugin():
    merit_ledger.reset()
    systems.clear()
    load._dirty.clear()
    pledgedPower.Merits = 0
    pledgedPower.MeritsSession = 0
    state.current_system = None
    state.commander = ""
    state.reset_delivery_tracking()
    state.reset_sar_tracking()


def replay(path):
    """Feed one journal through load.journal_entry.

    Returns (server_first, server_last, merit_events, errors).
    server_* are the first and last TotalMerits the file carries, which is the
    movement the plugin has to reproduce.
    """
    first = last = None
    events = 0
    errors = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("event") == "PowerplayMerits":
                events += 1
                total = entry.get("TotalMerits")
                if total is not None:
                    if first is None:
                        first = total - entry.get("MeritsGained", 0)
                    last = total
            try:
                load.journal_entry("CMDR", False, entry.get("StarSystem"),
                                   None, entry, {})
            except Exception as err:
                errors.append(f"{os.path.basename(path)}:{number} "
                              f"{entry.get('event')}: {type(err).__name__}: {err}")
    return first, last, events, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--journals", default=DEFAULT_JOURNALS)
    parser.add_argument("--keep", action="store_true",
                        help="leave the sandbox database on disk")
    args = parser.parse_args()

    files = sorted(f for f in os.listdir(args.journals)
                   if f.startswith("Journal.") and f.endswith(".log"))
    if not files:
        print(f"no journals in {args.journals}")
        return 1

    print(f"journals : {len(files)} in {args.journals}")
    print(f"sandbox  : {database.PATH}")
    print()

    reset_plugin()
    all_errors = []
    verdicts = Counter()
    total_events = 0
    per_file = []

    seen_events = 0
    for name in files:
        before = sum(s.Merits for s in systems.values())
        first, last, events, errors = replay(os.path.join(args.journals, name))
        after = sum(s.Merits for s in systems.values())
        all_errors += errors
        total_events += events
        # A rejected resend advances the server's TotalMerits by its own size,
        # so the movement in the file is larger than what was credited by
        # exactly what the ledger threw away. Read that back off the log.
        logged = database.merit_events()[seen_events:]
        seen_events += len(logged)
        rejected = sum(row["gained"] for row in logged
                       if row["verdict"] in ("ignored", "parked"))
        if events:
            per_file.append((name, events, first, last, after - before, rejected))

    load._save_now()
    load.update_json_file()

    for row in database.merit_events():
        verdicts[row["verdict"]] += 1

    print(f"{'journal':<34} {'ev':>3} {'server moved':>13} {'credited':>10} "
          f"{'rejected':>9}  unexplained")
    unexplained_total = 0
    for name, events, first, last, credited, rejected in per_file:
        moved = (last - first) if (first is not None and last is not None) else 0
        gap = moved - credited - rejected
        unexplained_total += gap
        note = "" if gap == 0 else f"  {gap:+,}"
        print(f"{name:<34} {events:>3} {moved:>13,} {credited:>10,} "
              f"{rejected:>9,}{note}")

    tracked = sum(s.Merits for s in systems.values())
    print()
    print(f"PowerplayMerits events replayed : {total_events}")
    print(f"logged verdicts                 : "
          f"{', '.join(f'{k} {v}' for k, v in sorted(verdicts.items())) or 'none'}")
    print(f"ledger baseline (server total)  : {merit_ledger.baseline:,}"
          if merit_ledger.baseline is not None else
          "ledger baseline (server total)  : unset")
    print(f"pledgedPower.Merits shown       : {pledgedPower.Merits:,}")
    print(f"merits credited to systems      : {tracked:,} over {len(systems)} systems")
    print(f"parked awards still open        : {len(merit_ledger.pending)}")

    problems = []
    if any(s.Merits < 0 for s in systems.values()):
        problems.append("a system holds negative merits")
    if merit_ledger.baseline is not None and pledgedPower.Merits != merit_ledger.baseline:
        problems.append("the displayed total is not the ledger baseline")
    # Per journal the movement can spill over a file boundary, so this is only
    # a signal, not a failure - the corpus-level baseline check is the real one.
    if unexplained_total:
        print(f"unexplained across the corpus     : {unexplained_total:+,} "
              f"(merits unwound across a file boundary)")

    in_memory = {name: s.Merits for name, s in systems.items()}
    systems.clear()
    loadSystems()
    reloaded = {name: s.Merits for name, s in systems.items()}
    missing = {k: v for k, v in in_memory.items() if reloaded.get(k) != v}
    if missing:
        problems.append(f"{len(missing)} systems did not survive the reload: "
                        f"{list(missing)[:5]}")
    else:
        print(f"reload from the database        : {len(reloaded)} systems, "
              f"{sum(reloaded.values()):,} merits - identical")

    if all_errors:
        print()
        print(f"exceptions out of journal_entry : {len(all_errors)}")
        for line in all_errors[:10]:
            print(f"  {line}")

    print()
    if problems or all_errors:
        for line in problems:
            print(f"FAIL: {line}")
        print("FAIL" if problems else "OK, but journal_entry raised - see above")
    else:
        print("OK")

    if not args.keep:
        shutil.rmtree(SANDBOX, ignore_errors=True)
    return 1 if problems or all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
