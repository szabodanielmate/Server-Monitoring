# 🖥️ Lightweight Cross-Platform Server Monitor

Könnyűsúlyú, platformfüggetlen (Linux, macOS, Windows) szerver- és konténermonitorozó eszköz Rich TUI (Text User Interface) felülettel, spike-védelemmel és webhookos riasztásokkal (Discord, Telegram).

---

## 📌 Főbb funkciók

- **Interaktív telepítő (ÚJ):** A telepítő scriptek automatikusan elindítanak egy varázslót (`configure.py`), ahol lépésről lépésre kiválaszthatod a figyelni kívánt partíciókat, küszöbértékeket és riasztási csatornákat.
- **Hardvererőforrások követése:** Valós idejű CPU-, RAM- és többpartíciós lemezhasználat-figyelés.
- **Hálózati forgalommérés:** Dinamikus fel- és letöltési sebesség mérése Megabit/másodpercben (`Mb/s`).
- **Okos Partíció-felderítés (ÚJ):** Automatikusan kiszűri a virtuális (`squashfs`, `tmpfs`) és a rendszer boot partícióit (`/boot`, `/boot/efi`), de a `.env` fájlon keresztül manuálisan is felülbírálható (`MONITORED_DISKS`).
- **Docker integráció:** Futó és leállt konténerek listázása a beépített `Healthcheck` státuszok (`healthy`, `unhealthy`, `starting`) követésével.
- **Spike-védelem (`ALERT_DURATION`):** Kiszűri a pillanatnyi terhelési tüskéket (pl. csomagfrissítés, build); csak tartósan fennálló hiba esetén riaszt.
- **Többcsatornás riasztás:** Azonnali webhook értesítések Discordra és Telegramra a gép nevével (`hostname`).
- **Forgó fájlnaplózás (`RotatingFileHandler`):** Riasztások és hibák naplózása méretkorláttal (5 MB, max 3 archívum).

---

## 📂 Mappaszerkezet

```text
server-monitor/
├── src/
│   ├── __init__.py                       # Python csomagazonosító
│   ├── config.py                         # Környezeti változók betöltése és validálása
│   ├── logger.py                         # Forgó fájl-naplózás (server_monitor.log)
│   ├── metrics.py                        # Rendszer- és Docker-adatgyűjtés
│   └── notifier.py                       # Spike-szűrés, cooldown és riasztásküldés
├── .env.example                          # Konfigurációs sablon
├── .env                                  # Helyi környezeti beállítások (nem kerül gitbe)
├── configure.py                          # Interaktív telepítő varázsló
├── monitor.py                            # Belépési pont és Rich TUI felület
├── requirements.txt                      # Python függőségek
├── setup.sh / run.sh                     # Linux/macOS indítószkriptek
└── windowsSetup.bat / windowsRun.bat     # Windows indítószkriptek
```

---

## ⚙️ Telepítés és indítás

### 1. Előfeltételek

- **Python 3.10+**
- **Docker Engine / Docker Desktop** (ha a konténereket is monitorozni szeretnéd)

---

### 2. Linux és macOS

1. Futtatási jogok megadása:
   ```bash
   chmod +x setup.sh run.sh
   ```
2. Környezet előkészítése és konfigurálása (az interaktív varázsló automatikusan elindul):
   ```bash
   ./setup.sh
   ```
3. Alkalmazás indítása:
   ```bash
   ./run.sh
   ```

---

### 3. Windows

1. Győződj meg róla, hogy a Python telepítve van (`Add Python to PATH` bekapcsolva):
   ```powershell
   python --version
   ```
2. Futtasd a telepítőt, amely letölti a csomagokat és elindítja az interaktív beállítást:
   ```cmd
   windowsSetup.bat
   ```
   A későbbi indításokhoz használd közvetlenül a `windowsRun.bat` fájlt.

---

## 🛠️ Konfiguráció (`.env`)

