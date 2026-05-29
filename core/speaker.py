"""Text-to-Speech via Kokoro TTS (lokal, kostenlos) mit macOS say-Fallback"""

import asyncio
import os
import subprocess
import tempfile
from pathlib import Path


class Speaker:
    def __init__(self, voice: str = "af_heart", speed: float = 1.0):
        self._voice = voice
        self._speed = speed
        self._kokoro = None
        self._kokoro_available = None

    def _check_kokoro(self) -> bool:
        if self._kokoro_available is None:
            try:
                from kokoro import KPipeline
                self._kokoro = KPipeline(lang_code="a")
                self._kokoro_available = True
            except Exception:
                self._kokoro_available = False
        return self._kokoro_available

    def _speak_kokoro(self, text: str):
        import sounddevice as sd
        import numpy as np
        from kokoro import KPipeline

        if self._kokoro is None:
            self._kokoro = KPipeline(lang_code="a")

        for _, _, audio in self._kokoro(text, voice=self._voice, speed=self._speed):
            sd.play(audio, samplerate=24000)
            sd.wait()

    def _speak_macos(self, text: str):
        subprocess.run(["say", "-r", "180", text], check=False)

    async def say(self, text: str):
        loop = asyncio.get_event_loop()
        if self._check_kokoro():
            await loop.run_in_executor(None, self._speak_kokoro, text)
        else:
            print("[Speaker] Kokoro nicht verfügbar, nutze macOS say")
            await loop.run_in_executor(None, self._speak_macos, text)
