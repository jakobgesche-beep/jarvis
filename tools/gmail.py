"""Gmail API – E-Mails lesen und senden (Phase 2)

Setup:
1. console.cloud.google.com → Projekt 'JARVIS' erstellen
2. Gmail API aktivieren
3. OAuth2 Credentials (Desktop App) → credentials.json herunterladen
4. credentials.json in ~/jarvis/ ablegen
5. Beim ersten Aufruf öffnet sich Browser zur Autorisierung
"""

import base64
import os
from email.mime.text import MIMEText
from pathlib import Path

CREDENTIALS_FILE = Path("./credentials.json")
TOKEN_FILE = Path("./data/gmail_token.json")
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
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

    return build("gmail", "v1", credentials=creds)


def read_emails(max_results: int = 5, query: str = "is:unread") -> list[dict]:
    service = _get_service()
    result = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    messages = result.get("messages", [])

    emails = []
    for msg in messages:
        detail = service.users().messages().get(userId="me", id=msg["id"], format="metadata",
                                                metadataHeaders=["From", "Subject", "Date"]).execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        emails.append({
            "id": msg["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": detail.get("snippet", ""),
        })
    return emails


def send_email(to: str, subject: str, body: str) -> str:
    service = _get_service()
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return f"E-Mail an {to} gesendet."
