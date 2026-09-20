"""The Overview window: what merits are where, and what to do with them.

Three tabs in one window:

    Session     - the systems holding merits, with Copy and Reset per system
    Systems     - every tracked system as a table; a row folds open in place
    Shiplocker  - the three Powerplay bags and the salvage hold

One Toplevel. Every draw throws the widgets away and builds them again, so
there is one code path for every click rather than a partial-update matrix per
action. What a draw must not throw away is the selection, the folds, the sort
and how far each list had been scrolled - all of that lives in _state, outside
the widgets.

Colours come from emt_ui/palette.py: the EDMC theme for the window, the eight
fixed tags for how a system is doing.
"""
import csv
import tkinter as tk
from tkinter import ttk, filedialog

from emt_core.config import configPlugin
from emt_core.duplicate import merit_ledger
from emt_core.logging import logger
from emt_core.report import report
from emt_models.power import pledgedPower
from emt_models.system import systems
from emt_ui.palette import TAGS, get_theme_colors, row_tag

FONT = "Segoe UI"

# Seven tenths of the screen, never past eight, and centred. A share rather
# than a stored geometry: a size saved on a 3840x2160 monitor opens off-screen
# on a laptop, and the tabs are fixed-width inside so there is nothing to
# measure off the content.
SCREEN_SHARE = 0.7
MAX_SHARE = 0.8
MIN_WIDTH = 900
MIN_HEIGHT = 560

TABS = ("Session", "Systems", "Shiplocker")

# The Systems table, in pixels: key, heading, width, anchor.
COLUMNS = (
    ("name", "System", 240, "w"),
    ("state", "State", 100, "w"),
    ("progress", "Progress", 92, "e"),
    ("power", "Power", 140, "w"),
    ("reinforcement", "Reinf", 112, "e"),
    ("real_undermining", "Real UM", 112, "e"),
    ("merits", "Merits", 120, "e"),
)

_window = None
_tracker_frame = None
_canvases = {}           # the scrolling canvases of the draw on screen
_scroll = {}             # how far each of them had been scrolled, by name

# What the window is showing. Kept out of the widgets: a draw destroys them.
_state = {
    "tab": "Session",
    "folded_open": set(),   # system names showing their detail in the table
    "sort": "progress",
    "reverse": False,
    "search": "",
    "power": "All powers",
    "state": "All states",
    "status": "",
}


def is_open():
    return _window is not None and bool(_window.winfo_exists())


def show_power_info(parent, pp=None, sy=None, tracker_frame=None):
    """Open the Overview window, or raise the one already open.

    Args:
        parent: The EDMC frame the window hangs off.
        pp: Unused. Kept because load.py and emt_ui/main.py pass it.
        sy: Unused, as above.
        tracker_frame: The TrackerFrame to refresh after a reset.
    """
    global _window, _tracker_frame

    if tracker_frame is not None:
        _tracker_frame = tracker_frame

    if is_open():
        _state["status"] = ""
        _draw()
        _raise()
        return _window

    _window = tk.Toplevel(parent)
    _window.title("EliteMeritTracker - Overview")
    _window.configure(background=get_theme_colors()['bg'])
    _window.bind("<Destroy>", _log_destroy, add="+")
    _window.bind("<Escape>", lambda event: _window.destroy())
    _size(_window)

    _state["folded_open"] = set()
    _state["status"] = ""
    _scroll.clear()
    _draw()
    _raise()
    return _window


def _raise():
    """Bring the window up over whatever is in front.

    lift() alone loses the race: a process without the foreground cannot take
    it. Topmost wins it, and is dropped the moment the window has the focus -
    every second it keeps the flag after that is a second it shadows whatever
    is clicked next.
    """
    if not is_open():
        return
    if _window.state() == "iconic":
        _window.deiconify()
    _window.attributes("-topmost", True)
    _window.bind("<FocusIn>", _drop_topmost, add="+")
    _window.lift()
    _window.focus_force()


def _drop_topmost(event):
    if not is_open():
        return
    if event.widget.winfo_toplevel() is not _window:
        return
    _window.attributes("-topmost", False)
    _window.unbind("<FocusIn>")


def _size(window):
    """Seven tenths of the screen, capped at eight, centred, with a floor.

    The cap is what keeps MIN_WIDTH from opening a window wider than the
    screen on a small display.
    """
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    width = min(max(MIN_WIDTH, int(screen_width * SCREEN_SHARE)),
                int(screen_width * MAX_SHARE))
    height = min(max(MIN_HEIGHT, int(screen_height * SCREEN_SHARE)),
                 int(screen_height * MAX_SHARE))
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)
    logger.debug(f"overview: {width}x{height}+{x}+{y}, "
                 f"{SCREEN_SHARE:.0%} of {screen_width}x{screen_height}")
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.minsize(min(MIN_WIDTH, width), min(MIN_HEIGHT, height))


def _log_destroy(event):
    if _window is not None and event.widget is _window:
        logger.debug("overview: the window was destroyed")


