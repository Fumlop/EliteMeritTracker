import tkinter as tk

def show_power_info(parent, power_info):
    # Erzeuge ein neues Fenster
    info_window = tk.Toplevel(parent)
    info_window.title("Power Info")
    
    # Zeige die Daten aus powerInfo an
    tk.Label(info_window, text="Powerplay Details", font=("Arial", 14, "bold")).pack(pady=10)

    # Zeige die einzelnen Daten
    tk.Label(info_window, text=f"Power Name: {power_info['PowerName']}").pack(anchor="w", padx=10, pady=2)
    tk.Label(info_window, text=f"Rank: {power_info['Rank']}").pack(anchor="w", padx=10, pady=2)
    tk.Label(info_window, text=f"Current Merits: {power_info['Merits']}").pack(anchor="w", padx=10, pady=2)
    tk.Label(info_window, text=f"Accumulated Merits (24h): {power_info['AccumulatedMerits']}").pack(anchor="w", padx=10, pady=2)
    tk.Label(info_window, text=f"Last Update: {power_info['LastUpdate']}").pack(anchor="w", padx=10, pady=2)

    # Button zum Schließen des Fensters
    tk.Button(info_window, text="Close", command=info_window.destroy).pack(pady=10)
