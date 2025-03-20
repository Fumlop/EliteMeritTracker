import tkinter as tk
import csv
import os
from tkinter import filedialog

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

def toggle_view():
    global detailed_view, csv_button
    detailed_view = not detailed_view  # Switch between views

    # Update button text
    toggle_button.config(text="Show Default View" if detailed_view else "Show Detailed View")

    # Clear the current table
    for widget in table_frame.winfo_children():
        widget.destroy()

    # Show CSV Export button only in detailed view
    if detailed_view:
        csv_button.pack(pady=10)
    else:
        csv_button.pack_forget()

    # Refresh the table
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
        writer = csv.writer(file)
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
    global table_frame, systems, update_scrollregion, toggle_button, detailed_view, csv_button
    detailed_view = False  # Default mode

    info_window = tk.Toplevel(parent)
    info_window.title("Power Info")
    info_window.geometry("1280x800")

    canvas = tk.Canvas(info_window)
    v_scrollbar = tk.Scrollbar(info_window, orient="vertical", command=canvas.yview)
    h_scrollbar = tk.Scrollbar(info_window, orient="horizontal", command=canvas.xview)
    table_frame = tk.Frame(canvas)

    def update_scrollregion(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    table_frame.bind("<Configure>", update_scrollregion)
    canvas.create_window((0, 0), window=table_frame, anchor="nw")
    canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
    canvas.pack(side="top", fill="both", expand=True)
    v_scrollbar.pack(side="right", fill="y")
    h_scrollbar.pack(side="bottom", fill="x")

    # Toggle button
    toggle_button = tk.Button(info_window, text="Show Detailed View", command=toggle_view)
    toggle_button.pack(pady=10)

    # CSV Export Button (hidden by default)
    csv_button = tk.Button(info_window, text="Export CSV", command=export_to_csv)
    csv_button.pack_forget()  # Hide initially

    tk.Label(table_frame, text="Powerplay Details", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=5, pady=10, sticky="w")

    tk.Label(table_frame, text=f"Power name: {power_info['PowerName']}", anchor="w").grid(row=1, column=0, columnspan=5, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Rank: {power_info['Rank']}", anchor="w").grid(row=2, column=0, columnspan=5, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Current merits: {power_info['Merits']}", anchor="w").grid(row=3, column=0, columnspan=5, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Last session merits: {power_info['AccumulatedMerits']}", anchor="w").grid(row=4, column=0, columnspan=5, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Last update: {power_info['LastUpdate']}", anchor="w").grid(row=5, column=0, columnspan=5, sticky="w", padx=10)

    systems = power_info.get("Systems", {})
    populate_table(table_frame, systems, update_scrollregion, initial_text)


def populate_table(table_frame, systems, update_scrollregion, initial_text=""):
    global detailed_view

    if detailed_view:
        headers = ["System", "Status", "Controlling Power", "Reinforcement", "Undermining", "Power Status"]
        col_widths = [20, 20, 20, 15, 15, 25]
    else:
        headers = ["System name", "Session merits", "", "", "Text"]
        col_widths = [20, 15, 15, 15, 60]

    # Create table headers
    for col, (header, width) in enumerate(zip(headers, col_widths)):
        tk.Label(table_frame, text=header, width=width, anchor="w", font=("Arial", 10, "bold")).grid(row=6, column=col, padx=5, pady=2)

    row_index = 7
    for system_name, system_data in systems.items():
        if detailed_view:
            state = system_data.get("state", "")
            progress = system_data.get("progress", 0) * 100
            controlling_power = system_data.get("power", "")
            reinforcement = system_data.get("statereinforcement", 0)
            undermining = system_data.get("stateundermining", 0)
            power_status = get_system_power_status_text(reinforcement, undermining)

            tk.Label(table_frame, text=system_name, width=20, anchor="w").grid(row=row_index, column=0, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=f"{state} ({progress:.2f}%)", width=20, anchor="w").grid(row=row_index, column=1, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=controlling_power, width=20, anchor="w").grid(row=row_index, column=2, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=reinforcement, width=15, anchor="w").grid(row=row_index, column=3, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=undermining, width=15, anchor="w").grid(row=row_index, column=4, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=power_status, width=25, anchor="w").grid(row=row_index, column=5, padx=5, pady=2, sticky="w")

        else:
            merits = str(system_data.get("sessionMerits", 0))
            dcText = initial_text.replace("@MeritsValue", merits).replace("@System", system_name)

            tk.Label(table_frame, text=system_name, width=15, anchor="w").grid(row=row_index, column=0, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=merits, width=15, anchor="w").grid(row=row_index, column=1, padx=5, pady=2, sticky="w")
            tk.Button(table_frame, text="Copy", command=lambda text=dcText: copy_to_clipboard(text)).grid(row=row_index, column=2, padx=5, pady=2, sticky="w")
            tk.Button(table_frame, text="Delete", command=lambda name=system_name: delete_entry(name, systems, table_frame, update_scrollregion)).grid(row=row_index, column=3, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=dcText, width=45, anchor="w", justify="left", wraplength=300).grid(row=row_index, column=4, padx=5, pady=2, sticky="w")

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