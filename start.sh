#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -f ".env" ]; then
    echo "Brak pliku .env — skopiuj .env.example do .env i uzupelnij."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Tworzenie virtualenv..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

echo "Start skryptu..."
python main.py
