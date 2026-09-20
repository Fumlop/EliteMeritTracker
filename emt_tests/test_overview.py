"""
Tests for emt_ui/details.py - the Overview window's filtering, sorting and the
report text. Nothing here builds a widget; the drawing needs a display.
"""
import pytest

from emt_core.config import configPlugin
from emt_models.system import StarSystem, systems
from emt_ui import details

EME = {
    "StarSystem": "Eme",
    "Merits": 293529,
    "PowerplayState": "Fortified",
    "ControllingPower": "Felicia Winters",
    "Powers": ["Felicia Winters", "Jerome Archer"],
    "PowerplayStateControlProgress": 0.640729,
    "PowerplayStateReinforcement": 132832,
    "PowerplayStateUndermining": 24958,
}
SCORPII = {
    "StarSystem": "Scorpii Sector MC-V a2-3",
    "Merits": 2632,
    "PowerplayState": "Stronghold",
    "ControllingPower": "Aisling Duval",
    "Powers": ["Aisling Duval"],
    "PowerplayStateControlProgress": 0.0698,
}
HIP = {
    "StarSystem": "HIP 44291",
    "Merits": 183892,
    "PowerplayState": "Fortified",
    "ControllingPower": "Felicia Winters",
    "Powers": ["Felicia Winters"],
    "PowerplayStateControlProgress": 0.3912,
    "PowerplayStateReinforcement": 88404,
    "PowerplayStateUndermining": 700,
}


def make(entry):
    system = StarSystem()
    system.from_dict(entry)
    return system


@pytest.fixture(autouse=True)
def three_systems():
    """Three systems in the global dict, and a clean _state, per test."""
    saved_systems = dict(systems)
    saved_state = dict(details._state)
    saved_template = configPlugin.copyText.get()

    systems.clear()
    for entry in (EME, SCORPII, HIP):
        systems[entry["StarSystem"]] = make(entry)
    details._state.update({
        "tab": "Session", "folded_open": set(), "sort": "name",
        "reverse": False, "search": "", "power": "All powers",
        "state": "All states", "status": "",
    })

    yield

    systems.clear()
    systems.update(saved_systems)
    details._state.clear()
    details._state.update(saved_state)
    configPlugin.copyText._value = saved_template


def names():
    return [name for name, _ in details._shown_systems()]


class TestFilters:
    def test_no_filter_shows_everything(self):
        assert len(names()) == 3

    def test_search_is_case_insensitive_and_partial(self):
        details._state["search"] = "hip"
        assert names() == ["HIP 44291"]

    def test_search_that_matches_nothing(self):
        details._state["search"] = "zzz"
        assert names() == []

    def test_power_filter(self):
        details._state["power"] = "Aisling Duval"
        assert names() == ["Scorpii Sector MC-V a2-3"]

    def test_state_filter(self):
        details._state["state"] = "Fortified"
        assert sorted(names()) == ["Eme", "HIP 44291"]

    def test_filters_combine(self):
        details._state["power"] = "Felicia Winters"
        details._state["search"] = "eme"
        assert names() == ["Eme"]


class TestSorting:
    def test_by_name(self):
        details._state["sort"] = "name"
        assert names() == ["Eme", "HIP 44291", "Scorpii Sector MC-V a2-3"]

    def test_by_merits_descending(self):
        details._state["sort"] = "merits"
        details._state["reverse"] = True
        assert names() == ["Eme", "HIP 44291", "Scorpii Sector MC-V a2-3"]

    def test_by_progress(self):
        details._state["sort"] = "progress"
        assert names() == ["Scorpii Sector MC-V a2-3", "HIP 44291", "Eme"]

    def test_by_reinforcement(self):
        details._state["sort"] = "reinforcement"
        assert names()[0] == "Scorpii Sector MC-V a2-3"

    def test_every_column_key_sorts(self):
        for key, _label, _width, _anchor in details.COLUMNS:
            details._state["sort"] = key
            assert len(names()) == 3

    def test_pick_sort_toggles_direction(self, monkeypatch):
        monkeypatch.setattr(details, "_draw", lambda: None)
        details._state["sort"] = "merits"
        details._state["reverse"] = False
        details._pick_sort("merits")
        assert details._state["reverse"] is True
        details._pick_sort("merits")
        assert details._state["reverse"] is False

    def test_pick_sort_on_a_new_column_starts_ascending(self, monkeypatch):
        monkeypatch.setattr(details, "_draw", lambda: None)
        details._state["sort"] = "merits"
        details._state["reverse"] = True
        details._pick_sort("name")
        assert details._state["sort"] == "name"
        assert details._state["reverse"] is False


class TestFolding:
    def test_toggle_opens_then_closes(self, monkeypatch):
        monkeypatch.setattr(details, "_draw", lambda: None)
        details._toggle_fold("Eme")
        assert "Eme" in details._state["folded_open"]
        details._toggle_fold("Eme")
        assert "Eme" not in details._state["folded_open"]

    def test_collapse_all(self, monkeypatch):
        monkeypatch.setattr(details, "_draw", lambda: None)
        details._state["folded_open"] = {"Eme", "HIP 44291"}
        details._collapse_all()
        assert details._state["folded_open"] == set()


class TestReportText:
    def test_the_default_template(self):
        text = details._report_text("Eme", systems["Eme"])
        assert text == ("@Leadership earned 293529 merits in Eme, "
                        "Felicia Winters 132832, Opposition 0")

    def test_system_status_is_replaced_before_system(self):
        # @System is a prefix of @SystemStatus: replacing it first leaves
        # "Status" behind.
        configPlugin.copyText._value = "@System @SystemStatus"
        assert details._report_text("Eme", systems["Eme"]) == "Eme Fort"

    def test_acquisition_uses_the_conflict_progress(self):
        system = make({
            "StarSystem": "Contested",
            "Merits": 10,
            "PowerplayState": "Unoccupied",
            "Powers": ["Felicia Winters", "Jerome Archer"],
            "PowerplayConflictProgress": [
                {"Power": "Felicia Winters", "ConflictProgress": 0.55},
                {"Power": "Jerome Archer", "ConflictProgress": 0.31},
            ],
        })
        configPlugin.copyText._value = "@CPControlling / @CPOpposition"
        text = details._report_text("Contested", system)
        assert "Felicia Winters 55.00%" in text
        assert "Jerome Archer 31.00%" in text

    def test_a_template_without_variables_is_untouched(self):
        configPlugin.copyText._value = "plain text"
        assert details._report_text("Eme", systems["Eme"]) == "plain text"


class TestSummary:
    def test_holds_state_power_and_progress(self):
        line = details._summary(systems["Eme"])
        assert "Fortified" in line
        assert "Felicia Winters" in line
        assert "64.07 %" in line

    def test_carries_the_net_line_when_there_is_one(self):
        assert "Reinf: 132,832" in details._summary(systems["Eme"])

    def test_a_quiet_system_has_no_net_line(self):
        assert "Reinf" not in details._summary(systems["Scorpii Sector MC-V a2-3"])


class TestWindowState:
    def test_three_tabs(self):
        assert details.TABS == ("Session", "Systems", "Shiplocker")

    def test_is_open_is_false_without_a_window(self):
        assert details.is_open() is False

    def test_pick_tab(self, monkeypatch):
        monkeypatch.setattr(details, "_draw", lambda: None)
        details._pick_tab("Systems")
        assert details._state["tab"] == "Systems"
        assert details._state["status"] == ""

    def test_the_window_is_never_wider_than_the_cap(self):
        assert details.SCREEN_SHARE < details.MAX_SHARE <= 1.0
