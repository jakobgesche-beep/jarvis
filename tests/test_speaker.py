"""Tests für Speaker – testet macOS say-Fallback ohne Kokoro"""

import pytest


def test_speaker_fallback(monkeypatch):
    """Speaker soll immer funktionieren, auch ohne Kokoro"""
    import subprocess
    called = []

    def fake_run(cmd, **kwargs):
        called.append(cmd)
        class R:
            returncode = 0
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)

    from core.speaker import Speaker
    import asyncio

    speaker = Speaker()
    monkeypatch.setattr(speaker, "_check_kokoro", lambda: False)
    asyncio.run(speaker.say("Test"))

    assert any("say" in str(c) for c in called)
