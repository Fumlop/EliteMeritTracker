import tkinter as tk
import csv
import os
from tkinter import filedialog

filter_power_var = None
filter_system_var = None
filter_state_var = None
filter_frame = None
data_frame = None


def copy_to_clipboard(text):
    root = tk.Tk()
    root.withdraw()
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    root.destroy()

def delete_entry(system_name, systems, table_frame, update_scrollregion):
    if system_name in systems:
        del systems[system_name]
        for widget in table_frame.winfo_children():
            widget.destroy()
        populate_table(table_frame, systems, update_scrollregion)

def toggle_view(power_info):
    global detailed_view, csv_button, systems

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
        add_power_info_headers(power_info)

    # Repopulate the table
    table_frame.after(100, lambda: populate_table(table_frame, systems, update_scrollregion, ""))



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

    headers = ["System", "Status", "Controlling Power", "Reinforcement", "Undermining", "Power Status"]
    
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file,delimiter=";")
        writer.writerow(headers)  # Write headers
        
        for system_name, system_data in systems.items():
            state = system_data.get("state", "")
            progress = system_data.get("progress", 0) * 100
            controlling_power = system_data.get("power", "")
            reinforcement = system_data.get("statereinforcement", 0)
            undermining = system_data.get("stateundermining", 0)
            power_status = get_system_power_status_text(reinforcement, undermining)

            writer.writerow([system_name, f"{state} ({progress:.2f}%)", controlling_power, reinforcement, undermining, power_status])

    print(f"CSV export successful: {file_path}")  # Debug log (replace with a messagebox if needed)

