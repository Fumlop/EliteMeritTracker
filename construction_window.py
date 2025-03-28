from imports import *

def show_construction_window(parent, power_info, initial_text):
    global table_frame, systems, update_scrollregion, toggle_button, csv_button, detailed_view, filter_frame, data_frame


    info_window = tk.Toplevel(parent)
    info_window.title("Construction Window")
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
   