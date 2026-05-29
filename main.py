"""JARVIS v3 – Einstiegspunkt"""

import asyncio
import os
import signal
import sys

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


async def run():
    memory = Memory()
    speaker = Speaker()
    brain = Brain(memory=memory)
    listener = Listener()

    await speaker.say("Jarvis ist bereit.")
    print("[JARVIS] Läuft. Sage 'Hey Jarvis' um zu starten.")

    await asyncio.gather(
        voice_loop(listener, brain, speaker),
        start_server(brain, memory),
    )


def main():
    def _shutdown(sig, frame):
        print("\n[JARVIS] Beende...")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    asyncio.run(run())


if __name__ == "__main__":
    main()
