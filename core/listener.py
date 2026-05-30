"""Mikrofon, Klatschen-Detection, STT via faster-whisper"""

import asyncio
import io
import threading
import time
from typing import AsyncGenerator, Callable

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 30
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)
SILENCE_TIMEOUT_S = 1.5

# Klatschen: kurzer, harter Lautstärkeimpuls
CLAP_THRESHOLD = 0.18
CLAP_COOLDOWN_S = 0.3
DOUBLE_CLAP_WINDOW_S = 0.9


class Listener:
    def __init__(self, model_size: str = "base"):
        self._model_size = model_size
        self._whisper = None
        self._clap_callback: Callable | None = None
        self._clap_thread: threading.Thread | None = None

    def _load_whisper(self):
        if self._whisper is None:
            from faster_whisper import WhisperModel
            print(f"[Listener] Lade Whisper '{self._model_size}'...")
            self._whisper = WhisperModel(
                self._model_size,
                device="cpu",
                compute_type="int8",
                num_workers=1,
                cpu_threads=2,
            )

    def _transcribe(self, audio: np.ndarray) -> str:
        self._load_whisper()
        segments, _ = self._whisper.transcribe(audio, language="de", beam_size=5)
        return " ".join(s.text for s in segments).strip()

    def transcribe_bytes(self, audio_bytes: bytes) -> str:
        """Transkribiert rohe PCM-Bytes (16kHz, mono, float32) – für API-Endpoint."""
        audio = np.frombuffer(audio_bytes, dtype=np.float32)
        return self._transcribe(audio)

    def transcribe_webm(self, data: bytes) -> str:
        """Transkribiert WebM/MP4-Audio aus dem Browser via ffmpeg."""
        import subprocess, tempfile, soundfile as sf
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(data)
            src = f.name
        dst = src + ".wav"
        try:
            subprocess.run(
                ["ffmpeg", "-i", src, "-ar", "16000", "-ac", "1", dst, "-y", "-loglevel", "quiet"],
                check=True, timeout=10,
            )
            audio, _ = sf.read(dst, dtype="float32")
            return self._transcribe(audio)
        except Exception as e:
            return ""
        finally:
            import os
            for p in [src, dst]:
                try: os.unlink(p)
                except: pass

    # ── Klatschen ──────────────────────────────────────────────────────────

    def start_clap_detection(self, callback: Callable):
        """Startet Doppelklatschen-Detection im Hintergrund."""
        self._clap_callback = callback
        self._clap_thread = threading.Thread(target=self._clap_loop, daemon=True)
        self._clap_thread.start()

    def _clap_loop(self):
        last_clap = 0.0
        clap_count = 0
        in_clap = False

        def audio_cb(indata, frames, time_info, status):
            nonlocal last_clap, clap_count, in_clap
            rms = float(np.sqrt(np.mean(indata ** 2)))
            now = time.time()

            if rms > CLAP_THRESHOLD and not in_clap:
                in_clap = True
                dt = now - last_clap
                if dt < DOUBLE_CLAP_WINDOW_S:
                    clap_count += 1
                    if clap_count >= 2:
                        clap_count = 0
                        # Doppelklatschen erkannt!
                        t = threading.Thread(target=self._clap_callback, daemon=True)
                        t.start()
                else:
                    clap_count = 1
                last_clap = now

            elif rms < 0.015:
                in_clap = False

        with sd.InputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32",
            blocksize=512, callback=audio_cb,
        ):
            while True:
                sd.sleep(50)

    # ── Aufnahme ───────────────────────────────────────────────────────────

    def _record_until_silence(self) -> np.ndarray | None:
        print("[Listener] Aufnahme läuft... (Stille beendet)")
        frames = []
        silence_frames = 0
        silence_limit = int(SILENCE_TIMEOUT_S * SAMPLE_RATE / CHUNK_SAMPLES)

        def callback(indata, frame_count, time_info, status):
            frames.append(indata.copy())

        with sd.InputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32",
            blocksize=CHUNK_SAMPLES, callback=callback,
        ):
            while True:
                sd.sleep(CHUNK_MS)
                if len(frames) < 2:
                    continue
                rms = float(np.sqrt(np.mean(frames[-1].flatten() ** 2)))
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
        print("[Listener] Drücke Enter für Aufnahme (oder klatsche 2× für Briefing)")
        while True:
            await loop.run_in_executor(None, input, "")
            audio = await loop.run_in_executor(None, self._record_until_silence)
            if audio is not None and len(audio) > SAMPLE_RATE * 0.3:
                transcript = await loop.run_in_executor(None, self._transcribe, audio)
                if transcript:
                    yield transcript
