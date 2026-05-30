"""Mikrofon, Klatschen-Detection, STT via faster-whisper – ein gemeinsamer Audiostream"""

import asyncio
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

# Klatschen-Parameter
CLAP_THRESHOLD = 0.20
DOUBLE_CLAP_WINDOW_S = 0.8
CLAP_MIN_GAP_S = 0.15  # Mindestabstand zwischen zwei Klatschen


class Listener:
    def __init__(self, model_size: str = "base"):
        self._model_size = model_size
        self._whisper = None

        # Geteilter Audiostream-Zustand
        self._recording = False
        self._rec_frames: list = []
        self._clap_callback: Callable | None = None

        # Klatschen-Tracking
        self._last_clap_time = 0.0
        self._clap_count = 0
        self._in_clap = False

        # Signale
        self._record_trigger = threading.Event()
        self._stop_record = threading.Event()

    def _load_whisper(self):
        if self._whisper is None:
            from faster_whisper import WhisperModel
            print("[Listener] Lade Whisper 'base'...")
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

    def transcribe_webm(self, data: bytes) -> str:
        """Transkribiert WebM-Audio vom Browser."""
        import subprocess, tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(data); src = f.name
        dst = src + ".wav"
        try:
            subprocess.run(
                ["ffmpeg", "-i", src, "-ar", "16000", "-ac", "1", dst, "-y", "-loglevel", "quiet"],
                check=True, timeout=15,
            )
            import soundfile as sf
            audio, _ = sf.read(dst, dtype="float32")
            return self._transcribe(audio)
        except Exception as e:
            print(f"[Listener] transcribe_webm Fehler: {e}")
            return ""
        finally:
            for p in [src, dst]:
                try: os.unlink(p)
                except: pass

    def start_clap_detection(self, callback: Callable):
        self._clap_callback = callback
        # Klatschen läuft über denselben Stream – kein separater Thread nötig

    def _process_clap(self, rms: float):
        """Wird pro Audio-Chunk aufgerufen um Klatschen zu erkennen."""
        if self._clap_callback is None or self._recording:
            return
        now = time.time()
        if rms > CLAP_THRESHOLD and not self._in_clap:
            self._in_clap = True
            dt = now - self._last_clap_time
            if CLAP_MIN_GAP_S < dt < DOUBLE_CLAP_WINDOW_S:
                self._clap_count += 1
                if self._clap_count >= 2:
                    self._clap_count = 0
                    print("[Listener] Doppelklatschen erkannt!")
                    t = threading.Thread(target=self._clap_callback, daemon=True)
                    t.start()
            elif dt >= DOUBLE_CLAP_WINDOW_S:
                self._clap_count = 1
            self._last_clap_time = now
        elif rms < 0.02:
            self._in_clap = False

    def _record_until_silence(self) -> np.ndarray | None:
        print("[Listener] Aufnahme läuft... (Stille beendet)")
        frames = []
        silence_frames = 0
        silence_limit = int(SILENCE_TIMEOUT_S * SAMPLE_RATE / CHUNK_SAMPLES)
        self._recording = True

        def callback(indata, frame_count, time_info, status):
            chunk = indata.copy()
            frames.append(chunk)
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            nonlocal silence_frames
            if rms < 0.01:
                silence_frames += 1
            else:
                silence_frames = 0

        with sd.InputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32",
            blocksize=CHUNK_SAMPLES, callback=callback,
        ):
            while silence_frames < silence_limit:
                sd.sleep(CHUNK_MS)

        self._recording = False
        if not frames:
            return None
        return np.concatenate(frames).flatten()

    async def listen(self) -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()

        # Hintergrund-Thread für Klatschen-Monitoring (getrennt vom Recording)
        if self._clap_callback:
            threading.Thread(target=self._clap_monitor_loop, daemon=True).start()

        print("[Listener] Drücke Enter für Aufnahme (oder 2× klatschen für Briefing)")
        while True:
            await loop.run_in_executor(None, input, "")
            audio = await loop.run_in_executor(None, self._record_until_silence)
            if audio is not None and len(audio) > SAMPLE_RATE * 0.3:
                transcript = await loop.run_in_executor(None, self._transcribe, audio)
                if transcript:
                    yield transcript

    def _clap_monitor_loop(self):
        """Leichtgewichtiger Klatschen-Monitor – läuft NUR wenn nicht aufgenommen wird."""
        def callback(indata, frames, time_info, status):
            if not self._recording:
                rms = float(np.sqrt(np.mean(indata ** 2)))
                self._process_clap(rms)

        with sd.InputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32",
            blocksize=512, callback=callback,
        ):
            while True:
                sd.sleep(20)
