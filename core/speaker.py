"""Text-to-Speech: edge-tts (Iron Man Stimme) mit macOS say-Fallback"""

import asyncio
import os
import subprocess
import tempfile
from pathlib import Path

EDGE_VOICE = os.getenv("JARVIS_VOICE", "de-DE-ConradNeural")  # Deutsch, professionell


class Speaker:
    def __init__(self):
        self._edge_ok: bool | None = None

    def _check_edge(self) -> bool:
        if self._edge_ok is None:
            try:
                import edge_tts  # noqa
                self._edge_ok = True
            except ImportError:
                self._edge_ok = False
        return self._edge_ok

    async def _speak_edge(self, text: str):
        import edge_tts
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp = f.name
        try:
            communicate = edge_tts.Communicate(text, voice=EDGE_VOICE)
            await communicate.save(tmp)
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: subprocess.run(["afplay", tmp], check=False)
            )
        finally:
            try:
                Path(tmp).unlink()
            except Exception:
                pass

    def _speak_macos(self, text: str):
        # Fallback: macOS say mit Alex-Stimme (am roboterhaftesten = Iron Man Feeling)
        subprocess.run(["say", "-v", "Alex", "-r", "175", text], check=False)

    async def say(self, text: str):
        if self._check_edge():
            try:
                await self._speak_edge(text)
                return
            except Exception as e:
                print(f"[Speaker] edge-tts Fehler: {e} – Fallback auf say")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._speak_macos, text)
