import random
import json

def generate_test_systems_json(path="system_merits_test.json", count=100):
    system_names = [
        "Sol", "Achenar", "Alioth", "Lave", "Diso", "Eravate", "Shinrarta Dezhra", "Leesti", "Riedquat", "Vequess",
        "CD-61 6801", "Eranin", "Ross 128", "Wolf 359", "LHS 3447", "Altair", "Arcturus", "Luyten's Star", "Barnard's Star", "Beta Hydri",
        "HIP 20277", "HR 7221", "LP 98-132", "HR 6421", "BD-11 5480", "HIP 16813", "HIP 22550", "LTT 18486", "Wolf 562", "HIP 9141",
        "LTT 9810", "Wolf 906", "Epsilon Indi", "HIP 69987", "Wolf 25", "HR 4690", "Delta Pavonis", "Colonia", "Sagittarius A*", "Beagle Point",
        "Maia", "Merope", "HR 1183", "Meliae", "Ngalinn", "Ceos", "Sothis", "Ngurii", "BD+03 2338", "HIP 10716", "LHS 3447",
        "Urqu", "Tewanta", "G 180-18", "HIP 77946", "VY Canis Majoris", "Sirius", "LHS 20", "EZ Aquarii", "HIP 10257", "G 99-49",
        "Orna", "Dromi", "Exphiay", "Tiliala", "HIP 71567", "CD-37 641", "Wregoe KC-I d10-0", "Phylur", "Nunda", "Fong Wang",
        "Anlave", "Aramzahd", "Aulin", "Orrere", "Zaonce", "Tionisla", "Orerve", "George Pantazis",
        "Reorte", "Uszaa", "Van Maanen's Star", "Xihe", "Yaso Kondi", "Zearla"
    ]

    states = ["Stronghold", "Exploited", "Reinforced", "Unoccupied"]
    powers = ["Edmund Mahon", "Felicia Winters", "Zachary Hudson", "Denton Patreus", "Aisling Duval", "Arissa Lavigny-Duval", "Li Yong-Rui"]

    data = {}

    for _ in range(count):
        system = random.choice(system_names) + f" {random.randint(1,999)}"
        state = random.choice(states)
        data[system] = {
            "sessionMerits": random.randint(1, 1000),
            "state": state,
            "power": random.choice(powers),
            "powerCompetition": [],
            "powerConflict":[],
            "progress": round(random.uniform(0.0, 1.0 if state == "Stronghold" else 2.0), 2),
            "statereinforcement": random.randint(0, 5000),
            "stateundermining": random.randint(0, 5000),
            "reported": False
        }

    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"✅ Testdaten gespeichert in {path}")

# Aufruf
generate_test_systems_json()
