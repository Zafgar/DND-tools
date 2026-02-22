import os
import shutil
import sys

# Määritellään projektin juuri
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MONSTERS_DIR = os.path.join(DATA_DIR, "monsters")
ENGINE_DIR = os.path.join(BASE_DIR, "engine")

print(f"--- D&D Tools Force Fix ---")
print(f"Juuri: {BASE_DIR}")

# 1. Varmistetaan oikea rakenne
os.makedirs(MONSTERS_DIR, exist_ok=True)
print(f"[OK] Kansiorakenne varmistettu: data/monsters/")

# 2. Luodaan __init__.py tiedostot
for path in [os.path.join(DATA_DIR, "__init__.py"), os.path.join(MONSTERS_DIR, "__init__.py")]:
    if not os.path.exists(path):
        with open(path, "w") as f: pass
        print(f"[LUOTU] {path}")

# 3. Lista tiedostoista, jotka PITÄÄ POISTAA (koska ne ovat väärissä paikoissa)
files_to_destroy = [
    os.path.join(BASE_DIR, "models.py"),
    os.path.join(BASE_DIR, "cr_1.py"),
    os.path.join(DATA_DIR, "cr_1.py"),
    os.path.join(ENGINE_DIR, "cr_1.py"),
    os.path.join(ENGINE_DIR, "library.py"),
    os.path.join(DATA_DIR, "monster", "cr_1.py"), # Väärä kansion nimi
]

# 4. Lista kansioista, jotka PITÄÄ POISTAA
dirs_to_destroy = [
    os.path.join(DATA_DIR, "monster"), # Yksikkömuoto on väärin
    os.path.join(BASE_DIR, "__pycache__"),
    os.path.join(DATA_DIR, "__pycache__"),
    os.path.join(ENGINE_DIR, "__pycache__"),
    os.path.join(os.path.join(BASE_DIR, "states"), "__pycache__"),
    os.path.join(os.path.join(BASE_DIR, "ui"), "__pycache__"),
]

print("\n--- Poistetaan roskat ---")
for f in files_to_destroy:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"[POISTETTU] {f}")
        except Exception as e:
            print(f"[VIRHE] Ei voitu poistaa {f}: {e}")

for d in dirs_to_destroy:
    if os.path.exists(d):
        try:
            shutil.rmtree(d)
            print(f"[POISTETTU KANSIO] {d}")
        except Exception as e:
            # Ei haittaa jos ei löydy
            pass

# 5. Tarkistetaan, että OIKEAT tiedostot ovat olemassa
required_files = [
    os.path.join(DATA_DIR, "models.py"),
    os.path.join(DATA_DIR, "library.py"),
    os.path.join(MONSTERS_DIR, "cr_1.py"),
    os.path.join(BASE_DIR, "main.py")
]

print("\n--- Tarkistetaan kriittiset tiedostot ---")
missing = False
for f in required_files:
    if not os.path.exists(f):
        print(f"[PUUTTUU] {f}")
        missing = True
    else:
        print(f"[OK] {f}")

if missing:
    print("\nVIRHE: Jokin kriittinen tiedosto puuttuu. Tarkista koodit.")
else:
    print("\nVALMIS! Kaikki näyttää puhtaalta.")
    print("Käynnistä peli nyt komennolla: python main.py")
import os
import shutil
import sys

# Määritellään projektin juuri
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MONSTERS_DIR = os.path.join(DATA_DIR, "monsters")
ENGINE_DIR = os.path.join(BASE_DIR, "engine")

print(f"--- D&D Tools Force Fix ---")
print(f"Juuri: {BASE_DIR}")

# 1. Varmistetaan oikea rakenne
os.makedirs(MONSTERS_DIR, exist_ok=True)
print(f"[OK] Kansiorakenne varmistettu: data/monsters/")

# 2. Luodaan __init__.py tiedostot
for path in [os.path.join(DATA_DIR, "__init__.py"), os.path.join(MONSTERS_DIR, "__init__.py")]:
    if not os.path.exists(path):
        with open(path, "w") as f: pass
        print(f"[LUOTU] {path}")

# 3. Lista tiedostoista, jotka PITÄÄ POISTAA (koska ne ovat väärissä paikoissa)
files_to_destroy = [
    os.path.join(BASE_DIR, "models.py"),
    os.path.join(BASE_DIR, "cr_1.py"),
    os.path.join(DATA_DIR, "cr_1.py"),
    os.path.join(ENGINE_DIR, "cr_1.py"),
    os.path.join(ENGINE_DIR, "library.py"),
    os.path.join(DATA_DIR, "monster", "cr_1.py"), # Väärä kansion nimi
]

# 4. Lista kansioista, jotka PITÄÄ POISTAA
dirs_to_destroy = [
    os.path.join(DATA_DIR, "monster"), # Yksikkömuoto on väärin
    os.path.join(BASE_DIR, "__pycache__"),
    os.path.join(DATA_DIR, "__pycache__"),
    os.path.join(ENGINE_DIR, "__pycache__"),
    os.path.join(os.path.join(BASE_DIR, "states"), "__pycache__"),
    os.path.join(os.path.join(BASE_DIR, "ui"), "__pycache__"),
]