def _clear(window):
    for child in window.winfo_children():
        child.destroy()


# ---------------------------------------------------------------- the drawing


def _draw():
    """Build the tab bar and the active tab into the empty window."""
    if not is_open():
        return
    colors = get_theme_colors()
    _remember_scroll()
    _clear(_window)
    _window.configure(background=colors['bg'])

    _tab_bar(_window, colors)

    body = tk.Frame(_window, background=colors['bg'])
    body.pack(side="top", fill="both", expand=True)

    if _state["tab"] == "Session":
        _session_tab(body, colors)
    elif _state["tab"] == "Systems":
        _systems_tab(body, colors)
    else:
        _shiplocker_tab(body, colors)

    _footer(_window, colors)


def _tab_bar(parent, colors):
    bar = tk.Frame(parent, background=colors['bg'],
                   highlightbackground=colors['button_bg'], highlightthickness=1)
    bar.pack(side="top", fill="x")
    for name in TABS:
        active = name == _state["tab"]
        button = tk.Label(
            bar, text=name, font=(FONT, 10, "bold" if active else "normal"),
            background=colors['bg'],
            foreground=colors['fg'] if active else colors['muted'],
            padx=18, pady=7, cursor="hand2",
        )
        button.pack(side="left")
        if active:
            underline = tk.Frame(bar, background=colors['highlight'], height=2)
            underline.place(in_=button, relwidth=1.0, anchor="sw", relx=0, rely=1.0)
        _clickable(button, lambda name=name: _pick_tab(name))


def _footer(parent, colors):
    text = _state["status"] or (
        f"{pledgedPower.Power} - Rank {pledgedPower.Rank} - "
        f"{pledgedPower.Merits:,} merits - pledged {pledgedPower.TimePledgedStr}"
        if pledgedPower.Power else "not pledged"
    )
    tk.Label(parent, text=text, font=(FONT, 8), anchor="w",
             background=colors['bg'], foreground=colors['muted']
             ).pack(side="bottom", fill="x", padx=12, pady=(2, 5))


# ------------------------------------------------------------- the session tab


def _session_tab(parent, colors):
    """Every system holding merits, with the report text it would produce."""
    tracked = {name: data for name, data in systems.items() if data.Merits > 0}

    head = tk.Frame(parent, background=colors['bg'])
    head.pack(side="top", fill="x", padx=18, pady=(14, 8))
    tk.Label(head, text="SYSTEMS HOLDING MERITS", font=(FONT, 8),
             background=colors['bg'], foreground=colors['muted']
             ).pack(side="left")
    tk.Label(head, text="tracked", font=(FONT, 8), background=colors['bg'],
             foreground=colors['muted']).pack(side="right", padx=(6, 0))
    tk.Label(head, text=f"{sum(d.Merits for d in tracked.values()):,}",
             font=(FONT, 16, "bold"), background=colors['bg'],
             foreground=colors['highlight']).pack(side="right")

    # The bottom bar is packed before the scrolling list, not after: pack gives
    # space in the order it is asked for, so a list that expands first leaves
    # the bar nothing and the last row is drawn under it.
    bar = tk.Frame(parent, background=colors['bg'])
    bar.pack(side="bottom", fill="x", padx=18, pady=10)
    _rounded(bar, "Copy all systems", _copy_all, colors, 130).pack(side="left", padx=(0, 8))
    _rounded(bar, "Export CSV", _export_csv, colors, 100).pack(side="left")
    _rounded(bar, "Reset all", _reset_all, colors, 90).pack(side="right")

    inner = _scrollable(parent, "session", colors)

    if not tracked:
        tk.Label(inner, text="No systems with merits yet.", font=(FONT, 10, "italic"),
                 background=colors['bg'], foreground=colors['muted']
                 ).pack(anchor="w", pady=20)
    for index, (name, data) in enumerate(tracked.items()):
        _session_row(inner, colors, name, data, index)


def _session_row(parent, colors, name, system, index):
    background = TAGS[row_tag(system, index)][0]
    row = tk.Frame(parent, background=colors['bg'])
    row.pack(side="top", fill="x", pady=(0, 6))

    tk.Frame(row, background=background, width=4).pack(side="left", fill="y")

    box = tk.Frame(row, background=colors['bg'], padx=12, pady=9,
                   highlightbackground=colors['button_bg'], highlightthickness=1)
    box.pack(side="left", fill="both", expand=True)

    buttons = tk.Frame(box, background=colors['bg'])
    buttons.pack(side="right", padx=(12, 0))
    text = _report_text(name, system)
    _rounded(buttons, "Copy", lambda: _copy(text, name), colors, 70).pack(side="left", padx=4)
    _rounded(buttons, "Reset", lambda: _reset(name), colors, 70).pack(side="left", padx=4)

    tk.Label(box, text=f"{system.Merits:,}", font=(FONT, 15, "bold"), width=11,
             anchor="e", background=colors['bg'], foreground=colors['highlight']
             ).pack(side="right")

    left = tk.Frame(box, background=colors['bg'])
    left.pack(side="left", fill="x", expand=True)
    tk.Label(left, text=name, font=(FONT, 11), anchor="w", background=colors['bg'],
             foreground=colors['fg']).pack(side="top", fill="x")
    tk.Label(left, text=_summary(system), font=(FONT, 8), anchor="w",
             background=colors['bg'], foreground=colors['muted']
             ).pack(side="top", fill="x", pady=(2, 0))
    tk.Label(left, text=text, font=("Consolas", 8), anchor="w", justify="left",
             background=colors['bg'], foreground=colors['fg']
             ).pack(side="top", fill="x", pady=(6, 0))


