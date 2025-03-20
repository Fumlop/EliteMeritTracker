import tkinter as tk

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

def show_power_info(parent, power_info, initial_text):
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

    tk.Label(table_frame, text="Powerplay Details", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=5, pady=10, sticky="w")

    tk.Label(table_frame, text=f"Power name: {power_info['PowerName']}", anchor="w").grid(row=1, column=0, columnspan=5, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Rank: {power_info['Rank']}", anchor="w").grid(row=2, column=0, columnspan=5, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Current merits: {power_info['Merits']}", anchor="w").grid(row=3, column=0, columnspan=5, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Last session merits: {power_info['AccumulatedMerits']}", anchor="w").grid(row=4, column=0, columnspan=5, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Last update: {power_info['LastUpdate']}", anchor="w").grid(row=5, column=0, columnspan=5, sticky="w", padx=10)

    systems = power_info.get("Systems", {})
    populate_table(table_frame, systems, update_scrollregion, initial_text)

def populate_table(table_frame, systems, update_scrollregion, initial_text=""):
    tk.Label(table_frame, text="System name", width=20, anchor="w", font=("Arial", 10, "bold")).grid(row=6, column=0, padx=5, pady=2)
    tk.Label(table_frame, text="Session merits", width=15, anchor="w", font=("Arial", 10, "bold")).grid(row=6, column=1, padx=5, pady=2)
    tk.Label(table_frame, text="Reported", width=7, anchor="w", font=("Arial", 10, "bold")).grid(row=6, column=2, padx=5, pady=2)
    tk.Label(table_frame, text="", width=5, anchor="w", font=("Arial", 10, "bold")).grid(row=6, column=3, padx=5, pady=2)
    tk.Label(table_frame, text="", width=5, anchor="w", font=("Arial", 10, "bold")).grid(row=6, column=4, padx=5, pady=2)
    tk.Label(table_frame, text="Text", width=60, anchor="w", font=("Arial", 10, "bold")).grid(row=6, column=5, padx=5, pady=2)
    
    row_index = 7
    for system_name, system_data in systems.items():
        merits = system_data.get("sessionMerits", 0)
        reported = system_data.get("reported", False) 
        if merits > 0:
            merits_str = str(merits)
            dcText = initial_text.replace("@MeritsValue", merits_str).replace("@System", system_name)

            tk.Label(table_frame, text=system_name, width=15, anchor="w").grid(row=row_index, column=0, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=merits_str, width=15, anchor="w").grid(row=row_index, column=1, padx=5, pady=2, sticky="w")
             # BooleanVar für den Checkbutton
            reported_var = tk.BooleanVar(value=reported)

            # Funktion zum Umschalten des reported-Status
            def toggle_reported(system=system_name, var=reported_var):
                systems[system]["reported"] = var.get()

            # Checkbutton zum Anzeigen und Ändern des reported-Status
            checkbutton = tk.Checkbutton(table_frame, variable=reported_var, command=lambda s=system_name, v=reported_var: toggle_reported(s, v))
            checkbutton.grid(row=row_index, column=2, padx=5, pady=2, sticky="w")
            tk.Button(table_frame, text="Copy", command=lambda text=dcText: copy_to_clipboard(text)).grid(row=row_index, column=3, padx=5, pady=2, sticky="w")
            tk.Button(table_frame, text="Delete", command=lambda name=system_name: delete_entry(name, systems, table_frame, update_scrollregion)).grid(row=row_index, column=4, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=dcText, width=45, anchor="w", justify="left", wraplength=300).grid(row=row_index, column=5, padx=5, pady=2, sticky="w")

            row_index += 1