print("\n--- Poistetaan roskat ---")
for f in files_to_destroy:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"[POISTETTU] {f}")
        except Exception as e:
            print(f"[VIRHE] Ei voitu poistaa {f}: {e}")

for d in dirs_to_destroy:
    if os.path.exists(d):
        try:
            shutil.rmtree(d)
            print(f"[POISTETTU KANSIO] {d}")
        except Exception as e:
            # Ei haittaa jos ei löydy
            pass

# 5. Tarkistetaan, että OIKEAT tiedostot ovat olemassa
required_files = [
    os.path.join(DATA_DIR, "models.py"),
    os.path.join(DATA_DIR, "library.py"),
    os.path.join(MONSTERS_DIR, "cr_1.py"),
    os.path.join(BASE_DIR, "main.py")
]

print("\n--- Tarkistetaan kriittiset tiedostot ---")
missing = False
for f in required_files:
    if not os.path.exists(f):
        print(f"[PUUTTUU] {f}")
        missing = True
    else:
        print(f"[OK] {f}")

if missing:
    print("\nVIRHE: Jokin kriittinen tiedosto puuttuu. Tarkista koodit.")
else:
    print("\nVALMIS! Kaikki näyttää puhtaalta.")
    print("Käynnistä peli nyt komennolla: python main.py")
import os
import shutil
import sys

# Määritellään projektin juuri
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MONSTERS_DIR = os.path.join(DATA_DIR, "monsters")
ENGINE_DIR = os.path.join(BASE_DIR, "engine")

print(f"--- D&D Tools Force Fix ---")
print(f"Juuri: {BASE_DIR}")

# 1. Varmistetaan oikea rakenne
os.makedirs(MONSTERS_DIR, exist_ok=True)
print(f"[OK] Kansiorakenne varmistettu: data/monsters/")

# 2. Luodaan __init__.py tiedostot
for path in [os.path.join(DATA_DIR, "__init__.py"), os.path.join(MONSTERS_DIR, "__init__.py")]:
    if not os.path.exists(path):
        with open(path, "w") as f: pass
        print(f"[LUOTU] {path}")

# 3. Lista tiedostoista, jotka PITÄÄ POISTAA (koska ne ovat väärissä paikoissa)
files_to_destroy = [
    os.path.join(BASE_DIR, "models.py"),
    os.path.join(BASE_DIR, "cr_1.py"),
    os.path.join(DATA_DIR, "cr_1.py"),
    os.path.join(ENGINE_DIR, "cr_1.py"),
    os.path.join(ENGINE_DIR, "library.py"),
    os.path.join(DATA_DIR, "monster", "cr_1.py"), # Väärä kansion nimi
]

# 4. Lista kansioista, jotka PITÄÄ POISTAA
dirs_to_destroy = [
    os.path.join(DATA_DIR, "monster"), # Yksikkömuoto on väärin
    os.path.join(BASE_DIR, "__pycache__"),
    os.path.join(DATA_DIR, "__pycache__"),
    os.path.join(ENGINE_DIR, "__pycache__"),
    os.path.join(os.path.join(BASE_DIR, "states"), "__pycache__"),
    os.path.join(os.path.join(BASE_DIR, "ui"), "__pycache__"),
]

print("\n--- Poistetaan roskat ---")
for f in files_to_destroy:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"[POISTETTU] {f}")
        except Exception as e:
            print(f"[VIRHE] Ei voitu poistaa {f}: {e}")

for d in dirs_to_destroy:
    if os.path.exists(d):
        try:
            shutil.rmtree(d)
            print(f"[POISTETTU KANSIO] {d}")
        except Exception as e:
            # Ei haittaa jos ei löydy
            pass

# 5. Tarkistetaan, että OIKEAT tiedostot ovat olemassa
required_files = [
    os.path.join(DATA_DIR, "models.py"),
    os.path.join(DATA_DIR, "library.py"),
    os.path.join(MONSTERS_DIR, "cr_1.py"),
    os.path.join(BASE_DIR, "main.py")
]

print("\n--- Tarkistetaan kriittiset tiedostot ---")
missing = False
for f in required_files:
    if not os.path.exists(f):
        print(f"[PUUTTUU] {f}")
        missing = True
    else:
        print(f"[OK] {f}")

if missing:
    print("\nVIRHE: Jokin kriittinen tiedosto puuttuu. Tarkista koodit.")
else:
    print("\nVALMIS! Kaikki näyttää puhtaalta.")
    print("Käynnistä peli nyt komennolla: python main.py")
# --- KONFIGURAATIO ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
FPS = 60

# --- VÄRIPALETTI (Dark UI) ---
COLORS = {
    "bg": (20, 22, 25),
    "panel": (35, 37, 40),
    "border": (60, 63, 65),
    "text_main": (220, 220, 220),
    "text_dim": (150, 150, 150),
    "accent": (100, 149, 237),      # Cornflower Blue
    "accent_hover": (120, 169, 255),
    "danger": (220, 53, 69),        # Red
    "success": (40, 167, 69),       # Green
    "grid": (50, 50, 50),
    "player": (0, 200, 255),
    "enemy": (255, 80, 80)
}