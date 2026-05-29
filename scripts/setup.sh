#!/bin/bash
# JARVIS v3 – Einmaliges Setup-Script
set -e

echo "=== JARVIS v3 Setup ==="

# Python 3.12 prüfen
if ! command -v python3.12 &>/dev/null; then
    echo "Installiere Python 3.12..."
    brew install python@3.12
fi

# Virtual Environment
if [ ! -d ".venv" ]; then
    echo "Erstelle venv..."
    python3.12 -m venv .venv
fi

source .venv/bin/activate

# Dependencies
echo "Installiere Python-Pakete..."
pip install --upgrade pip
pip install -r requirements.txt

# Playwright Browser
echo "Installiere Playwright Chromium..."
playwright install chromium

# .env prüfen
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  .env wurde erstellt. Bitte OPENAI_API_KEY eintragen!"
    echo "    Öffne: nano .env"
fi

# Data-Verzeichnis
mkdir -p data

echo ""
echo "✅ Setup abgeschlossen!"
echo ""
echo "Nächste Schritte:"
echo "  1. Trage deinen OpenAI API Key in .env ein"
echo "  2. source .venv/bin/activate"
echo "  3. python main.py"
echo ""
echo "macOS Berechtigungen (WICHTIG):"
echo "  Systemeinstellungen → Datenschutz → Mikrofon → Terminal ✓"
echo "  Systemeinstellungen → Datenschutz → Bedienungshilfen → Terminal ✓"
