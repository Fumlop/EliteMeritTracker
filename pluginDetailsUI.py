import tkinter as tk
from tkinter import ttk, filedialog
import csv

from config import config, appname
from theme import theme
from report import Report, report
from system import systems
from power import pledgedPower
from pluginConfig import configPlugin
from merit_log import logger, plugin_name
from typing import Dict, Any, List, Optional

# Global GUI variables
data_frame_default = None
data_frame_detailed = None
detailed_view = False
toggle_button = None
csv_button = None
copy_all_button = None
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
            from load import this
            if this.currentSystemFlying and this.currentSystemFlying.StarSystem == system_name:
                main_tracker_frame.update_display(this.currentSystemFlying)


def toggle_view():
    global detailed_view, csv_button, copy_all_button, systems, pledgedPower

    # Check if window still exists
    if info_window is None or not info_window.winfo_exists():
        return

    detailed_view = not detailed_view

    toggle_button.config(text="Show Default View" if detailed_view else "Show Detailed View")

    for widget in table_frame.winfo_children():
        widget.destroy()

    if detailed_view:
        csv_button.grid(row=0, column=1, padx=5)
        copy_all_button.grid_forget()
    else:
        csv_button.grid_forget()
        copy_all_button.grid(row=0, column=2, padx=5)
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
        return {
            'bg': bg,
            'fg': theme.current.get('foreground', '#ff8c00'),
            'active_bg': theme.current.get('activebackground', '#000000'),
            'active_fg': theme.current.get('activeforeground', '#ff8c00'),
            'highlight': theme.current.get('highlight', '#ff8c00'),
            'button_bg': get_button_bg(bg),
        }
    except Exception:
        return {
            'bg': '#000000',
            'fg': '#ff8c00',
            'active_bg': '#000000',
            'active_fg': '#ff8c00',
            'highlight': '#ff8c00',
            'button_bg': '#1a1a1a',
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
    global table_frame, toggle_button, csv_button, copy_all_button, detailed_view, filter_frame
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

    copy_all_button = RoundedButton(button_frame, "Copy All Systems", copy_all_systems_to_clipboard_or_report, colors, width=130, height=28, radius=6)
    copy_all_button.grid(row=0, column=2, padx=5, pady=3)

    # Scrollable content area
    canvas = tk.Canvas(main_frame, highlightthickness=0, background=colors['bg'])
    canvas.pack(side="left", fill="both", expand=True)

    v_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    v_scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=v_scrollbar.set)
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1*(event.delta//120), "units"))

    def on_close():
        global info_window
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
            dcText = f"{configPlugin.copyText.get().replace('@MeritsValue', merits).replace('@System', system_name)}"
            if '@CPOpposition' in dcText:
                dcText = dcText.replace('@CPOpposition', f"Opposition {str(system_data.PowerplayStateUndermining)}")
            if '@CPControlling' in dcText:
                dcText = dcText.replace('@CPControlling', f"{system_data.ControllingPower} {str(system_data.PowerplayStateReinforcement)}")
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
    global detailed_view, data_frame_default, systems, pledgedPower, treeview

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
            ("System", 250, "w"),       # Left align (first column) - wider for long system names
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
            dcText = configPlugin.copyText.get().replace('@MeritsValue', str(merits)).replace('@System', system_name)
            if '@CPOpposition' in dcText:
                dcText = dcText.replace('@CPOpposition', f"Opposition {str(system_data.PowerplayStateUndermining)}")
            if '@CPControlling' in dcText:
                dcText = dcText.replace('@CPControlling', f"{system_data.ControllingPower} {str(system_data.PowerplayStateReinforcement)}")

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
