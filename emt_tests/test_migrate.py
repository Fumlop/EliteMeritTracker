"""
Tests for emt_core/migrate.py - the one-time JSON to SQLite import.
"""
import json
import os
import sqlite3

import pytest

from emt_core import database, migrate

SYSTEMS = {
    "Eme": {
        "StarSystem": "Eme",
        "Merits": 293529,
        "Active": False,
        "PowerplayState": "Fortified",
        "ControllingPower": "Felicia Winters",
        "Powers": ["Felicia Winters", "Jerome Archer"],
        "PowerplayStateControlProgress": 0.640729,
        "PowerplayStateReinforcement": 132832,
        "PowerplayStateUndermining": 24958,
        "reported": False,
    },
    "Scorpii Sector MC-V a2-3": {
        "StarSystem": "Scorpii Sector MC-V a2-3",
        "Merits": 2632,
        "Active": False,
        "PowerplayState": "Stronghold",
        "ControllingPower": "Aisling Duval",
        "Powers": ["Aisling Duval"],
        "PowerplayStateControlProgress": 0.0698,
        "PowerplayStateReinforcement": 0,
        "PowerplayStateUndermining": 0,
        "reported": False,
    },
}

POWER = {
    "Power": "Felicia Winters",
    "Commander": "Fumlop",
    "Merits": 9044583,
    "MeritsSession": 10,
    "Rank": "1133",
    "TimePledged": 59525785,
    "TimePledgedStr": "1y 323d 22h",
}

BACKPACK = {
    "umbag": {"powerresearch": {"Eme": 4, "Cerno": 2}},
    "reinfbag": {},
    "acqbag": {"powermedical": {"Eme": 7}},
}

SALVAGE = {
    "Psi-5 Aurigae": {
        "system_name": "Psi-5 Aurigae",
        "inventory": {
            "wreckagecomponents": {"name": "wreckagecomponents", "count": 11},
            "usscargoblackbox": {"name": "usscargoblackbox", "count": 5},
        },
    },
    "Cerno": {
        "system_name": "Cerno",
        "inventory": {"wreckagecomponents": {"name": "wreckagecomponents", "count": 1}},
    },
}


@pytest.fixture
def db(tmp_path):
    return str(tmp_path / "db" / "merittracker.db")


@pytest.fixture
def source(tmp_path):
    """A data/ folder holding all four files."""
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "systems.json").write_text(json.dumps(SYSTEMS), encoding="utf-8")
    (folder / "power.json").write_text(json.dumps(POWER), encoding="utf-8")
    (folder / "backpack.json").write_text(json.dumps(BACKPACK), encoding="utf-8")
    (folder / "salvage.json").write_text(json.dumps(SALVAGE), encoding="utf-8")
    return str(folder)


def rows(db, sql, *args):
    with sqlite3.connect(db) as conn:
        return conn.execute(sql, args).fetchall()


class TestFirstRun:
    def test_imports_every_system(self, source, db):
        result = migrate.run(source, db)
        assert result["imported"]["systems"] == 2
        names = {row[0] for row in rows(db, "SELECT name FROM systems")}
        assert names == set(SYSTEMS)

    def test_systems_carry_the_commander_from_power_json(self, source, db):
        migrate.run(source, db)
        assert rows(db, "SELECT DISTINCT commander FROM systems") == [("Fumlop",)]

    def test_the_commander_is_pinned_so_the_next_start_finds_the_rows(self, source, db):
        # The imported rows are keyed by power.json's Commander, so
        # database.commander() has to resolve to it at the next start.
        migrate.run(source, db)
        assert database.load_meta("commander", None, db) == "Fumlop"

    def test_power_lands_in_meta(self, source, db):
        migrate.run(source, db)
        stored = rows(db, "SELECT value FROM meta WHERE key = 'power'")[0][0]
        assert json.loads(stored) == POWER

    def test_backpack_becomes_one_row_per_item_and_system(self, source, db):
        migrate.run(source, db)
        found = rows(
            db,
            "SELECT kind, item, system, count FROM inventory "
            "WHERE kind IN ('umbag', 'acqbag') ORDER BY kind, system",
        )
        assert found == [
            ("acqbag", "powermedical", "Eme", 7),
            ("umbag", "powerresearch", "Cerno", 2),
            ("umbag", "powerresearch", "Eme", 4),
        ]

    def test_salvage_becomes_inventory_rows(self, source, db):
        migrate.run(source, db)
        found = rows(
            db,
            "SELECT item, system, count FROM inventory WHERE kind = 'salvage' "
            "ORDER BY system, item",
        )
        assert found == [
            ("wreckagecomponents", "Cerno", 1),
            ("usscargoblackbox", "Psi-5 Aurigae", 5),
            ("wreckagecomponents", "Psi-5 Aurigae", 11),
        ]

    def test_writes_the_marker(self, source, db):
        migrate.run(source, db)
        marker = migrate.done_path(db)
        assert os.path.isfile(marker)
        assert "systems: 2 imported" in open(marker, encoding="utf-8").read()

    def test_leaves_the_json_where_it_is(self, source, db):
        migrate.run(source, db)
        assert sorted(os.listdir(source)) == [
            "backpack.json", "power.json", "salvage.json", "systems.json"
        ]