def _summary(system):
    """The one-line state of a system, as the row sub-line shows it."""
    parts = [system.getSystemStateText(), system.ControllingPower,
             f"{system.getSystemProgressNumber():.2f} %"]
    net = system.getPowerPlayCycleNetStatusText()
    if net:
        parts.append(net)
    return "  -  ".join(part for part in parts if part)


# ------------------------------------------------------------- the systems tab


def _systems_tab(parent, colors):
    _filter_strip(parent, colors)
    _systems_header(parent, colors)

    shown = _shown_systems()

    # Before the list, so the list does not take the bar's space. See
    # _session_tab.
    bar = tk.Frame(parent, background=colors['bg'])
    bar.pack(side="bottom", fill="x", padx=18, pady=10)
    _rounded(bar, "Copy all systems", _copy_all, colors, 130).pack(side="left", padx=(0, 8))
    _rounded(bar, "Export CSV", _export_csv, colors, 100).pack(side="left", padx=(0, 8))
    _rounded(bar, "Collapse all", _collapse_all, colors, 100).pack(side="left")
    tk.Label(bar, text=f"{len(shown)} of {len(systems)} systems", font=(FONT, 8),
             background=colors['bg'], foreground=colors['muted']).pack(side="right")

    inner = _scrollable(parent, "systems", colors, padx=(0, 0))
    if not shown:
        tk.Label(inner, text="No system matches the filters.",
                 font=(FONT, 10, "italic"), background=colors['bg'],
                 foreground=colors['muted']).pack(anchor="w", padx=16, pady=20)
    for index, (name, data) in enumerate(shown):
        _systems_row(inner, colors, name, data, index)
        if name in _state["folded_open"]:
            _systems_detail(inner, colors, name, data)


def _filter_strip(parent, colors):
    strip = tk.Frame(parent, background=colors['bg'])
    strip.pack(side="top", fill="x", padx=16, pady=(12, 10))

    tk.Label(strip, text="SEARCH", font=(FONT, 8), background=colors['bg'],
             foreground=colors['muted']).pack(side="left", padx=(0, 6))
    search = tk.Entry(strip, width=24, font=(FONT, 9), relief="solid", borderwidth=1,
                      background=colors['bg'], foreground=colors['fg'],
                      insertbackground=colors['fg'])
    search.insert(0, _state["search"])
    search.pack(side="left")
    search.bind("<KeyRelease>", lambda event: _set_search(search.get()))

    powers = ["All powers"] + sorted(
        {d.ControllingPower for d in systems.values() if d.ControllingPower}
    )
    states = ["All states"] + sorted(
        {d.getSystemStateText() for d in systems.values() if d.PowerplayState}
    )
    _dropdown(strip, colors, "POWER", powers, _state["power"], _set_power)
    _dropdown(strip, colors, "STATE", states, _state["state"], _set_state)


def _dropdown(parent, colors, label, values, current, on_pick):
    tk.Label(parent, text=label, font=(FONT, 8), background=colors['bg'],
             foreground=colors['muted']).pack(side="left", padx=(16, 6))
    variable = tk.StringVar(value=current if current in values else values[0])
    box = ttk.Combobox(parent, textvariable=variable, values=values,
                       width=18, state="readonly", font=(FONT, 9))
    box.pack(side="left")
    box.bind("<<ComboboxSelected>>", lambda event: on_pick(variable.get()))


def _cell(parent, text, width, anchor, background, foreground, font, expand=False):
    """One table cell, `width` pixels wide.

    A Label's own `width` is in characters, so COLUMNS' pixel widths have to be
    held by a Frame with pack_propagate off - sized in characters the seven
    columns came out about twice as wide as the window.
    """
    box = tk.Frame(parent, background=background, width=width)
    box.pack(side="left", fill="both", expand=expand)
    if not expand:
        box.pack_propagate(False)
    tk.Label(box, text=text, font=font, anchor=anchor, padx=8, pady=6,
             background=background, foreground=foreground
             ).pack(side="left", fill="both", expand=True)
    return box


