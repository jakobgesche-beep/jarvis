"""JARVIS v3 – Einstiegspunkt mit nativem Mac-Fenster"""

import asyncio
import os
import signal
import sys
import threading

from dotenv import load_dotenv

load_dotenv()

from core.listener import Listener
from core.speaker import Speaker
from core.brain import Brain
from core.memory import Memory
from core.api import start_server

MAX_CONSECUTIVE_ERRORS = 5


async def voice_loop(listener: Listener, brain: Brain, speaker: Speaker):
    consecutive_errors = 0
    async for transcript in listener.listen():
        if not transcript.strip():
            continue
        print(f"[USER] {transcript}")
        try:
            response = await brain.process(transcript)
            consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            print(f"[JARVIS] Fehler: {e}")
            response = "Entschuldigung, da ist leider etwas schiefgelaufen."
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                await speaker.say("Ich habe zu viele Fehler erlebt und beende mich jetzt.")
                sys.exit(1)
        print(f"[JARVIS] {response}")
        try:
            await speaker.say(response)
        except Exception as e:
            print(f"[JARVIS] Sprachausgabe fehlgeschlagen: {e}")


async def backend(memory, speaker, brain, listener):
    await speaker.say("Jarvis ist bereit.")
    await asyncio.gather(
        voice_loop(listener, brain, speaker),
        start_server(brain, memory),
    )


def run_backend(memory, speaker, brain, listener):
    asyncio.run(backend(memory, speaker, brain, listener))


def main():
    # Objekte erstellen
    memory = Memory()
    speaker = Speaker()
    brain = Brain(memory=memory)
    listener = Listener()

    # Backend im Hintergrund-Thread starten (Voice + API-Server)
    t = threading.Thread(
        target=run_backend,
        args=(memory, speaker, brain, listener),
        daemon=True,
    )
    t.start()

    # Kurz warten bis API-Server hochgefahren ist
    import time
    time.sleep(2)

    # Natives Mac-Fenster mit der Chat-UI
    try:
        import webview

        port = int(os.getenv("JARVIS_API_PORT", "8080"))

        webview.create_window(
            title="JARVIS",
            url=f"http://localhost:{port}/app/",
            width=420,
            height=780,
            resizable=True,
            min_size=(360, 600),
        )
        webview.start()
    except Exception as e:
        # Kein pywebview → Browser öffnen als Fallback
        print(f"[JARVIS] Kein nativer Fenster-Support ({e}), öffne Browser...")
        import webbrowser
        port = int(os.getenv("JARVIS_API_PORT", "8080"))
        webbrowser.open(f"http://localhost:{port}/app/")
        # Hauptthread am Leben halten
        signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
        t.join()


if __name__ == "__main__":
    main()
