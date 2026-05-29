# JARVIS v3 – Checkliste

---

## Setup

- [ ] Homebrew installieren (falls nicht vorhanden): `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- [ ] Python 3.12 installieren: `brew install python@3.12`
- [ ] Projektordner öffnen: `cd ~/jarvis`
- [ ] Virtual Environment erstellen: `python3.12 -m venv .venv`
- [ ] Virtual Environment aktivieren: `source .venv/bin/activate`
- [ ] `.env` Datei erstellen: `cp .env.example .env`
- [ ] OpenAI Account erstellen auf platform.openai.com
- [ ] OpenAI API Key in `.env` eintragen: `OPENAI_API_KEY=sk-...`
- [ ] $10 auf OpenAI aufladen (reicht 2–3 Monate)
- [ ] Alle Dependencies installieren: `pip install -r requirements.txt`
- [ ] Playwright Browser installieren: `playwright install chromium`
- [ ] macOS Berechtigung freischalten: Systemeinstellungen → Datenschutz → Mikrofon → Terminal ✓
- [ ] macOS Berechtigung freischalten: Systemeinstellungen → Datenschutz → Bedienungshilfen → Terminal ✓
- [ ] macOS Berechtigung freischalten: Systemeinstellungen → Datenschutz → Automation → Terminal ✓

---

## Phase 1 – Voice & Control

### Listener (STT)
- [x] `core/listener.py`: Mikrofon-Aufnahme mit `sounddevice` testen
- [x] `core/listener.py`: RMS-basierte Silence-Detection implementieren (1.5s Stille = Ende)
- [x] `core/listener.py`: faster-whisper Modell `base` herunterladen und integrieren (~150 MB, einmalig)
- [ ] `core/listener.py`: faster-whisper STT testen – kurzen Satz aufnehmen und transkribieren
- [x] `core/listener.py`: Wake-Word-Detection "Hey Jarvis" mit `openwakeword` einbauen
- [x] `core/listener.py`: Wake-Word in Hintergrund-Thread laufen lassen (non-blocking)

### Speaker (TTS)
- [ ] `core/speaker.py`: Kokoro TTS installieren: `pip install kokoro soundfile`
- [ ] `core/speaker.py`: Kokoro Modell beim ersten Start herunterladen (~300 MB)
- [ ] `core/speaker.py`: Kokoro TTS testen – kurzen Text vorlesen lassen
- [ ] `core/speaker.py`: macOS `say`-Fallback testen (funktioniert sofort ohne Setup)
- [x] `core/speaker.py`: Automatischen Fallback bei Kokoro-Fehler verifizieren

### macOS-Steuerung
- [ ] `tools/macos.py`: `open_app("Safari")` testen – öffnet Safari via AppleScript
- [ ] `tools/macos.py`: `send_notification("Test", "Hallo")` testen
- [ ] `tools/macos.py`: `get_frontmost_app()` testen – gibt aktive App zurück
- [ ] `tools/macos.py`: `set_volume(50)` testen
- [ ] `tools/macos.py`: `open_url("https://google.com")` testen

### Brain (LLM)
- [x] `core/brain.py`: GPT-4o mini API-Verbindung testen (simpler Prompt)
- [x] `core/brain.py`: System-Prompt auf Deutsch tunen
- [x] `core/brain.py`: Tool `open_app` via Function-Calling testen
- [x] `core/brain.py`: Tool `send_notification` via Function-Calling testen
- [x] `core/brain.py`: Tool `run_applescript` via Function-Calling testen

### Kern-Loop
- [x] `main.py`: Listener + Brain + Speaker zusammenführen
- [ ] `main.py`: Vollständigen 9-Schritte-Loop testen
- [x] `main.py`: Fehlerbehandlung einbauen (API-Fehler, Mikrofon-Fehler)
- [ ] **MEILENSTEIN**: Gesprochener Befehl "Hey Jarvis, öffne Safari" funktioniert end-to-end

---

## Phase 2 – Smart Automation

### Gmail
- [ ] Google Cloud Console öffnen: console.cloud.google.com
- [ ] Neues Projekt erstellen: "JARVIS"
- [ ] Gmail API aktivieren: APIs & Services → Library → Gmail API → Enable
- [ ] OAuth2 Credentials erstellen: Credentials → Create → OAuth Client ID → Desktop App
- [ ] `credentials.json` herunterladen und in `~/jarvis/` ablegen
- [ ] OAuth2 Flow einmal durchführen (Browser öffnet sich zur Autorisierung)
- [ ] `tools/gmail.py`: `read_emails()` testen – zeigt letzte 5 ungelesene E-Mails
- [ ] `tools/gmail.py`: `send_email()` testen – Test-Mail an eigene Adresse senden
- [x] `core/brain.py`: Tool `read_emails` im Tool-Calling registrieren
- [x] `core/brain.py`: Tool `send_email` im Tool-Calling registrieren
- [ ] Test: "Jarvis, lies mir meine ungelesenen E-Mails vor"

### Google Calendar
- [ ] Google Calendar API aktivieren (gleiches JARVIS-Projekt in Cloud Console)
- [ ] Calendar Scopes zu OAuth hinzufügen: `calendar.readonly` + `calendar.events`
- [ ] `tools/calendar.py`: `get_events()` testen – zeigt Termine der nächsten 7 Tage
- [ ] `tools/calendar.py`: `create_event()` testen – erstellt Test-Termin
- [x] `core/brain.py`: Tool `get_calendar_events` im Tool-Calling registrieren
- [x] `core/brain.py`: Tool `create_calendar_event` im Tool-Calling registrieren
- [ ] Test: "Jarvis, was steht diese Woche an?"

### Browser-Automation
- [ ] `tools/browser.py`: `search_web("Wetter München")` testen
- [ ] `tools/browser.py`: `take_screenshot_and_describe(url)` testen – Screenshot + Vision
- [ ] `tools/browser.py`: `goto_and_extract(url)` testen – Text von Webseite extrahieren
- [x] `core/brain.py`: Tool `search_web` im Tool-Calling registrieren
- [ ] Test: "Jarvis, google mir den Wetterbericht für morgen"

### Notion
- [ ] notion.so → Einstellungen → Integrationen → Neue Integration "JARVIS" erstellen
- [ ] Integration Token in `.env` eintragen: `NOTION_TOKEN=secret_...`
- [ ] Gewünschte Notion-Seite mit JARVIS-Integration teilen (Share → JARVIS einladen)
- [ ] `tools/notion.py`: `create_page()` testen – erstellt Test-Seite
- [ ] `tools/notion.py`: `search_pages()` testen – findet bestehende Seiten
- [x] `core/brain.py`: Tool `save_to_notion` im Tool-Calling registrieren
- [ ] Test: "Jarvis, speichere das in Notion"

### Tool-Routing finalisieren
- [x] Alle Tools in `brain.py` vollständig registriert (12 Tools)
- [ ] **MEILENSTEIN**: "Jarvis, lies meine E-Mails vor und erstell mir einen Kalender-Eintrag" funktioniert

---

## Phase 3 – Autonomous Agent

### Long-Term Memory
- [x] `core/memory.py`: SQLite `conversations`-Tabelle befüllt sich korrekt
- [x] `core/memory.py`: `facts`-Tabelle testen – Fakten speichern und abrufen
- [x] `core/memory.py`: ChromaDB installieren und initialisieren
- [x] `core/memory.py`: OpenAI `text-embedding-3-small` für Embeddings integrieren
- [x] `core/memory.py`: Semantische Suche testen – relevante vergangene Gespräche finden
- [x] `core/brain.py`: Kontext aus Memory in jeden Prompt einbauen
- [ ] Test: Jarvis erinnert sich an Informationen aus vergangenen Gesprächen

### ReAct Agent Loop
- [x] `core/brain.py`: ReAct-Loop implementieren (Think → Act → Observe → Repeat)
- [x] ReAct max. Schritte begrenzen (5 Iterationen) um Endlosschleifen zu verhindern
- [ ] ReAct-Loop testen: "Jarvis, recherchiere die 3 günstigsten MacBook-Hüllen und speichere sie in Notion"
- [x] Fehlerbehandlung im ReAct-Loop (Tool schlägt fehl → Brain formuliert Fehler-Antwort)

### Ollama Offline-Fallback
- [ ] Ollama installieren: `brew install ollama`
- [ ] Llama 3.2 3B Modell herunterladen: `ollama pull llama3.2:3b`
- [ ] Ollama Server testen: `ollama run llama3.2:3b "Hallo"`
- [x] `core/brain.py`: Smart-Routing einbauen – einfache Q&A → Ollama (gratis)
- [x] `core/brain.py`: Komplexe Tasks / Tool-Calls automatisch zu GPT-4o mini routen
- [ ] Sensible Daten (Passwörter, Bankdaten) immer lokal via Ollama verarbeiten
- [ ] Test: Einfache Wissensfragen gehen an Ollama, Tool-Calls an GPT-4o mini

### Proaktiver Modus
- [ ] `scripts/morning_briefing.sh` testen – läuft manuell durch
- [ ] LaunchAgent installieren: `./scripts/install_launchagent.sh`
- [ ] LaunchAgent verifizieren: täglich um 08:00 startet Briefing
- [ ] E-Mail-Monitoring einbauen: Bei wichtiger E-Mail → macOS Notification + Sprachausgabe
- [ ] 15-Minuten-Erinnerung vor Kalender-Terminen implementieren
- [ ] Wöchentliche Zusammenfassung in Notion speichern
- [ ] **MEILENSTEIN**: Jarvis weckt dich morgens, erinnert an Termine und handelt selbstständig

---

## Tests

- [ ] `pytest tests/test_macos.py` – alle macOS-Tests grün
- [ ] `pytest tests/test_speaker.py` – Speaker-Fallback Test grün
- [ ] Manueller End-to-End-Test: 10 verschiedene Sprachbefehle durchspielen
- [ ] Latenz messen: Ziel < 2 Sekunden von Sprache bis Antwort

---

## Kosten prüfen

- [ ] Nach Woche 2: OpenAI-Kosten prüfen (Ziel: < $1)
- [ ] Nach Woche 4: Kosten prüfen (Ziel: < $3/Monat)
- [ ] Ollama-Routing optimieren falls Kosten zu hoch