def _systems_header(parent, colors):
    head = tk.Frame(parent, background=colors['button_bg'])
    head.pack(side="top", fill="x")
    font = (FONT, 8, "bold")
    for key, label, width, anchor in COLUMNS:
        text = label
        if _state["sort"] == key:
            text = f"{label} {'v' if _state['reverse'] else '^'}"
        cell = _cell(head, text, width, anchor, colors['button_bg'],
                     colors['fg'], font)
        _clickable(cell, lambda key=key: _pick_sort(key))
    _cell(head, "Opposition", 0, "w", colors['button_bg'], colors['fg'], font,
          expand=True)


def _systems_row(parent, colors, name, system, index):
    background, foreground = TAGS[row_tag(system, index)]
    row = tk.Frame(parent, background=background)
    row.pack(side="top", fill="x")

    open_here = name in _state["folded_open"]
    values = {
        "name": ("v  " if open_here else ">  ") + name,
        "state": system.getSystemStateText(),
        "progress": f"{system.getSystemProgressNumber():.1f} %",
        "power": system.ControllingPower,
        "reinforcement": f"{system.PowerplayStateReinforcement:,}",
        "real_undermining": f"{getattr(system, 'RealUndermining', 0):,}",
        "merits": f"{system.Merits:,}",
    }
    font = (FONT, 9)
    for key, _label, width, anchor in COLUMNS:
        _cell(row, values[key], width, anchor, background, foreground, font)
    opposition = ", ".join(system.Opposition) if system.Opposition else ""
    _cell(row, opposition, 0, "w", background, foreground, font, expand=True)

    _clickable(row, lambda: _toggle_fold(name))


def _systems_detail(parent, colors, name, system):
    """The folded-open body of one row: progress, opposition, the report text
    and the two buttons that act on it."""
    background = TAGS[row_tag(system, 0)][0]
    holder = tk.Frame(parent, background=colors['bg'])
    holder.pack(side="top", fill="x")
    tk.Frame(holder, background=background, width=4).pack(side="left", fill="y")

    box = tk.Frame(holder, background=colors['bg'], padx=18, pady=14)
    box.pack(side="left", fill="both", expand=True)

    buttons = tk.Frame(box, background=colors['bg'])
    buttons.pack(side="right", fill="y", padx=(20, 0))
    text = _report_text(name, system)
    _rounded(buttons, "Copy report", lambda: _copy(text, name), colors, 120
             ).pack(side="top", pady=(0, 8))
    _rounded(buttons, "Reset system", lambda: _reset(name), colors, 120).pack(side="top")
    about = " - ".join(str(part) for part in (
        system.PrimaryEconomy, system.SystemSecurity, system.SystemGovernment
    ) if part)
    if about:
        tk.Label(buttons, text=about, font=(FONT, 8), justify="left", anchor="w",
                 background=colors['bg'], foreground=colors['muted']
                 ).pack(side="top", pady=(10, 0), fill="x")

    left = tk.Frame(box, background=colors['bg'])
    left.pack(side="left", fill="both", expand=True)

    progress = system.getSystemProgressNumber()
    line = tk.Frame(left, background=colors['bg'])
    line.pack(side="top", fill="x")
    tk.Label(line, text="CONTROL PROGRESS", font=(FONT, 8), background=colors['bg'],
             foreground=colors['muted']).pack(side="left")
    tk.Label(line, text=f"{progress:.2f} %", font=(FONT, 10, "bold"),
             background=colors['bg'], foreground=colors['highlight']).pack(side="right")

    track = tk.Frame(left, background=colors['button_bg'], height=14)
    track.pack(side="top", fill="x", pady=(6, 0))
    track.pack_propagate(False)
    filled = max(0.0, min(1.0, progress / 100.0))
    if filled:
        bar = tk.Frame(track, background=background)
        bar.place(relwidth=filled, relheight=1.0)

    decay = system.PowerplayStateUndermining - getattr(system, 'RealUndermining', 0)
    net = system.PowerplayStateReinforcement - getattr(system, 'RealUndermining', 0)
    tk.Label(left, text=f"Raw undermining {system.PowerplayStateUndermining:,}  -  "
                        f"{decay:,} decay  -  NET {net:+,}",
             font=(FONT, 8), anchor="w", background=colors['bg'],
             foreground=colors['muted']).pack(side="top", fill="x", pady=(10, 0))

    if system.Opposition:
        chips = tk.Frame(left, background=colors['bg'])
        chips.pack(side="top", fill="x", pady=(8, 0))
        for power in system.Opposition:
            tk.Label(chips, text=power, font=(FONT, 8), padx=7, pady=2,
                     background=colors['bg'], foreground=colors['fg'],
                     highlightbackground=colors['button_bg'], highlightthickness=1
                     ).pack(side="left", padx=(0, 5))

    tk.Label(left, text=text, font=("Consolas", 8), anchor="w", justify="left",
             background=colors['bg'], foreground=colors['fg'],
             highlightbackground=colors['button_bg'], highlightthickness=1,
             padx=10, pady=8).pack(side="top", fill="x", pady=(12, 0))