def show_power_info(parent, power_info, initial_text):
    global table_frame, systems, update_scrollregion, toggle_button, csv_button, detailed_view, filter_frame, data_frame

    detailed_view = False  

    info_window = tk.Toplevel(parent)
    info_window.title("Power Info")
    info_window.geometry("1280x800")

    main_frame = tk.Frame(info_window)
    main_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(main_frame)
    canvas.pack(side="left", fill="both", expand=True)

    v_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    v_scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=v_scrollbar.set)
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1*(event.delta//120), "units"))


    table_frame = tk.Frame(canvas)
    for i in range(6):  # 6 Spalten, falls mehr, erhöhe die Zahl
        table_frame.columnconfigure(i, weight=1)
    canvas.create_window((0, 0), window=table_frame, anchor="nw")

    def update_scrollregion(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    table_frame.bind("<Configure>", update_scrollregion)
    
    # Zeige Powerplay-Details in Default View
    if not detailed_view:
        add_power_info_headers(power_info)


    button_frame = tk.Frame(info_window)
    button_frame.pack(side="top", pady=5, anchor="center")  # Buttons mittig ausrichten

    toggle_button = tk.Button(button_frame, text="Show Detailed View", command=lambda: toggle_view(power_info))
    toggle_button.grid(row=0, column=0, padx=5)

    csv_button = tk.Button(button_frame, text="Export CSV", command=export_to_csv)
    csv_button.grid(row=0, column=1, padx=5)
    csv_button.grid_forget()  # Erst in detailed_view anzeigen

    systems = power_info.get("Systems", {})

    populate_table(table_frame, systems, update_scrollregion, initial_text)


    
def add_power_info_headers(power_info):
    """
    Ensures Power Info (Name, Rank, Merits, etc.) is only shown in Default View.
    """
    if detailed_view:
        return  # Do not show headers in Detailed View

    tk.Label(table_frame, text="Powerplay Details", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=6, pady=10, sticky="w")

    tk.Label(table_frame, text=f"Power name: {power_info['PowerName']}", anchor="w").grid(row=1, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Rank: {power_info['Rank']}", anchor="w").grid(row=2, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Current merits: {power_info['Merits']}", anchor="w").grid(row=3, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Last session merits: {power_info['AccumulatedMerits']}", anchor="w").grid(row=4, column=0, columnspan=6, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Last update: {power_info['LastUpdate']}", anchor="w").grid(row=5, column=0, columnspan=6, sticky="w", padx=10)


def populate_table(table_frame, systems, update_scrollregion, initial_text="", show_filters_only=False):
    global detailed_view

    if detailed_view:
        headers = ["System", "Status", "Controlling Power", "Reinforcement", "Undermining", "Power Status"]
        col_widths = [25, 20, 25, 15, 15, 25]  # Einheitliche Breiten
    else:
        headers = ["System name", "Session merits","Reported", "", "", "Text"]
        col_widths = [20, 15, 15, 10, 10, 60]
    if detailed_view:
        header_index = 0
    else: 
        header_index = 6
    # Create table headers
    for col, (header, width) in enumerate(zip(headers, col_widths)):
            tk.Label(table_frame, text=header, width=width, anchor="w", font=("Arial", 10, "bold")).grid(
                row=6, column=col, padx=5, pady=2, sticky="w"
            )
    if detailed_view:
        # Filterzeile und Datenbereich getrennt behandeln
        add_detailed_view_filter_buttons(table_frame, systems)

        global data_frame
        data_frame = tk.Frame(table_frame)
        data_frame.grid(row=9, column=0, columnspan=6, sticky="w")

        if show_filters_only:
            return  # Nur Filter anzeigen, keine Datenzeilen

        populate_table_data_rows(data_frame, systems)
        return  # kein doppeltes Rendern darunter
    else:
        row_index = 7
    for system_name, system_data in systems.items():
        controlling_power = system_data.get("power", "").strip() 
        merits = str(system_data.get("sessionMerits", 0))            
        
        if int(merits) > 0:
            reported = system_data.get("reported", False)
            dcText = initial_text.replace("@MeritsValue", merits).replace("@System", system_name)
            # BooleanVar für den Checkbutton
            reported_var = tk.BooleanVar(value=reported)

            # Funktion zum Umschalten des reported-Status
            def toggle_reported(system=system_name, var=reported_var):
                systems[system]["reported"] = var.get()

            # Checkbutton zum Anzeigen und Ändern des reported-Status
            checkbutton = tk.Checkbutton(table_frame, variable=reported_var, command=lambda s=system_name, v=reported_var: toggle_reported(s, v))
            checkbutton.grid(row=row_index, column=2, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=system_name, width=15, anchor="w").grid(row=row_index, column=0, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=merits, width=15, anchor="w").grid(row=row_index, column=1, padx=5, pady=2, sticky="w")
            tk.Button(table_frame, text="Copy", command=lambda text=dcText: copy_to_clipboard(text)).grid(row=row_index, column=3, padx=5, pady=2, sticky="w")
            tk.Button(table_frame, text="Delete", command=lambda name=system_name: delete_entry(name, systems, table_frame, update_scrollregion)).grid(row=row_index, column=4, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=dcText, width=45, anchor="w", justify="left", wraplength=300).grid(row=row_index, column=5, padx=5, pady=2, sticky="w")
            row_index += 1

        

def get_system_power_status_text(reinforcement, undermining):
    if reinforcement == 0 and undermining == 0:
        return "Neutral"  # If both are 0, show neutral

    total = reinforcement + undermining  # Total value

    # Calculate actual percentage share
    reinforcement_percentage = (reinforcement / total) * 100
    undermining_percentage = (undermining / total) * 100

    if reinforcement > undermining:
        return f"Reinforced {reinforcement_percentage:.2f}%"
    else:
        return f"Undermined {undermining_percentage:.2f}%"
    
def add_detailed_view_filter_buttons(parent_frame, systems):
    global filter_power_var, filter_system_var, filter_state_var, filter_frame

    if filter_frame:
        filter_frame.destroy()

    filter_frame = tk.Frame(parent_frame)
    filter_frame.grid(row=8, column=0, columnspan=6, sticky="w", padx=10)  # Linksbündig setzen
    for i in range(6):  # 6 Spalten anpassen
        filter_frame.columnconfigure(i, weight=1)

    powers = sorted(set(data.get("power", "") for data in systems.values() if data.get("power", "")))
    states = sorted(set(data.get("state", "") for data in systems.values() if data.get("state", "")))
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
    global data_frame

    selected_system = filter_system_var.get()
    selected_state = filter_state_var.get()
    selected_power = filter_power_var.get()

    filtered = {}
    for name, data in systems.items():
        if selected_system != "All" and name != selected_system:
            continue
        if selected_state != "All" and data.get("state") != selected_state:
            continue
        if selected_power != "All" and data.get("power") != selected_power:
            continue
        filtered[name] = data

    for widget in data_frame.winfo_children():
        widget.destroy()

    populate_table_data_rows(data_frame, filtered)

def populate_table_data_rows(parent, systems):
    for i in range(6):  # Anzahl der Spalten
        parent.columnconfigure(i, weight=1)
    row_index = 9
    for system_name, system_data in systems.items():
        controlling_power = system_data.get("power", "").strip() 
        merits = str(system_data.get("sessionMerits", 0))

        if not controlling_power:
            continue

        state = system_data.get("state", "")
        progress = system_data.get("progress", 0) * 100
        reinforcement = system_data.get("statereinforcement", 0)
        undermining = system_data.get("stateundermining", 0)
        power_status = get_system_power_status_text(reinforcement, undermining)


        tk.Label(table_frame, text=system_name, width=20, anchor="w").grid(row=row_index, column=0, padx=5, pady=2, sticky="w")
        tk.Label(table_frame, text=f"{state} ({progress:.2f}%)", width=20, anchor="w").grid(row=row_index, column=1, padx=5, pady=2, sticky="w")
        tk.Label(table_frame, text=controlling_power, width=20, anchor="w").grid(row=row_index, column=2, padx=5, pady=2, sticky="w")
        tk.Label(table_frame, text=reinforcement, width=15, anchor="w").grid(row=row_index, column=3, padx=5, pady=2, sticky="w")
        tk.Label(table_frame, text=undermining, width=15, anchor="w").grid(row=row_index, column=4, padx=5, pady=2, sticky="w")
        tk.Label(table_frame, text=power_status, width=25, anchor="w").grid(row=row_index, column=5, padx=5, pady=2, sticky="w")

        row_index += 1