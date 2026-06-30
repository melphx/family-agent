"""Family Agent — approval + dashboard web UI."""
import json
import time
from datetime import datetime, timezone
from flask import Flask, request, redirect

# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------
PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Family Agent</title>
<style>
:root {{
  --bg:#f0f2f5;--surface:#fff;--border:#e4e6ea;
  --text:#111827;--muted:#6b7280;--light:#f9fafb;
  --green:#16a34a;--green-bg:#dcfce7;--green-light:#f0fdf4;
  --red:#dc2626;--red-bg:#fee2e2;
  --blue:#2563eb;--blue-bg:#dbeafe;--blue-light:#eff6ff;
  --yellow:#d97706;--yellow-bg:#fef3c7;
  --purple:#7c3aed;--purple-bg:#ede9fe;
  --orange:#ea580c;--orange-bg:#ffedd5;
  --r:14px;--shadow:0 1px 8px rgba(0,0,0,.08);
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}

/* HEADER */
header{{background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);color:#fff;padding:0 20px}}
.header-inner{{max-width:760px;margin:0 auto;padding:18px 0;display:flex;align-items:center;gap:14px}}
.logo{{font-size:28px;filter:drop-shadow(0 2px 4px rgba(0,0,0,.2))}}
.header-text h1{{font-size:20px;font-weight:700;letter-spacing:-.3px}}
.header-text p{{font-size:13px;opacity:.75;margin-top:1px}}
.badge{{margin-left:auto;background:#ef4444;color:#fff;font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.7}}}}

/* LAYOUT */
main{{max-width:760px;margin:0 auto;padding:20px 16px 60px}}

/* STAT CARDS */
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:20px}}
.stat{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:16px;box-shadow:var(--shadow);text-align:center}}
.stat-icon{{font-size:22px;margin-bottom:6px}}
.stat-num{{font-size:26px;font-weight:800;line-height:1}}
.stat-label{{font-size:11px;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:.04em}}
.stat-red .stat-num{{color:var(--red)}}
.stat-green .stat-num{{color:var(--green)}}
.stat-blue .stat-num{{color:var(--blue)}}

/* SECTION */
.section-title{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:24px 0 10px;display:flex;align-items:center;gap:6px}}
.section-title::after{{content:"";flex:1;height:1px;background:var(--border)}}

