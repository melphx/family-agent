"""Google Calendar connector — reads upcoming events and creates new ones.

Uses the same Google OAuth token as Gmail (secrets/gmail_token.json).
The token must include the calendar.events scope — re-run gmail_auth.py
with the updated scopes if you authorized Gmail first without calendar.
"""
import os
from datetime import datetime, timezone

from agent.connectors.base import Connector

TOKEN_FILE = os.path.join("secrets", "gmail_token.json")
CALENDAR_ID = "primary"


def build_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    scopes = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ]
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(f"{TOKEN_FILE} not found. Run gmail_auth.py first.")
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, scopes)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


class CalendarConnector(Connector):
    name = "calendar"

    def _cfg(self):
        return self.cfg.get("connectors", {}).get("calendar", {})

    def fetch_events(self) -> list:
        if not self._cfg().get("enabled"):
            return []
        try:
            service = build_service()
            now = datetime.now(timezone.utc).isoformat()
            result = service.events().list(
                calendarId=CALENDAR_ID,
                timeMin=now,
                maxResults=20,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            events = []
            for item in result.get("items", []):
                start = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date", "")
                events.append({
                    "source": "calendar",
                    "id": item.get("id"),
                    "title": item.get("summary", ""),
                    "start": start,
                    "text": f"Calendar event: {item.get('summary', '')} at {start}",
                })
            return events
        except Exception as e:
            print(f"[calendar] fetch error: {e}")
            return []

    def execute(self, action_type: str, payload: dict) -> str:
        if action_type == "create_event":
            try:
                service = build_service()
                # payload expects: title, start_datetime (ISO), end_datetime (ISO),
                # optionally: description, location
                event = {
                    "summary": payload.get("title", "Family event"),
                    "description": payload.get("description", ""),
                    "location": payload.get("location", ""),
                    "start": {"dateTime": payload["start_datetime"], "timeZone": payload.get("timezone", "America/New_York")},
                    "end":   {"dateTime": payload["end_datetime"],   "timeZone": payload.get("timezone", "America/New_York")},
                }
                created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
                return f"Created event '{event['summary']}' — {created.get('htmlLink')}"
            except Exception as e:
                return f"[calendar] create_event failed: {e}"
        return f"[calendar] unsupported action: {action_type}"
