"""Mikrofon-Aufnahme, Wake-Word-Detection, STT via faster-whisper"""

import asyncio
import queue
import threading
from typing import AsyncGenerator

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 30  # webrtcvad benötigt 10/20/30ms Chunks
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)
SILENCE_TIMEOUT_S = 1.5


class Listener:
    def __init__(self, model_size: str = "base"):
        self._model_size = model_size
        self._whisper = None
        self._audio_q: queue.Queue = queue.Queue()

    def _load_whisper(self):
        if self._whisper is None:
            from faster_whisper import WhisperModel
            self._whisper = WhisperModel(self._model_size, device="auto", compute_type="int8")

    def _transcribe(self, audio: np.ndarray) -> str:
        self._load_whisper()
        segments, _ = self._whisper.transcribe(audio, language="de", beam_size=5)
        return " ".join(s.text for s in segments).strip()

    async def listen(self) -> AsyncGenerator[str, None]:
        """Dauerhaft auf Wake-Word warten, dann transkribieren."""
        loop = asyncio.get_event_loop()

        # TODO Phase 1: openwakeword Wake-Word-Detection einbauen
        # Für den Start: Einfacher Modus – Enter-Taste triggert Aufnahme
        print("[Listener] Drücke Enter für Aufnahme (Wake-Word kommt in Phase 1)")

        while True:
            await loop.run_in_executor(None, input, "")
            audio = await loop.run_in_executor(None, self._record_until_silence)
            if audio is not None and len(audio) > SAMPLE_RATE * 0.3:
                transcript = await loop.run_in_executor(None, self._transcribe, audio)
                if transcript:
                    yield transcript

    def _record_until_silence(self) -> np.ndarray | None:
        print("[Listener] Aufnahme läuft... (Stille beendet)")
        frames = []
        silence_frames = 0
        silence_limit = int(SILENCE_TIMEOUT_S * SAMPLE_RATE / CHUNK_SAMPLES)

        def callback(indata, frame_count, time_info, status):
            frames.append(indata.copy())

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                            dtype="float32", blocksize=CHUNK_SAMPLES,
                            callback=callback):
            while True:
                sd.sleep(CHUNK_MS)
                if len(frames) < 2:
                    continue
                last = frames[-1].flatten()
                rms = float(np.sqrt(np.mean(last ** 2)))
                if rms < 0.01:
                    silence_frames += 1
                else:
                    silence_frames = 0
                if silence_frames >= silence_limit:
                    break

        if not frames:
            return None
        return np.concatenate(frames).flatten()
