"""JARVIS v3 – Einstiegspunkt"""

import asyncio
import os
import signal
import sys
import threading
import time

# Crash-Fix: ctranslate2/faster-whisper crasht auf Intel Mac mit OpenMP Multi-Threading
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

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


async def run_async(memory, speaker, brain, listener):
    await speaker.say("Jarvis ist bereit.")
    await asyncio.gather(
        voice_loop(listener, brain, speaker),
        start_server(brain, memory),
    )


def run_backend(memory, speaker, brain, listener):
    asyncio.run(run_async(memory, speaker, brain, listener))


def wait_for_server(port: int, timeout: int = 15) -> bool:
    """Wartet bis der API-Server antwortet."""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    port = int(os.getenv("JARVIS_API_PORT", "8080"))

    memory = Memory()
    speaker = Speaker()
    brain = Brain(memory=memory)
    listener = Listener()

    # Backend (Voice-Loop + API-Server) im Hintergrund starten
    t = threading.Thread(
        target=run_backend,
        args=(memory, speaker, brain, listener),
        daemon=True,
    )
    t.start()

    # Warten bis Server wirklich bereit ist
    print(f"[JARVIS] Starte API-Server auf Port {port}...")
    ready = wait_for_server(port)
    if ready:
        print(f"[JARVIS] Server bereit – öffne http://localhost:{port}/app/")
    else:
        print("[JARVIS] Server-Timeout – öffne trotzdem...")

    # HUD im Standard-Browser öffnen (kein pywebview = kein Crash)
    import webbrowser
    webbrowser.open(f"http://localhost:{port}/app/")

    # Hauptthread am Leben halten
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    t.join()


if __name__ == "__main__":
    main()
