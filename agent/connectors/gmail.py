"""Gmail connector — Phase 1: READ-ONLY.

Authenticates with the dedicated family Gmail and turns recent messages into
normalized events the reasoner can act on. It only ever READS here. Sending email
is still a stubbed action (Phase 2) so that even an approved 'send_email' cannot
actually leave the box yet — read-only by construction.

Credentials (created in Google Cloud, see PHASE1-GMAIL-SETUP.md):
  secrets/google_client.json   OAuth client (Desktop app) you download from Google
  secrets/gmail_token.json     minted by gmail_auth.py after you consent once
"""
import os
import base64

from agent.connectors.base import Connector

CLIENT_FILE = os.path.join("secrets", "google_client.json")
TOKEN_FILE = os.path.join("secrets", "gmail_token.json")


def build_service(scopes):
    """Build an authorized Gmail API client from the saved token (refreshing if needed).
    Imports are local so the package still imports without google libs installed."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(
            f"{TOKEN_FILE} not found. Run `python gmail_auth.py` once to authorize."
        )
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, scopes)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _header(headers, name):
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


class GmailConnector(Connector):
    name = "gmail"

    def _cfg(self):
        return self.cfg.get("connectors", {}).get("gmail", {})

    def fetch_events(self) -> list:
        gc = self._cfg()
        if not gc.get("enabled"):
            return []
        scopes = gc.get("scopes", ["https://www.googleapis.com/auth/gmail.readonly"])
        query = gc.get("query", "is:unread newer_than:7d")
        max_results = int(gc.get("max_results", 10))

        service = build_service(scopes)
        resp = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()

        events = []
        for ref in resp.get("messages", []):
            msg = service.users().messages().get(
                userId="me", id=ref["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()
            headers = msg.get("payload", {}).get("headers", [])
            subject = _header(headers, "Subject")
            sender = _header(headers, "From")
            snippet = msg.get("snippet", "")
            events.append({
                "source": "gmail",
                "id": ref["id"],
                "from": sender,
                "subject": subject,
                "text": f"From {sender} | {subject} | {snippet}",
            })
        return events

    def execute(self, action_type: str, payload: dict) -> str:
        if action_type == "send_email":
            # Phase 2 will implement real sending (and require gmail.send scope).
            return f"[stub] would send email to {payload.get('to')} re '{payload.get('subject')}'"
        return f"[gmail] unsupported action: {action_type}"
