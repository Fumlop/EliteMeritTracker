r"""The JSON files of 0.4 and before, read into the database once.

    data\systems.json    -> systems
    data\power.json      -> meta['power']
    data\backpack.json   -> inventory, kind 'umbag' / 'reinfbag' / 'acqbag'
    data\salvage.json    -> inventory, kind 'salvage'

Run at every start. The first run imports everything it can read and writes
db\migrate.done; every run after that sees the marker and returns before
opening a single file.

Nothing is deleted or moved: data\*.json stays where it is. That is the
rollback - remove the db folder, downgrade, the JSON is still there.

A file that cannot be read is logged, listed in migrate.done, and does not stop
the rest. Only a database that cannot be written leaves no migrate.done, and
the next start tries the whole import again.

A row already in the database wins over its file (INSERT OR IGNORE), so a
second run after a failed one never duplicates or overwrites.

No tkinter. Tests in emt_tests/test_migrate.py.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone

from emt_core import database
from emt_core.logging import logger
from emt_core.storage import get_data_dir

DONE = "migrate.done"

KINDS = ("systems", "power", "inventory")

# A value SQLite will not store - a list where a number goes, a missing system
# name. It skips that file. Anything else, a disk error, fails the import.
BAD_VALUE = (sqlite3.InterfaceError, sqlite3.ProgrammingError,
             sqlite3.IntegrityError, OverflowError, TypeError, ValueError,
             AttributeError, KeyError)


def done_path(db=None):
    """Path of the marker file, beside the database."""
    return os.path.join(os.path.dirname(db or database.PATH), DONE)


def run(source=None, db=None):
    """Import the JSON under `source` into `db`.

    Args:
        source: Folder holding the JSON files. Defaults to the plugin's data/.
        db: Database file. Defaults to database.PATH.

    Returns:
        {"imported": {...}, "kept": {...}, "failed": [(path, reason), ...]},
        or None when migrate.done is already there and nothing was done.
    """
    marker = done_path(db)
    if os.path.exists(marker):
        return None
    source = source or get_data_dir()
    result = {
        "imported": {kind: 0 for kind in KINDS},
        "kept": {kind: 0 for kind in KINDS},
        "failed": [],
    }
    with database.connect(db) as conn:
        # The report is kept in the database too, committed with the import: a
        # migrate.done that failed to write after the commit is written again
        # from here, instead of a second import bringing deleted rows back.
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (DONE,)).fetchone()
        if row is None:
            # Explicit, so the per-file savepoints nest inside one transaction
            # rather than each committing on release.
            conn.execute("BEGIN")
            commander = _power(conn, source, result)
            _systems(conn, source, result, commander)
            _backpack(conn, source, result, commander)
            _salvage(conn, source, result, commander)
            when = datetime.now(timezone.utc).isoformat(timespec="seconds")
            lines = [f"migrated {when} from {source}"]
            lines += [
                f"{kind}: {count} imported, {result['kept'][kind]} already in the database"
                for kind, count in result["imported"].items()
            ]
            lines += [f"skipped {path}: {reason}" for path, reason in result["failed"]]
            report = "\n".join(lines) + "\n"
            conn.execute("INSERT INTO meta (key, value) VALUES (?, ?)", (DONE, report))
    if row is not None:
        _write_marker(marker, row[0])
        return None
    _write_marker(marker, report)
    for path, reason in result["failed"]:
        logger.warning(f"migrate: skipped {path}: {reason}")
    logger.info("migrate: " + "; ".join(lines[1:1 + len(KINDS)]))
    return result


def _write_marker(path, text):
    """Write the marker through a temp file, so a half-written one never reads
    as a finished import."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(temp, path)


def _read(source, name, result):
    """Parse one JSON file.

    Returns:
        The parsed object, or None when the file is missing or unreadable. An
        unreadable file is recorded in result["failed"].
    """
    path = os.path.join(source, name)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as err:
        result["failed"].append((path, str(err)))
        return None


def _count(result, kind, inserted):
    result["imported" if inserted else "kept"][kind] += 1


