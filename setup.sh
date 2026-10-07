#!/usr/bin/env bash
set -e

# Belépés a script saját könyvtárába
cd "$(dirname "$0")"

echo "=========================================="
echo "  Szerver Monitoring - Telepítő (Unix)    "
echo "=========================================="

# 1. Python 3 ellenőrzése
if ! command -v python3 &>/dev/null; then
    echo "[X] A python3 nem található a rendszeren!"
    echo "Kérlek telepítsd a csomagkezelőddel (pl. sudo apt install python3 python3-venv python3-pip)"
    exit 1
fi

PYTHON_BIN="python3"
echo "[OK] $($PYTHON_BIN --version) elérhető."

# 2. Virtuális környezet (.venv) vizsgálata és létrehozása
if [ ! -f ".venv/bin/python" ]; then
    echo "[*] Virtuális környezet létrehozása (.venv)..."
    $PYTHON_BIN -m venv .venv
    echo "[OK] .venv sikeresen létrehozva."
else
    echo "[OK] A meglévő .venv környezet használata."
fi

# 3. Függőségek telepítése / frissítése
echo "[*] Csomagok ellenőrzése és telepítése..."
./.venv/bin/python -m pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt
echo "[OK] Függőségek sikeresen telepítve!"

# 4. Interaktív konfiguráció futtatása
if [ ! -f ".env" ]; then
    echo ""
    echo "[*] Nincs mentett beállítás (.env), interaktív konfigurátor indítása..."
    echo ""
    ./.venv/bin/python configure.py
else
    echo "[OK] Létező .env konfiguráció megtalálva."
    read -r -p "Szeretnéd elindítani a konfigurációs varázslót? [y/N]: " RECONFIG
    if [[ "$RECONFIG" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        ./.venv/bin/python configure.py
    fi
fi

echo ""
echo "=========================================="
echo "  Telepítés kész! Minden készen áll.      "
echo "=========================================="
echo ""

# 5. Opcionális azonnali indítás
read -r -p "Elindítod most a monitoringot? [Y/n]: " START_NOW
START_NOW=${START_NOW:-y}

if [[ "$START_NOW" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    exec ./run.sh
else
    echo "Későbbi indításhoz használd: ./run.sh"
fi