# E2E: Overview Reset persists

Script: `lab/e2e_overview_reset.py`. Output kept in `lab/e2e_overview_reset.out.txt`.

## Premise

The Overview's Reset and Reset all used to zero merits in memory only. The
database kept the old value until EDMC closed cleanly, so a crash or kill
brought the merits back. Only the main panel's dustbin saved.

Done means: after an Overview reset, a restart that reads only the database
sees the reset - and nothing else moved.

## How it could fail

1. The reset system's row is not written: it comes back with its merits.
2. Too much is written: other systems lose merits, or rows are deleted.
3. The ledger written with the rows is wrong: the baseline or a parked award
   is lost, so the next event after a restart is judged against nothing. (The
   per-system credits that `forget()` banks are RAM only by design -
   `MeritLedger.export_state` - so a restart cannot be asked about them.)
4. Session merits (`pledgedPower.MeritsSession`) change - the user chose to
   leave them alone.
5. Reset all declined at the confirmation still writes.
6. The database write fails and the window still says "Reset X" (checked for
   Reset and Reset all).

Each is one check in the script. A restart is simulated by clearing the
in-memory `systems` and calling the plugin's own `loadSystems()` against the
sandbox database. No widget is drawn: `details._draw` returns early without a
window, which is what keeps this runnable without a display.
