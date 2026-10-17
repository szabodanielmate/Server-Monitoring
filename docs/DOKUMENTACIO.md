# Server Monitoring – teljes dokumentáció

A dokumentáció a projekt 2026. október 17-én átvizsgált forráskódját írja le. A példákban szereplő alapértékek a jelenlegi implementációra vonatkoznak. Az ábrák Mermaid formátumúak; megjelenítésükhöz Mermaid-támogatású Markdown-nézet szükséges, például a GitHub fájlnézete.

## Tartalom

1. [Rendeltetés](#1-rendeltetés)
2. [Rendszerkövetelmények és függőségek](#2-rendszerkövetelmények-és-függőségek)
3. [Fájlok és felelősségek](#3-fájlok-és-felelősségek)
4. [Topológia és adatáramlás](#4-topológia-és-adatáramlás)
5. [Telepítés és indítás](#5-telepítés-és-indítás)
6. [Konfiguráció](#6-konfiguráció)
7. [Adatgyűjtés és megjelenítés](#7-adatgyűjtés-és-megjelenítés)
8. [Riasztások](#8-riasztások)
9. [Naplózás és tárolás](#9-naplózás-és-tárolás)
10. [Üzemeltetés és hibaelhárítás](#10-üzemeltetés-és-hibaelhárítás)
11. [Fejlesztői áttekintés és korlátok](#11-fejlesztői-áttekintés-és-korlátok)

## 1. Rendeltetés

A program egy helyi gép erőforrásait figyeli, teljes képernyős terminálfelületen jeleníti meg az eredményeket, és tartós CPU-, RAM- vagy lemezterhelés esetén riasztást készít. Az értesítések opcionálisan Discordra és Telegramra küldhetők.

| Funkció | Megjelenítés | Küszöbértékes riasztás |
| --- | --- | --- |
| Összesített CPU-használat | Igen | Igen |
| RAM-használat | Igen | Igen |
| Partíciók telítettsége | Igen | Igen, partíciónként |
| Összesített hálózati sebesség | Igen | Nincs |
| Docker-konténerek állapota és healthcheckje | Igen, opcionálisan | Nincs |

A program nem végez automatikus hibajavítást, konténer-újraindítást vagy lemeztakarítást. Nincs webes felület, bejövő HTTP-szolgáltatás, idősoros adatbázis vagy több gépet összesítő központi komponens. A rendszeradatokat azon a gépen méri, ahol a Python-folyamat fut; konténerbe telepítés esetén a futtatási környezet korlátozhatja a látható adatokat.

## 2. Rendszerkövetelmények és függőségek

### Futtatási környezet

- A projekt README-je Python **3.10+** verziót jelöl meg. A telepítők csak a Python elérhetőségét ellenőrzik, a verziókövetelményt külön nem validálják.
- Célplatformok: Linux, macOS és Windows. A platformfüggetlen tervezés nem jelent minden platformon elvégzett futtatási tesztet.
- Python `venv` és `pip` szükséges a telepítőkhöz. Unix rendszereken Bash, Windowson a `.bat` fájlokhoz parancsértelmező szükséges.
- Írási jog szükséges a projektkönyvtárhoz a virtuális környezet, a konfiguráció és a napló létrehozásához.
- A csomagok letöltéséhez hálózat szükséges. Futás közben külső hálózati kapcsolatot az engedélyezett értesítési csatornák igényelnek.
- A Docker-funkcióhoz elérhető Docker Engine vagy Docker Desktop és a Docker API használatára jogosult felhasználó szükséges.

### Közvetlen Python-függőségek

Az alábbi verziófeltételek a projekt `requirements.txt` fájljából származnak, nem a gépen telepített verziókat jelölik.

| Csomag | Deklarált verzió | Szerep | Használó modul |
| --- | --- | --- | --- |
| `psutil` | `>=5.9.0` | CPU, memória, partíciók, lemezfoglaltság, hálózati számlálók | `src/metrics.py`, `configure.py` |
| `rich` | `>=13.0.0` | Élő terminálfelület, táblázatok, panelek, interaktív kérdések | `monitor.py`, `configure.py` |
| `httpx` | `>=0.27.0` | Szinkron HTTP POST kérések az értesítésekhez | `src/notifier.py` |
| `python-dotenv` | `>=1.0.0` | `.env` betöltése környezeti változókká | `src/config.py` |
| `docker` | `>=7.0.0` | Python Docker SDK, kapcsolat és konténeradatok | `src/metrics.py` |

A Docker Python-csomagot a telepítő akkor is telepíti, ha a Docker-monitorozás ki van kapcsolva. Kézi telepítésnél a program kezeli a `docker` import hiányát, de a többi közvetlen függőség szükséges az induláshoz.

A standard könyvtári `os`, `sys`, `time`, `socket`, `pathlib`, `typing` és `logging` modulokat nem kell külön telepíteni.

A közvetett függőségeket a pip oldja fel. Nincs rögzített verziókat tartalmazó lockfájl vagy felső verziókorlát, ezért két külön időpontban végzett telepítés eltérő csomagverziókat eredményezhet. Az adott telepítés ellenőrzése Unix alatt:

```bash
./.venv/bin/python -m pip list
./.venv/bin/python -m pip check
```

Windows PowerShellben:

```powershell
.\.venv\Scripts\python.exe -m pip list
.\.venv\Scripts\python.exe -m pip check
```

## 3. Fájlok és felelősségek

| Fájl | Feladat |
| --- | --- |
| `monitor.py` | Belépési pont, inicializálás, mérési ciklus, Rich felület, riasztásellenőrzések meghívása |
| `src/config.py` | Projektgyökér meghatározása, `.env` betöltése, `Config` osztály |
| `src/metrics.py` | `MetricsCollector`: rendszer- és Docker-adatok összegyűjtése |
| `src/notifier.py` | `AlertNotifier`: időzítők, küszöbök, üzenetformázás és küldés |
| `src/logger.py` | Közös `server_monitor` logger és forgó fájlkezelő |
| `src/__init__.py` | Python-csomagjelölő |
| `configure.py` | Küszöbök, partíciók, Docker és értesítések interaktív beállítása |
| `.env.example` | Másolható konfigurációs sablon |
| `.env` | Helyi beállítások és opcionális értesítési hitelesítő adatok; futás során létrehozandó |
| `requirements.txt` | Közvetlen Python-függőségek |
| `setup.sh`, `windowsSetup.bat` | Környezet telepítése, konfigurálás és opcionális azonnali indítás |
| `run.sh`, `windowsRun.bat` | A monitor indítása a virtuális környezetből |
| `.gitignore` | Többek között a `.venv`, `.env`, Python-cache, `.DS_Store`, valamint az aktív és archivált szervernaplók kizárása |
| `README.md` | Rövid projektismertető és gyorsindítás |

## 4. Topológia és adatáramlás

### Komponensek és külső kapcsolatok

```mermaid
flowchart LR
    OS["Helyi operációs rendszer"] -->|psutil| MET["src/metrics.py"]
    DOCKER["Docker Engine / Desktop"] -->|Docker SDK| MET
    ENV[".env és környezeti változók"] --> CFG["src/config.py"]
    CFG --> MAIN["monitor.py"]
    CFG --> MET
    CFG --> ALERT["src/notifier.py"]
    CFG --> LOG["src/logger.py"]
    MET -->|Mért értékek és konténerlista| MAIN
    MAIN --> UI["Rich terminálfelület"]
    MAIN -->|CPU, RAM, lemezek| ALERT
    MAIN -->|Indulás és leállás| LOG
    ALERT --> LOG
    LOG --> FILE["server_monitor.log és archívumok"]
    ALERT -->|HTTP POST, ha beállított| DISCORD["Discord webhook"]
    ALERT -->|HTTPS POST, ha beállított| TELEGRAM["Telegram Bot API"]
```

A monitor Docker-kliense a `docker.from_env()` beállításait használja. Ha a környezet távoli Docker-végpontra mutat, a konténerlista arról érkezhet, miközben a CPU-, RAM-, lemez- és hálózati adatok továbbra is a Python-folyamat helyi környezetéből származnak.

### Telepítési útvonal

```mermaid
flowchart TD
    SETUP["setup.sh / windowsSetup.bat"] --> PY["Python elérhetőségének ellenőrzése"]
    PY --> VENV[".venv létrehozása vagy újrahasználata"]
    VENV --> PIP["pip frissítése, requirements.txt telepítése"]
    PIP --> EXISTS{"Van .env?"}
    EXISTS -->|Nincs| CONF["configure.py"]
    EXISTS -->|Van| ASK{"Újrakonfigurálás?"}
    ASK -->|Igen| CONF
    ASK -->|Nem| START{"Azonnali indítás?"}
    CONF --> ENV[".env mentése"]
    ENV --> START
    START -->|Igen| MON["monitor.py indítása"]
    START -->|Nem| END["Később run.sh / windowsRun.bat"]
```

Az ábra a telepítők szándékolt menetét mutatja. A Windows újrakonfigurálási kérdésének ismert változókiértékelési hibáját a hibaelhárítás rész ismerteti.

### Futási ciklus

```mermaid
flowchart TD
    RUN["run.sh / windowsRun.bat"] --> MAIN["monitor.py betöltése"]
    MAIN --> INIT["Config, logger, MetricsCollector, AlertNotifier"]
    INIT --> SYS["Rendszermetrikák lekérése"]
    SYS --> ENABLED{"Docker engedélyezett?"}
    ENABLED -->|Igen| DOC["Konténeradatok lekérése"]
    ENABLED -->|Nem| EMPTY["Üres konténerlista"]
    DOC --> CHECK["CPU, RAM és lemezek riasztásellenőrzése"]
    EMPTY --> CHECK
    CHECK --> UI["Terminálfelület frissítése"]
    UI --> SLEEP["CHECK_INTERVAL idejű várakozás"]
    SLEEP --> SYS
    UI -. "Ctrl+C a fő ciklusban" .-> STOP["Leállási napló, kilépés"]
```

A lépések sorban futnak. A tényleges mintaköz a beállított várakozásból és az adatgyűjtés, értesítésküldés, illetve megjelenítés idejéből áll. Az alapértelmezett 3 másodperc ezért nem garantált pontos mintavételi periódus.

## 5. Telepítés és indítás

A parancsokat a projekt gyökérkönyvtárából futtasd.

### Linux és macOS

```bash
python3 --version
chmod +x setup.sh run.sh
./setup.sh
```

A telepítő létrehozza a `.venv` környezetet, telepíti a csomagokat, majd szükség esetén megnyitja a konfigurátort. A végén felajánlja az indítást. Később:

```bash
./run.sh
```

A Unix-indító hiányzó Python-környezet vagy `.env` esetén meghívja a telepítőt, majd annak visszatérése után maga is elindítja a monitort. Ha a beágyazott telepítő már elindított egy monitort, annak leállása után az indító újra elindíthatja azt. Az első telepítést ezért közvetlenül a `setup.sh` futtatásával érdemes végezni.

### Windows

PowerShellből:

```powershell
python --version
.\windowsSetup.bat
```

Későbbi indítás:

```powershell
.\windowsRun.bat
```

A Windows-indító hiányzó virtuális környezet esetén a `windowsSetup.bat` fájlt hívja, majd kilép; ebben az ágban az indulás a telepítőben adott választól függ. Meglévő környezet esetén aktiválja azt, és futtatja a `monitor.py` fájlt. A `.env` meglétét a Windows-indító nem ellenőrzi.

### Kézi telepítés, varázsló nélkül

Unix:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
# Csak ha még nincs saját .env fájlod:
cp .env.example .env
# Szerkeszd a .env fájlt, majd:
./.venv/bin/python monitor.py
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# Csak ha még nincs saját .env fájlod:
Copy-Item .env.example .env
# Szerkeszd a .env fájlt, majd:
.\.venv\Scripts\python.exe monitor.py
```

Leállítás: **Ctrl+C**. A fő ciklus ezt naplózza és 0-s kilépési kóddal zárul. Az indítás előtti konfigurációs vagy importhibákra ez a kezelés nem terjed ki.

## 6. Konfiguráció

A `src/config.py` a projektgyökérben lévő `.env` fájlt tölti be. A már meglévő folyamat-környezeti változók elsőbbséget élveznek. Az értékek a modul betöltésekor állnak be; módosítás után indítsd újra a monitort.

| Változó | Kódbeli alapérték | Jelentés |
| --- | --- | --- |
| `CPU_THRESHOLD` | `85.0` | CPU-riasztási küszöb, százalék |
| `RAM_THRESHOLD` | `90.0` | RAM-riasztási küszöb, százalék |
| `DISK_THRESHOLD` | `90.0` | Minden figyelt lemez közös küszöbe, százalék |
| `CHECK_INTERVAL` | `3` | Ciklusvégi várakozás, egész másodperc |
| `ALERT_DURATION` | `30` | Tartós túlterhelés szükséges ideje, egész másodperc |
| `ALERT_COOLDOWN` | `300` | Azonos hibaperióduson belüli ismétlés időköze, egész másodperc |
| `MONITORED_DISKS` | Üres | Vesszővel elválasztott csatolási pontok vagy eszköznevek; üresen automatikus felderítés |
| `ENABLE_DOCKER` | `false` | Bekapcsoló értékek: `true`, `1`, `yes`, kis- és nagybetűtől függetlenül |
| `DISCORD_WEBHOOK_URL` | Üres | Discord webhook címe; üresen nincs Discord-küldés |
| `TELEGRAM_BOT_TOKEN` | Üres | Telegram bot tokenje |
| `TELEGRAM_CHAT_ID` | Üres | Célbeszélgetés azonosítója; Telegramhoz a token és az ID egyaránt szükséges |

**Docker-alapérték eltérés:** a kód hiányzó beállítás esetén kikapcsolja a Docker-funkciót, de a `.env.example` `true` értéket tartalmaz, és a konfigurátor is alapból felajánlja a bekapcsolást.

Minimális, külső értesítések nélküli példa:

```dotenv
CPU_THRESHOLD=85.0
RAM_THRESHOLD=90.0
DISK_THRESHOLD=90.0
CHECK_INTERVAL=3
ALERT_DURATION=30
ALERT_COOLDOWN=300
MONITORED_DISKS=
ENABLE_DOCKER=false
DISCORD_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Partíciópéldák, a tényleges géphez igazítva:

```dotenv
# Linux: gyökér és külön adattároló
MONITORED_DISKS=/,/mnt/storage
```

```dotenv
# Windows: a normalizálás miatt a meghajtó betűjele is használható
MONITORED_DISKS=C:,D:
```

### A konfigurátor viselkedése

A `configure.py` bekéri a CPU-, RAM- és lemezküszöböt, megjeleníti a talált partíciókat, majd rákérdez a Dockerre és külön-külön az értesítési csatornákra. Az időzítéseket nem kérdezi meg: mindig `3`, `30`, `300` értékkel írja ki őket.

Az `all` választás az éppen felderített partíciók konkrét listáját menti. Új lemezek későbbi automatikus felvételéhez hagyd üresen a `MONITORED_DISKS` értékét. A konfigurátor szűrése nem teljesen azonos a futás közbeni szűréssel.

Újrafuttatáskor a konfigurátor felülírja a `.env` fájlt, és nem tölti vissza a korábbi értékeket alapválaszként. Közvetlenül futtatva az aktuális munkakönyvtárba ment, ezért a projektgyökérből indítsd:

```bash
./.venv/bin/python configure.py
```

```powershell
.\.venv\Scripts\python.exe configure.py
```

A numerikus bevitelhez nincs tartományellenőrzés. Százalékos értékhez pontot használj, például `85.5`. Hibás szöveg vagy tizedes időzítés importkori hibát okozhat. Használj 0–100 közötti küszöböket, pozitív mintaközt és nem negatív riasztási időket; ezt jelenleg az üzemeltetőnek kell biztosítania.

## 7. Adatgyűjtés és megjelenítés

### CPU és memória

A CPU összesített terhelését a `psutil.cpu_percent(interval=None)` adja. Az első minta még nem feltétlenül reprezentatív. A RAM adatai a `psutil.virtual_memory()` eredményéből érkeznek. A kijelzett használt és teljes memória `1024³` bájttal osztott érték, tehát a felület `GB` felirata alatt valójában GiB szerepel.

### Lemezek

A felderítés alapja a `psutil.disk_partitions(all=False)`. A program:

1. Kihagyja a `squashfs`, `tmpfs`, `devtmpfs`, `overlay`, `iso9660`, `nullfs`, `autofs`, `proc`, `sysfs`, `devpts` fájlrendszereket.
2. Kihagyja a `/System/Volumes/Update` vagy `/System/Volumes/VM` szöveget tartalmazó csatolási pontokat.
3. Automatikus módban kihagyja a `/boot`, `/boot/efi` és `/boot/` alatti köteteket.
4. Ha van `MONITORED_DISKS`, csatolási pont vagy eszköznév alapján szűr. Az összehasonlítás kisbetűsítve, a záró perjelek eltávolításával történik.
5. Csatolási pont alapján kiszűri az ismétlődéseket, és kihagyja a nulla méretű köteteket.

A boot-kötetek explicit kiválaszthatók, de a fájlrendszer- és macOS-kizárások ettől még érvényben maradnak. Ha automatikus módban nincs eredmény, a program megpróbálja a `/` lemezhasználatát lekérni. Explicit lista esetén nincs ilyen helyettesítés: hibás lista mellett üres lehet a lemeztábla és elmarad a lemezriasztás.

A kapacitások itt is GiB-ben számolódnak, `GB` felirattal. A lemezmérés telítettséget jelent, nem I/O-sebességet vagy hardveres állapotvizsgálatot.

### Hálózat

A program a `psutil.net_io_counters()` összesített bájtszámlálóinak különbségét osztja az eltelt idővel:

```text
bájt/másodperc = (aktuális számláló − előző számláló) / eltelt másodperc
kijelzett érték = bájt/másodperc × 8 / 1024²
```

A felirat `Mb/s`, de a számítás bináris Mibit/s-nak felel meg, nem a decimális, 1 000 000 bittel számoló Mbit/s-nak. Ez az aktuális összesített forgalom becslése, nem internetes sebességteszt. Az `AKTÍV` jelzés állandó felirata ennek a sornak, nem internetelérési vizsgálat eredménye.

### Docker

Inicializáláskor a gyűjtő megpróbál kapcsolódni, és `ping()` hívással ellenőrzi a kapcsolatot. Minden ciklusban `containers.list(all=True)` történik, így a leállított konténerek is szerepelnek.

A megjelenített adatok: konténernév, állapot, healthcheck státusz és az első image-tag. Tag hiányában `unknown`, healthcheck hiányában `-` jelenik meg. A program a Docker által már előállított healthcheck eredményét olvassa, saját ellenőrző parancsot nem futtat.

Induláskori kapcsolódási hiba után nincs új klienslétrehozási kísérlet; a monitor újraindítása szükséges. Lekérdezési hibánál üres vagy részleges lista is visszatérhet, külön hibajelzés nélkül.

### Felület és állapotjelzések

| Feltétel | Jelzés |
| --- | --- |
| Érték kisebb, mint a küszöb 80%-a | Zöld `OK` |
| Érték legalább a küszöb 80%-a, de még a küszöb alatt van | Sárga `FIGYELEM` |
| Érték eléri vagy meghaladja a küszöböt | Piros `KRITIKUS` |

85%-os CPU-küszöbnél a sárga jelzés 68%-tól, a piros 85%-tól látható. A szín azonnal változik; a külső riasztásra külön időzítés vonatkozik.

A Rich felület másodpercenként két újrarajzolásra van beállítva, ez nem jelent másodpercenként két új mérést. A fejléc időbélyege az utolsó felületgenerálás ideje. Docker engedélyezésekor a fő nézet két oszlopra oszlik.

## 8. Riasztások

### Döntési folyamat

```mermaid
flowchart TD
    VALUE["Új érték, metrikánként"] --> LIMIT{"Érték legalább a küszöb?"}
    LIMIT -->|Nem| RESET["Kezdőidő és alerted_states törlése"]
    LIMIT -->|Igen| FIRST{"Van túlterhelési kezdőidő?"}
    FIRST -->|Nincs| SAVE["Kezdőidő mentése és INFO napló"]
    FIRST -->|Van| DURATION{"Eltelt az ALERT_DURATION?"}
    DURATION -->|Nem| WAIT["Következő minta"]
    DURATION -->|Igen| SENT{"Volt riasztás ebben a hibaperiódusban?"}
    SENT -->|Nem| SEND["WARNING napló és beállított csatornák küldési kísérlete"]
    SENT -->|Igen| COOL{"Eltelt az ALERT_COOLDOWN?"}
    COOL -->|Nem| WAIT
    COOL -->|Igen| SEND
    SEND --> STORE["Riasztási időpont és állapot mentése"]
    STORE --> WAIT
    RESET --> WAIT
    SAVE --> WAIT
```

Az állapot CPU-ra, RAM-ra és minden lemezre külön él. Az azonosító a metrika kisbetűsített neve, például `cpu` vagy `lemez (/)`.

Alapértékekkel, ideális 3 másodperces mintaközzel:

| Idő az első magas mintától | CPU | Eredmény |
| --- | --- | --- |
| 0 mp | 90% | Időzítő indul |
| 3–27 mp | Minden minta legalább 85% | Még nincs riasztás |
| 30 mp | 90% | Első riasztási kísérlet |
| 330 mp | Továbbra is legalább 85% | Ismételt riasztási kísérlet |
| Következő, 85% alatti minta | 60% | Hibaperiódus lezárása |

A „folyamatos” túlterhelés az egymást követő mintákra vonatkozik. A két minta közötti rövid visszaeséseket a program nem feltétlenül látja.

### Fontos időzítési részletek

- Új hibaperiódus első riasztását a korábbi hibaperiódus cooldownja nem korlátozza. Normál minta után az `alerted_states` törlődik, bár a legutóbbi riasztási idő megmarad.
- Az első magas minta csak időzítőt indít, ezért `ALERT_DURATION=0` mellett is egy következő magas minta szükséges a riasztáshoz.
- Újraindításkor minden időzítő és állapot elveszik.
- Nincs helyreállási értesítés, automatikus hibajavítás vagy csatornánkénti újraküldési sor.
- Sikertelen küldés és beállított csatorna hiánya esetén is riasztottnak jelöli az állapotot, és érvényesíti az ismétlési időt.
- Az időzítés `time.time()` alapján működik; a rendszeróra módosítása befolyásolhatja.

### Értesítési csatornák

Az üzenet tartalmazza a helyi gép nevét, a metrika nevét, a jelenlegi értéket, a küszöböt, az észlelt fennállás idejét és a helyi időbélyeget.

| Csatorna | Kérés | Sikernek tekintett HTTP-kód |
| --- | --- | --- |
| Discord | A megadott webhook URL-re küldött POST, `content` JSON-mezővel | `200`, `204` |
| Telegram | POST a `https://api.telegram.org/bot<TOKEN>/sendMessage` címre, `chat_id`, `text`, `parse_mode` mezőkkel | `200` |

Mindkét csatorna külön `httpx.Client(timeout=5.0)` klienst használ. A kérések egymás után, a fő mérési ciklusban futnak; a lassú küldés késlelteti a következő mérést. Az 5 másodperc HTTPX-időtúllépési beállítás, nem az egész ciklus garantált felső időkorlátja.

A Telegram régi `Markdown` módot kap. A program a dupla csillagokat szimplára cseréli, de a dinamikus mezők speciális karaktereit nem escape-eli teljeskörűen, ezért egyes gép- vagy metrikanevek formázási hibát okozhatnak.

## 9. Naplózás és tárolás

A napló a projektgyökér `server_monitor.log` fájlja. A `RotatingFileHandler` beállítása: `5 × 1024 × 1024` bájt névleges mérethatár és három archívum. Ez nagyjából 20 MiB helyigény az aktív és a három archív fájlra együtt.

```text
server_monitor.log
server_monitor.log.1
server_monitor.log.2
server_monitor.log.3
```

| Szint | Esemény |
| --- | --- |
| `INFO` | Főprogram indulása, Ctrl+C-s leállás, túlterhelési időzítő indulása |
| `WARNING` | Riasztás létrehozása |
| `ERROR` | Kezelt HTTP-hibák és értesítésküldési kivételek |

A „Riasztás kiküldve” bejegyzés **a hálózati küldés előtt** keletkezik, így nem igazolja a kézbesítést. A program nem naplóz minden mért értéket, a Docker-hibákat pedig több helyen elnyeli.

A `.env` tokeneket és webhook címet tartalmazhat. A fájl szerepel a `.gitignore` listában. A konfigurátor ezeket az értékeket nem maszkolt bevitellel kéri be. A küldési kivételek szövege URL-t, így akár érzékeny adatot is tartalmazhat; megosztás előtt ellenőrizd a naplót. A `.gitignore` `server_monitor.log*` szabálya az aktív naplót és minden ilyen nevű archív vagy tömörített változatot (például `server_monitor.log.1`, `server_monitor.log.3.gz`) kizár a projekt minden almappájában is. A `.DS_Store` fájlok szintén minden almappában kizártak.

## 10. Üzemeltetés és hibaelhárítás

### Háttérben tartás

A program alapvetően interaktív terminálalkalmazás. Unix alatt egy már telepített `tmux` használatával megtartható a munkamenet:

```bash
tmux new -s monitor
./run.sh
```

Leválás: `Ctrl+B`, majd `D`. Visszatérés:

```bash
tmux attach -t monitor
```

A `tmux` opcionális rendszerprogram, nem Python-függőség. Nincs mellékelt systemd-unit, Windows-szolgáltatás, automatikus rendszerindítás vagy külön headless mód. A README-ben szereplő VBS-példa az ablakot rejti el; szolgáltatásfelügyeletet és automatikus újraindítást nem biztosít.

### Gyakori hibák

| Tünet | Lehetséges ok és teendő |
| --- | --- |
| `python` vagy `python3` nem található | Ellenőrizd a Python telepítését és a PATH-ot. |
| `No module named ...` | A megfelelő `.venv` Pythonjával telepítsd a `requirements.txt` csomagjait. |
| `ValueError` induláskor | Ellenőrizd a `.env` és a külső környezeti változók számait; százalékhoz pont, időzítéshez egész szám kell. |
| Negatív várakozási idő miatti leállás | Állíts pozitív `CHECK_INTERVAL` értéket. |
| Nem változik a beállítás | Indítsd újra a monitort; ellenőrizd, nem írja-e felül külső környezeti változó a `.env`-et. |
| Nem jelenik meg lemez | Ellenőrizd a csatolási pontot, a `MONITORED_DISKS` listát és a kizárt fájlrendszereket. |
| Üres a Docker-tábla | Lehet üres lista, hiányzó Docker SDK, API-hozzáférési vagy kapcsolódási hiba; a felület nem különbözteti meg ezeket. |
| Docker elindítása után is üres a lista | Ha a monitor indulásakor nem volt kapcsolat, indítsd újra a monitort. |
| Piros státusz mellett nincs üzenet | Várd meg az `ALERT_DURATION` idejét; ellenőrizd a csatornabeállításokat, a cooldown állapotát és a napló hibáit. |
| A napló küldést jelez, üzenet mégsem érkezik | A bejegyzés nem kézbesítési igazolás; keresd az utána következő HTTP- vagy hálózati hibát. |
| Telegram HTTP 400 | Ellenőrizd a célazonosítót és a Markdownban problémás gép-/metrikaneveket. |
| A felület időnként megakad | A rendszer-, Docker- és HTTP-hívások a fő ciklust blokkolhatják. |
| Windows alatt az újrakonfigurálási válasz hatástalan | A `RECONF` változó ugyanabban a zárójeles blokkban `%RECONF%` alakban olvasódik ki, ahol beállítják. Futtasd közvetlenül a `.venv\Scripts\python.exe configure.py` parancsot. |

### Ellenőrzés telepítés után

1. A megfelelő Python-környezetben futtasd a `pip check` parancsot.
2. Indítsd el a programot, és ellenőrizd a CPU-, RAM- és lemezsorokat.
3. Docker használatakor ellenőrizd, hogy a várt konténerek láthatók-e.
4. Ellenőrizd a `server_monitor.log` indulási bejegyzését.
5. Ha értesítést is tesztelsz, erre kijelölt csatornát használj. A CPU-küszöb ideiglenes `0` értéke riasztást válthat ki terhelésgenerálás nélkül; utána állítsd vissza az értéket és indítsd újra a programot. Ez a teszt tényleges üzeneteket küldhet.

## 11. Fejlesztői áttekintés és korlátok

### Belső interfészek

| Hívás | Visszatérés / hatás |
| --- | --- |
| `MetricsCollector(enable_docker)` | Docker-kliens és kezdeti hálózati számlálók inicializálása |
| `get_system_metrics()` | Szótár: `cpu_percent`, `ram_percent`, `ram_used_gb`, `ram_total_gb`, `disks`, `net_upload_mbps`, `net_download_mbps` |
| `_get_disks_metrics()` | Lista, elemenként: `device`, `mount`, `fstype`, `percent`, `used_gb`, `total_gb` |
| `get_docker_metrics()` | Lista, elemenként: `name`, `status`, `health`, `image` |
| `generate_layout(metrics, containers)` | Rich `Layout` fejléc-, fő- és láblécrésszel |
| `check_and_alert(metrics)` | CPU, RAM és minden kapott lemez továbbítása a notifiernek |
| `AlertNotifier.check_metric(name, value, threshold)` | Küszöbellenőrzés, állapotkezelés, szükség esetén küldés |
| `setup_logger()` | Közös logger visszaadása; csak meglévő handler hiányában ad új fájlkezelőt |

Az `AlertNotifier` három memóriabeli szótárat használ: `breach_start_times`, `last_alert_times`, `alerted_states`. Nincs lemezre mentett riasztási állapot. Ha egy korábban figyelt lemez eltűnik a mért listából, a régi állapotát nem takarítja ki külön a program.

A `monitor.py` már importáláskor létrehozza a naplózót, a gyűjtőt és a riasztáskezelőt. Emiatt puszta importja is naplófájl-létrehozást és engedélyezett Docker mellett kapcsolódási kísérletet okozhat. A fő ciklus csak a közvetlen indításkor lép életbe.

### A jelenlegi verzió határai

- Nincs automatikus tesztcsomag a vizsgált projektfájlok között.
- Nincs konfigurációs séma, teljes validáció vagy futás közbeni újratöltés.
- Nincs általános hibakezelés a fő ciklus körül a `KeyboardInterrupt` kivételén túl; nem kezelt gyűjtési hiba leállíthatja a folyamatot.
- Nincs HTTP-újrapróbálkozás, csatornánkénti kézbesítési állapot vagy helyreállási üzenet.
- A Docker-kapcsolat hibái nem kapnak egyértelmű naplózást vagy felületi állapotot.
- A hálózat és a Docker csak megjelenítési funkció; konténerenkénti CPU-/RAM-adatok sincsenek.
- A Windows-telepítő zárójeles blokkban használt `%errorlevel%` ellenőrzése is korábban kiértékelt értéket láthat a virtuális környezet létrehozásakor.
- Az indítók továbbadják a parancssori argumentumokat, de a `monitor.py` nem definiál parancssori kapcsolókat.

Ez a dokumentum forráskód-alapú leírás; elkészítése nem jelent Windows/Linux futtatási, valódi webhook-kézbesítési vagy teljes platformkompatibilitási tesztet.