def _shown_systems():
    """The systems the filters let through, sorted. [(name, system), ...]"""
    search = _state["search"].lower()
    rows = []
    for name, data in systems.items():
        if search and search not in name.lower():
            continue
        if _state["power"] != "All powers" and data.ControllingPower != _state["power"]:
            continue
        if _state["state"] != "All states" and data.getSystemStateText() != _state["state"]:
            continue
        rows.append((name, data))

    keys = {
        "name": lambda pair: pair[0].lower(),
        "state": lambda pair: pair[1].getSystemStateText().lower(),
        "progress": lambda pair: pair[1].getSystemProgressNumber(),
        "power": lambda pair: (pair[1].ControllingPower or "").lower(),
        "reinforcement": lambda pair: pair[1].PowerplayStateReinforcement,
        "real_undermining": lambda pair: getattr(pair[1], 'RealUndermining', 0),
        "merits": lambda pair: pair[1].Merits,
    }
    rows.sort(key=keys.get(_state["sort"], keys["name"]), reverse=_state["reverse"])
    return rows


# ---------------------------------------------------------- the shiplocker tab


def _shiplocker_tab(parent, colors):
    """The three Powerplay bags and the salvage hold, one table each."""
    from emt_models.backpack import playerBackpack
    from emt_models.salvage import salvageInventory, VALID_POWERPLAY_SALVAGE_TYPES
    from emt_ppdata.undermining import get_um_display_name
    from emt_ppdata.reinforcement import get_reinf_display_name
    from emt_ppdata.acquisition import get_acq_display_name

    inner = _scrollable(parent, "shiplocker", colors)

    bags = (
        ("Undermining", playerBackpack.umbag, get_um_display_name),
        ("Reinforcement", playerBackpack.reinfbag, get_reinf_display_name),
        ("Acquisition", playerBackpack.acqbag, get_acq_display_name),
    )
    for title, bag, display_name in bags:
        rows = [
            (system, item, count, display_name(item))
            for item, per_system in sorted(bag.items.items())
            for system, count in sorted(per_system.items())
        ]
        _inventory_table(inner, colors, title, rows, bag.get_total(),
                         on_edit=lambda item, system, count, bag=bag:
                             _edit_bag_count(bag, item, system, count),
                         on_add=lambda bag=bag: _add_bag_entry(bag))

    salvage_rows = [
        (name, item, cargo.count, VALID_POWERPLAY_SALVAGE_TYPES.get(item, item))
        for name, salvage in sorted(salvageInventory.items())
        for item, cargo in sorted(salvage.inventory.items())
        if cargo.count > 0
    ]
    _inventory_table(inner, colors, "Salvage", salvage_rows,
                     sum(row[2] for row in salvage_rows),
                     on_edit=_edit_salvage_count, on_add=None)


def _inventory_table(parent, colors, title, rows, total, on_edit, on_add):
    frame = tk.Frame(parent, background=colors['bg'])
    frame.pack(side="top", fill="x", pady=(0, 18))

    head = tk.Frame(frame, background=colors['bg'])
    head.pack(side="top", fill="x")
    tk.Label(head, text=title.upper(), font=(FONT, 10, "bold"), background=colors['bg'],
             foreground=colors['fg']).pack(side="left")
    tk.Label(head, text=f"{total:,} items", font=(FONT, 8), background=colors['bg'],
             foreground=colors['muted']).pack(side="right")

    columns = tk.Frame(frame, background=colors['button_bg'])
    columns.pack(side="top", fill="x", pady=(6, 0))
    for label, width, expand in (("System", 34, False), ("Item", 30, False),
                                 ("Count", 10, False), ("", 0, True)):
        tk.Label(columns, text=label, font=(FONT, 8, "bold"), anchor="w", padx=8,
                 pady=5, width=width or None, background=colors['button_bg'],
                 foreground=colors['fg']).pack(side="left", fill="both", expand=expand)

    if not rows:
        tk.Label(frame, text="empty", font=(FONT, 9, "italic"), anchor="w",
                 background=colors['bg'], foreground=colors['muted']
                 ).pack(side="top", fill="x", padx=8, pady=8)

    for index, (system, item, count, display) in enumerate(rows):
        background = (colors['table_row_even'] if index % 2 == 0
                      else colors['table_row_odd'])
        row = tk.Frame(frame, background=background)
        row.pack(side="top", fill="x")
        for text, width in ((system, 34), (display, 30), (f"{count:,}", 10)):
            tk.Label(row, text=text, font=(FONT, 9), anchor="w", padx=8, pady=5,
                     width=width, background=background, foreground=colors['fg']
                     ).pack(side="left")
        tk.Label(row, text="click to edit", font=(FONT, 8), anchor="e", padx=8,
                 background=background, foreground=colors['muted']
                 ).pack(side="left", fill="both", expand=True)
        _clickable(row, lambda item=item, system=system, count=count:
                   on_edit(item, system, count))

    if on_add is not None:
        _rounded(frame, "+ Add entry", on_add, colors, 110).pack(side="top", anchor="w",
                                                                pady=(8, 0))