A gyökérkönyvtárban lévő `.env` fájl segítségével testreszabható a rendszer működése (a `configure.py` generálja):

```ini
# ==========================================
# KÜSZÖBÉRTÉKEK (Százalékban)
# ==========================================
CPU_THRESHOLD=85.0
RAM_THRESHOLD=90.0
DISK_THRESHOLD=90.0

# ==========================================
# IDŐZÍTÉSEK (Másodpercben)
# ==========================================
# Dashboard frissítési gyakorisága
CHECK_INTERVAL=3

# Hány másodpercig kell a terhelésnek FOLYAMATOSAN fennállnia a riasztáshoz? (Spike-szűrés)
ALERT_DURATION=30

# Két azonos riasztás közötti minimális várakozási idő (Spam-védelem)
ALERT_COOLDOWN=300

# ==========================================
# MEREVLEMEZEK ÉS PARTÍCIÓK
# Vesszővel elválasztott csatolási pontok (ha üres, minden valós lemezt figyel)
# ==========================================
MONITORED_DISKS=/,/mnt/storage,D:\

# ==========================================
# RIASZTÁSI CSATORNÁK (Opcionális)
# ==========================================
# Discord Webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Telegram Bot adatok
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=-1001234567890

# ==========================================
# DOCKER INTEGRÁCIÓ
# ==========================================
# Konténerek monitorozása (true / false)
ENABLE_DOCKER=true
```

---

## 🚀 Háttérben futtatás

### Linux (tmux használatával)
A terminál bezárása után is futó felülethez:
```bash
# Új munkamenet indítása
tmux new -s monitor

# Indítás
./run.sh

# Háttérbe küldés: nyomd le a Ctrl + B, majd a D billentyűt.
# Visszatérés:
tmux attach -t monitor
```

### Windows (Konzolablak nélküli indítás)
Hozz létre egy `silent.vbs` fájlt az alábbi tartalommal a projekt gyökerében:
```vbs
CreateObject("Wscript.Shell").Run "windowsRun.bat", 0, False
```
Erre duplán kattintva a monitor láthatatlanul fut a háttérben.

---

## 📋 Naplózási struktúra (`server_monitor.log`)

A rendszer a forgónaplózás elvét követi:
- **Fájlméret:** legfeljebb 5 MB fájlonként, maximum 3 biztonsági mentéssel (`server_monitor.log.1`, stb.).
- **Naplózott események:**
  - Szolgáltatás indulása és leállása.
  - Küszöbérték-túllépés kezdete (időzítő indulása).
  - Sikeresen kiküldött webhook riasztások a szerver gazdagépnevével (`hostname`).
  - Webhook küldési és hálózati hibák (HTTP hibakódok, timeoutok).

---

## 🆕 Legutóbbi frissítések (Changelog)

- **Interaktív Config Varázsló (`configure.py`)**: Létrehozásra került egy platformfüggetlen konfiguráló szkript, ami a `setup` folyamat során bekéri a felhasználótól a Telegram/Discord webhookokat, a küszöbértékeket, a figyelni kívánt partíciókat, és automatikusan generálja a `.env` fájlt. 
- **Okos Partícióválasztás (`MONITORED_DISKS`)**: A `metrics.py` és a `config.py` fel lett készítve arra, hogy csak a `.env`-ben megadott lemezeket mutassa a Dashboardon. 
- **Zajszűrés**: A `/boot` és `/boot/efi` statikus rendszerkötetek automatikusan kikerültek az alapértelmezett felderítésből, megelőzve a hamis riasztásokat a TUI felületen.
- **Windows telepítő javítása**: A `windowsSetup.bat` közvetlenül a virtuális környezetből hívja meg a Pythont a `.bat` alapú `activate` helyett, ezzel megszüntetve a telepítési elakadásokat.
- **Hálózati sebesség**: A forgalommérő átváltott `KB/s`-ről a szabványos `Mb/s` (Megabit/másodperc) kijelzésre.