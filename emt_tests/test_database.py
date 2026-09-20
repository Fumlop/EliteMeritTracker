"""
Tests for emt_core/database.py - schema, connection handling and backups.
"""
import json
import os
import sqlite3

import pytest

from emt_core import database
from emt_models.system import StarSystem


@pytest.fixture
def db(tmp_path):
    """Path to a database file that does not exist yet."""
    return str(tmp_path / "db" / "merittracker.db")


@pytest.fixture
def fortified():
    """A Fortified system with reinforcement, undermining and decay."""
    system = StarSystem()
    system.from_dict({
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
    })
    return system


class TestSchema:
    def test_creates_the_file_and_every_table(self, db):
        with database.connect(db) as conn:
            tables = {
                row[0] for row in
                conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
        assert os.path.isfile(db)
        assert {"systems", "merit_events", "inventory", "meta"} <= tables

    def test_stamps_the_schema_version(self, db):
        with database.connect(db) as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == database.SCHEMA_VERSION

    def test_turns_on_wal(self, db):
        with database.connect(db) as conn:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"

    def test_reopening_keeps_the_data(self, db, fortified):
        with database.connect(db) as conn:
            database.write_system(conn, database.system_row(fortified))
        with database.connect(db) as conn:
            assert conn.execute("SELECT COUNT(*) FROM systems").fetchone()[0] == 1

    def test_a_newer_schema_warns_but_still_opens(self, db):
        with database.connect(db):
            pass
        with sqlite3.connect(db) as raw:
            raw.execute(f"PRAGMA user_version = {database.SCHEMA_VERSION + 1}")
        # No raise: an older plugin beside a newer file reads what it can.
        with database.connect(db) as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == database.SCHEMA_VERSION + 1


class TestConnect:
    def test_commits_when_the_block_ends(self, db, fortified):
        with database.connect(db) as conn:
            database.write_system(conn, database.system_row(fortified))
        with database.connect(db) as conn:
            assert conn.execute("SELECT name FROM systems").fetchone()[0] == "Eme"

    def test_rolls_back_when_the_block_raises(self, db, fortified):
        with pytest.raises(RuntimeError):
            with database.connect(db) as conn:
                database.write_system(conn, database.system_row(fortified))
                raise RuntimeError("boom")
        with database.connect(db) as conn:
            assert conn.execute("SELECT COUNT(*) FROM systems").fetchone()[0] == 0


class TestSystemRow:
    def test_columns_line_up_with_their_names(self, fortified):
        row = dict(zip(database.SYSTEM_COLUMNS, database.system_row(fortified, "Fumlop")))
        assert row["name"] == "Eme"
        assert row["commander"] == "Fumlop"
        assert row["power"] == "Felicia Winters"
        assert row["state"] == "Fortified"
        assert row["merits"] == 293529
        assert row["reinforcement"] == 132832
        assert row["undermining"] == 24958

    def test_progress_is_a_percentage(self, fortified):
        row = dict(zip(database.SYSTEM_COLUMNS, database.system_row(fortified)))
        assert row["progress"] == pytest.approx(64.0729, abs=0.001)

    def test_data_round_trips_through_from_dict(self, fortified):
        row = dict(zip(database.SYSTEM_COLUMNS, database.system_row(fortified)))
        again = StarSystem()
        again.from_dict(json.loads(row["data"]))
        assert again.StarSystem == fortified.StarSystem
        assert again.Merits == fortified.Merits
        assert again.PowerplayStateReinforcement == fortified.PowerplayStateReinforcement

    def test_real_undermining_is_carried(self, fortified):
        row = dict(zip(database.SYSTEM_COLUMNS, database.system_row(fortified)))
        assert row["real_undermining"] == fortified.RealUndermining


class TestWriteSystem:
    def test_replace_overwrites_the_same_commander(self, db, fortified):
        with database.connect(db) as conn:
            database.write_system(conn, database.system_row(fortified, "Fumlop"))
            fortified.Merits = 400000
            database.write_system(conn, database.system_row(fortified, "Fumlop"))
            rows = conn.execute("SELECT merits FROM systems").fetchall()
        assert rows == [(400000,)]

    def test_no_replace_leaves_the_existing_row(self, db, fortified):
        with database.connect(db) as conn:
            database.write_system(conn, database.system_row(fortified, "Fumlop"))
            fortified.Merits = 400000
            written = database.write_system(
                conn, database.system_row(fortified, "Fumlop"), replace=False
            )
            rows = conn.execute("SELECT merits FROM systems").fetchall()
        assert written is False
        assert rows == [(293529,)]

    def test_two_commanders_keep_their_own_row(self, db, fortified):
        with database.connect(db) as conn:
            database.write_system(conn, database.system_row(fortified, "Fumlop"))
            database.write_system(conn, database.system_row(fortified, "Other"))
            count = conn.execute("SELECT COUNT(*) FROM systems").fetchone()[0]
        assert count == 2


class TestBackup:
    def test_copies_a_database_that_has_rows(self, db, fortified):
        with database.connect(db) as conn:
            database.write_system(conn, database.system_row(fortified))
        copy = database.backup(db)
        assert copy and os.path.isfile(copy)
        with sqlite3.connect(copy) as raw:
            assert raw.execute("SELECT name FROM systems").fetchone()[0] == "Eme"

    def test_refuses_an_empty_database(self, db):
        with database.connect(db):
            pass
        assert database.backup(db) is None

    def test_missing_database_is_not_an_error(self, db):
        assert database.backup(db) is None

    def test_keeps_only_the_newest(self, db, fortified):
        with database.connect(db) as conn:
            database.write_system(conn, database.system_row(fortified))
        for _ in range(3):
            database.backup(db, keep=2)
        folder = os.path.join(os.path.dirname(db), "backups")
        assert len(os.listdir(folder)) == 2

    def test_leaves_no_temp_file_behind(self, db, fortified):
        with database.connect(db) as conn:
            database.write_system(conn, database.system_row(fortified))
        database.backup(db)
        folder = os.path.join(os.path.dirname(db), "backups")
        assert not [name for name in os.listdir(folder) if name.endswith(".tmp")]
