@echo off
setlocal
cd /d "%~dp0"

:: Ha még nincs felépítve a környezet, hívjuk meg a setupot
if not exist ".venv\Scripts\python.exe" (
    echo [!] A kornyezet nincs telepitve. Setup inditasa...
    call setup.bat
    exit /b
)

:: Környezet aktiválása és futtatás
call .venv\Scripts\activate.bat
python monitor.py %*

if %errorlevel% neq 0 (
    pause
)