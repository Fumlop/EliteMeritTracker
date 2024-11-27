import tkinter as tk

def copy_to_clipboard(text):
    root = tk.Tk()
    root.withdraw()
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    root.destroy()

def show_power_info(parent, power_info, initial_text):
    # Erzeuge ein neues Fenster
    info_window = tk.Toplevel(parent)
    info_window.title("Power Info")
    info_window.geometry("1280x800")  # Breite x Höhe

    # Scrollbare Canvas für den Tabellenbereich
    canvas = tk.Canvas(info_window)
    v_scrollbar = tk.Scrollbar(info_window, orient="vertical", command=canvas.yview)
    h_scrollbar = tk.Scrollbar(info_window, orient="horizontal", command=canvas.xview)

    # Frame für den Inhalt
    table_frame = tk.Frame(canvas)

    # Scrollregion aktualisieren, wenn sich der Inhalt ändert
    def update_scrollregion(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    table_frame.bind("<Configure>", update_scrollregion)

    # Erstelle ein Fenster in der Canvas
    canvas.create_window((0, 0), window=table_frame, anchor="nw")

    # Scrollbars mit der Canvas verbinden
    canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    # Platzierung von Canvas und Scrollbars
    canvas.pack(side="top", fill="both", expand=True)
    v_scrollbar.pack(side="right", fill="y")
    h_scrollbar.pack(side="bottom", fill="x")

    # Zeige die Daten aus powerInfo an
    tk.Label(table_frame, text="Powerplay Details", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=4, pady=10, sticky="w")

    tk.Label(table_frame, text=f"Power Name: {power_info['PowerName']}", anchor="w").grid(row=1, column=0, columnspan=4, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Rank: {power_info['Rank']}", anchor="w").grid(row=2, column=0, columnspan=4, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Current Merits: {power_info['Merits']}", anchor="w").grid(row=3, column=0, columnspan=4, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Last Session Merits: {power_info['AccumulatedMerits']}", anchor="w").grid(row=4, column=0, columnspan=4, sticky="w", padx=10)
    tk.Label(table_frame, text=f"Last Update: {power_info['LastUpdate']}", anchor="w").grid(row=5, column=0, columnspan=4, sticky="w", padx=10)

    # Tabellenkopf
    tk.Label(table_frame, text="System Name", width=20, anchor="w", font=("Arial", 10, "bold")).grid(row=6, column=0, padx=5, pady=2)
    tk.Label(table_frame, text="Session Merits", width=15, anchor="w", font=("Arial", 10, "bold")).grid(row=6, column=1, padx=5, pady=2)
    tk.Label(table_frame, text="    ", width=5, anchor="w", font=("Arial", 10, "bold")).grid(row=6, column=2, padx=5, pady=2)
    tk.Label(table_frame, text="Text", width=60, anchor="w", font=("Arial", 10, "bold")).grid(row=6, column=3, padx=5, pady=2)
    
    combined_text = build_combined_text(systems)
    combined_button = tk.Button(
        table_frame, text="Copy All", command=lambda: copy_to_clipboard(combined_text)
    )
    combined_button.grid(row=7, column=2, columnspan=1, pady=10)
    # Füllen der Tabelle
    power_info = clean_empty_systems(power_info)
    systems = power_info.get("Systems", {})
    lastrow = 0
    if systems:
        for i, (system_name, system_data) in enumerate(
            ((name, data) for name, data in systems.items() if data.get("sessionMerits", 0) > 0),
            start=8
        ):
            merits = str(system_data.get("sessionMerits", 0))
            dcText = initial_text.replace("@MeritsValue", merits).replace("@System", system_name)

            tk.Label(table_frame, text=system_name, width=15, anchor="w", justify="left").grid(row=i, column=0, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=merits, width=15, anchor="w", justify="left").grid(row=i, column=1, padx=5, pady=2, sticky="w")
            tk.Button(
                table_frame,
                text="Copy",
                command=lambda text=dcText: copy_to_clipboard(text)
            ).grid(row=i, column=2, padx=5, pady=2, sticky="w")
            tk.Label(table_frame, text=dcText, width=60, anchor="w", justify="left", wraplength=600).grid(row=i, column=3, padx=5, pady=2, sticky="w")
    else:
        tk.Label(table_frame, text="No systems available", anchor="w").grid(row=7, column=0, columnspan=4, padx=5, pady=2)

def build_combined_text(systems):
    # Baut den kombinierten Text
    return ", ".join(
        f"{data.get('sessionMerits', 0)} Merits {name}"
        for name, data in systems.items()
        if data.get("sessionMerits", 0) > 0
    )

def clean_empty_systems(power_info):
    systems = power_info.get("Systems", {})
    # Filtere Systeme mit nicht-leerem Namen und Merits > 0
    cleaned_systems = {k: v for k, v in systems.items() if k}
    power_info["Systems"] = cleaned_systems
    return power_info