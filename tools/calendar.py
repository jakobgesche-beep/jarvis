"""Google Calendar API – Termine lesen und erstellen (Phase 2)

Nutzt dieselben OAuth2 Credentials wie gmail.py.
Scopes in credentials.json um calendar.readonly + calendar.events erweitern.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

CREDENTIALS_FILE = Path("./credentials.json")
TOKEN_FILE = Path("./data/calendar_token.json")
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]


def _get_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def get_events(days_ahead: int = 7) -> list[dict]:
    service = _get_service()
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)

    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=20,
    ).execute()

    events = []
    for e in result.get("items", []):
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        events.append({
            "summary": e.get("summary", "Kein Titel"),
            "start": start,
            "location": e.get("location", ""),
            "description": e.get("description", ""),
        })
    return events


def create_event(title: str, start_iso: str, duration_minutes: int = 60,
                 description: str = "") -> str:
    from datetime import datetime
    service = _get_service()
    start = datetime.fromisoformat(start_iso)
    end = start + timedelta(minutes=duration_minutes)

    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": "Europe/Berlin"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Europe/Berlin"},
    }
    created = service.events().insert(calendarId="primary", body=event).execute()
    return f"Termin '{title}' am {start.strftime('%d.%m. um %H:%M')} erstellt."
