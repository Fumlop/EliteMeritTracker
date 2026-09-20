r"""SQLite store for systems, merit events and inventory.

    %LOCALAPPDATA%\EliteMeritTracker\db\merittracker.db

Outside the plugin folder. The updater skips data/ (load.py:251), but a manual
reinstall - delete the folder, unzip the release - does not, and merit history
is the one thing that cannot be re-earned.

A connection per piece of work, opened and closed around it. The journal
callback, the update check and the UI all write, so no connection is ever
shared between threads.

Each row keeps indexed columns for querying plus the whole record as JSON in
`data`, so a record comes back exactly as it went in and StarSystem.from_dict()
keeps working unchanged.

No tkinter and no emt_models import: emt_models writes through this module, so
importing it here would be a cycle. Tests in emt_tests/test_database.py.
"""
import contextlib
import json
import os
import sqlite3
from datetime import datetime, timezone

from emt_core.logging import logger

ROOT = os.path.join(
    os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
    "EliteMeritTracker",
)
DIR = os.path.join(ROOT, "db")
PATH = os.path.join(DIR, "merittracker.db")

# PRAGMA user_version. Every table is CREATE ... IF NOT EXISTS, so an older
# file is upgraded by running the schema again.
SCHEMA_VERSION = 1
TIMEOUT_S = 5.0
BACKUPS_KEPT = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS systems (
    name TEXT NOT NULL,
    commander TEXT NOT NULL DEFAULT '',
    power TEXT,
    state TEXT,
    merits INTEGER NOT NULL DEFAULT 0,
    progress REAL,
    reinforcement INTEGER,
    undermining INTEGER,
    real_undermining INTEGER,
    active INTEGER NOT NULL DEFAULT 0,
    reported INTEGER NOT NULL DEFAULT 0,
    updated TEXT,
    data TEXT NOT NULL,
    PRIMARY KEY (name, commander));
CREATE INDEX IF NOT EXISTS systems_power ON systems (power);

