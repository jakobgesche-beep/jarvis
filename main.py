"""JARVIS v3 – Einstiegspunkt"""

import asyncio
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from core.listener import Listener
from core.speaker import Speaker
from core.brain import Brain
from core.memory import Memory


async def run():
    memory = Memory()
    speaker = Speaker()
    brain = Brain(memory=memory)
    listener = Listener()

    await speaker.say("Jarvis ist bereit.")
    print("[JARVIS] Läuft. Sage 'Hey Jarvis' um zu starten.")

    async for transcript in listener.listen():
        if not transcript.strip():
            continue

        print(f"[USER] {transcript}")
        response = await brain.process(transcript)
        print(f"[JARVIS] {response}")
        await speaker.say(response)


def main():
    def _shutdown(sig, frame):
        print("\n[JARVIS] Beende...")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    asyncio.run(run())


if __name__ == "__main__":
    main()
