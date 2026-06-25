"""One-time Gmail authorization for a headless server.

Run once:  python gmail_auth.py

It starts a tiny local consent server on port 8765 and prints a Google URL. Because
the server is headless, you reach it from your own browser through an SSH tunnel:

    # on YOUR computer, in a separate terminal:
    ssh -L 8765:localhost:8765 root@SERVER_IP

Then open the printed URL in your browser, pick the family Gmail, approve the
read-only permission, and Google redirects back through the tunnel. The script saves
secrets/gmail_token.json and prints your 5 most recent subjects to prove it works.
Requires secrets/google_client.json (the OAuth client you downloaded from Google).
"""
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CLIENT_FILE = os.path.join("secrets", "google_client.json")
TOKEN_FILE = os.path.join("secrets", "gmail_token.json")


def main():
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    if not os.path.exists(CLIENT_FILE):
        raise SystemExit(
            f"Missing {CLIENT_FILE}. Download your OAuth client (Desktop app) from "
            "Google Cloud and save it there. See PHASE1-GMAIL-SETUP.md."
        )

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_FILE, SCOPES)
    # Headless: don't try to launch a browser on the server; we use the SSH tunnel.
    creds = flow.run_local_server(
        host="localhost", port=8765, open_browser=False,
        bind_addr="0.0.0.0",
        authorization_prompt_message="Open this URL in your (tunneled) browser:\n{url}",
        success_message="Authorized. You can close this tab and return to the terminal.",
    )

    os.makedirs("secrets", exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    print(f"\nSaved {TOKEN_FILE}.")

    # quick proof: list 5 recent subjects
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    resp = service.users().messages().list(userId="me", maxResults=5).execute()
    print("\nMost recent messages:")
    for ref in resp.get("messages", []):
        m = service.users().messages().get(
            userId="me", id=ref["id"], format="metadata",
            metadataHeaders=["Subject"],
        ).execute()
        subj = next((h["value"] for h in m["payload"]["headers"]
                     if h["name"] == "Subject"), "(no subject)")
        print(f"  - {subj}")
    print("\nGmail is connected. Set mode: live and connectors.gmail.enabled: true in config.yaml.")


if __name__ == "__main__":
    main()
