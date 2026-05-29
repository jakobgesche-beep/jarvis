# JARVIS v3

Vollständig autonomer, sprechender KI-Assistent – lokal auf dem MacBook Air M4.

---

## Was ist JARVIS?

JARVIS ist ein persönlicher KI-Assistent der auf dem eigenen Mac läuft. Du sprichst mit ihm wie mit einem Menschen – er hört zu, versteht was du meinst, führt Aktionen aus und antwortet mit natürlicher Stimme. Alles passiert lokal: kein Server, kein Abo, keine Cloud außer dem Sprachmodell.

Das Ziel ist ein Assistent der echte Arbeit abnimmt: E-Mails lesen und beantworten, Kalender verwalten, im Internet recherchieren, Apps öffnen, Erinnerungen setzen – und das alles durch einfache gesprochene Befehle.

---

## Was JARVIS kann

### Phase 1 – Sprechen und zuhören

- Erkennt das Wake-Word **"Hey Jarvis"** ohne dass man etwas drücken muss
- Nimmt Sprachbefehle auf und erkennt automatisch wenn du fertig gesprochen hast
- Transkribiert Sprache lokal in Text (keine Daten verlassen den Mac)
- Antwortet mit natürlicher synthetischer Stimme
- Öffnet Apps, stellt Lautstärke ein, sendet Notifications, steuert macOS via Sprache

Beispiele:
```
"Hey Jarvis, öffne Safari"
"Hey Jarvis, stelle die Lautstärke auf 50 Prozent"
"Hey Jarvis, zeig mir eine Notification in 5 Minuten"
```

### Phase 2 – Smarte Automatisierung

- Liest und sendet **E-Mails** via Gmail
- Zeigt **Kalender-Termine** an und erstellt neue
- Öffnet den **Browser**, sucht im Internet und fasst Ergebnisse zusammen
- Macht **Screenshots** und analysiert was auf dem Bildschirm zu sehen ist
- Speichert Notizen und Recherchen in **Notion**

Beispiele:
```
"Hey Jarvis, lies mir meine ungelesenen E-Mails vor"
"Hey Jarvis, was steht diese Woche in meinem Kalender?"
"Hey Jarvis, google den Wetterbericht für morgen und sag mir ob ich einen Schirm brauche"
"Hey Jarvis, erstelle einen Termin morgen um 15 Uhr – Meeting mit Thomas"
"Hey Jarvis, speichere das in Notion unter Ideen"
```

### Phase 3 – Autonomer Agent

- **Erinnert sich** an vergangene Gespräche, Fakten und Präferenzen
- Führt **mehrstufige Aufgaben** selbstständig aus ohne Schritt-für-Schritt-Anweisungen
- Proaktiver **Morgen-Briefing** täglich um 8 Uhr: Kalender, wichtige E-Mails, Wetter
- Erinnert **15 Minuten vor Terminen** automatisch mit Kontext-Infos
- Benachrichtigt bei **wichtigen E-Mails** sofort
- Arbeitet **offline** für einfache Tasks (lokales Sprachmodell via Ollama)
- Verarbeitet **sensible Daten** (Passwörter, Bankdaten) immer lokal – nie in die Cloud

Beispiele:
```
"Hey Jarvis, recherchiere die 3 günstigsten Flüge nach Berlin nächste Woche
 und schreib mir eine Zusammenfassung in Notion"

"Hey Jarvis, schau ob Thomas auf meine letzte E-Mail geantwortet hat,
 und falls ja – lies sie vor und schlag mir eine Antwort vor"
```

---

## Wie funktioniert das technisch?

```
Du sprichst
    → Wake-Word erkannt ("Hey Jarvis")
    → Aufnahme startet, Stille beendet sie automatisch
    → faster-whisper transkribiert lokal in ~100ms
    → GPT-4o mini versteht den Befehl und wählt das passende Tool
    → Tool wird ausgeführt (AppleScript / Gmail / Browser / etc.)
    → Ergebnis wird zu einer Antwort formuliert
    → Kokoro TTS spricht die Antwort aus
    → Zurück zum Anfang
```

Der gesamte Prozess dauert unter 2 Sekunden.

---

## Tech-Stack

| Komponente | Technologie | Kosten |
|-----------|-------------|--------|
| Spracherkennung (STT) | faster-whisper (lokal auf M4) | $0 |
| Stimme (TTS) | Kokoro TTS (lokal, Open Source) | $0 |
| KI-Gehirn | GPT-4o mini (OpenAI API) | ~$1–3/Monat |
| KI-Fallback | Ollama + Llama 3.2 (lokal) | $0 |
| Gedächtnis | SQLite + ChromaDB (lokal) | $0 |
| Browser-Steuerung | Playwright (Open Source) | $0 |
| E-Mail / Kalender | Google APIs (Free Tier) | $0 |
| Mac-Steuerung | AppleScript (eingebaut) | $0 |
| Notizen | Notion API (Free Plan) | $0 |
| **Gesamt** | | **~$1–3/Monat** |

Zum Vergleich: Dieselben Funktionen als Cloud-Services würden ~$120/Monat kosten.

---

## Voraussetzungen

- MacBook mit Apple Silicon (M1/M2/M3/M4) – für optimale lokale Modell-Performance
- macOS Ventura oder neuer
- OpenAI API Key (ca. $10 aufladen reicht für 2–3 Monate)
- Google-Account für Gmail und Kalender
- Notion-Account (kostenlos)

---

## Schnellstart

```bash
cd ~/jarvis
./scripts/setup.sh
# .env öffnen und OPENAI_API_KEY eintragen
python main.py
```

Alle Schritte im Detail: [PLAN.md](PLAN.md)

---

## Projektstruktur

```
~/jarvis/
├── main.py              # Einstiegspunkt
├── core/
│   ├── brain.py         # LLM-Integration + Tool-Calling
│   ├── listener.py      # Mikrofon + Wake-Word + Transkription
│   ├── speaker.py       # Text-to-Speech
│   └── memory.py        # Kurzzeit- und Langzeitgedächtnis
├── tools/
│   ├── macos.py         # macOS-Steuerung via AppleScript
│   ├── gmail.py         # E-Mail lesen und senden
│   ├── calendar.py      # Kalender verwalten
│   ├── browser.py       # Web-Recherche und Screenshots
│   └── notion.py        # Notizen speichern
├── scripts/             # Setup und Automatisierung
├── tests/               # Automatisierte Tests
├── PLAN.md              # Aufgaben-Checkliste
└── CLAUDE.md            # Kontext für Claude Code
```

---

## Kosten-Philosophie

Sparen an der richtigen Stelle:
- **STT, TTS, Memory, Browser, APIs**: komplett kostenlos durch lokale Open-Source-Lösungen
- **LLM**: hier wird nicht gespart – GPT-4o mini ist günstig aber qualitativ stark genug für zuverlässiges Tool-Calling
- **Kein Abo**: alles Pay-per-Use oder kostenlos – nur zahlen was wirklich genutzt wird