def _one_file(conn, result, path, work):
    """Run `work` inside a savepoint.

    A bad value rolls that file back and is recorded; the transaction around it
    stays usable for the files after it.
    """
    conn.execute("SAVEPOINT f")
    try:
        work()
    except BAD_VALUE as err:
        conn.execute("ROLLBACK TO f")
        result["failed"].append((path, str(err)))
    finally:
        conn.execute("RELEASE f")


def _power(conn, source, result):
    """power.json -> meta['power']. Returns the commander name, or ''.

    Read first: every other table is keyed by commander, and power.json is the
    only file that holds it.
    """
    path = os.path.join(source, "power.json")
    data = _read(source, "power.json", result)
    if not isinstance(data, dict):
        return ""
    commander = str(data.get("Commander", "") or "")

    def work():
        cursor = conn.execute(
            "INSERT OR IGNORE INTO meta (key, value) VALUES (?, ?)",
            ("power", json.dumps(data)),
        )
        _count(result, "power", cursor.rowcount)
        # The rows below are keyed by this name, and database.commander() has
        # to resolve to it at the next start or the import reads back empty.
        # Committed with the import, not after it.
        if commander:
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                         ("commander", json.dumps(commander)))

    _one_file(conn, result, path, work)
    return commander


def _systems(conn, source, result, commander):
    r"""systems.json -> systems.

    Each entry is rehydrated through StarSystem.from_dict() and turned into a
    row by database.system_row(), the same call the runtime writer uses, so a
    migrated row and a fresh one cannot disagree on a computed column.
    """
    from emt_models.system import StarSystem       # emt_models imports emt_core

    path = os.path.join(source, "systems.json")
    data = _read(source, "systems.json", result)
    if not isinstance(data, dict):
        return
    for name, entry in data.items():
        if not isinstance(entry, dict):
            result["failed"].append((path, f"{name}: not an object"))
            continue

        def work(name=name, entry=entry):
            system = StarSystem()
            system.from_dict(entry)
            # from_dict takes StarSystem out of the entry; a file written by a
            # version that keyed on the dict only would have no name in it.
            if not entry.get("StarSystem"):
                system.StarSystem = name
            row = database.system_row(system, commander)
            _count(result, "systems", database.write_system(conn, row, replace=False))

        _one_file(conn, result, path, work)


def _backpack(conn, source, result, commander):
    """backpack.json -> inventory, one row per (bag, item, system).

    Bag.items is {item: {system: count}} (emt_models/backpack.py:13).
    """
    path = os.path.join(source, "backpack.json")
    data = _read(source, "backpack.json", result)
    if not isinstance(data, dict):
        return
    for kind in database.BAG_KINDS:
        bag = data.get(kind)
        if not isinstance(bag, dict):
            continue
        for item, systems in bag.items():
            if not isinstance(systems, dict):
                result["failed"].append((path, f"{kind}/{item}: not an object"))
                continue
            for system, count in systems.items():
                _insert_item(conn, result, path, kind, commander, item, system, count)


def _salvage(conn, source, result, commander):
    """salvage.json -> inventory, kind 'salvage'.

    The file is {system: {"system_name": ..., "inventory": {item: {"name", "count"}}}}
    (emt_models/salvage.py:67).
    """
    path = os.path.join(source, "salvage.json")
    data = _read(source, "salvage.json", result)
    if not isinstance(data, dict):
        return
    for system, entry in data.items():
        if not isinstance(entry, dict):
            result["failed"].append((path, f"{system}: not an object"))
            continue
        inventory = entry.get("inventory")
        if not isinstance(inventory, dict):
            continue
        for item, cargo in inventory.items():
            count = cargo.get("count") if isinstance(cargo, dict) else cargo
            _insert_item(conn, result, path, database.SALVAGE_KIND,
                         commander, item, system, count)


def _insert_item(conn, result, path, kind, commander, item, system, count):
    def work():
        cursor = conn.execute(
            "INSERT OR IGNORE INTO inventory "
            "(kind, commander, item, system, count) VALUES (?, ?, ?, ?, ?)",
            (kind, commander, item, system, int(count)),
        )
        _count(result, "inventory", cursor.rowcount)

    _one_file(conn, result, f"{path} [{kind}/{item}/{system}]", work)
