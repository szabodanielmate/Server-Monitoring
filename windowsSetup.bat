@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Szerver Monitoring - Windows Telepito
echo ==========================================

:: 1. Python elérhetőség ellenőrzése
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] A Python 3 nem talalhato a PATH-ban!
    echo Kerlek toltsd le a https://www.python.org oldalrol,
    echo es a telepitesnel pipald be az "Add Python to PATH" opciot!
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
echo [OK] %PYTHON_VER% megtalalva.

:: 2. Virtuális környezet (.venv) vizsgálata
if not exist ".venv\Scripts\python.exe" (
    echo [*] .venv mappa letrehozasa...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [X] Nem sikerult letrehozni a virtualis kornyezetet!
        pause
        exit /b 1
    )
    echo [OK] .venv sikeresen letrehozva.
) else (
    echo [OK] .venv virtualis kornyezet mar letezik.
)

:: 3. Függőségek telepítése
call .venv\Scripts\activate.bat
echo [*] Pip es Python csomagok ellenorzese...
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if %errorlevel% neq 0 (
    echo [X] Hiba tortent a fuggosegek telepitese soran!
    pause
    exit /b 1
)
echo [OK] Minden fuggoseg sikeresen telepitve!

:: 4. .env fájl ellenőrzése
if not exist ".env" (
    if exist ".env.example" (
        echo [*] .env letrehozasa a .env.example alapjan...
        copy .env.example .env >nul
        echo [OK] .env fajl letrehozva.
    )
) else (
    echo [OK] .env konfiguracio megtalalva.
)

echo.
echo ==========================================
echo   Minden keszen all! All good to go!
echo ==========================================
echo.

:: 5. Azonnali indítás bekérése (Y/N)
set /p START_NOW="Elinditod most a monitoringot? [Y/n]: "
if /i "%START_NOW%"=="y" goto run
if "%START_NOW%"=="" goto run
goto end

:run
echo [*] Monitoring inditasa...
python monitor.py
goto finish

:end
echo Kesobbi inditashoz hasznald a run.bat fajlt!
pause

:finish