# JARVIS v3 – Projektplan

## Überblick

| | |
|---|---|
| **Ziel** | Vollständig autonomer, sprechender KI-Agent auf macOS |
| **Hardware** | MacBook Air M4 |
| **Stack** | Python 3.12, GPT-4o mini, faster-whisper, Kokoro TTS, SQLite+ChromaDB |
| **Kosten** | ~$2/Monat (nur LLM-Calls) |

---

## Phasen-Roadmap

### Phase 1 – Voice & Control (Woche 1–2)
Grundgerüst: Sprechen, Zuhören, Mac steuern

- [ ] Python 3.12 + venv einrichten
- [ ] `listener.py`: Mikrofon-Aufnahme mit Silence-Detection (webrtcvad)
- [ ] `listener.py`: Wake-Word-Detection "Hey Jarvis" (openwakeword)
- [ ] `listener.py`: faster-whisper STT integrieren (base.en Modell)
- [ ] `speaker.py`: Kokoro TTS installieren und testen
- [ ] `speaker.py`: macOS `say`-Fallback wenn Kokoro nicht verfügbar
- [ ] `macos.py`: AppleScript-Wrapper (open_app, notify, get_frontmost)
- [ ] `brain.py`: GPT-4o mini mit System-Prompt + Tool-Calling
- [ ] `main.py`: Vollständiger Kern-Loop (9 Schritte) zusammenführen
- [ ] **Meilenstein**: "Hey Jarvis, öffne Safari" funktioniert end-to-end

### Phase 2 – Smart Automation (Woche 3–4)
Externe Dienste anbinden

- [ ] `gmail.py`: OAuth2 Flow + E-Mails lesen/senden
- [ ] `calendar.py`: Google Calendar lesen/schreiben
- [ ] `browser.py`: Playwright headless Browser-Automation
- [ ] `browser.py`: Screenshot → GPT-4o Vision Analyse
- [ ] `notion.py`: Notion API – Seiten erstellen/lesen
- [ ] `brain.py`: Tool-Routing für alle 9 definierten Tools
- [ ] **Meilenstein**: "Jarvis, lies meine E-Mails vor" funktioniert

### Phase 3 – Autonomous Agent (Woche 5–6)
Gedächtnis, Autonomie, Proaktivität

- [ ] `memory.py`: SQLite Long-Term Memory
- [ ] `memory.py`: ChromaDB Vector-Search (Semantic Retrieval)
- [ ] `memory.py`: OpenAI text-embedding-3-small für Embeddings
- [ ] `brain.py`: ReAct-Loop (Think → Act → Observe → Repeat)
- [ ] Proaktiver Modus via macOS LaunchAgent (Tages-Briefing 8 Uhr)
- [ ] Ollama-Fallback für Offline-Betrieb + sensible Daten
- [ ] Smart-Routing: Einfache Tasks → Ollama, Komplexe → GPT-4o mini
- [ ] **Meilenstein**: Jarvis führt mehrstufige Tasks selbstständig aus

---

## Kern-Loop (Phase 1)

```
1. Mikrofon hört dauerhaft (Hintergrund-Thread)
2. Wake-Word "Hey Jarvis" erkannt → Aufnahme starten
3. Silence-Detection → Aufnahme beenden (~1.5s Stille)
4. faster-whisper transkribiert lokal (~100ms)
5. GPT-4o mini wählt Tool + generiert Plan
6. Tool wird ausgeführt (AppleScript / API / Browser)
7. Ergebnis → GPT-4o mini generiert Antwort
8. Kokoro TTS spricht Antwort aus
9. Zurück zu Schritt 1
```

---

## Definierte Tools (Phase 2)

| Tool | Beschreibung | Kosten |
|------|-------------|--------|
| `open_app(app_name)` | macOS-App via AppleScript öffnen | $0 |
| `search_web(query)` | Playwright öffnet Browser und sucht | $0 |
| `read_emails(filter)` | Gmail API, optional mit Filter | $0 |
| `send_email(to, subject, body)` | Gmail API senden | $0 |
| `create_calendar_event(...)` | Google Calendar erstellen | $0 |
| `get_calendar_events(date_range)` | Termine abfragen | $0 |
| `save_to_notion(content, db)` | Notion-Seite erstellen | $0 |
| `run_applescript(script)` | Direkte macOS-Steuerung | $0 |
| `get_weather(location)` | Via Playwright oder Weather API | $0 |

---

## Technologie-Entscheidungen

| Komponente | Gewählt | Grund |
|-----------|---------|-------|
| STT | faster-whisper (lokal) | Kostenlos, ~100ms, M4-optimiert |
| TTS | Kokoro TTS | Beste kostenlose Qualität 2024/25 |
| LLM | GPT-4o mini | Bestes Preis/Leistung für Tool-Calling |
| LLM Fallback | Ollama + Llama 3.2 | Offline, sensible Daten |
| Memory | SQLite + ChromaDB | 100% lokal, keine Cloud |
| Browser | Playwright | Beste Python-Integration |
| Email/Cal | Google APIs | Komplett kostenlos |

---

## macOS Berechtigungen (WICHTIG)

Vor dem ersten Start in Systemeinstellungen freischalten:
- Datenschutz → Mikrofon → Terminal/Python
- Datenschutz → Bedienungshilfen → Terminal
- Datenschutz → Automation → Terminal

---

## Offene Fragen / Entscheidungen

- [ ] Wake-Word: `openwakeword` vs `pvporcupine` (kostenlos vs. besser)
- [ ] LLM: OpenAI GPT-4o mini vs. Anthropic Claude Haiku (ähnlicher Preis)
- [ ] Proaktiver Modus: LaunchAgent vs. Hintergrund-Thread in main.py
- [ ] UI: Kein UI (reines Voice-Interface) vs. minimales Status-Fenster

---

## Kostenübersicht (monatlich)

| Service | Kosten |
|---------|--------|
| GPT-4o mini (~100 Anfragen/Tag) | ~$1–3 |
| OpenAI Embeddings | ~$0.01 |
| Alles andere | $0 |
| **GESAMT** | **~$1–3/Monat** |
