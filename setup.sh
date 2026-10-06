#!/usr/bin/env bash
set -e

# Színek a formázott terminálos visszajelzéshez
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}  Szerver Monitoring - Függőség Ellenőrző  ${NC}"
echo -e "${CYAN}==========================================${NC}"

# 1. Python 3 ellenőrzése
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] A Python 3 nem található a rendszeren.${NC}"
    if [ -f /etc/debian_version ]; then
        echo -e "${YELLOW}[*] Telepítés apt csomagkezelővel...${NC}"
        sudo apt update && sudo apt install -y python3
    else
        echo -e "${RED}[X] Kérlek, telepítsd a Python 3-at a rendszered csomagkezelőjével!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}[✔] Python 3 megtalálva:${NC} $(python3 --version)"
fi

# 2. python3-venv és ensurepip ellenőrzése (Debian/Ubuntu specifikus)
echo -e "[*] Venv modul elérhetőségének vizsgálata..."
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${YELLOW}[!] A python3-venv modul hiányzik a rendszerről.${NC}"
    if [ -f /etc/debian_version ]; then
        echo -e "${YELLOW}[*] Telepítés sudo apt-tal...${NC}"
        sudo apt update
        sudo apt install -y python3-venv python3-pip
        echo -e "${GREEN}[✔] python3-venv sikeresen telepítve!${NC}"
    else
        echo -e "${RED}[X] Nem Debian/Ubuntu rendszer, kérlek manuálisan telepítsd a venv modult!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}[✔] Python venv támogatás elérhető.${NC}"
fi

# 3. Virtuális környezet (.venv) vizsgálata
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}[*] .venv mappa nem létezik. Létrehozás folyamatban...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}[✔] .venv sikeresen létrehozva.${NC}"
else
    echo -e "${GREEN}[✔] .venv virtuális környezet már létezik.${NC}"
fi

# 4. Pip és csomagok telepítése / frissítése
echo -e "[*] Python csomagok ellenőrzése a requirements.txt alapján..."
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt
echo -e "${GREEN}[✔] Minden Python függőség telepítve és naprakész.${NC}"

# 5. Konfiguráció (.env) ellenőrzése
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}[!] .env fájl nem található. Mintafájl (.env.example) másolása...${NC}"
        cp .env.example .env
        echo -e "${GREEN}[✔] .env fájl létrehozva alapértelmezett értékekkel.${NC}"
    else
        echo -e "${RED}[!] Figyelem: sem .env, sem .env.example nem található!${NC}"
    fi
else
    echo -e "${GREEN}[✔] .env konfigurációs fájl megtalálva.${NC}"
fi

echo -e "\n${GREEN}==========================================${NC}"
echo -e "${GREEN}  ✓ Minden rendben! All good to go!        ${NC}"
echo -e "${GREEN}==========================================${NC}\n"

# 6. Azonnali indítás bekérése (Y/n)
read -p "Elindítod most a monitoringot? [Y/n]: " -n 1 -r
echo # Új sor a lenyomott gomb után

if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo -e "${CYAN}[*] Monitoring indítása...${NC}\n"
    exec ./.venv/bin/python monitor.py
else
    echo -e "Későbbi indításhoz használd: ${CYAN}./run.sh${NC}\n"
fi