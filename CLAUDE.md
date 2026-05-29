# JARVIS v3 – Claude Code Kontext

## Was ist dieses Projekt?

JARVIS ist ein vollständig autonomer, sprechender KI-Assistent der lokal auf einem MacBook Air M4 läuft. Er hört auf das Wake-Word "Hey Jarvis", versteht gesprochene Befehle, führt Aktionen auf dem Mac aus und antwortet mit synthetischer Stimme – komplett ohne Cloud-Infrastruktur außer dem LLM.

## Architektur

```
main.py → listener → brain → tools → speaker
                ↕
            memory
```

- **listener.py** nimmt Audio auf, erkennt das Wake-Word und transkribiert mit faster-whisper
- **brain.py** ist der GPT-4o mini Kern – er entscheidet welches Tool aufgerufen wird (Function Calling)
- **memory.py** verwaltet Short-Term (letzte 20 Nachrichten) und Long-Term (SQLite + ChromaDB) Gedächtnis
- **speaker.py** gibt Antworten mit Kokoro TTS aus, Fallback auf macOS `say`
- **tools/** sind einzelne Module für macOS, Gmail, Calendar, Browser, Notion

## Ordnerstruktur

```
~/jarvis/
├── main.py              # Einstiegspunkt, async Event-Loop
├── core/
│   ├── brain.py         # LLM + Tool-Calling (GPT-4o mini)
│   ├── listener.py      # Mikrofon + Wake-Word + STT
│   ├── speaker.py       # TTS (Kokoro) + Fallback (say)
│   └── memory.py        # SQLite + ChromaDB
├── tools/
│   ├── macos.py         # AppleScript-Wrapper
│   ├── gmail.py         # Gmail OAuth2
│   ├── calendar.py      # Google Calendar
│   ├── browser.py       # Playwright headless
│   └── notion.py        # Notion API
├── scripts/
│   ├── setup.sh         # Einmaliges Setup
│   ├── morning_briefing.sh
│   └── install_launchagent.sh
├── tests/
├── data/                # SQLite DB + ChromaDB (gitignored)
├── .env                 # API Keys (gitignored)
├── requirements.txt
├── PLAN.md              # Checkliste mit allen Aufgaben
└── README.md            # Projektbeschreibung
```

## Entwicklungsumgebung starten

```bash
cd ~/jarvis
source .venv/bin/activate
python main.py
```

## Wichtige Konventionen

- **Python 3.12**, async/await überall wo sinnvoll
- **Keine globalen Singletons** – Klassen werden in `main.py` instanziiert und per Parameter weitergegeben
- **Jedes Tool-Modul** ist eigenständig importierbar und ohne laufenden Jarvis testbar
- **Fehler in Tools** werfen Exceptions nie still – sie geben einen lesbaren Fehler-String zurück damit der Brain eine sinnvolle Antwort formulieren kann
- **`.env`** enthält alle Secrets – nie hardcoden, nie committen

## Kosten-Prinzip

- Kostenlos wo möglich (faster-whisper, Kokoro, SQLite, ChromaDB, Playwright, Google APIs)
- Pay-per-Use nur für LLM-Calls: GPT-4o mini (~$0.0002/Anfrage)
- Einfache Tasks über Ollama (lokal, $0) routen wenn möglich
- Ziel: < $3/Monat bei 50–100 Anfragen/Tag

## Phase-Status

Aktuell in **Phase 1** (Voice & Control). Alle Skeleton-Dateien sind vorhanden, die Implementierung läuft nach PLAN.md.

- Phase 1: Voice-Loop, Wake-Word, STT/TTS, macOS-Steuerung
- Phase 2: Gmail, Calendar, Browser, Notion
- Phase 3: Long-Term Memory, ReAct-Loop, proaktiver Modus

## Häufige Aufgaben

**Neues Tool hinzufügen:**
1. Funktion in `tools/` schreiben (gibt immer einen String zurück)
2. Tool-Definition in `_TOOLS` Liste in `brain.py` eintragen
3. Lambda in `_TOOL_MAP` in `brain.py` eintragen

**faster-whisper Modell wechseln:**
- `base` (150 MB, ~100ms) → Standard
- `small` (500 MB, ~200ms) → besser bei Akzent oder Rauschen
- In `listener.py` Zeile `Listener(model_size="base")` ändern

**LLM-Modell wechseln:**
- `.env`: `JARVIS_LLM_MODEL=gpt-4o` für maximale Qualität
- `.env`: `JARVIS_LLM_MODEL=gpt-4o-mini` für normalen Betrieb (Standard)

## macOS-Berechtigungen (ohne die nichts funktioniert)

Systemeinstellungen → Datenschutz & Sicherheit:
- Mikrofon → Terminal aktivieren
- Bedienungshilfen → Terminal aktivieren
- Automation → Terminal aktivieren

## Tests ausführen

```bash
pytest tests/ -v
```

Tests laufen lokal ohne API-Keys (nur macOS-Tools und Speaker-Fallback).
