# Family Agent — First Layer

A small, model-agnostic agent core with a **propose → approve** safety gate.
This scaffold runs end-to-end in **demo mode with no credentials**, so you can see the
core loop (event → reason → proposed action → human approval → execute) before wiring
up Gmail, Calendar, OpenAI, payments, or phone.

It maps directly to the architecture in `../family-agent-blueprint.md`.

```
family-agent/
├── run.py                  # entrypoint: runs one agent cycle, then serves the approval page
├── config.example.yaml     # copy to config.yaml and fill in
├── requirements.txt
├── agent/
│   ├── core.py             # orchestrator: watchers -> reasoner -> planner -> approval queue
│   ├── approvals.py        # the approval queue (SQLite) — the safety heart
│   ├── memory.py           # readable memory store (people, recurring obligations, log)
│   ├── llm.py              # OpenAI wrapper (demo mode if no key)
│   ├── web/approval_app.py # one-tap approve/deny page for your phone
│   └── connectors/
│       ├── base.py         # Connector interface + ProposedAction model
│       ├── gmail.py        # stub: read email (Gmail API) — TODO creds
│       ├── calendar.py     # stub: read/create events (Google Calendar API) — TODO creds
│       └── web_monitor.py  # stub: watch a website (e.g. Digby's karate) for changes
```

## Quick start (demo mode, no accounts needed)

```bash
cd family-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml      # demo mode works without editing it
python run.py
```

This runs one agent cycle. In demo mode it injects a sample "Digby karate" event,
the reasoner proposes a draft email + a calendar reminder, and both land in the
**approval queue** instead of being sent. Then it starts the approval page at
http://localhost:8000 where you approve or deny each one. Nothing leaves the machine.

## Going live (Phase 1+), in order

1. **OpenAI**: put your key in `config.yaml` (or `OPENAI_API_KEY` env). Reasoner switches from canned to real.
2. **Gmail (read-only first)**: create a Google Cloud project, enable the Gmail API, download OAuth client creds to `secrets/google_client.json`, then run the gmail connector auth. Scope: `gmail.readonly` to start.
3. **Calendar**: same Google project, enable Calendar API, add `calendar.events` scope.
4. **Approval channel**: expose the approval page over HTTPS (reverse proxy) or have it email/text you the approve links.
5. **Commerce / phone**: later phases — see the blueprint. Use limited virtual cards; use Twilio for real calling (Google Voice has no calling API).

## Safety defaults (do not weaken for the prototype)

- Every connector action is a **ProposedAction** first. Nothing outbound or paid executes without an approval row flipped to `approved`.
- `auto_approve_types` in config is limited to read/monitor actions only.
- All proposals and executions are logged in `data/agent.db`.
- Keep `secrets/` out of version control (see `.gitignore`).

## Troubleshooting

- **`sqlite3 disk I/O error`**: you're running from a synced/network folder (Dropbox,
  a mounted share, some cloud drives). SQLite needs real file locking. Run from a
  local disk (a VPS works fine), or move the project under your home directory.
