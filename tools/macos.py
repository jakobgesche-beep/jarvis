"""AppleScript-Wrapper für macOS-Steuerung"""

import subprocess


def _run_applescript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout.strip() or result.stderr.strip()


def open_app(app_name: str) -> str:
    return _run_applescript(f'tell application "{app_name}" to activate')


def send_notification(title: str, message: str) -> str:
    return _run_applescript(
        f'display notification "{message}" with title "{title}"'
    )


def get_frontmost_app() -> str:
    return _run_applescript(
        'tell application "System Events" to name of first process whose frontmost is true'
    )


def set_volume(level: int) -> str:
    level = max(0, min(100, level))
    return _run_applescript(f"set volume output volume {level}")


def run_applescript(script: str) -> str:
    return _run_applescript(script)


def open_url(url: str, browser: str = "Safari") -> str:
    return _run_applescript(
        f'tell application "{browser}" to open location "{url}"'
    )


def spotlight_search(query: str) -> str:
    script = f'''
    tell application "System Events"
        key code 49 using {{command down, space down}}
    end tell
    delay 0.5
    tell application "System Events"
        keystroke "{query}"
    end tell
    '''
    return _run_applescript(script)


def get_clipboard() -> str:
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    return result.stdout


def set_clipboard(text: str) -> str:
    subprocess.run(["pbcopy"], input=text.encode(), check=False)
    return "In Zwischenablage kopiert."


def type_text(text: str) -> str:
    return _run_applescript(
        f'tell application "System Events" to keystroke "{text}"'
    )
