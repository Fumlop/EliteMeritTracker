import tkinter as tk

def copy_to_clipboard(text):
    root = tk.Tk()
    root.withdraw()  # Versteckt das Hauptfenster
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()  # Aktualisiert die Zwischenablage
    root.destroy()

def show_power_info(parent, power_info, initial_text):
    # Erzeuge ein neues Fenster
    info_window = tk.Toplevel(parent)
    info_window.title("Power Info")
    
    # Zeige die Daten aus powerInfo an
    tk.Label(info_window, text="Powerplay Details", font=("Arial", 14, "bold")).pack(pady=10)

    # Zeige die einzelnen Daten
    tk.Label(info_window, text=f"Power Name: {power_info['PowerName']}").pack(anchor="w", padx=10, pady=2)
    tk.Label(info_window, text=f"Rank: {power_info['Rank']}").pack(anchor="w", padx=10, pady=2)
    tk.Label(info_window, text=f"Current Merits: {power_info['Merits']}").pack(anchor="w", padx=10, pady=2)
    tk.Label(info_window, text=f"Last Session Merits: {power_info['AccumulatedMerits']}").pack(anchor="w", padx=10, pady=2)
    tk.Label(info_window, text=f"Last Update: {power_info['LastUpdate']}").pack(anchor="w", padx=10, pady=2)

    # Tabelle für Systems
    tk.Label(info_window, text="Systems", font=("Arial", 12, "bold")).pack(pady=5)
    table_frame = tk.Frame(info_window)
    table_frame.pack(padx=10, pady=5)

    # Tabellenkopf
    tk.Label(table_frame, text="System Name", width=20, anchor="w", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=2)
    tk.Label(table_frame, text="Session Merits", width=15, anchor="w", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=2)
    tk.Label(table_frame, text="Text", width=10, anchor="w", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=2)

    systems = power_info.get("Systems", {})
    if systems:
        for i, (system_name, system_data) in enumerate(systems.items(), start=1):
            merits = str(system_data.get("sessionMerits", 0))

            # Text dynamisch ersetzen
            dcText = initial_text.replace("@MertitsValue", merits).replace("@System", system_name)
            
            tk.Label(table_frame, text=system_name, width=20, anchor="w").grid(row=i, column=0, padx=5, pady=2)
            tk.Label(table_frame, text=merits, width=15, anchor="w").grid(row=i, column=1, padx=5, pady=2)
            tk.Label(table_frame, text=dcText, width=15, anchor="w").grid(row=i, column=2, padx=5, pady=2)
            
            # Übergabe von dcText als Standardargument
            tk.Button(
                table_frame,
                text="Copy/Paste",
                command=lambda text=dcText: copy_to_clipboard(dcText)
            ).grid(row=i, column=3, padx=5, pady=2)
    else:
        tk.Label(table_frame, text="No systems available", anchor="w").grid(row=1, column=0, padx=5, pady=2)

    # Button zum Schließen des Fensters
    tk.Button(info_window, text="Close", command=info_window.destroy).pack(pady=10)