/* CARDS */
.card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:16px;margin-bottom:10px;box-shadow:var(--shadow)}}
.card-top{{display:flex;align-items:flex-start;gap:12px}}
.type-icon{{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0}}
.ti-send_email   {{background:var(--blue-bg)}}
.ti-create_event {{background:var(--green-bg)}}
.ti-place_call   {{background:var(--yellow-bg)}}
.ti-check_website{{background:var(--purple-bg)}}
.ti-order_item   {{background:var(--orange-bg)}}
.card-meta{{flex:1;min-width:0}}
.card-type{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:2px}}
.card-summary{{font-size:15px;font-weight:600;line-height:1.4}}
.payload{{background:var(--light);border-radius:8px;padding:10px 12px;margin:10px 0 0;font-size:13px;color:#374151;line-height:1.7}}
.payload-row{{display:grid;grid-template-columns:90px 1fr;gap:4px}}
.pk{{color:var(--muted);font-size:12px}}
.pv{{word-break:break-word}}
.actions{{display:flex;gap:8px;margin-top:12px}}
.btn{{display:inline-flex;align-items:center;justify-content:center;gap:5px;padding:10px 0;border-radius:10px;font-size:14px;font-weight:600;text-decoration:none;flex:1;transition:filter .15s}}
.btn:active{{filter:brightness(.9)}}
.btn-ok{{background:var(--green);color:#fff}}
.btn-no{{background:var(--light);color:var(--text);border:1px solid var(--border)}}

/* STATUS PILLS */
.pill{{display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:700;padding:3px 8px;border-radius:999px;text-transform:uppercase;letter-spacing:.04em;margin-left:auto;flex-shrink:0}}
.pill-executed{{background:var(--green-bg);color:var(--green)}}
.pill-denied{{background:var(--red-bg);color:var(--red)}}
.pill-approved{{background:var(--blue-bg);color:var(--blue)}}
.result{{font-size:12px;color:var(--muted);margin-top:6px;line-height:1.5}}

/* CALENDAR */
.cal-event{{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border)}}
.cal-event:last-child{{border-bottom:none}}
.cal-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.dot-ot{{background:#7c3aed}}.dot-pt{{background:#2563eb}}.dot-other{{background:#16a34a}}
.cal-info{{flex:1;min-width:0}}
.cal-title{{font-size:14px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.cal-time{{font-size:12px;color:var(--muted)}}
.cal-date{{text-align:right;flex-shrink:0}}
.cal-day{{font-size:18px;font-weight:800;line-height:1}}
.cal-month{{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}}
.cal-empty{{color:var(--muted);font-size:14px;padding:12px 0}}

/* EMPTY */
.empty{{text-align:center;padding:32px 16px;color:var(--muted)}}
.empty-icon{{font-size:32px;margin-bottom:8px}}

/* FOOTER */
.footer{{text-align:center;margin-top:24px}}
.refresh{{color:var(--blue);font-size:13px;text-decoration:none;display:inline-flex;align-items:center;gap:4px}}
.refresh:active{{opacity:.7}}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="logo">🏠</div>
    <div class="header-text">
      <h1>Family Agent</h1>
      <p>Wills Family · {now}</p>
    </div>
    {badge}
  </div>
</header>
<main>

  <!-- STATS -->
  <div class="stats">
    <div class="stat stat-red">
      <div class="stat-icon">⏳</div>
      <div class="stat-num">{pending_count}</div>
      <div class="stat-label">Pending</div>
    </div>
    <div class="stat stat-green">
      <div class="stat-icon">✅</div>
      <div class="stat-num">{done_count}</div>
      <div class="stat-label">Completed</div>
    </div>
    <div class="stat stat-blue">
      <div class="stat-icon">📅</div>
      <div class="stat-num">{upcoming_count}</div>
      <div class="stat-label">Upcoming</div>
    </div>
  </div>

  <!-- PENDING -->
  <div class="section-title">Needs your approval</div>
  {cards}

  <!-- CALENDAR -->
  <div class="section-title">Upcoming appointments</div>
  <div class="card">{calendar}</div>

  <!-- RECENT -->
  <div class="section-title">Recent activity</div>
  {recent}

  <div class="footer"><a class="refresh" href="/">↻ Refresh</a></div>
</main>
</body>
</html>"""

TYPE_ICONS = {
    "send_email": "✉️", "create_event": "📅",
    "place_call": "📞", "check_website": "🔍", "order_item": "📦",
}
TYPE_LABELS = {
    "send_email": "Send Email", "create_event": "Add to Calendar",
    "place_call": "Place Call", "check_website": "Check Website", "order_item": "Order Item",
}


def _payload_html(raw):
    if isinstance(raw, str):
        try:
            p = json.loads(raw) if raw else {}
        except Exception:
            return f'<div class="pv">{raw}</div>'
    else:
        p = raw or {}
    return "".join(
        f'<div class="payload-row"><span class="pk">{k}</span><span class="pv">{v}</span></div>'
        for k, v in p.items()
    )


def _pending_card(p):
    icon = TYPE_ICONS.get(p["type"], "⚡")
    label = TYPE_LABELS.get(p["type"], p["type"])
    return (
        f'<div class="card">'
        f'<div class="card-top">'
        f'<div class="type-icon ti-{p["type"]}">{icon}</div>'
        f'<div class="card-meta">'
        f'<div class="card-type">{label} · {p["connector"]}</div>'
        f'<div class="card-summary">{p["summary"]}</div>'
        f'</div></div>'
        f'<div class="payload">{_payload_html(p["payload"])}</div>'
        f'<div class="actions">'
        f'<a class="btn btn-ok" href="/decide?id={p["id"]}&ok=1">✓ Approve</a>'
        f'<a class="btn btn-no" href="/decide?id={p["id"]}&ok=0">✕ Deny</a>'
        f'</div></div>'
    )


def _recent_card(r):
    icon = TYPE_ICONS.get(r["type"], "⚡")
    status = r["status"]
    pill_cls = f"pill-{status}" if status in ("executed", "denied", "approved") else "pill-approved"
    status_label = {"executed": "✓ Done", "denied": "✕ Denied", "approved": "Approved"}.get(status, status)
    result = r.get("result") or ""
    return (
        f'<div class="card">'
        f'<div class="card-top">'
        f'<div class="type-icon ti-{r["type"]}">{icon}</div>'
        f'<div class="card-meta">'
        f'<div class="card-type">{TYPE_LABELS.get(r["type"], r["type"])} · {r["connector"]}</div>'
        f'<div class="card-summary">{r["summary"]}</div>'
        f'</div>'
        f'<span class="pill {pill_cls}">{status_label}</span>'
        f'</div>'
        + (f'<div class="result">{result}</div>' if result else "")
        + '</div>'
    )


def _cal_row(event):
    title = event.get("title", "Event")
    start = event.get("start", "")
    # Determine dot colour by title keywords
    tl = title.lower()
    if "ot" in tl or "occupational" in tl:
        dot = "dot-ot"
    elif "pt" in tl or "physical" in tl or "therapy" in tl:
        dot = "dot-pt"
    else:
        dot = "dot-other"
    # Parse date for display
    day = month = time_str = ""
    try:
        if "T" in start:
            dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            day = dt.strftime("%-d")
            month = dt.strftime("%b")
            time_str = dt.strftime("%-I:%M %p")
        else:
            dt = datetime.strptime(start, "%Y-%m-%d")
            day = dt.strftime("%-d")
            month = dt.strftime("%b")
            time_str = "All day"
    except Exception:
        day, month, time_str = "—", "", start
    return (
        f'<div class="cal-event">'
        f'<div class="cal-date"><div class="cal-day">{day}</div><div class="cal-month">{month}</div></div>'
        f'<div class="cal-dot {dot}"></div>'
        f'<div class="cal-info"><div class="cal-title">{title}</div><div class="cal-time">{time_str}</div></div>'
        f'</div>'
    )


def serve(agent, port: int = 8000):
    app = Flask(__name__)

    def render():
        pending = agent.queue.list(status="pending")
        past = [r for r in agent.queue.list() if r["status"] != "pending"]
        done_count = sum(1 for r in past if r["status"] == "executed")

        # Calendar events
        cal_events = []
        try:
            cal_events = agent.connectors["calendar"].fetch_events()
        except Exception:
            pass
        upcoming_count = len(cal_events)

        # Stats
        now_str = datetime.now().strftime("%a %b %-d, %-I:%M %p")

        # Badge
        badge = (
            f'<span class="badge">{len(pending)}</span>'
            if pending else ""
        )

        # Pending cards
        if pending:
            cards = "".join(_pending_card(p) for p in pending)
        else:
            cards = '<div class="empty"><div class="empty-icon">✅</div>Nothing waiting on you.</div>'

        # Calendar
        if cal_events:
            calendar = "".join(_cal_row(e) for e in cal_events[:10])
        else:
            calendar = '<div class="cal-empty">No upcoming events — or calendar not connected yet.</div>'

        # Recent
        recent = "".join(_recent_card(r) for r in past[:15]) or \
            '<div class="empty"><div class="empty-icon">📭</div>No activity yet.</div>'

        return PAGE.format(
            now=now_str,
            badge=badge,
            pending_count=len(pending),
            done_count=done_count,
            upcoming_count=upcoming_count,
            cards=cards,
            calendar=calendar,
            recent=recent,
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
