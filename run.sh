#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# Ha még nem létezik a .venv vagy a pip benne, futtassuk le a setupot
if [ ! -f ".venv/bin/python" ] || [ ! -f ".env" ]; then
    echo "[!] A környezet még nincs előkészítve. Setup indítása..."
    bash setup.sh
fi

# Futtatás
exec ./.venv/bin/python monitor.py "$@"