# ---------------------------------------------------------------- the actions


def _pick_tab(name):
    _state["tab"] = name
    _state["status"] = ""
    _draw()


def _pick_sort(key):
    if _state["sort"] == key:
        _state["reverse"] = not _state["reverse"]
    else:
        _state["sort"] = key
        _state["reverse"] = False
    _draw()


def _toggle_fold(name):
    folded = _state["folded_open"]
    folded.discard(name) if name in folded else folded.add(name)
    _draw()


def _collapse_all():
    _state["folded_open"] = set()
    _draw()


def _set_search(text):
    _state["search"] = text
    _draw()


def _set_power(value):
    _state["power"] = value
    _draw()


def _set_state(value):
    _state["state"] = value
    _draw()


def _report_text(name, system):
    """Expand the copy-text template for one system.

    @SystemStatus is replaced before @System: the other way round leaves a
    "Status" remnant in the output.
    """
    text = configPlugin.copyText.get().replace('@MeritsValue', str(system.Merits))
    if '@SystemStatus' in text:
        text = text.replace('@SystemStatus', system.getSystemStatusShort())
    text = text.replace('@System', name)
    conflict = system.PowerplayConflictProgress
    if '@CPControlling' in text:
        if conflict:
            text = text.replace(
                '@CPControlling',
                f"{system.ControllingPower} {system.getSystemProgressNumber():.2f}%")
        else:
            text = text.replace(
                '@CPControlling',
                f"{system.ControllingPower} {system.PowerplayStateReinforcement}")
    if '@CPOpposition' in text:
        if conflict and len(conflict) > 1:
            second = conflict[1]
            text = text.replace('@CPOpposition',
                                f"{second.power} {second.progress * 100:.2f}%")
        else:
            real_um = getattr(system, 'RealUndermining', system.PowerplayStateUndermining)
            text = text.replace('@CPOpposition', f"Opposition {real_um}")
    return text


def _copy(text, name):
    """Send the report to Discord if a webhook is set, otherwise to the
    clipboard. A Discord send also clears the system, as it always has."""
    if configPlugin.discordHook.get():
        report.send_to_discord(text)
        _reset(name)
        return
    if is_open():
        _window.clipboard_clear()
        _window.clipboard_append(text)
        _window.update()
    _state["status"] = f"Copied {name} to the clipboard"
    _draw()


def _copy_all():
    texts = [_report_text(name, data) for name, data in systems.items()
             if data.Merits > 0]
    if not texts:
        _state["status"] = "Nothing to copy"
        _draw()
        return
    _copy("\n".join(texts), "Systems worked on")


def _reset(name):
    """Zero a system's merits and forget its credits in the ledger."""
    if name in systems:
        systems[name].Merits = 0
        merit_ledger.forget(name)
        _refresh_tracker(name)
    _state["folded_open"].discard(name)
    _state["status"] = f"Reset {name}"
    _draw()


def _reset_all():
    for name, data in systems.items():
        if data.Merits > 0:
            data.Merits = 0
            merit_ledger.forget(name)
    _state["folded_open"] = set()
    _state["status"] = "Reset every system"
    _refresh_tracker(None)
    _draw()


def _refresh_tracker(name):
    if _tracker_frame is None:
        return
    from emt_core.state import state
    current = state.current_system
    if current and (name is None or current.StarSystem == name):
        _tracker_frame.update_display(current)