CREATE TABLE IF NOT EXISTS merit_events (
    id INTEGER PRIMARY KEY,
    stamp TEXT NOT NULL,
    commander TEXT NOT NULL DEFAULT '',
    power TEXT NOT NULL,
    total INTEGER NOT NULL,
    gained INTEGER NOT NULL,
    delta INTEGER NOT NULL,
    system TEXT,
    verdict TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS merit_events_stamp ON merit_events (stamp);

CREATE TABLE IF NOT EXISTS inventory (
    kind TEXT NOT NULL,
    commander TEXT NOT NULL DEFAULT '',
    item TEXT NOT NULL,
    system TEXT NOT NULL,
    count INTEGER NOT NULL,
    PRIMARY KEY (kind, commander, item, system));

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT);
"""

# inventory.kind. The three backpack bags keep their attribute names from
# emt_models/backpack.py; salvage is emt_models/salvage.py.
BAG_KINDS = ("umbag", "reinfbag", "acqbag")
SALVAGE_KIND = "salvage"


@contextlib.contextmanager
def connect(path=None):
    """Open a connection for one piece of work.

    Committed when the block ends, rolled back when it raises, closed either
    way. The schema is created or upgraded on the way in.

    Args:
        path: Database file. Defaults to PATH.

    Yields:
        sqlite3.Connection
    """
    path = path or PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path, timeout=TIMEOUT_S)
    try:
        _prepare(conn, path)
        with conn:
            yield conn
    finally:
        conn.close()


def _prepare(conn, path):
    """Create or upgrade the schema. Runs outside the caller's transaction,
    because PRAGMA journal_mode cannot be set inside one."""
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version < SCHEMA_VERSION:
        if version == 0:
            conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    elif version > SCHEMA_VERSION:
        logger.warning(
            f"{path} is schema {version}, this plugin knows {SCHEMA_VERSION}"
        )


SYSTEM_COLUMNS = ("name", "commander", "power", "state", "merits", "progress",
                  "reinforcement", "undermining", "real_undermining", "active",
                  "reported", "updated", "data")


def system_row(system, commander=""):
    """Build the systems row for a StarSystem.

    The one place a StarSystem becomes columns, so a migrated row and a row
    written at runtime cannot disagree. Duck-typed rather than annotated:
    emt_models imports emt_core, so importing StarSystem here would be a cycle.

    `progress` is getSystemProgressNumber() - a percentage, and for an
    acquisition system it comes from the conflict progress rather than from
    PowerplayStateControlProgress.

    Args:
        system: A StarSystem.
        commander: Commander name. '' when unknown.

    Returns:
        tuple in SYSTEM_COLUMNS order.
    """
    return (
        system.StarSystem,
        commander,
        system.ControllingPower,
        system.getSystemStateText(),
        int(system.Merits),
        float(system.getSystemProgressNumber()),
        int(system.PowerplayStateReinforcement),
        int(system.PowerplayStateUndermining),
        int(getattr(system, "RealUndermining", system.PowerplayStateUndermining)),
        int(bool(system.Active)),
        int(bool(system.reported)),
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        json.dumps(system.to_dict()),
    )


def write_system(conn, row, replace=True):
    """Write one systems row.

    Args:
        conn: Connection from connect().
        row: Tuple from system_row().
        replace: True overwrites an existing (name, commander).
                 False leaves it alone, which is what an import wants.

    Returns:
        True if the row was written.
    """
    verb = "INSERT OR REPLACE" if replace else "INSERT OR IGNORE"
    columns = ", ".join(SYSTEM_COLUMNS)
    marks = ", ".join("?" * len(SYSTEM_COLUMNS))
    cursor = conn.execute(f"{verb} INTO systems ({columns}) VALUES ({marks})", row)
    return bool(cursor.rowcount)


# ----------------------------------------------------------- what the models use
#
# Each call opens and closes its own connection. Every read answers [] or None
# when the database cannot be read: a store that is not there has to leave the
# plugin running on an empty model rather than stop it loading.


def save_systems(rows, commander="", db=None):
    """Write every systems row in one transaction, and drop the rows for this
    commander that are no longer in `rows`.

    The JSON store rewrote the whole file, so a system dropped from the
    in-memory dict left the store too - that is what made the main panel's
    Reset stick. Without the delete a reset system is read back at the next
    start with its old merits.

    An empty `rows` is a no-op rather than a mass delete: a failed load leaves
    the model empty, and the next autosave must not turn that into data loss.

    Args:
        rows: Tuples from system_row(), all for the same commander.
        commander: The commander the rows belong to.
        db: Database file. Defaults to PATH.

    Returns:
        True if the write went through.
    """
    if not rows:
        return True
    try:
        names = [row[0] for row in rows]
        marks = ", ".join("?" * len(names))
        with connect(db) as conn:
            conn.execute(
                f"DELETE FROM systems WHERE commander = ? AND name NOT IN ({marks})",
                [commander] + names,
            )
            for row in rows:
                write_system(conn, row)
        return True
    except (sqlite3.Error, OSError) as err:
        logger.error(f"could not save systems: {err}")
        return False


def load_systems(commander="", db=None):
    """The stored records for one commander, newest column values included.

    Returns:
        [dict, ...] - each the to_dict() that went in. [] on any failure.
    """
    try:
        with connect(db) as conn:
            rows = conn.execute(
                "SELECT data FROM systems WHERE commander = ? ORDER BY rowid",
                (commander,),
            ).fetchall()
        return [json.loads(data) for (data,) in rows]
    except (sqlite3.Error, OSError, ValueError) as err:
        logger.error(f"could not read systems: {err}")
        return []


def save_inventory(kind, commander, rows, db=None):
    """Replace one kind of inventory for one commander.

    Args:
        kind: One of BAG_KINDS or SALVAGE_KIND.
        commander: Commander name, '' when unknown.
        rows: [(item, system, count), ...]. A count of 0 or less is dropped.
        db: Database file.

    Returns:
        True if the write went through.
    """
    try:
        with connect(db) as conn:
            conn.execute("DELETE FROM inventory WHERE kind = ? AND commander = ?",
                         (kind, commander))
            conn.executemany(
                "INSERT OR REPLACE INTO inventory "
                "(kind, commander, item, system, count) VALUES (?, ?, ?, ?, ?)",
                [(kind, commander, item, system, int(count))
                 for item, system, count in rows if int(count) > 0],
            )
        return True
    except (sqlite3.Error, OSError, TypeError, ValueError) as err:
        logger.error(f"could not save {kind}: {err}")
        return False


def load_inventory(kind, commander="", db=None):
    """[(item, system, count), ...] for one kind.

    Returns None - not [] - when the read failed, so a caller can tell a real
    empty bag from a database that would not open. The caller must not clear
    what it has on None: save_inventory() replaces, so an emptied model would
    delete the stored rows at the next save.
    """
    try:
        with connect(db) as conn:
            return [tuple(row) for row in conn.execute(
                "SELECT item, system, count FROM inventory "
                "WHERE kind = ? AND commander = ? ORDER BY item, system",
                (kind, commander),
            )]
    except (sqlite3.Error, OSError) as err:
        logger.error(f"could not read {kind}: {err}")
        return None


MERIT_EVENT_COLUMNS = ("stamp", "commander", "power", "total", "gained",
                       "delta", "system", "verdict")


def record_merit_event(stamp, commander, power, total, gained, delta,
                       system, verdict, db=None):
    """Append one PowerplayMerits decision to the log.

    Every award the ledger sees, and what it did with it. The resend threshold
    in emt_core/duplicate.py was tuned on 5 journals / 84 events; this is what
    lets it be re-checked against a real season's worth.

    Args:
        stamp: The journal timestamp, as written.
        commander: Commander name, '' when unknown.
        power: The pledged power the award was for.
        total: TotalMerits as the server reported it.
        gained: MeritsGained as the server reported it.
        delta: What the ledger actually credited.
        system: Where it was credited, or None.
        verdict: 'credited', 'parked', 'restored', 'unwound' or 'ignored'.

    Returns:
        True if the row was written.
    """
    marks = ", ".join("?" * len(MERIT_EVENT_COLUMNS))
    columns = ", ".join(MERIT_EVENT_COLUMNS)
    try:
        with connect(db) as conn:
            conn.execute(f"INSERT INTO merit_events ({columns}) VALUES ({marks})",
                         (str(stamp or ""), commander, power or "", int(total or 0),
                          int(gained or 0), int(delta or 0), system, verdict))
        return True
    except (sqlite3.Error, OSError, TypeError, ValueError) as err:
        # A lost log line must never cost the award it describes.
        logger.warning(f"could not log the merit event: {err}")
        return False


def merit_events(limit=None, commander=None, db=None):
    """The logged events, newest last. [dict, ...], or [] on any failure."""
    where, args = "", []
    if commander is not None:
        where, args = "WHERE commander = ? ", [commander]
    tail = ""
    if limit:
        # Newest `limit`, still handed back oldest first.
        tail = f"ORDER BY id DESC LIMIT {int(limit)}"
    try:
        with connect(db) as conn:
            rows = conn.execute(
                f"SELECT id, {', '.join(MERIT_EVENT_COLUMNS)} FROM merit_events "
                f"{where}{tail or 'ORDER BY id'}", args).fetchall()
        events = [dict(zip(("id",) + MERIT_EVENT_COLUMNS, row)) for row in rows]
        return events[::-1] if tail else events
    except (sqlite3.Error, OSError) as err:
        logger.error(f"could not read the merit log: {err}")
        return []


def save_progress(rows, ledger_state, db=None):
    """Write the systems an event changed, and the ledger, in one transaction.

    The incremental counterpart of save_systems(): no DELETE, because this
    carries only what just changed. Replacing the whole set belongs to
    plugin_stop and to a reset, which are the only places a system disappears.

    The ledger travels with the rows because it has to. It holds the baseline
    and the awards parked as suspected resends, and both are needed to decide
    the next event - a crash that kept the merits but lost the ledger would
    give the parked awards back twice or not at all.

    Args:
        rows: Tuples from system_row(), only the changed ones.
        ledger_state: MeritLedger.export_state(), or None to leave it alone.
        db: Database file.

    Returns:
        True if the write went through.
    """
    if not rows and ledger_state is None:
        return True
    try:
        with connect(db) as conn:
            for row in rows:
                write_system(conn, row)
            if ledger_state is not None:
                conn.execute(
                    "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                    ("ledger", json.dumps(ledger_state)))
        return True
    except (sqlite3.Error, OSError, TypeError, ValueError) as err:
        logger.error(f"could not save progress: {err}")
        return False


def save_meta(key, value, db=None):
    """Store one JSON-serialisable value under `key`. True if it was stored."""
    try:
        with connect(db) as conn:
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                         (key, json.dumps(value)))
        return True
    except (sqlite3.Error, OSError, TypeError, ValueError) as err:
        logger.error(f"could not save meta {key}: {err}")
        return False


def load_meta(key, default=None, db=None):
    """The value stored under `key`, or `default`."""
    try:
        with connect(db) as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else default
    except (sqlite3.Error, OSError, ValueError) as err:
        logger.error(f"could not read meta {key}: {err}")
        return default


def commander(db=None):
    """The commander every load and save is keyed by.

    The live journal name when there is one, otherwise the last one stored -
    plugin_start3 loads before any journal line arrives, so without the stored
    name a restart would read an empty database.
    """
    try:
        from emt_core.state import state
        if state.commander:
            return str(state.commander)
    except ImportError:
        pass
    return load_meta("commander", "", db) or ""


def remember_commander(name, db=None):
    """Store the commander name, so the next start loads the same rows."""
    if name:
        save_meta("commander", str(name), db)


# The commander the models in memory were last read under. None until something
# has been read. load.py compares it with commander() when LoadGame names the
# pilot, and reloads when they differ - without that the models keep one
# commander's data and the next save writes it under another's name.
_loaded = None


def loaded_commander():
    return _loaded


def mark_loaded(name):
    global _loaded
    _loaded = name


def adopt(name, db=None):
    r"""Give the rows saved before the commander was known to `name`.

    Rows land under '' whenever the pilot is not named yet: everything the
    migration imports from a `power.json` with no Commander, and anything
    saved between plugin_start3 and LoadGame. Left there they would be
    stranded the moment the real name arrived.

    Only adopts when `name` owns nothing yet, so a second commander never
    takes the first one's rows.

    Returns:
        True if any row was moved.
    """
    if not name:
        return False
    try:
        with connect(db) as conn:
            held = sum(
                conn.execute(f"SELECT COUNT(*) FROM {table} WHERE commander = ?",
                             (name,)).fetchone()[0]
                for table in ("systems", "inventory")
            )
            if held:
                return False
            moved = sum(
                conn.execute(f"UPDATE {table} SET commander = ? WHERE commander = ''",
                             (name,)).rowcount
                for table in ("systems", "inventory")
            )
            if moved:
                conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                             ("commander", json.dumps(str(name))))
                logger.info(f"adopted {moved} unowned rows for {name}")
        return bool(moved)
    except (sqlite3.Error, OSError) as err:
        logger.error(f"could not adopt rows for {name}: {err}")
        return False


def backup(path=None, keep=BACKUPS_KEPT):
    r"""Copy the database into db\backups\, keeping the newest `keep`.

    Through a temp file, and only when the copy is worth keeping: an emptied or
    corrupt database backed up twice would leave nothing to go back to.

    Args:
        path: Database file. Defaults to PATH.
        keep: How many backups to keep.

    Returns:
        Path of the copy, or None if nothing was copied.
    """
    path = path or PATH
    if not os.path.isfile(path):
        return None
    folder = os.path.join(os.path.dirname(path), "backups")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    target = os.path.join(folder, f"merittracker-{stamp}.db")
    try:
        os.makedirs(folder, exist_ok=True)
        with contextlib.closing(sqlite3.connect(path, timeout=TIMEOUT_S)) as source, \
                contextlib.closing(sqlite3.connect(target + ".tmp")) as copy:
            check = source.execute("PRAGMA quick_check").fetchone()[0]
            rows = sum(
                source.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("systems", "merit_events", "inventory")
            )
            if check != "ok" or not rows:
                raise sqlite3.DatabaseError(
                    f"not backed up: quick_check {check}, {rows} rows"
                )
            source.backup(copy)
        os.replace(target + ".tmp", target)
    except (sqlite3.Error, OSError) as err:
        logger.warning(f"could not back up {path}: {err}")
        with contextlib.suppress(OSError):
            os.remove(target + ".tmp")
        return None
    copies = sorted(
        name for name in os.listdir(folder)
        if name.startswith("merittracker-") and name.endswith(".db")
    )
    for name in copies[:-keep]:
        try:
            os.remove(os.path.join(folder, name))
        except OSError as err:
            logger.warning(f"could not remove old backup {name}: {err}")
    return target
