import tkinter as tk
from tkinter import ttk, filedialog
import csv

from config import config, appname
from theme import theme
from emt_core.report import Report, report
from emt_models.system import systems
from emt_models.power import pledgedPower
from emt_core.config import configPlugin
from emt_core.logging import logger, plugin_name
from typing import Dict, Any, List, Optional

# Global GUI variables
data_frame_default = None
data_frame_detailed = None
detailed_view = False
toggle_button = None
csv_button = None
copy_all_button = None
shiplocker_button = None
csv_border = None
copy_all_border = None
table_frame = None
filter_frame = None
filter_system_var = None
filter_state_var = None
filter_power_var = None
main_tracker_frame = None
info_window = None
treeview = None
sort_column = None
sort_reverse = False
outer_scrollbar = None  # Outer scrollbar for default view


def copy_to_clipboard_or_report(text, name, table_frame, update_scrollregion):
    global report, systems
    if configPlugin.discordHook.get():
        report.send_to_discord(text)
        delete_entry(name, table_frame, update_scrollregion)
    else:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()


def delete_entry(system_name, table_frame, update_scrollregion):
    global data_frame_default, data_frame_detailed, detailed_view, systems, pledgedPower, main_tracker_frame

    if system_name in systems:
        systems[system_name].Merits = 0

        if detailed_view and data_frame_detailed:
            for widget in data_frame_detailed.winfo_children():
                widget.destroy()
        elif not detailed_view and data_frame_default:
            for widget in data_frame_default.winfo_children():
                widget.destroy()

        populate_table(table_frame, update_scrollregion)

        if main_tracker_frame:
            from emt_core.state import state
            if state.current_system and state.current_system.StarSystem == system_name:
                main_tracker_frame.update_display(state.current_system)


def toggle_view():
    global detailed_view, csv_button, copy_all_button, shiplocker_button, systems, pledgedPower

    # Check if window still exists
    if info_window is None or not info_window.winfo_exists():
        return

    detailed_view = not detailed_view

    toggle_button.config(text="Show Default View" if detailed_view else "Show Detailed View")

    for widget in table_frame.winfo_children():
        widget.destroy()

    if detailed_view:
        csv_button.grid(row=0, column=1, padx=5)
        shiplocker_button.grid_forget()
        copy_all_button.grid_forget()
    else:
        csv_button.grid_forget()
        shiplocker_button.grid(row=0, column=2, padx=5)
        copy_all_button.grid(row=0, column=3, padx=5)
        add_power_info_headers()

    colors = get_theme_colors()
    table_frame.after(100, lambda: (populate_table(table_frame, update_scrollregion), apply_theme_to_widget(info_window, colors)))


def save_window_size(window):
    try:
        if window and window.winfo_exists():
            w = window.winfo_width()
            h = window.winfo_height()
            config.set("power_info_width", str(w))
            config.set("power_info_height", str(h))
    except tk.TclError:
        pass  # Window already destroyed


def export_to_csv():
    """Export system data to CSV file"""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")],
        title="Save CSV File"
    )

    if not file_path:
        return

    headers = ["System", "Status", "Controlling Power", "Powerplay Cycle", "Reinforcement", "Undermining", "Opposition"]

    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(headers)
        for system_name, system_data in systems.items():
            state = system_data.PowerplayState
            progress = system_data.getSystemProgressNumber()
            controlling_power = system_data.ControllingPower
            opposition = ", ".join(system_data.Opposition) if system_data.Opposition else ""
            reinforcement = system_data.PowerplayStateReinforcement
            undermining = system_data.PowerplayStateUndermining
            power_status = system_data.getPowerPlayCycleNetStatusText()
            writer.writerow([system_name, f"{state} ({progress:.2f}%)", controlling_power, power_status, reinforcement, undermining, opposition])

    logger.info(f"CSV export successful: {file_path}")


