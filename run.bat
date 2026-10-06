@echo off
setlocal
cd /d "%~dp0"

:: 1. Python elérhetőség ellenőrzése
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] A Python nem talalhato a PATH-ban! Kerlek telepitsd a python.org-rol.
    pause
    exit /b 1
)

:: 2. Virtuális környezet (.venv) inicializálása Windowsra
if not exist ".venv\Scripts\python.exe" (
    echo [*] Windows virtualis kornyezet letrehozasa...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [*] Pip es fuggosegek telepitese...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo [✔] Telepites befejezodott!
) else (
    call .venv\Scripts\activate.bat
)

:: 3. Konfigurációs fájl ellenőrzése
if not exist ".env" (
    if exist ".env.example" (
        echo [!] .env nem talalhato, .env.example masolasa...
        copy .env.example .env >nul
    )
)

:: 4. A monitor indítása
python monitor.py %*

pause