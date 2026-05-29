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
- **brain.py** ist der Groq LLM-Kern (llama-3.3-70b-versatile, kostenlos) – er entscheidet welches Tool aufgerufen wird (Function Calling + ReAct-Loop)
- **memory.py** verwaltet Short-Term (letzte 20 Nachrichten) und Long-Term (SQLite + ChromaDB + lokale sentence-transformers Embeddings) Gedächtnis
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

- **Python 3.11**, async/await überall wo sinnvoll
- **Keine globalen Singletons** – Klassen werden in `main.py` instanziiert und per Parameter weitergegeben
- **Jedes Tool-Modul** ist eigenständig importierbar und ohne laufenden Jarvis testbar
- **Fehler in Tools** werfen Exceptions nie still – sie geben einen lesbaren Fehler-String zurück damit der Brain eine sinnvolle Antwort formulieren kann
- **`.env`** enthält alle Secrets – nie hardcoden, nie committen

## Kosten-Prinzip

**$0/Monat** – alles kostenlos:
- LLM: Groq API (kostenlos, llama-3.3-70b-versatile) → API Key auf groq.com
- STT: faster-whisper (lokal)
- TTS: Kokoro (lokal) + macOS say (Fallback)
- Wake-Word: openwakeword (lokal)
- Embeddings: sentence-transformers all-MiniLM-L6-v2 (lokal, ~90 MB)
- DB: SQLite + ChromaDB (lokal)
- Browser: Playwright headless (lokal)
- Google APIs: Gmail + Calendar (kostenlose Kontingente reichen)

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

**LLM-Modell wechseln (alle kostenlos auf Groq):**
- `.env`: `JARVIS_LLM_MODEL=llama-3.3-70b-versatile` → Standard, beste Qualität
- `.env`: `JARVIS_LLM_MODEL=llama-3.1-8b-instant` → schneller, weniger komplex

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
