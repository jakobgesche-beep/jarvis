"""Mikrofon-Aufnahme, Wake-Word-Detection via openwakeword, STT via faster-whisper"""

import asyncio
import threading
from typing import AsyncGenerator

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 30
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)
SILENCE_TIMEOUT_S = 1.5
WAKEWORD_THRESHOLD = 0.5
WAKEWORD_CHUNK = 1280  # ~80ms bei 16kHz, von openwakeword erwartet


class Listener:
    def __init__(self, model_size: str = "base", wake_word: str = "hey_jarvis"):
        self._model_size = model_size
        self._wake_word = wake_word
        self._whisper = None

    def _load_whisper(self):
        if self._whisper is None:
            from faster_whisper import WhisperModel
            print(f"[Listener] Lade Whisper '{self._model_size}'...")
            self._whisper = WhisperModel(self._model_size, device="auto", compute_type="int8")

    def _transcribe(self, audio: np.ndarray) -> str:
        self._load_whisper()
        segments, _ = self._whisper.transcribe(audio, language="de", beam_size=5)
        return " ".join(s.text for s in segments).strip()

    def _has_wake_word(self) -> bool:
        try:
            from openwakeword.model import Model
            Model(wakeword_models=[self._wake_word], inference_framework="onnx")
            return True
        except Exception:
            return False

    def _wait_for_wake_word(self):
        """Blockiert bis das Wake-Word erkannt wird."""
        from openwakeword.model import Model

        oww = Model(wakeword_models=[self._wake_word], inference_framework="onnx")
        detected = threading.Event()

        def callback(indata, frames, time_info, status):
            scores = oww.predict(indata.flatten())
            if any(v >= WAKEWORD_THRESHOLD for v in scores.values()):
                detected.set()

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=WAKEWORD_CHUNK,
            callback=callback,
        ):
            detected.wait()

    def _record_until_silence(self) -> np.ndarray | None:
        print("[Listener] Aufnahme läuft... (Stille beendet)")
        frames = []
        silence_frames = 0
        silence_limit = int(SILENCE_TIMEOUT_S * SAMPLE_RATE / CHUNK_SAMPLES)

        def callback(indata, frame_count, time_info, status):
            frames.append(indata.copy())

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=CHUNK_SAMPLES,
            callback=callback,
        ):
            while True:
                sd.sleep(CHUNK_MS)
                if len(frames) < 2:
                    continue
                last = frames[-1].flatten()
                rms = float(np.sqrt(np.mean(last**2)))
                if rms < 0.01:
                    silence_frames += 1
                else:
                    silence_frames = 0
                if silence_frames >= silence_limit:
                    break

        if not frames:
            return None
        return np.concatenate(frames).flatten()

    async def listen(self) -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()
        use_wake_word = await loop.run_in_executor(None, self._has_wake_word)

        if use_wake_word:
            print(f"[Listener] Warte auf Wake-Word '{self._wake_word}'...")
            while True:
                await loop.run_in_executor(None, self._wait_for_wake_word)
                print("[Listener] Wake-Word erkannt!")
                audio = await loop.run_in_executor(None, self._record_until_silence)
                if audio is not None and len(audio) > SAMPLE_RATE * 0.3:
                    transcript = await loop.run_in_executor(None, self._transcribe, audio)
                    if transcript:
                        yield transcript
                print(f"[Listener] Warte auf Wake-Word '{self._wake_word}'...")
        else:
            print("[Listener] openwakeword nicht verfügbar – Drücke Enter für Aufnahme.")
            while True:
                await loop.run_in_executor(None, input, "")
                audio = await loop.run_in_executor(None, self._record_until_silence)
                if audio is not None and len(audio) > SAMPLE_RATE * 0.3:
                    transcript = await loop.run_in_executor(None, self._transcribe, audio)
                    if transcript:
                        yield transcript
