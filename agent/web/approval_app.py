"""One-tap approval page for your phone."""
import json
import time
from flask import Flask, request, redirect

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Family Agent</title>
<style>
  :root {{
    --bg: #f5f5f7;
    --surface: #ffffff;
    --border: #e0e0e5;
    --text: #1a1a2e;
    --muted: #6b7280;
    --green: #16a34a;
    --green-bg: #dcfce7;
    --red: #dc2626;
    --red-bg: #fee2e2;
    --blue: #2563eb;
    --blue-bg: #dbeafe;
    --yellow: #d97706;
    --yellow-bg: #fef3c7;
    --purple: #7c3aed;
    --purple-bg: #ede9fe;
    --radius: 16px;
    --shadow: 0 2px 12px rgba(0,0,0,.07);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }}
  header {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    position: sticky;
    top: 0;
    z-index: 10;
  }}
  .logo {{ font-size: 24px; }}
  .header-text h1 {{ font-size: 18px; font-weight: 700; }}
  .header-text p {{ font-size: 13px; color: var(--muted); }}
  .badge {{
    margin-left: auto;
    background: var(--red);
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    border-radius: 999px;
    padding: 2px 8px;
    display: {badge_display};
  }}
  main {{ max-width: 680px; margin: 0 auto; padding: 20px 16px 40px; }}
  .section-title {{
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: var(--muted);
    margin: 24px 0 10px;
  }}
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px;
    margin-bottom: 12px;
    box-shadow: var(--shadow);
  }}
  .card-header {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 10px;
  }}
  .type-icon {{
    width: 38px; height: 38px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
  }}
  .type-send_email    {{ background: var(--blue-bg); }}
  .type-create_event  {{ background: var(--green-bg); }}
  .type-place_call    {{ background: var(--yellow-bg); }}
  .type-check_website {{ background: var(--purple-bg); }}
  .type-order_item    {{ background: var(--red-bg); }}
  .card-meta {{ flex: 1; }}
  .card-type {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .05em;
    color: var(--muted);
    margin-bottom: 2px;
  }}
  .card-summary {{ font-size: 15px; font-weight: 600; line-height: 1.4; }}
  .payload {{
    background: var(--bg);
    border-radius: 10px;
    padding: 12px;
    margin: 12px 0;
    font-size: 13px;
    color: #374151;
    line-height: 1.6;
  }}
  .payload-row {{ display: flex; gap: 6px; margin-bottom: 4px; }}
  .payload-key {{ color: var(--muted); min-width: 80px; flex-shrink: 0; }}
  .payload-val {{ word-break: break-word; }}
  .actions {{ display: flex; gap: 8px; margin-top: 14px; }}
  .btn {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 10px 18px;
    border-radius: 10px;
    font-size: 14px; font-weight: 600;
    text-decoration: none;
    transition: opacity .15s;
  }}
  .btn:active {{ opacity: .7; }}
  .btn-approve {{ background: var(--green); color: #fff; flex: 1; justify-content: center; }}
  .btn-deny    {{ background: var(--bg); color: var(--text); border: 1px solid var(--border); flex: 1; justify-content: center; }}
  .status-pill {{
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 11px; font-weight: 600;
    padding: 3px 8px; border-radius: 999px;
    text-transform: uppercase; letter-spacing: .04em;
  }}
  .pill-executed {{ background: var(--green-bg); color: var(--green); }}
  .pill-denied   {{ background: var(--red-bg); color: var(--red); }}
  .pill-approved {{ background: var(--blue-bg); color: var(--blue); }}
  .result-text {{ font-size: 12px; color: var(--muted); margin-top: 6px; }}
  .empty {{
    text-align: center;
    padding: 40px 20px;
    color: var(--muted);
    font-size: 15px;
  }}
  .empty .icon {{ font-size: 36px; margin-bottom: 8px; }}
  .refresh {{
    display: block;
    text-align: center;
    color: var(--blue);
    font-size: 13px;
    margin-top: 20px;
    text-decoration: none;
  }}
</style>
</head>
<body>
<header>
  <div class="logo">🏠</div>
  <div class="header-text">
    <h1>Family Agent</h1>
    <p>Wills Family · Approval Queue</p>
  </div>
  <span class="badge">{pending_count}</span>
</header>
<main>
  <div class="section-title">Needs your approval</div>
  {cards}
  <div class="section-title">Recent activity</div>
  {recent}
  <a class="refresh" href="/">↻ Refresh</a>
</main>
</body>
</html>"""

TYPE_ICONS = {
    "send_email":    "✉️",
    "create_event":  "📅",
    "place_call":    "📞",
    "check_website": "🔍",
    "order_item":    "📦",
}

TYPE_LABELS = {
    "send_email":    "Send Email",
    "create_event":  "Add to Calendar",
    "place_call":    "Place Call",
    "check_website": "Check Website",
    "order_item":    "Order Item",
}


def _payload_html(payload_raw):
    if isinstance(payload_raw, str):
        try:
            payload = json.loads(payload_raw) if payload_raw else {}
        except Exception:
            return f'<div class="payload-row"><span class="payload-val">{payload_raw}</span></div>'
    else:
        payload = payload_raw or {}
    rows = ""
    for k, v in payload.items():
        rows += (
            f'<div class="payload-row">'
            f'<span class="payload-key">{k}</span>'
            f'<span class="payload-val">{v}</span>'
            f'</div>'
        )
    return rows or ""


def _pending_card(p):
    icon = TYPE_ICONS.get(p["type"], "⚡")
    label = TYPE_LABELS.get(p["type"], p["type"])
    return (
        f'<div class="card">'
        f'<div class="card-header">'
        f'<div class="type-icon type-{p["type"]}">{icon}</div>'
        f'<div class="card-meta">'
        f'<div class="card-type">{label} · {p["connector"]}</div>'
        f'<div class="card-summary">{p["summary"]}</div>'
        f'</div></div>'
        f'<div class="payload">{_payload_html(p["payload"])}</div>'
        f'<div class="actions">'
        f'<a class="btn btn-approve" href="/decide?id={p["id"]}&ok=1">✓ Approve</a>'
        f'<a class="btn btn-deny"    href="/decide?id={p["id"]}&ok=0">✕ Deny</a>'
        f'</div></div>'
    )


def _recent_card(r):
    icon = TYPE_ICONS.get(r["type"], "⚡")
    status = r["status"]
    pill_class = f"pill-{status}" if status in ("executed", "denied", "approved") else "pill-approved"
    status_label = {"executed": "✓ Done", "denied": "✕ Denied", "approved": "✓ Approved"}.get(status, status)
    result = r.get("result") or ""
    return (
        f'<div class="card">'
        f'<div class="card-header">'
        f'<div class="type-icon type-{r["type"]}">{icon}</div>'
        f'<div class="card-meta">'
        f'<div class="card-type">{TYPE_LABELS.get(r["type"], r["type"])} · {r["connector"]}</div>'
        f'<div class="card-summary">{r["summary"]}</div>'
        f'</div>'
        f'<span class="status-pill {pill_class}">{status_label}</span>'
        f'</div>'
        + (f'<div class="result-text">{result}</div>' if result else "")
        + f'</div>'
    )


def serve(agent, port: int = 8000):
    app = Flask(__name__)

    def render():
        pending = agent.queue.list(status="pending")
        past = [r for r in agent.queue.list() if r["status"] != "pending"]

        if pending:
            cards = "".join(_pending_card(p) for p in pending)
            badge_display = "inline-flex"
            pending_count = str(len(pending))
        else:
            cards = '<div class="empty"><div class="icon">✅</div>Nothing waiting on you right now.</div>'
            badge_display = "none"
            pending_count = ""

        recent = "".join(_recent_card(r) for r in past[:20]) or \
            '<div class="empty"><div class="icon">📭</div>No activity yet.</div>'

        return PAGE.format(
            cards=cards,
            recent=recent,
            badge_display=badge_display,
            pending_count=pending_count,
        )

    @app.route("/")
    def index():
        return render()

    @app.route("/decide")
    def decide():
        pid = request.args.get("id")
        ok = request.args.get("ok") == "1"
        agent.queue.decide(pid, ok)
        if ok:
            agent.execute_approved()
        return redirect("/")

    app.run(host="0.0.0.0", port=port)
