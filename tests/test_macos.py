"""Tests für macOS-Tools – laufen lokal ohne API-Keys"""

import pytest
from tools.macos import get_frontmost_app, _run_applescript


def test_applescript_basic():
    result = _run_applescript('return "hello"')
    assert result == "hello"


def test_get_frontmost_app():
    app = get_frontmost_app()
    assert isinstance(app, str)
    assert len(app) > 0


def test_send_notification():
    from tools.macos import send_notification
    result = send_notification("Test", "JARVIS Test-Notification")
    assert result is not None