def adjust_color_brightness(hex_color, factor):
    """Adjust color brightness. factor > 1 = lighter, factor < 1 = darker"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    if factor > 1:  # Lighten
        r = min(255, int(r + (255 - r) * (factor - 1)))
        g = min(255, int(g + (255 - g) * (factor - 1)))
        b = min(255, int(b + (255 - b) * (factor - 1)))
    else:  # Darken
        r = max(0, int(r * factor))
        g = max(0, int(g * factor))
        b = max(0, int(b * factor))

    return f'#{r:02x}{g:02x}{b:02x}'


def get_button_bg(bg_color):
    """Get a button background that contrasts with the window background"""
    # Parse the background color to determine if it's dark or light
    hex_color = bg_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

    if luminance < 0.5:
        # Dark theme - make button slightly lighter
        return adjust_color_brightness(bg_color, 1.4)
    else:
        # Light theme - make button slightly darker
        return adjust_color_brightness(bg_color, 0.85)


def get_theme_colors():
    """Get EDMC theme colors, with sensible fallbacks"""
    try:
        bg = theme.current.get('background', '#000000')
        button_bg = get_button_bg(bg)

        # Determine if dark theme based on background luminance
        hex_color = bg.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        is_dark = luminance < 0.5

        return {
            'bg': bg,
            'fg': theme.current.get('foreground', '#ff8c00'),
            'active_bg': theme.current.get('activebackground', '#000000'),
            'active_fg': theme.current.get('activeforeground', '#ff8c00'),
            'highlight': theme.current.get('highlight', '#ff8c00'),
            'button_bg': button_bg,
            'table_row_even': adjust_color_brightness(bg, 1.2 if is_dark else 0.95),
            'table_row_odd': adjust_color_brightness(bg, 1.4 if is_dark else 0.9),
        }
    except Exception:
        return {
            'bg': '#000000',
            'fg': '#ff8c00',
            'active_bg': '#000000',
            'active_fg': '#ff8c00',
            'highlight': '#ff8c00',
            'button_bg': '#1a1a1a',
            'table_row_even': '#1a1a1a',
            'table_row_odd': '#2a2a2a',
        }


def apply_theme_to_widget(widget, colors):
    """Recursively apply theme colors to a widget and its children"""
    try:
        widget_type = widget.winfo_class()

        # Apply colors based on widget type
        if widget_type in ('Frame', 'Toplevel', 'Canvas'):
            widget.configure(background=colors['bg'])
        elif widget_type == 'Label':
            widget.configure(background=colors['bg'], foreground=colors['fg'])
        elif widget_type == 'Button':
            widget.configure(
                background=colors['button_bg'],
                foreground=colors['fg'],
                activebackground=colors['highlight'],
                activeforeground=colors['bg'],
                borderwidth=0
            )

        # Recursively apply to children
        for child in widget.winfo_children():
            apply_theme_to_widget(child, colors)
    except Exception as e:
        pass  # Some widgets may not support certain options


class RoundedButton(tk.Canvas):
    """A button with rounded corners using Canvas"""
    def __init__(self, parent, text, command, colors, width=100, height=28, radius=8, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0,
                        background=colors['bg'], **kwargs)
        self.command = command
        self.colors = colors
        self.radius = radius
        self.btn_width = width
        self.btn_height = height
        self.text = text
        self.hover = False

        self._draw_button()

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, fill):
        """Draw a rounded rectangle"""
        self.delete("button")
        # Draw rounded rectangle using arcs and rectangles
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, fill=fill, outline=fill, tags="button")
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, fill=fill, outline=fill, tags="button")
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, fill=fill, outline=fill, tags="button")
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, fill=fill, outline=fill, tags="button")
        self.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline=fill, tags="button")
        self.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline=fill, tags="button")

    def _draw_button(self):
        fill = self.colors['highlight'] if self.hover else self.colors['button_bg']
        text_color = self.colors['bg'] if self.hover else self.colors['fg']
        self._draw_rounded_rect(0, 0, self.btn_width, self.btn_height, self.radius, fill)
        self.delete("text")
        self.create_text(self.btn_width/2, self.btn_height/2, text=self.text, fill=text_color,
                        font=("Arial", 9), tags="text")

    def _on_enter(self, event):
        self.hover = True
        self._draw_button()

    def _on_leave(self, event):
        self.hover = False
        self._draw_button()

    def _on_click(self, event):
        if self.command:
            self.command()

    def config(self, **kwargs):
        if 'text' in kwargs:
            self.text = kwargs.pop('text')
            self._draw_button()
        super().config(**kwargs)


def create_bordered_button(parent, text, command, colors, width=None):
    """Create a rounded button"""
    # Calculate width based on text length if not specified
    char_width = 8  # Approximate pixels per character
    padding = 24
    btn_width = max(80, len(text) * char_width + padding) if width is None else width * 10
    return RoundedButton(parent, text, command, colors, width=btn_width, height=28, radius=6)


def show_power_info(parent, pp, sy, tracker_frame=None):
    global table_frame, toggle_button, csv_button, copy_all_button, shiplocker_button, detailed_view, filter_frame
    global systems, pledgedPower, update_scrollregion, main_tracker_frame, info_window

    pledgedPower = pp
    systems = sy
    main_tracker_frame = tracker_frame
    detailed_view = False

    # Get theme colors
    colors = get_theme_colors()

    info_window = tk.Toplevel(parent)
    info_window.title("Power Info - Elite Merit Tracker")
    saved_width = str(configPlugin.power_info_width) or "1280"
    saved_height = str(configPlugin.power_info_height) or "800"
    info_window.geometry(f"{saved_width}x{saved_height}")
    info_window.configure(background=colors['bg'])

    # Main container
    main_frame = tk.Frame(info_window, background=colors['bg'])
    main_frame.pack(fill="both", expand=True)

    # Button frame at top
    button_frame = tk.Frame(main_frame, background=colors['bg'])
    button_frame.pack(side="top", fill="x", padx=10, pady=5)

    toggle_button = RoundedButton(button_frame, "Show Detailed View", toggle_view, colors, width=140, height=28, radius=6)
    toggle_button.grid(row=0, column=0, padx=5, pady=3)

    csv_button = RoundedButton(button_frame, "Export CSV", export_to_csv, colors, width=100, height=28, radius=6)
    csv_button.grid(row=0, column=1, padx=5, pady=3)
    csv_button.grid_forget()

    # Show Shiplocker button (placed before Copy All Systems)
    shiplocker_button = RoundedButton(button_frame, "Show Shiplocker", lambda: show_backpack_view(info_window), colors, width=120, height=28, radius=6)
    shiplocker_button.grid(row=0, column=2, padx=5, pady=3)

    copy_all_button = RoundedButton(button_frame, "Copy All Systems", copy_all_systems_to_clipboard_or_report, colors, width=130, height=28, radius=6)
    copy_all_button.grid(row=0, column=3, padx=5, pady=3)

    # Scrollable content area
    global outer_scrollbar
    canvas = tk.Canvas(main_frame, highlightthickness=0, background=colors['bg'])
    canvas.pack(side="left", fill="both", expand=True)

    outer_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    outer_scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=outer_scrollbar.set)
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1*(event.delta//120), "units"))

    def on_close():
        global info_window
        if info_window and info_window.winfo_exists():
            save_window_size(info_window)
            info_window.destroy()
        info_window = None

    info_window.protocol("WM_DELETE_WINDOW", on_close)

    table_frame = tk.Frame(canvas, background=colors['bg'])
    for i in range(7):
        table_frame.columnconfigure(i, weight=1)
    canvas_window = canvas.create_window((0, 0), window=table_frame, anchor="nw")

    def update_scrollregion(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def resize_table_frame(event):
        # Make table_frame fill the canvas width and height
        canvas.itemconfig(canvas_window, width=event.width, height=event.height)

    table_frame.bind("<Configure>", update_scrollregion)
    canvas.bind("<Configure>", resize_table_frame)

    if not detailed_view:
        add_power_info_headers()

    populate_table(table_frame, update_scrollregion)

    # Apply theme to the entire window AFTER all widgets are created
    apply_theme_to_widget(info_window, colors)


def copy_all_systems_to_clipboard_or_report():
    global systems, configPlugin, report
    all_texts = []
    for system_name, system_data in systems.items():
        merits = str(system_data.Merits)
        if int(merits) > 0:
            dcText = configPlugin.copyText.get().replace('@MeritsValue', merits)
            if '@SystemStatus' in dcText:
                dcText = dcText.replace('@SystemStatus', system_data.getSystemStatusShort())
            dcText = dcText.replace('@System', system_name)
            if '@CPControlling' in dcText:
                # For acquisition systems, show progress percentage instead of reinforcement
                if system_data.PowerplayConflictProgress and len(system_data.PowerplayConflictProgress) > 0:
                    progress = system_data.getSystemProgressNumber()
                    dcText = dcText.replace('@CPControlling', f"{system_data.ControllingPower} {progress:.2f}%")
                else:
                    dcText = dcText.replace('@CPControlling', f"{system_data.ControllingPower} {str(system_data.PowerplayStateReinforcement)}")
            if '@CPOpposition' in dcText:
                # For acquisition systems, show 2nd place power progress percentage
                if system_data.PowerplayConflictProgress and len(system_data.PowerplayConflictProgress) > 1:
                    second_power = system_data.PowerplayConflictProgress[1]
                    progress = second_power.progress * 100
                    dcText = dcText.replace('@CPOpposition', f"{second_power.power} {progress:.2f}%")
                else:
                    dcText = dcText.replace('@CPOpposition', f"Opposition {str(system_data.PowerplayStateUndermining)}")
            all_texts.append(dcText)
    combined_text = "\n".join(all_texts)
    copy_to_clipboard_or_report(combined_text, "Systems worked on", table_frame, update_scrollregion)


def add_power_info_headers():
    global systems, pledgedPower, table_frame
    if detailed_view:
        return

    colors = get_theme_colors()
    lbl_opts = {'background': colors['bg'], 'foreground': colors['fg']}

    # Title
    title = tk.Label(table_frame, text="Powerplay Details", font=("Arial", 16, "bold"), **lbl_opts)
    title.grid(row=0, column=0, columnspan=7, pady=(10, 15), sticky="w", padx=10)

    # Power info
    info_frame = tk.Frame(table_frame, background=colors['bg'])
    info_frame.grid(row=1, column=0, columnspan=7, sticky="w", padx=10, pady=5)

    labels = [
        ("Power:", pledgedPower.Power),
        ("Rank:", str(pledgedPower.Rank)),
        ("Total Merits:", f"{pledgedPower.Merits:,}"),
        ("Time Pledged:", pledgedPower.TimePledgedStr),
    ]

    for i, (label, value) in enumerate(labels):
        lbl = tk.Label(info_frame, text=label, font=("Arial", 10, "bold"), **lbl_opts)
        lbl.grid(row=0, column=i*2, sticky="w", padx=(0, 5))

        val = tk.Label(info_frame, text=value, font=("Arial", 10), **lbl_opts)
        val.grid(row=0, column=i*2+1, sticky="w", padx=(0, 20))

    # Separator
    sep = ttk.Separator(table_frame, orient="horizontal")
    sep.grid(row=2, column=0, columnspan=7, sticky="ew", padx=10, pady=10)


def sort_treeview(tree, col, reverse):
    """Sort treeview by column"""
    global sort_column, sort_reverse

    data = [(tree.set(child, col), child) for child in tree.get_children('')]

    # Try numeric sort first
    try:
        data.sort(key=lambda t: float(t[0].replace(',', '').replace('%', '').split('(')[-1].split(')')[0]) if t[0] else 0, reverse=reverse)
    except (ValueError, IndexError, AttributeError):
        data.sort(key=lambda t: t[0].lower() if t[0] else '', reverse=reverse)

    for index, (val, child) in enumerate(data):
        tree.move(child, '', index)

    sort_column = col
    sort_reverse = reverse

    # Update header to show sort direction
    for column in tree["columns"]:
        if column == col:
            tree.heading(column, text=f"{column} {'▼' if reverse else '▲'}",
                        command=lambda c=col: sort_treeview(tree, c, not reverse))
        else:
            tree.heading(column, text=column,
                        command=lambda c=column: sort_treeview(tree, c, False))


def populate_table(table_frame, update_scrollregion, show_filters_only=False):
    global detailed_view, data_frame_default, systems, pledgedPower, treeview, outer_scrollbar

    colors = get_theme_colors()
    lbl_opts = {'background': colors['bg'], 'foreground': colors['fg']}

    if configPlugin.discordHook.get():
        textCopyReport = "report"
        textCopyReportHeader = "Discord"
        tlColumn = ""
    else:
        textCopyReport = "copy"
        textCopyReportHeader = "Clipboard"
        tlColumn = "Reset"

    # ----- DETAILED VIEW with Treeview -----
    if detailed_view:
        # Hide outer scrollbar - treeview has its own
        if outer_scrollbar:
            outer_scrollbar.pack_forget()
        # Reset all column weights first
        for i in range(7):
            table_frame.columnconfigure(i, weight=0)
        # Make table_frame expand to fill canvas - single column layout for detailed view
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=0)  # Filter row - no expansion
        table_frame.rowconfigure(1, weight=1)  # Treeview row - expand

        # Filter frame
        filter_container = tk.Frame(table_frame, background=colors['bg'])
        filter_container.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        create_filter_widgets(filter_container)

        # Treeview frame - expand to fill space
        tree_frame = tk.Frame(table_frame, background=colors['bg'])
        tree_frame.grid(row=1, column=0, columnspan=7, sticky="nsew", padx=10, pady=5)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("System", "Status", "Progress", "Power", "Cycle", "Reinf", "Underm", "Opposition")

        # Configure treeview style for better row separation and theme matching
        style = ttk.Style()

        # Use clam theme as base for better customization on Windows
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        style.configure("Spaced.Treeview",
            rowheight=28,
            font=("Arial", 9),
            background=colors['bg'],
            foreground=colors['fg'],
            fieldbackground=colors['bg'],
            borderwidth=0
        )
        style.configure("Spaced.Treeview.Heading",
            font=("Arial", 9, "bold"),
            background=colors['button_bg'],
            foreground=colors['fg'],
            borderwidth=1,
            relief="flat"
        )
        style.map("Spaced.Treeview",
            background=[('selected', colors['highlight'])],
            foreground=[('selected', colors['bg'])]
        )
        style.map("Spaced.Treeview.Heading",
            background=[('active', colors['highlight'])],
            foreground=[('active', colors['bg'])]
        )

        # Style scrollbars to match theme
        style.configure("Vertical.TScrollbar",
            background=colors['button_bg'],
            troughcolor=colors['bg'],
            borderwidth=0
        )
        style.configure("Horizontal.TScrollbar",
            background=colors['button_bg'],
            troughcolor=colors['bg'],
            borderwidth=0
        )

        treeview = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Spaced.Treeview")

        # Configure columns - first column left, all others centered
        col_config = [
            ("System", 220, "w"),       # Left align (first column) - wider for long system names
            ("Status", 100, "center"),
            ("Progress", 80, "center"),
            ("Power", 120, "center"),
            ("Cycle", 100, "center"),
            ("Reinf", 70, "center"),
            ("Underm", 70, "center"),
            ("Opposition", 150, "center"),
        ]
        for col, width, anchor in col_config:
            treeview.heading(col, text=col, command=lambda c=col: sort_treeview(treeview, c, False))
            # System column: fixed width, no shrinking; others can shrink
            if col == "System":
                treeview.column(col, width=width, minwidth=width, anchor=anchor, stretch=False)
            else:
                treeview.column(col, width=width, minwidth=50, anchor=anchor)

        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=treeview.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=treeview.xview)
        treeview.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        treeview.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Populate treeview
        populate_treeview(treeview, systems)

        # Configure tag colors with darker/lighter variants for better separation
        # Using slightly different shades and adding a visible border effect via contrasting colors
        treeview.tag_configure('danger', background='#a01010', foreground='#fff')
        treeview.tag_configure('danger_alt', background='#701010', foreground='#fff')
        treeview.tag_configure('safe', background='#107010', foreground='#fff')
        treeview.tag_configure('safe_alt', background='#105010', foreground='#fff')
        treeview.tag_configure('warning', background='#d07000', foreground='#fff')
        treeview.tag_configure('warning_alt', background='#a05000', foreground='#fff')
        treeview.tag_configure('neutral', background='#606060', foreground='#fff')
        treeview.tag_configure('neutral_alt', background='#404040', foreground='#fff')
        return

    # ----- DEFAULT VIEW -----
    # Show outer scrollbar for default view
    if outer_scrollbar:
        outer_scrollbar.pack(side="right", fill="y")

    # Reset row weights from detailed view - no row expansion needed for default view
    table_frame.rowconfigure(0, weight=0)
    table_frame.rowconfigure(1, weight=0)
    table_frame.rowconfigure(2, weight=0)
    table_frame.rowconfigure(3, weight=0)
    # Restore column weights for default view (7 columns)
    for i in range(7):
        table_frame.columnconfigure(i, weight=1)

    if data_frame_default:
        data_frame_default.destroy()

    data_frame_default = tk.Frame(table_frame, background=colors['bg'])
    data_frame_default.grid(row=3, column=0, columnspan=7, sticky="nsew", padx=10, pady=5)

    # Headers
    headers = ["System", "Session Merits", textCopyReportHeader, tlColumn, "Report Text"]

    for col, header in enumerate(headers):
        if header:
            lbl = tk.Label(data_frame_default, text=header, font=("Arial", 10, "bold"), anchor="w", **lbl_opts)
            lbl.grid(row=0, column=col, padx=5, pady=(5, 10), sticky="w")

    row_index = 1
    for system_name, system_data in systems.items():
        merits = system_data.Merits

        if merits > 0:
            dcText = configPlugin.copyText.get().replace('@MeritsValue', str(merits))
            if '@SystemStatus' in dcText:
                dcText = dcText.replace('@SystemStatus', system_data.getSystemStatusShort())
            dcText = dcText.replace('@System', system_name)
            if '@CPControlling' in dcText:
                # For acquisition systems, show progress percentage instead of reinforcement
                if system_data.PowerplayConflictProgress and len(system_data.PowerplayConflictProgress) > 0:
                    progress = system_data.getSystemProgressNumber()
                    dcText = dcText.replace('@CPControlling', f"{system_data.ControllingPower} {progress:.2f}%")
                else:
                    dcText = dcText.replace('@CPControlling', f"{system_data.ControllingPower} {str(system_data.PowerplayStateReinforcement)}")
            if '@CPOpposition' in dcText:
                # For acquisition systems, show 2nd place power progress percentage
                if system_data.PowerplayConflictProgress and len(system_data.PowerplayConflictProgress) > 1:
                    second_power = system_data.PowerplayConflictProgress[1]
                    progress = second_power.progress * 100
                    dcText = dcText.replace('@CPOpposition', f"{second_power.power} {progress:.2f}%")
                else:
                    dcText = dcText.replace('@CPOpposition', f"Opposition {str(system_data.PowerplayStateUndermining)}")

            # System name
            tk.Label(data_frame_default, text=system_name, width=28, anchor="w", **lbl_opts).grid(
                row=row_index, column=0, padx=5, pady=2, sticky="w")

            # Merits (bold, highlight color)
            tk.Label(data_frame_default, text=f"{merits:,}", width=12, anchor="w",
                    font=("Arial", 10, "bold"), background=colors['bg'], foreground=colors['highlight']).grid(
                row=row_index, column=1, padx=5, pady=2, sticky="w")

            # Copy button
            copy_btn = create_bordered_button(
                data_frame_default, textCopyReport,
                lambda text=dcText, name=system_name: copy_to_clipboard_or_report(text, name, table_frame, update_scrollregion),
                colors, width=6
            )
            copy_btn.grid(row=row_index, column=2, padx=5, pady=2)

            # Reset button
            if tlColumn:
                reset_btn = create_bordered_button(
                    data_frame_default, "Reset",
                    lambda name=system_name: delete_entry(name, table_frame, update_scrollregion),
                    colors, width=6
                )
                reset_btn.grid(row=row_index, column=3, padx=5, pady=2)

            # Report text
            tk.Label(data_frame_default, text=dcText, width=50, anchor="w", wraplength=350, **lbl_opts).grid(
                row=row_index, column=4, padx=5, pady=2, sticky="w")

            row_index += 1

    # Empty state
    if row_index == 1:
        tk.Label(data_frame_default, text="No systems with merits yet. Start earning merits!",
                font=("Arial", 11, "italic"), **lbl_opts).grid(row=1, column=0, columnspan=5, pady=20)


def create_filter_widgets(parent):
    """Create filter dropdown widgets for detailed view"""
    global filter_system_var, filter_state_var, filter_power_var

    colors = get_theme_colors()
    lbl_opts = {'background': colors['bg'], 'foreground': colors['fg']}

    tk.Label(parent, text="Filters:", font=("Arial", 10, "bold"), **lbl_opts).grid(row=0, column=0, padx=(0, 10), sticky="w")

    powers = sorted({data.ControllingPower for data in systems.values() if data.ControllingPower})
    states = sorted({data.PowerplayState for data in systems.values() if data.PowerplayState})
    system_names = sorted(systems.keys())

    filter_system_var = tk.StringVar(value="All Systems")
    filter_state_var = tk.StringVar(value="All States")
    filter_power_var = tk.StringVar(value="All Powers")

    # System filter
    tk.Label(parent, text="System:", **lbl_opts).grid(row=0, column=1, padx=5)
    system_menu = ttk.Combobox(parent, textvariable=filter_system_var,
                               values=["All Systems"] + system_names, width=20, state="readonly")
    system_menu.grid(row=0, column=2, padx=5)

    # State filter
    tk.Label(parent, text="State:", **lbl_opts).grid(row=0, column=3, padx=5)
    state_menu = ttk.Combobox(parent, textvariable=filter_state_var,
                              values=["All States"] + states, width=15, state="readonly")
    state_menu.grid(row=0, column=4, padx=5)

    # Power filter
    tk.Label(parent, text="Power:", **lbl_opts).grid(row=0, column=5, padx=5)
    power_menu = ttk.Combobox(parent, textvariable=filter_power_var,
                              values=["All Powers"] + powers, width=20, state="readonly")
    power_menu.grid(row=0, column=6, padx=5)

    # Bind filter changes
    for var in [filter_system_var, filter_state_var, filter_power_var]:
        var.trace_add("write", lambda *args: refresh_filtered_treeview())


def refresh_filtered_treeview():
    """Refresh treeview with filtered data"""
    global treeview, systems

    if not treeview:
        return

    selected_system = filter_system_var.get()
    selected_state = filter_state_var.get()
    selected_power = filter_power_var.get()

    filtered = {}
    for name, data in systems.items():
        if selected_system != "All Systems" and name != selected_system:
            continue
        if selected_state != "All States" and data.PowerplayState != selected_state:
            continue
        if selected_power != "All Powers" and data.ControllingPower != selected_power:
            continue
        filtered[name] = data

    # Clear and repopulate
    for item in treeview.get_children():
        treeview.delete(item)

    populate_treeview(treeview, filtered)


def populate_treeview(tree, data):
    """Populate treeview with system data"""
    row_index = 0
    for system_name, system_data in data.items():
        controlling_power = system_data.ControllingPower
        opposition = ", ".join(system_data.Opposition) if system_data.Opposition else ""
        progress = system_data.getSystemProgressNumber()
        state_text = system_data.getSystemStateText()

        # Determine status tag
        if controlling_power == "no power":
            base_tag = 'neutral'
        else:
            display_progress = progress - 100 if progress > 100 and state_text != "Stronghold" else progress
            if 0 <= display_progress < 20:
                base_tag = 'danger'
            elif 20 <= display_progress < 80:
                base_tag = 'safe'
            elif display_progress >= 80:
                base_tag = 'safe' if state_text == "Stronghold" else 'warning'
            else:
                base_tag = 'neutral'

        # Alternate between normal and _alt tag for zebra striping
        tag = base_tag if row_index % 2 == 0 else f"{base_tag}_alt"

        if not system_data.PowerplayConflictProgress or len(system_data.PowerplayConflictProgress) == 0:
            power_status = system_data.getPowerPlayCycleNetStatusText()
            reinforcement = system_data.PowerplayStateReinforcement
            undermining = system_data.PowerplayStateUndermining
        else:
            power_status = "Conflict"
            reinforcement = "-"
            undermining = "-"

        tree.insert("", "end", values=(
            system_name,
            state_text,
            f"{progress:.1f}%",
            controlling_power,
            power_status,
            reinforcement,
            undermining,
            opposition
        ), tags=(tag,))
        row_index += 1


# ============================================================
# Backpack View Window
# ============================================================

backpack_window = None


def show_backpack_view(parent):
    """Show backpack contents in a new window with three tables for UM, ACQ, and Reinforcement"""
    global backpack_window
    from emt_models.backpack import playerBackpack
    from emt_ppdata.undermining import get_um_display_name
    from emt_ppdata.reinforcement import get_reinf_display_name
    from emt_ppdata.acquisition import get_acq_display_name

    # Close existing window if open
    if backpack_window and backpack_window.winfo_exists():
        backpack_window.lift()
        return

    colors = get_theme_colors()

    backpack_window = tk.Toplevel(parent)
    backpack_window.title("Shiplocker - Elite Merit Tracker")
    backpack_window.geometry("1200x800")
    backpack_window.configure(background=colors['bg'])

    # Main container
    main_frame = tk.Frame(backpack_window, background=colors['bg'])
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Top button frame
    button_frame = tk.Frame(main_frame, background=colors['bg'])
    button_frame.pack(side="top", fill="x", pady=(0, 10))

    # Return to Overview button
    return_button = RoundedButton(button_frame, "Return to Overview",
                                   lambda: backpack_window.destroy() if backpack_window else None,
                                   colors, width=140, height=28, radius=6)
    return_button.pack(side="left", padx=5)

    def on_close():
        global backpack_window
        if backpack_window and backpack_window.winfo_exists():
            backpack_window.destroy()
        backpack_window = None

    backpack_window.protocol("WM_DELETE_WINDOW", on_close)

    # Create scrollable canvas
    canvas = tk.Canvas(main_frame, highlightthickness=0, background=colors['bg'])
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Content frame inside canvas
    content_frame = tk.Frame(canvas, background=colors['bg'])
    canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")

    def update_scrollregion(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def resize_content_frame(event):
        canvas.itemconfig(canvas_window, width=event.width)

    content_frame.bind("<Configure>", update_scrollregion)
    canvas.bind("<Configure>", resize_content_frame)
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1*(event.delta//120), "units"))

    # Helper function to create a table
    def create_backpack_table(parent_frame, title, bag, display_name_func):
        """Create a treeview table for a bag type"""
        frame = tk.Frame(parent_frame, background=colors['bg'])
        frame.pack(fill="both", expand=True, pady=10)

        # Title
        title_label = tk.Label(frame, text=title, font=("Helvetica", 14, "bold"),
                               background=colors['bg'], foreground=colors['fg'])
        title_label.pack(anchor="w", pady=(0, 5))

        # Treeview
        tree_frame = tk.Frame(frame, background=colors['bg'])
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(tree_frame, columns=("System", "Count", "Data Type"),
                           show="headings", height=8)

        # Sorting state for this tree
        tree.sort_column = None
        tree.sort_reverse = False

        def sort_by_column(col, col_index):
            """Sort tree contents when a column header is clicked"""
            # Toggle sort direction if clicking same column
            if tree.sort_column == col:
                tree.sort_reverse = not tree.sort_reverse
            else:
                tree.sort_reverse = False
            tree.sort_column = col

            # Get all items with their values
            items = [(tree.item(item)["values"], item) for item in tree.get_children("")]

            # Sort based on column
            if col_index == 1:  # Count - numeric sort
                items.sort(key=lambda x: int(x[0][col_index]) if x[0][col_index] and str(x[0][col_index]).strip() else 0,
                          reverse=tree.sort_reverse)
            else:  # System and Data Type - string sort
                items.sort(key=lambda x: str(x[0][col_index]).lower(), reverse=tree.sort_reverse)

            # Rearrange items in sorted order
            for index, (values, item) in enumerate(items):
                tree.move(item, "", index)

                # Update alternating row colors
                tag = "even" if index % 2 == 0 else "odd"
                tree.item(item, tags=(tag,))

        # Configure columns with sorting
        tree.heading("System", text="System", anchor="w",
                    command=lambda: sort_by_column("System", 0))
        tree.heading("Count", text="Count (double-click to edit)", anchor="center",
                    command=lambda: sort_by_column("Count", 1))
        tree.heading("Data Type", text="Data Type", anchor="w",
                    command=lambda: sort_by_column("Data Type", 2))

        tree.column("System", width=300, anchor="w")
        tree.column("Count", width=100, anchor="center")
        tree.column("Data Type", width=250, anchor="w")

        # Scrollbar for table
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

        # Populate table
        row_index = 0
        for data_type, systems_dict in sorted(bag.items.items()):
            for system_name, count in sorted(systems_dict.items()):
                display_name = display_name_func(data_type)
                tag = "even" if row_index % 2 == 0 else "odd"
                tree.insert("", "end", values=(system_name, count, display_name),
                           tags=(tag,))
                row_index += 1

        # Configure row tags for alternating colors with better contrast
        tree.tag_configure("even", background=colors['table_row_even'], foreground=colors['fg'])
        tree.tag_configure("odd", background=colors['table_row_odd'], foreground=colors['fg'])

        # Change cursor to indicate editable Count column
        def on_motion(event):
            region = tree.identify_region(event.x, event.y)
            column = tree.identify_column(event.x)
            if region == "cell" and column == "#2":  # Count column
                tree.config(cursor="hand2")
            else:
                tree.config(cursor="")

        tree.bind("<Motion>", on_motion)

        # Add double-click to edit Count
        def on_double_click(event):
            item = tree.selection()
            if not item:
                return

            # Get the clicked column
            column = tree.identify_column(event.x)
            if column != "#2":  # Only allow editing Count column
                return

            # Get item values
            values = tree.item(item[0], "values")
            system_name = values[0]
            data_type_display = values[2]

            # Find the actual data_type key from display name
            data_type_key = None
            for dt_key, systems_dict in bag.items.items():
                if system_name in systems_dict and display_name_func(dt_key) == data_type_display:
                    data_type_key = dt_key
                    break

            if not data_type_key:
                return

            # Create entry widget for editing
            bbox = tree.bbox(item[0], column)
            if not bbox:
                return

            entry = tk.Entry(tree, justify="center")
            entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

            # Get current count value
            current_value = bag.items[data_type_key].get(system_name, 0)
            entry.insert(0, str(current_value) if current_value > 0 else "")
            entry.focus()
            entry.select_range(0, tk.END)

            def save_edit(event=None):
                try:
                    new_value = entry.get().strip()
                    int_value = int(new_value) if new_value else 0

                    # Update count
                    if int_value > 0:
                        bag.items[data_type_key][system_name] = int_value
                        # Update tree display
                        tree.item(item[0], values=(system_name, int_value, data_type_display))
                    else:
                        # Remove entry if count is 0
                        if system_name in bag.items[data_type_key]:
                            del bag.items[data_type_key][system_name]
                        # If no systems left, remove the data type
                        if not bag.items[data_type_key]:
                            del bag.items[data_type_key]
                        # Remove the row
                        tree.delete(item[0])

                    # Update total
                    total = bag.get_total()
                    total_label.config(text=f"Total: {total} items")

                    # Save to JSON
                    from emt_models.backpack import save_backpack
                    save_backpack()
                except ValueError:
                    pass  # Invalid input, ignore
                finally:
                    entry.destroy()

            def cancel_edit(event=None):
                entry.destroy()

            entry.bind("<Return>", save_edit)
            entry.bind("<FocusOut>", save_edit)
            entry.bind("<Escape>", cancel_edit)

        tree.bind("<Double-Button-1>", on_double_click)

        # Add "Add New Entry" button below table
        add_button_frame = tk.Frame(frame, background=colors['bg'])
        add_button_frame.pack(fill="x", pady=(5, 0))

        def add_new_entry():
            """Add a new entry to the backpack"""
            # Create a dialog to get system name and data type
            dialog = tk.Toplevel(backpack_window)
            dialog.title("Add New Entry")
            dialog.geometry("400x250")
            dialog.configure(background=colors['bg'])
            dialog.transient(backpack_window)
            dialog.grab_set()

            # Center the dialog
            dialog.update_idletasks()
            x = backpack_window.winfo_x() + (backpack_window.winfo_width() // 2) - (dialog.winfo_width() // 2)
            y = backpack_window.winfo_y() + (backpack_window.winfo_height() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")

            tk.Label(dialog, text="System Name:", background=colors['bg'], foreground=colors['fg']).pack(pady=(10, 5))
            system_entry = tk.Entry(dialog, width=40)
            system_entry.pack(pady=5)
            system_entry.focus()

            tk.Label(dialog, text="Data Type:", background=colors['bg'], foreground=colors['fg']).pack(pady=(10, 5))

            # Get available data types for this bag
            if bag.name == "undermining":
                from emt_ppdata.undermining import VALID_UNDERMINING_DATA_TYPES
                data_types = VALID_UNDERMINING_DATA_TYPES
            elif bag.name == "reinforcement":
                from emt_ppdata.reinforcement import VALID_REINFORCEMENT_DATA_TYPES
                data_types = VALID_REINFORCEMENT_DATA_TYPES
            else:  # acquisition
                from emt_ppdata.acquisition import VALID_ACQUISITION_DATA_TYPES
                data_types = VALID_ACQUISITION_DATA_TYPES

            data_type_var = tk.StringVar(dialog)
            data_type_var.set(list(data_types.keys())[0])  # Default to first option
            data_type_dropdown = ttk.Combobox(dialog, textvariable=data_type_var,
                                             values=list(data_types.keys()), width=37, state="readonly")
            data_type_dropdown.pack(pady=5)

            tk.Label(dialog, text="Count:", background=colors['bg'], foreground=colors['fg']).pack(pady=(10, 5))
            count_entry = tk.Entry(dialog, width=40)
            count_entry.insert(0, "1")
            count_entry.pack(pady=5)

            def save_new_entry():
                system_name = system_entry.get().strip()
                data_type = data_type_var.get()
                try:
                    count = int(count_entry.get().strip())
                    if system_name and count > 0:
                        # Add to bag
                        bag.add_item(data_type, count, system_name)

                        # Add to tree
                        display_name = display_name_func(data_type)
                        row_index = len(tree.get_children(""))
                        tag = "even" if row_index % 2 == 0 else "odd"
                        tree.insert("", "end", values=(system_name, count, display_name),
                                   tags=(tag,))

                        # Update total
                        total = bag.get_total()
                        total_label.config(text=f"Total: {total} items")

                        # Save to JSON
                        from emt_models.backpack import save_backpack
                        save_backpack()

                        dialog.destroy()
                except ValueError:
                    pass  # Invalid count

            def cancel_new_entry():
                dialog.destroy()

            button_frame = tk.Frame(dialog, background=colors['bg'])
            button_frame.pack(pady=20)

            save_btn = RoundedButton(button_frame, "Add", save_new_entry, colors, width=80, height=28, radius=6)
            save_btn.pack(side="left", padx=5)

            cancel_btn = RoundedButton(button_frame, "Cancel", cancel_new_entry, colors, width=80, height=28, radius=6)
            cancel_btn.pack(side="left", padx=5)

            # Bind Enter to save
            system_entry.bind("<Return>", lambda e: count_entry.focus())
            count_entry.bind("<Return>", lambda e: save_new_entry())
            dialog.bind("<Escape>", lambda e: cancel_new_entry())

        add_button = RoundedButton(add_button_frame, "+ Add New Entry", add_new_entry, colors, width=120, height=28, radius=6)
        add_button.pack(side="left", pady=5)

        # Total label
        total = bag.get_total()
        total_label = tk.Label(add_button_frame, text=f"Total: {total} items",
                              font=("Helvetica", 10, "bold"),
                              background=colors['bg'], foreground=colors['fg'])
        total_label.pack(side="right", pady=5)

        return tree

    def create_salvage_table(parent_frame, title, colors):
        """Create a treeview table for salvage items (PowerPlay Item-type materials)"""
        from emt_models.salvage import salvageInventory, VALID_POWERPLAY_SALVAGE_TYPES, save_salvage

        frame = tk.Frame(parent_frame, background=colors['bg'])
        frame.pack(fill="both", expand=True, pady=10)

        # Title
        title_label = tk.Label(frame, text=title, font=("Helvetica", 14, "bold"),
                               background=colors['bg'], foreground=colors['fg'])
        title_label.pack(anchor="w", pady=(0, 5))

        # Treeview
        tree_frame = tk.Frame(frame, background=colors['bg'])
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(tree_frame, columns=("System", "Item Type", "Count"),
                           show="headings", height=8)

        # Sorting state for this tree
        tree.sort_column = None
        tree.sort_reverse = False

        def sort_by_column(col, col_index):
            """Sort tree contents when a column header is clicked"""
            # Toggle sort direction if clicking same column
            if tree.sort_column == col:
                tree.sort_reverse = not tree.sort_reverse
            else:
                tree.sort_reverse = False
            tree.sort_column = col

            # Get all items with their values
            items = [(tree.item(item)["values"], item) for item in tree.get_children("")]

            # Sort based on column
            if col_index == 2:  # Count - numeric sort
                items.sort(key=lambda x: int(x[0][col_index]) if x[0][col_index] and str(x[0][col_index]).strip() else 0,
                          reverse=tree.sort_reverse)
            else:  # System and Item Type - string sort
                items.sort(key=lambda x: str(x[0][col_index]).lower(), reverse=tree.sort_reverse)

            # Rearrange items in sorted order
            for index, (values, item) in enumerate(items):
                tree.move(item, "", index)

                # Update alternating row colors
                tag = "even" if index % 2 == 0 else "odd"
                tree.item(item, tags=(tag,))

        # Configure columns with sorting
        tree.heading("System", text="System", anchor="w",
                    command=lambda: sort_by_column("System", 0))
        tree.heading("Item Type", text="Item Type", anchor="w",
                    command=lambda: sort_by_column("Item Type", 1))
        tree.heading("Count", text="Count (double-click to edit)", anchor="center",
                    command=lambda: sort_by_column("Count", 2))

        tree.column("System", width=300, anchor="w")
        tree.column("Item Type", width=300, anchor="w")
        tree.column("Count", width=100, anchor="center")

        # Scrollbar for table
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

        # Populate table
        row_index = 0
        total_items = 0
        for system_name, salvage in sorted(salvageInventory.items()):
            for item_type, cargo in sorted(salvage.inventory.items()):
                count = cargo.count
                if count > 0:
                    display_name = VALID_POWERPLAY_SALVAGE_TYPES.get(item_type, item_type)
                    tag = "even" if row_index % 2 == 0 else "odd"
                    tree.insert("", "end", values=(system_name, display_name, count),
                               tags=(tag,))
                    total_items += count
                    row_index += 1

        # Configure row tags for alternating colors
        tree.tag_configure("even", background=colors['table_row_even'], foreground=colors['fg'])
        tree.tag_configure("odd", background=colors['table_row_odd'], foreground=colors['fg'])

        # Change cursor to indicate editable Count column
        def on_motion(event):
            region = tree.identify_region(event.x, event.y)
            column = tree.identify_column(event.x)
            if region == "cell" and column == "#3":  # Count column
                tree.config(cursor="hand2")
            else:
                tree.config(cursor="")

        tree.bind("<Motion>", on_motion)

        # Add double-click to edit Count
        def on_double_click(event):
            item = tree.selection()
            if not item:
                return

            # Get the clicked column
            column = tree.identify_column(event.x)
            if column != "#3":  # Only allow editing Count column
                return

            # Get item values
            values = tree.item(item[0], "values")
            system_name = values[0]
            item_type_display = values[1]

            # Find the actual item_type key from display name
            item_type_key = None
            for salvage in salvageInventory.values():
                for it_key, cargo in salvage.inventory.items():
                    if VALID_POWERPLAY_SALVAGE_TYPES.get(it_key) == item_type_display:
                        item_type_key = it_key
                        break
                if item_type_key:
                    break

            if not item_type_key or system_name not in salvageInventory:
                return

            # Create entry widget for editing
            bbox = tree.bbox(item[0], column)
            if not bbox:
                return

            entry = tk.Entry(tree, justify="center")
            entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

            # Get current count value
            current_value = salvageInventory[system_name].inventory.get(item_type_key)
            count = current_value.count if current_value else 0
            entry.insert(0, str(count) if count > 0 else "")
            entry.focus()
            entry.select_range(0, tk.END)

            def save_edit(event=None):
                try:
                    new_value = entry.get().strip()
                    int_value = int(new_value) if new_value else 0

                    # Update count
                    if int_value > 0:
                        if item_type_key in salvageInventory[system_name].inventory:
                            salvageInventory[system_name].inventory[item_type_key].count = int_value
                        else:
                            from emt_models.ppcargo import Cargo
                            salvageInventory[system_name].inventory[item_type_key] = Cargo(item_type_key)
                            salvageInventory[system_name].inventory[item_type_key].count = int_value
                        # Update tree display
                        tree.item(item[0], values=(system_name, item_type_display, int_value))
                    else:
                        # Remove entry if count is 0
                        if item_type_key in salvageInventory[system_name].inventory:
                            del salvageInventory[system_name].inventory[item_type_key]
                        # If no items left in system, remove the system
                        if not salvageInventory[system_name].inventory:
                            del salvageInventory[system_name]
                        # Remove the row
                        tree.delete(item[0])

                    # Update total
                    new_total = sum(
                        cargo.count
                        for salvage in salvageInventory.values()
                        for cargo in salvage.inventory.values()
                    )
                    total_label.config(text=f"Total: {new_total} items")

                    # Save to JSON
                    save_salvage()
                except ValueError:
                    pass  # Invalid input, ignore
                finally:
                    entry.destroy()

            def cancel_edit(event=None):
                entry.destroy()

            entry.bind("<Return>", save_edit)
            entry.bind("<FocusOut>", save_edit)
            entry.bind("<Escape>", cancel_edit)

        tree.bind("<Double-Button-1>", on_double_click)

        # Add "Add New Entry" button below table
        add_button_frame = tk.Frame(frame, background=colors['bg'])
        add_button_frame.pack(fill="x", pady=(5, 0))

        def add_new_entry():
            """Add a new salvage entry"""
            # Create a dialog to get system name and item type
            dialog = tk.Toplevel(backpack_window)
            dialog.title("Add New Salvage Entry")
            dialog.geometry("400x250")
            dialog.configure(background=colors['bg'])
            dialog.transient(backpack_window)
            dialog.grab_set()

            # Center the dialog
            dialog.update_idletasks()
            x = backpack_window.winfo_x() + (backpack_window.winfo_width() // 2) - (dialog.winfo_width() // 2)
            y = backpack_window.winfo_y() + (backpack_window.winfo_height() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")

            tk.Label(dialog, text="System Name:", background=colors['bg'], foreground=colors['fg']).pack(pady=(10, 5))
            system_entry = tk.Entry(dialog, width=40)
            system_entry.pack(pady=5)
            system_entry.focus()

            tk.Label(dialog, text="Item Type:", background=colors['bg'], foreground=colors['fg']).pack(pady=(10, 5))

            # Get PowerPlay salvage types (filter out legacy salvage types)
            power_salvage_types = {k: v for k, v in VALID_POWERPLAY_SALVAGE_TYPES.items()
                                  if k.startswith('power')}

            item_type_var = tk.StringVar(dialog)
            item_type_var.set(list(power_salvage_types.keys())[0])  # Default to first option
            item_type_dropdown = ttk.Combobox(dialog, textvariable=item_type_var,
                                             values=list(power_salvage_types.keys()), width=37, state="readonly")
            item_type_dropdown.pack(pady=5)

            tk.Label(dialog, text="Count:", background=colors['bg'], foreground=colors['fg']).pack(pady=(10, 5))
            count_entry = tk.Entry(dialog, width=40)
            count_entry.insert(0, "1")
            count_entry.pack(pady=5)

            def save_new_entry():
                system_name = system_entry.get().strip()
                item_type = item_type_var.get()
                try:
                    count = int(count_entry.get().strip())
                    if system_name and count > 0:
                        # Add to salvage inventory
                        from emt_models.salvage import Salvage
                        if system_name not in salvageInventory:
                            salvageInventory[system_name] = Salvage(system_name)

                        salvageInventory[system_name].add_cargo(item_type, count)

                        # Add to tree
                        display_name = VALID_POWERPLAY_SALVAGE_TYPES.get(item_type, item_type)
                        row_index = len(tree.get_children(""))
                        tag = "even" if row_index % 2 == 0 else "odd"
                        tree.insert("", "end", values=(system_name, display_name, count),
                                   tags=(tag,))

                        # Update total
                        new_total = sum(
                            cargo.count
                            for salvage in salvageInventory.values()
                            for cargo in salvage.inventory.values()
                        )
                        total_label.config(text=f"Total: {new_total} items")

                        # Save to JSON
                        save_salvage()

                        dialog.destroy()
                except ValueError:
                    pass  # Invalid count

            def cancel_new_entry():
                dialog.destroy()

            button_frame = tk.Frame(dialog, background=colors['bg'])
            button_frame.pack(pady=20)

            save_btn = RoundedButton(button_frame, "Add", save_new_entry, colors, width=80, height=28, radius=6)
            save_btn.pack(side="left", padx=5)

            cancel_btn = RoundedButton(button_frame, "Cancel", cancel_new_entry, colors, width=80, height=28, radius=6)
            cancel_btn.pack(side="left", padx=5)

            # Bind Enter to save
            system_entry.bind("<Return>", lambda e: count_entry.focus())
            count_entry.bind("<Return>", lambda e: save_new_entry())
            dialog.bind("<Escape>", lambda e: cancel_new_entry())

        add_button = RoundedButton(add_button_frame, "+ Add New Entry", add_new_entry, colors, width=120, height=28, radius=6)
        add_button.pack(side="left", pady=5)

        # Total label
        total_label = tk.Label(add_button_frame, text=f"Total: {total_items} items",
                              font=("Helvetica", 10, "bold"),
                              background=colors['bg'], foreground=colors['fg'])
        total_label.pack(side="right", pady=5)

        return tree

    # Create three tables (Reinforcement, Acquisition, Undermining)
    create_backpack_table(content_frame, "Reinforcement Data",
                         playerBackpack.reinfbag, get_reinf_display_name)

    create_backpack_table(content_frame, "Acquisition Data (ACQ)",
                         playerBackpack.acqbag, get_acq_display_name)

    create_backpack_table(content_frame, "Undermining Data (UM)",
                         playerBackpack.umbag, get_um_display_name)

    # Create salvage table for PowerPlay Item-type materials
    create_salvage_table(content_frame, "PowerPlay Items (Salvage)", colors)

    # Apply theme
    apply_theme_to_widget(backpack_window, colors)