class TestSecondRun:
    def test_returns_none_and_changes_nothing(self, source, db):
        migrate.run(source, db)
        before = rows(db, "SELECT COUNT(*) FROM systems")
        assert migrate.run(source, db) is None
        assert rows(db, "SELECT COUNT(*) FROM systems") == before

    def test_a_deleted_marker_does_not_import_twice(self, source, db):
        migrate.run(source, db)
        os.remove(migrate.done_path(db))
        # The meta row survives, so the import is not repeated - the marker is
        # written again from it.
        assert migrate.run(source, db) is None
        assert rows(db, "SELECT COUNT(*) FROM systems") == [(2,)]
        assert os.path.isfile(migrate.done_path(db))

    def test_a_row_deleted_by_hand_stays_deleted(self, source, db):
        migrate.run(source, db)
        with sqlite3.connect(db) as conn:
            conn.execute("DELETE FROM systems WHERE name = 'Eme'")
        os.remove(migrate.done_path(db))
        migrate.run(source, db)
        names = {row[0] for row in rows(db, "SELECT name FROM systems")}
        assert "Eme" not in names


class TestBadInput:
    def test_unparseable_file_is_skipped_and_the_rest_imported(self, source, db):
        with open(os.path.join(source, "salvage.json"), "w", encoding="utf-8") as handle:
            handle.write("{not json")
        result = migrate.run(source, db)
        assert result["imported"]["systems"] == 2
        assert any("salvage.json" in path for path, _ in result["failed"])

    def test_a_bad_system_does_not_stop_the_others(self, source, db):
        broken = dict(SYSTEMS)
        broken["Bad"] = ["not", "an", "object"]
        with open(os.path.join(source, "systems.json"), "w", encoding="utf-8") as handle:
            json.dump(broken, handle)
        result = migrate.run(source, db)
        assert result["imported"]["systems"] == 2
        assert result["failed"]

    def test_missing_files_are_not_a_failure(self, tmp_path, db):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = migrate.run(str(empty), db)
        assert result["failed"] == []
        assert result["imported"]["systems"] == 0
        assert os.path.isfile(migrate.done_path(db))

    def test_a_missing_commander_becomes_empty_string(self, source, db):
        no_cmdr = dict(POWER)
        no_cmdr.pop("Commander")
        with open(os.path.join(source, "power.json"), "w", encoding="utf-8") as handle:
            json.dump(no_cmdr, handle)
        migrate.run(source, db)
        assert rows(db, "SELECT DISTINCT commander FROM systems") == [("",)]


class TestImportedValues:
    def test_progress_is_stored_as_a_percentage(self, source, db):
        migrate.run(source, db)
        found = rows(db, "SELECT progress FROM systems WHERE name = 'Eme'")
        assert found[0][0] == pytest.approx(64.0729, abs=0.001)

    def test_data_holds_the_whole_record(self, source, db):
        migrate.run(source, db)
        stored = rows(db, "SELECT data FROM systems WHERE name = 'Eme'")[0][0]
        entry = json.loads(stored)
        assert entry["StarSystem"] == "Eme"
        assert entry["PowerplayStateReinforcement"] == 132832

    def test_state_matches_getSystemStateText(self, source, db):
        migrate.run(source, db)
        found = dict(rows(db, "SELECT name, state FROM systems"))
        assert found["Eme"] == "Fortified"
        assert found["Scorpii Sector MC-V a2-3"] == "Stronghold"


def test_schema_is_created_by_the_import(source, db):
    migrate.run(source, db)
    with sqlite3.connect(db) as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version == database.SCHEMA_VERSION