def _export_csv():
    """Every tracked system as semicolon-separated CSV."""
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")],
        title="Save CSV File",
    )
    if not path:
        return
    headers = ["System", "Status", "Controlling Power", "Powerplay Cycle",
               "Reinforcement", "Undermining", "Opposition", "Merits"]
    try:
        with open(path, mode="w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(headers)
            for name, data in systems.items():
                writer.writerow([
                    name,
                    data.getSystemStateText(),
                    data.ControllingPower,
                    data.getPowerPlayCycleNetStatusText(),
                    data.PowerplayStateReinforcement,
                    getattr(data, 'RealUndermining', data.PowerplayStateUndermining),
                    ", ".join(data.Opposition) if data.Opposition else "",
                    data.Merits,
                ])
    except OSError as err:
        logger.warning(f"could not write {path}: {err}")
        _state["status"] = f"Could not write {path}"
        _draw()
        return
    _state["status"] = f"Exported to {path}"
    _draw()


# ------------------------------------------------------------ the edit dialogs


def _edit_bag_count(bag, item, system, count):
    """Set one bag entry's count. 0 removes it."""
    from emt_models.backpack import save_backpack

    new = _ask_count(f"{system} - {item}", count)
    if new is None:
        return
    if new > 0:
        bag.items.setdefault(item, {})[system] = new
    else:
        bag.items.get(item, {}).pop(system, None)
        if item in bag.items and not bag.items[item]:
            del bag.items[item]
    save_backpack()
    _draw()


def _edit_salvage_count(item, system, count):
    """Set one salvage entry's count. 0 removes it."""
    from emt_models.salvage import salvageInventory, save_salvage

    new = _ask_count(f"{system} - {item}", count)
    if new is None:
        return
    salvage = salvageInventory.get(system)
    if salvage is None:
        return
    if new > 0 and item in salvage.inventory:
        salvage.inventory[item].count = new
    else:
        salvage.inventory.pop(item, None)
    save_salvage()
    _draw()


def _ask_count(title, current):
    """A modal count box. The new count, or None when it was cancelled.

    One dialog for both tables, where there used to be two near-identical ones.
    """
    colors = get_theme_colors()
    box = tk.Toplevel(_window)
    box.title("Count")
    box.configure(background=colors['bg'])
    box.transient(_window)
    box.resizable(False, False)

    tk.Label(box, text=title, font=(FONT, 9), background=colors['bg'],
             foreground=colors['fg']).pack(padx=20, pady=(16, 8))
    entry = tk.Entry(box, width=14, justify="center", font=(FONT, 11),
                     relief="solid", borderwidth=1, background=colors['bg'],
                     foreground=colors['fg'], insertbackground=colors['fg'])
    entry.insert(0, str(current))
    entry.select_range(0, tk.END)
    entry.pack(padx=20)

    answer = {"value": None}

    def save(event=None):
        text = entry.get().strip()
        try:
            answer["value"] = max(0, int(text)) if text else 0
        except ValueError:
            answer["value"] = None
        box.destroy()

    buttons = tk.Frame(box, background=colors['bg'])
    buttons.pack(padx=20, pady=16)
    _rounded(buttons, "Save", save, colors, 80).pack(side="left", padx=5)
    _rounded(buttons, "Cancel", box.destroy, colors, 80).pack(side="left", padx=5)

    entry.bind("<Return>", save)
    box.bind("<Escape>", lambda event: box.destroy())
    _centre_over(box, _window)
    entry.focus_set()
    box.grab_set()
    box.wait_window()
    return answer["value"]


def _add_bag_entry(bag):
    """Add one (item, system, count) to a bag."""
    from emt_models.backpack import save_backpack

    if bag.name == "undermining":
        from emt_ppdata.undermining import VALID_UNDERMINING_DATA_TYPES as types
    elif bag.name == "reinforcement":
        from emt_ppdata.reinforcement import VALID_REINFORCEMENT_DATA_TYPES as types
    else:
        from emt_ppdata.acquisition import VALID_ACQUISITION_DATA_TYPES as types

    colors = get_theme_colors()
    box = tk.Toplevel(_window)
    box.title("Add entry")
    box.configure(background=colors['bg'])
    box.transient(_window)
    box.resizable(False, False)

    tk.Label(box, text="System", font=(FONT, 8), anchor="w", background=colors['bg'],
             foreground=colors['muted']).pack(fill="x", padx=20, pady=(16, 4))
    system_entry = tk.Entry(box, width=34, font=(FONT, 10), relief="solid",
                            borderwidth=1, background=colors['bg'],
                            foreground=colors['fg'], insertbackground=colors['fg'])
    system_entry.pack(padx=20)

    tk.Label(box, text="Data type", font=(FONT, 8), anchor="w", background=colors['bg'],
             foreground=colors['muted']).pack(fill="x", padx=20, pady=(12, 4))
    type_variable = tk.StringVar(value=list(types.keys())[0])
    ttk.Combobox(box, textvariable=type_variable, values=list(types.keys()),
                 width=31, state="readonly").pack(padx=20)

    tk.Label(box, text="Count", font=(FONT, 8), anchor="w", background=colors['bg'],
             foreground=colors['muted']).pack(fill="x", padx=20, pady=(12, 4))
    count_entry = tk.Entry(box, width=34, font=(FONT, 10), relief="solid",
                           borderwidth=1, background=colors['bg'],
                           foreground=colors['fg'], insertbackground=colors['fg'])
    count_entry.insert(0, "1")
    count_entry.pack(padx=20)

    def save(event=None):
        name = system_entry.get().strip()
        try:
            count = int(count_entry.get().strip())
        except ValueError:
            return
        if name and count > 0:
            bag.add_item(type_variable.get(), count, name)
            save_backpack()
        box.destroy()
        _draw()

    buttons = tk.Frame(box, background=colors['bg'])
    buttons.pack(padx=20, pady=16)
    _rounded(buttons, "Add", save, colors, 80).pack(side="left", padx=5)
    _rounded(buttons, "Cancel", box.destroy, colors, 80).pack(side="left", padx=5)

    count_entry.bind("<Return>", save)
    box.bind("<Escape>", lambda event: box.destroy())
    _centre_over(box, _window)
    system_entry.focus_set()
    box.grab_set()
    box.wait_window()


def _centre_over(box, parent):
    """update_idletasks first: a Toplevel reports 1x1 until Tk has laid it
    out, and centring on 1x1 puts it in the corner."""
    box.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - box.winfo_width()) // 2
    y = parent.winfo_y() + (parent.winfo_height() - box.winfo_height()) // 2
    box.geometry(f"+{max(0, x)}+{max(0, y)}")


