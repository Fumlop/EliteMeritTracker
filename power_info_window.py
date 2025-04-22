from imports import *
from report import Report
filter_power_var = None
filter_system_var = None
filter_state_var = None
filter_frame = None
data_frame_default = None
data_frame_detailed = None
header_frame_default = None
update_scrollregion = None

report = Report()
pledgedPower = None
systems = None

def copy_to_clipboard_or_report(text):
    global report
    if configPlugin.discordHook:
        report.send_to_discord(text)
    else:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()

def delete_entry(system_name, table_frame, update_scrollregion):
    global data_frame_default, data_frame_detailed, detailed_view,systems, pledgedPower

    if system_name in systems:
        systems[system_name].Merits = 0

        if detailed_view and data_frame_detailed:
            for widget in data_frame_detailed.winfo_children():
                widget.destroy()
        elif not detailed_view and data_frame_default:
            for widget in data_frame_default.winfo_children():
                widget.destroy()

        populate_table(table_frame, update_scrollregion)

def toggle_view():
    global detailed_view, csv_button, systems, pledgedPower

    detailed_view = not detailed_view  # Switch between views

    # Update button text
    toggle_button.config(text="Show Default View" if detailed_view else "Show Detailed View")

    # Clear the current table (but NOT the parent window)
    for widget in table_frame.winfo_children():
        widget.destroy()

    # Show CSV Export button only in detailed view
    if detailed_view:
        csv_button.grid(row=0, column=2, padx=10, pady=5, sticky="w")
    else:
        csv_button.grid_forget()

    # Show headers only in default view
    if not detailed_view:
        add_power_info_headers()

    # Repopulate the table
    table_frame.after(100, lambda: populate_table(table_frame, update_scrollregion))

def save_window_size(info_window):
    w = info_window.winfo_width()
    h = info_window.winfo_height()
    config.set("power_info_width", str(w))
    config.set("power_info_height", str(h))

def export_to_csv():
    """
    Exports the system data in detailed view to a user-selected CSV file.
    """
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")],
        title="Save CSV File"
    )

    if not file_path:  # User canceled
        return

    headers = ["System", "Status", "Controlling Power", "Powerplay Cycle","Reinforcement", "Undermining","Opposition" ]
    
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file,delimiter=";")
        writer.writerow(headers)  # Write headers
        for system_name, system_data in systems.items():
            state = system_data.PowerplayState
            progress = system_data.getSystemProgressNumber()
            controlling_power = system_data.ControllingPower
            opposition = system_data.Opposition
            reinforcement = system_data.PowerplayStateReinforcement
            undermining = system_data.PowerplayStateUndermining
            power_status =system_data.getPowerPlayCycleNetStatusText()

            writer.writerow([system_name, f"{state} ({progress:.2f}%)", controlling_power, power_status, reinforcement, undermining, opposition ])

    print(f"CSV export successful: {file_path}")  # Debug log (replace with a messagebox if needed)

