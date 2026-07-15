"""Gmail connector — reads email and sends approved replies.

Credentials (created in Google Cloud, see PHASE1-GMAIL-SETUP.md):
  secrets/google_client.json   OAuth client (Desktop app) you download from Google
  secrets/gmail_token.json     minted by gmail_auth.py after you consent once
"""
import os
import base64
from email.mime.text import MIMEText

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


def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    if mime == "text/html":
        data = payload.get("body", {}).get("data", "")
        if data:
            html = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
            # Strip tags crudely for plain-text consumption by LLM
            import re
            return re.sub(r"<[^>]+>", " ", html).strip()
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result
    return ""


def _extract_image_refs(payload: dict) -> list:
    """Recursively find image attachments in a Gmail message payload.
    Returns list of dicts with 'mime', and either 'data' (inline) or 'attachment_id' (needs fetch)."""
    refs = []
    mime = payload.get("mimeType", "")
    if mime in ("image/png", "image/jpeg", "image/jpg", "image/gif"):
        body = payload.get("body", {})
        data = body.get("data", "")
        attachment_id = body.get("attachmentId", "")
        if data:
            refs.append({"mime": mime, "data": data})
        elif attachment_id:
            refs.append({"mime": mime, "attachment_id": attachment_id})
    for part in payload.get("parts", []):
        refs.extend(_extract_image_refs(part))
    return refs


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
                userId="me", id=ref["id"], format="full",
            ).execute()
            headers = msg.get("payload", {}).get("headers", [])
            subject = _header(headers, "Subject")
            sender = _header(headers, "From")
            date = _header(headers, "Date")
            body = _extract_body(msg.get("payload", {}))
            image_refs = _extract_image_refs(msg.get("payload", {}))
            # Fetch attachment data for any large images not returned inline
            images = []
            for img in image_refs:
                if img.get("data"):
                    images.append({"mime": img["mime"], "data": img["data"]})
                elif img.get("attachment_id"):
                    try:
                        att = service.users().messages().attachments().get(
                            userId="me", messageId=ref["id"], id=img["attachment_id"]
                        ).execute()
                        if att.get("data"):
                            images.append({"mime": img["mime"], "data": att["data"]})
                    except Exception as e:
                        print(f"[gmail] Failed to fetch attachment: {e}")
            event = {
                "source": "gmail",
                "id": ref["id"],
                "from": sender,
                "subject": subject,
                "date": date,
                "text": f"From: {sender}\nSubject: {subject}\nDate: {date}\n\n{body}",
            }
            if images:
                event["images"] = images
            events.append(event)
        return events

    def execute(self, action_type: str, payload: dict) -> str:
        if action_type == "send_email":
            try:
                scopes = [
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.send",
                ]
                service = build_service(scopes)
                msg = MIMEText(payload.get("body", ""))
                msg["to"] = payload.get("to", "")
                msg["subject"] = payload.get("subject", "")
                if payload.get("reply_to_id"):
                    msg["In-Reply-To"] = payload["reply_to_id"]
                    msg["References"] = payload["reply_to_id"]
                raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
                sent = service.users().messages().send(
                    userId="me", body={"raw": raw}
                ).execute()
                return f"Sent email to {payload.get('to')} (id: {sent.get('id')})"
            except Exception as e:
                return f"[gmail] send failed: {e}"
        return f"[gmail] unsupported action: {action_type}"