# ------------------------------------------------------------------ the parts


class RoundedButton(tk.Canvas):
    """The plugin's button: a rounded rectangle drawn on a canvas, because
    tk.Button has no corner radius."""

    def __init__(self, parent, text, command, colors, width=100, height=26,
                 radius=6, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0,
                         background=colors['bg'], **kwargs)
        self.text = text
        self.command = command
        self.colors = colors
        self.btn_width = width
        self.btn_height = height
        self.radius = radius
        self.hover = False
        self._draw_button()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.configure(cursor="hand2")

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, fill):
        self.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90,
                        fill=fill, outline=fill)
        self.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90,
                        fill=fill, outline=fill)
        self.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90,
                        fill=fill, outline=fill)
        self.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90,
                        fill=fill, outline=fill)
        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline=fill)
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline=fill)

    def _draw_button(self):
        fill = self.colors['highlight'] if self.hover else self.colors['button_bg']
        text_color = self.colors['bg'] if self.hover else self.colors['fg']
        self.delete("all")
        self._draw_rounded_rect(1, 1, self.btn_width - 1, self.btn_height - 1,
                                self.radius, fill)
        self.create_text(self.btn_width / 2, self.btn_height / 2, text=self.text,
                         fill=text_color, font=(FONT, 9))

    def _on_enter(self, event):
        self.hover = True
        self._draw_button()

    def _on_leave(self, event):
        self.hover = False
        self._draw_button()

    def _on_click(self, event):
        if self.command:
            self.command()


def _rounded(parent, text, command, colors, width=100):
    return RoundedButton(parent, text, command, colors, width=width)


def _clickable(widget, command):
    """A whole row, clickable.

    Tk hands a click to the widget under the pointer and does not pass it to
    the parent, so a row only responds if every label in it does.
    """
    def press(event):
        command()

    pending = [widget]
    while pending:
        current = pending.pop()
        current.configure(cursor="hand2")
        current.bind("<Button-1>", press)
        pending.extend(current.winfo_children())


def _remember_scroll():
    """Where each list had been scrolled to, before the draw throws it away."""
    for name, canvas in _canvases.items():
        try:
            if canvas.winfo_exists():
                _scroll[name] = canvas.yview()[0]
        except tk.TclError:                      # destroyed between the two calls
            pass
    _canvases.clear()


def _scrollable(parent, name, colors, padx=(18, 0)):
    """A canvas with a frame in it, because Tk has no scrolling frame.

    Returns the inner frame. `name` is what the scroll position is remembered
    under, so a redraw puts the list back where it was rather than at the top.
    """
    box = tk.Frame(parent, background=colors['bg'])
    box.pack(side="top", fill="both", expand=True, padx=padx, pady=(4, 0))
    canvas = tk.Canvas(box, background=colors['bg'], highlightthickness=0)
    bar = tk.Scrollbar(box, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, background=colors['bg'])

    inner.bind("<Configure>",
               lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
    window = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.bind("<Configure>", lambda event: canvas.itemconfig(window, width=event.width))
    canvas.configure(yscrollcommand=bar.set)

    canvas.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")

    _canvases[name] = canvas
    _wheel(canvas)
    # After the layout, not now: the scrollregion is set by the <Configure> the
    # rows above are about to fire, and moving to a fraction of nothing is a
    # move to the top.
    canvas.after_idle(lambda: _restore_scroll(canvas, name))
    return inner


def _restore_scroll(canvas, name):
    try:
        if canvas.winfo_exists():
            canvas.yview_moveto(_scroll.get(name, 0.0))
    except tk.TclError:
        pass


def _wheel(canvas):
    """The wheel scrolls whichever list the pointer is over.

    bind_all while the pointer is inside, because the rows live in frames
    inside the canvas and the event goes to the widget under the pointer.
    Whatever was bound is put back on the way out: EDMC and other plugins bind
    the wheel the same way, and unbind_all takes theirs with it.
    """
    def scroll(event):
        canvas.yview_scroll(-int(event.delta / 120), "units")

    def enter(event):
        canvas.emt_previous = canvas.bind_all("<MouseWheel>")
        canvas.bind_all("<MouseWheel>", scroll)

    def leave(event):
        canvas.unbind_all("<MouseWheel>")
        if getattr(canvas, "emt_previous", None):
            canvas.bind_all("<MouseWheel>", canvas.emt_previous)
            canvas.emt_previous = None

    canvas.bind("<Enter>", enter, add="+")
    canvas.bind("<Leave>", leave, add="+")
    canvas.bind("<Destroy>", leave, add="+")