def show_power_info(parent, pp, sy):
    global table_frame, toggle_button, csv_button, detailed_view, filter_frame, data_frame, systems, pledgedPower, update_scrollregion
    update_scrollregion = lambda event=None: canvas.configure(scrollregion=canvas.bbox("all"))
    
    pledgedPower = pp
    systems = sy

    detailed_view = False  

    info_window = tk.Toplevel(parent)
    info_window.title("Power Info")
    saved_width = str(configPlugin.power_info_width) or "1280"
    saved_height = str(configPlugin.power_info_height) or "800"
    info_window.geometry(f"{saved_width}x{saved_height}")

    main_frame = tk.Frame(info_window)
    main_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(main_frame)
    canvas.pack(side="left", fill="both", expand=True)

    v_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    v_scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=v_scrollbar.set)
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1*(event.delta//120), "units"))

    info_window.protocol("WM_DELETE_WINDOW", lambda: (save_window_size(info_window), info_window.destroy()))
    
    table_frame = tk.Frame(canvas)
    for i in range(6):  # 6 Spalten, falls mehr, erhöhe die Zahl
        table_frame.columnconfigure(i, weight=1)
    canvas.create_window((0, 0), window=table_frame, anchor="nw")

    def update_scrollregion(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    table_frame.bind("<Configure>", update_scrollregion)
    
    # Zeige Powerplay-Details in Default View
    if not detailed_view:
        add_power_info_headers()


    button_frame = tk.Frame(info_window)
    button_frame.pack(side="top", pady=5, anchor="center")  # Buttons mittig ausrichten

    toggle_button = tk.Button(button_frame, text="Show Detailed View", command=lambda: toggle_view())
    toggle_button.grid(row=0, column=0, padx=5)

    csv_button = tk.Button(button_frame, text="Export CSV", command=export_to_csv)
    csv_button.grid(row=0, column=1, padx=5)
    csv_button.grid_forget()  # Erst in detailed_view anzeigen
    populate_table(table_frame, update_scrollregion)
    
def add_power_info_headers():
    global systems, pledgedPower
    if detailed_view:
        return  # Do not show headers in Detailed View

    tk.Label(table_frame, text="Powerplay Details", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=6, pady=10, sticky="w")

    tk.Label(table_frame, text=f"Power name: {pledgedPower.Power}", anchor="w").grid(row=1, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Rank: {pledgedPower.Rank}", anchor="w").grid(row=2, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Current merits: {pledgedPower.Merits}", anchor="w").grid(row=3, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Time pledged: {pledgedPower.TimePledgedStr}", anchor="w").grid(row=4, column=0, columnspan=6, sticky="w", padx=10)


def populate_table(table_frame, update_scrollregion, show_filters_only=False):
    global detailed_view, data_frame_default,systems, pledgedPower

    if configPlugin.discordHook:
        textCopyReport = "report"
        textCopyReportHeader = "Report to discord"
    else:
        textCopyReport = "copy"
        textCopyReportHeader = "Copy to clipboard"

    if detailed_view:
        headers = ["System", "Status", "Controlling Power", "Powerplay Cycle", "Reinforcement", "Undermining","Opposition" ]
        col_widths = [30, 20, 25, 15, 15, 15, 25]
        header_row = 6
        filter_row = 7
        data_start_row = 8
    else:
        headers = ["System name", "Session merits", textCopyReportHeader, "", "Text", ""]
        col_widths = [30, 15, 15, 10, 10, 60]
        header_row = 0
        data_start_row = 7

    # Header erzeugen
    if (detailed_view):
        for col, (header, width) in enumerate(zip(headers, col_widths)):
            tk.Label(table_frame, text=header, width=width, anchor="w", font=("Arial", 10, "bold")).grid(
                row=header_row, column=col, padx=5, pady=2, sticky="w"
            )

    # ----- DETAILED VIEW -----
    if detailed_view:
        # Filterzeile (unter Header)
        add_detailed_view_filter_buttons(table_frame)

        # alte Datenzeilen entfernen (ab Zeile data_start_row)
        for widget in table_frame.grid_slaves():
            row = int(widget.grid_info()["row"])
            if row >= data_start_row:
                widget.destroy()

        if show_filters_only:
            return

        populate_table_data_rows(table_frame, systems, data_start_row)
        return

    # ----- DEFAULT VIEW -----
    if data_frame_default:
        data_frame_default.destroy()

    data_frame_default = tk.Frame(table_frame)
    data_frame_default.grid(row=data_start_row, column=0, columnspan=6, sticky="w")

    for i, width in enumerate(col_widths):
        data_frame_default.columnconfigure(i, weight=1, minsize=width * 7)

    row_index = 1
    created_widgets = []
    for col, (header, width) in enumerate(zip(headers, col_widths)):
        label = tk.Label(data_frame_default, text=header, width=width, anchor="w", font=("Arial", 12, "bold"))
        label.grid(row=header_row, column=col, padx=5, pady=2, sticky="w")
        label.grid_remove()
        created_widgets.append(label)
    for system_name, system_data in systems.items():
        merits = str(system_data.Merits)

        if int(merits) > 0:
            dcText = f"{configPlugin.copyText.replace('@MeritsValue', merits).replace('@System', system_name)}"
            if '@CPOpposition' in dcText:
                dcText = dcText.replace('@CPOpposition', str(system_data.PowerplayStateUndermining))

            if '@CPPledged' in dcText:
                dcText = dcText.replace('@CPPledged', str(system_data.PowerplayStateReinforcement))

            widgets = [
                tk.Label(data_frame_default, text=system_name, width=15, anchor="w"),
                tk.Label(data_frame_default, text=f"{merits}", width=15, anchor="w"),
                tk.Button(data_frame_default, text=textCopyReport, command=lambda text=dcText: copy_to_clipboard_or_report(text)),
                tk.Label(data_frame_default, text=dcText, width=45, anchor="w", justify="left", wraplength=300),
                tk.Button(data_frame_default, text="Delete", command=lambda name=system_name: delete_entry(name, table_frame, update_scrollregion)),
            ]

            for col, widget in enumerate(widgets):
                widget.grid(row=row_index, column=col, padx=5, pady=2, sticky="w")
                widget.grid_remove()
                created_widgets.append(widget)

            row_index += 1

    # Alles am Ende sichtbar machen
    for widget in created_widgets:
        widget.grid()
        
def add_detailed_view_filter_buttons(parent_frame):
    global filter_power_var, filter_system_var, filter_state_var, filter_frame,systems, pledgedPower

    if filter_frame:
        filter_frame.destroy()

    filter_frame = tk.Frame(parent_frame)
    filter_frame.grid(row=8, column=0, columnspan=6, sticky="w", padx=10)  # Linksbündig setzen
    for i in range(6):  # 6 Spalten anpassen
        filter_frame.columnconfigure(i, weight=1)
    powers = sorted({data.ControllingPower for data in systems.values() if data.ControllingPower})
    states = sorted({data.PowerplayState for data in systems.values() if data.PowerplayState})

    system_names = sorted(systems.keys())

    filter_system_var = tk.StringVar(value="All")
    filter_state_var = tk.StringVar(value="All")
    filter_power_var = tk.StringVar(value="All")

    # System Filter (1. Spalte)
    tk.OptionMenu(table_frame, filter_system_var, *(["All"] + system_names)).grid(
        row=7, column=0, padx=5, pady=2, sticky="w"
    )

    # Status Filter (2. Spalte)
    tk.OptionMenu(table_frame, filter_state_var, *(["All"] + states)).grid(
        row=7, column=1, padx=5, pady=2, sticky="w"
    )

    # Power Filter (3. Spalte)
    tk.OptionMenu(table_frame, filter_power_var, *(["All"] + powers)).grid(
        row=7, column=2, padx=5, pady=2, sticky="w"
    )

    for var in [filter_system_var, filter_state_var, filter_power_var]:
        var.trace_add("write", lambda *args: refresh_filtered_table())

def refresh_filtered_table():
    global table_frame,systems, pledgedPower

    selected_system = filter_system_var.get()
    selected_state = filter_state_var.get()
    selected_power = filter_power_var.get()

    filtered = {}
    for name, data in systems.items():
        if selected_system != "All" and name != selected_system:
            continue
        if selected_state != "All" and data.PowerplayState != selected_state:
            continue
        if selected_power != "All" and data.ControllingPower != selected_power:
            continue
        filtered[name] = data

    for widget in table_frame.grid_slaves():
        row = int(widget.grid_info()["row"])
        if row >= 8:
            widget.destroy()

    populate_table_data_rows(table_frame, filtered, start_row=8)

def populate_table_data_rows(parent, filtered, start_row=8):
    global systems, pledgedPower
    for i in range(6):
        parent.columnconfigure(i, weight=1)

    row_index = start_row
    created_widgets = []  # Sammle Widgets für spätere Anzeige

    for system_name, system_data in filtered.items():
        
        controlling_power = system_data.ControllingPower
        opposition = ", ".join(system_data.Opposition)
        progress = system_data.getSystemProgressNumber()
        state = f"{(system_data.PowerplayState)} ({progress:.2f}%)"
        if not system_data.PowerplayConflictProgress or len(system_data.PowerplayConflictProgress)==0:
            power_status = system_data.getPowerPlayCycleNetStatusText()
            reinforcement = system_data.PowerplayStateReinforcement
            undermining = system_data.PowerplayStateUndermining
        else:
            power_status = ""
            reinforcement = 0
            undermining = 0
        reinforce_font = ("Arial", 10, "bold") if "NET +" in power_status else ("Arial", 10, "normal")
        undermining_font = ("Arial", 10, "bold") if "NET -" in power_status else ("Arial", 10, "normal")
        # Labels vorerst unsichtbar setzen (grid, dann remove)
        widgets = [
            tk.Label(parent, text=system_name, width=20, anchor="w"),
            tk.Label(parent, text=state, width=20, anchor="w"),
            tk.Label(parent, text=controlling_power, width=20, anchor="w", font=reinforce_font),
            tk.Label(parent, text=power_status, width=25, anchor="w"),
            tk.Label(parent, text=reinforcement, width=15, anchor="w"),
            tk.Label(parent, text=undermining, width=15, anchor="w"),
            tk.Label(parent, text=opposition, width=45, anchor="w", font=undermining_font)
        ]

        for col, widget in enumerate(widgets):
            widget.grid(row=row_index, column=col, padx=5, pady=2, sticky="w")
            widget.grid_remove()  # Noch unsichtbar
            created_widgets.append(widget)
        row_index += 1

    # Am Ende: alle Widgets anzeigen
    for widget in created_widgets:
        widget.grid()
