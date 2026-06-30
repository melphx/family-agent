"""Family Agent — approval + dashboard web UI."""
import json
import calendar
from datetime import datetime, date, timezone, timedelta
from flask import Flask, request, redirect

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Family Agent</title>
<style>
:root{{
  --bg:#eef0f5;--surface:#fff;--border:#e2e5eb;
  --text:#111827;--muted:#6b7280;--light:#f8f9fb;
  --green:#16a34a;--green-bg:#dcfce7;
  --red:#dc2626;--red-bg:#fee2e2;
  --blue:#2563eb;--blue-bg:#dbeafe;
  --yellow:#d97706;--yellow-bg:#fef3c7;
  --purple:#7c3aed;--purple-bg:#ede9fe;
  --orange:#ea580c;--orange-bg:#ffedd5;
  --teal:#0891b2;--teal-bg:#cffafe;
  --r:14px;--sh:0 2px 10px rgba(0,0,0,.07);
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}

/* HEADER */
header{{background:linear-gradient(135deg,#0f2444 0%,#1d4ed8 100%);color:#fff;padding:0 24px}}
.header-inner{{max-width:1200px;margin:0 auto;padding:16px 0;display:flex;align-items:center;gap:14px}}
.logo{{font-size:28px}}
.header-text h1{{font-size:19px;font-weight:700}}
.header-text p{{font-size:12px;opacity:.65;margin-top:1px}}
.badge{{margin-left:auto;background:#ef4444;color:#fff;font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.65}}}}

/* SUMMARY BANNER */
.summary-bar{{background:linear-gradient(135deg,#1e3a5f,#1d4ed8);color:#fff;padding:0 24px}}
.summary-inner{{max-width:1200px;margin:0 auto;padding:14px 0 16px}}
.summary-label{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;opacity:.6;margin-bottom:6px}}
.summary-text{{font-size:15px;line-height:1.6;opacity:.92}}

/* STATS */
.stats-bar{{background:var(--surface);border-bottom:1px solid var(--border);padding:0 24px}}
.stats-inner{{max-width:1200px;margin:0 auto;display:flex;gap:0}}
.stat{{padding:14px 28px 14px 0;display:flex;align-items:center;gap:10px;border-right:1px solid var(--border);margin-right:28px}}
.stat:last-child{{border-right:none}}
.stat-icon{{font-size:20px}}
.stat-num{{font-size:22px;font-weight:800;line-height:1}}
.stat-label{{font-size:11px;color:var(--muted);margin-top:1px}}
.sn-red{{color:var(--red)}} .sn-green{{color:var(--green)}} .sn-blue{{color:var(--blue)}} .sn-purple{{color:var(--purple)}}

/* LAYOUT */
.layout{{max-width:1200px;margin:0 auto;padding:20px 24px 60px;display:grid;grid-template-columns:300px 1fr;gap:20px}}
@media(max-width:760px){{.layout{{grid-template-columns:1fr}}}}

/* SECTION TITLE */
.stitle{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:0 0 10px;display:flex;align-items:center;gap:6px}}
.stitle::after{{content:"";flex:1;height:1px;background:var(--border)}}

/* CARDS */
.card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:16px;margin-bottom:10px;box-shadow:var(--sh)}}

/* CALENDAR */
.cal-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}}
.cal-month-title{{font-size:15px;font-weight:700}}
.cal-nav{{display:flex;gap:6px}}
.cal-nav a{{color:var(--blue);text-decoration:none;font-size:18px;padding:2px 6px;border-radius:6px}}
.cal-nav a:hover{{background:var(--blue-bg)}}
.cal-grid{{display:grid;grid-template-columns:repeat(7,1fr);gap:2px;text-align:center}}
.cal-dow{{font-size:10px;font-weight:700;color:var(--muted);padding:4px 0;text-transform:uppercase}}
.cal-cell{{aspect-ratio:1;display:flex;flex-direction:column;align-items:center;justify-content:center;border-radius:8px;font-size:12px;font-weight:500;position:relative;cursor:default}}
.cal-cell.other-month{{color:var(--border)}}
.cal-cell.today{{background:var(--blue);color:#fff;font-weight:800}}
.cal-cell.has-event::after{{content:"";position:absolute;bottom:3px;width:5px;height:5px;border-radius:50%;background:var(--green)}}
.cal-cell.today.has-event::after{{background:#fff}}
.cal-divider{{border:none;border-top:1px solid var(--border);margin:12px 0}}
.cal-upcoming-title{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:8px}}
.cal-event-row{{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid var(--border)}}
.cal-event-row:last-child{{border-bottom:none}}
.cal-badge{{min-width:36px;text-align:center}}
.cal-bday{{font-size:17px;font-weight:800;line-height:1}}
.cal-bmon{{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}}
.cal-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.d-ot{{background:var(--purple)}} .d-pt{{background:var(--blue)}} .d-other{{background:var(--green)}}
.cal-info .cal-title{{font-size:13px;font-weight:600;line-height:1.3}}
.cal-info .cal-time{{font-size:11px;color:var(--muted)}}

/* PENDING CARD */
.pcard{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:16px;margin-bottom:10px;box-shadow:var(--sh)}}
.pcard-top{{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px}}
.type-icon{{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}}
.ti-send_email{{background:var(--blue-bg)}} .ti-create_event{{background:var(--green-bg)}}
.ti-place_call{{background:var(--yellow-bg)}} .ti-check_website{{background:var(--purple-bg)}}
.ti-order_item{{background:var(--orange-bg)}}
.pcard-meta .pcard-type{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}}
.pcard-meta .pcard-summary{{font-size:14px;font-weight:600;line-height:1.4;margin-top:2px}}
.payload{{background:var(--light);border-radius:8px;padding:10px;font-size:12px;color:#374151;line-height:1.7;margin-bottom:10px}}
.pr{{display:grid;grid-template-columns:80px 1fr;gap:2px}}
.pk{{color:var(--muted)}} .pv{{word-break:break-word}}
.actions{{display:flex;gap:8px}}
.btn{{display:inline-flex;align-items:center;justify-content:center;gap:5px;padding:9px 0;border-radius:10px;font-size:13px;font-weight:600;text-decoration:none;flex:1;transition:filter .15s}}
.btn:active{{filter:brightness(.88)}}
.btn-ok{{background:var(--green);color:#fff}}
.btn-no{{background:var(--light);color:var(--text);border:1px solid var(--border)}}

/* RECENT CARD */
.rcard{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:14px;margin-bottom:8px;box-shadow:var(--sh);display:flex;align-items:flex-start;gap:10px}}
.rcard-body{{flex:1;min-width:0}}
.rcard-type{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}}
.rcard-summary{{font-size:13px;font-weight:600;margin-top:2px;line-height:1.4}}
.rcard-result{{font-size:11px;color:var(--muted);margin-top:4px}}
.pill{{display:inline-flex;align-items:center;font-size:10px;font-weight:700;padding:3px 8px;border-radius:999px;text-transform:uppercase;letter-spacing:.04em;flex-shrink:0}}
.p-executed{{background:var(--green-bg);color:var(--green)}}
.p-denied{{background:var(--red-bg);color:var(--red)}}
.p-approved{{background:var(--blue-bg);color:var(--blue)}}

.empty{{text-align:center;padding:28px;color:var(--muted);font-size:14px}}
.empty-icon{{font-size:28px;margin-bottom:6px}}
.refresh{{display:block;text-align:center;color:var(--blue);font-size:12px;text-decoration:none;margin-top:16px}}
</style>
</head>
<body>

<header>
  <div class="header-inner">
    <div class="logo">🏠</div>
    <div class="header-text">
      <h1>Family Agent</h1>
      <p>Wills Family Dashboard</p>
    </div>
    {badge}
  </div>
</header>

<div class="summary-bar">
  <div class="summary-inner">
    <div class="summary-label">Today's Summary</div>
    <div class="summary-text">{summary_text}</div>
  </div>
</div>

<div class="stats-bar">
  <div class="stats-inner">
    <div class="stat"><div class="stat-icon">⏳</div><div><div class="stat-num sn-red">{pending_count}</div><div class="stat-label">Pending</div></div></div>
    <div class="stat"><div class="stat-icon">✅</div><div><div class="stat-num sn-green">{done_count}</div><div class="stat-label">Completed</div></div></div>
    <div class="stat"><div class="stat-icon">📅</div><div><div class="stat-num sn-blue">{upcoming_count}</div><div class="stat-label">Upcoming</div></div></div>
    <div class="stat"><div class="stat-icon">📋</div><div><div class="stat-num sn-purple">{total_count}</div><div class="stat-label">All time</div></div></div>
  </div>
</div>

<div class="layout">

  <!-- LEFT: CALENDAR -->
  <div class="left-col">
    <div class="stitle">Calendar</div>
    <div class="card">
      <div class="cal-header">
        <div class="cal-month-title">{cal_month_title}</div>
      </div>
      <div class="cal-grid">
        <div class="cal-dow">Su</div><div class="cal-dow">Mo</div><div class="cal-dow">Tu</div>
        <div class="cal-dow">We</div><div class="cal-dow">Th</div><div class="cal-dow">Fr</div>
        <div class="cal-dow">Sa</div>
        {cal_cells}
      </div>
      <hr class="cal-divider">
      <div class="cal-upcoming-title">Upcoming</div>
      {cal_list}
    </div>
  </div>

  <!-- RIGHT: APPROVALS + ACTIVITY -->
  <div class="right-col">
    <div class="stitle">Needs your approval</div>
    {cards}

    <div class="stitle" style="margin-top:20px">Recent activity</div>
    {recent}

    <a class="refresh" href="/">↻ Refresh</a>
  </div>

</div>
</body>
</html>"""

TYPE_ICONS  = {"send_email":"✉️","create_event":"📅","place_call":"📞","check_website":"🔍","order_item":"📦"}
TYPE_LABELS = {"send_email":"Send Email","create_event":"Add to Calendar","place_call":"Place Call","check_website":"Check Website","order_item":"Order Item"}


def _payload_html(raw):
    if isinstance(raw, str):
        try:
            p = json.loads(raw) if raw else {}
        except Exception:
            return f'<div class="pv">{raw}</div>'
    else:
        p = raw or {}
    return "".join(
        f'<div class="pr"><span class="pk">{k}</span><span class="pv">{v}</span></div>'
        for k, v in p.items()
    )


def _pending_card(p):
    icon  = TYPE_ICONS.get(p["type"], "⚡")
    label = TYPE_LABELS.get(p["type"], p["type"])
    return (
        f'<div class="pcard">'
        f'<div class="pcard-top">'
        f'<div class="type-icon ti-{p["type"]}">{icon}</div>'
        f'<div class="pcard-meta">'
        f'<div class="pcard-type">{label} · {p["connector"]}</div>'
        f'<div class="pcard-summary">{p["summary"]}</div>'
        f'</div></div>'
        f'<div class="payload">{_payload_html(p["payload"])}</div>'
        f'<div class="actions">'
        f'<a class="btn btn-ok" href="/decide?id={p["id"]}&ok=1">✓ Approve</a>'
        f'<a class="btn btn-no" href="/decide?id={p["id"]}&ok=0">✕ Deny</a>'
        f'</div></div>'
    )


def _recent_card(r):
    icon   = TYPE_ICONS.get(r["type"], "⚡")
    status = r["status"]
    pill_cls = {"executed":"p-executed","denied":"p-denied","approved":"p-approved"}.get(status,"p-approved")
    label    = {"executed":"✓ Done","denied":"✕ Denied","approved":"Approved"}.get(status, status)
    result   = r.get("result") or ""
    return (
        f'<div class="rcard">'
        f'<div class="type-icon ti-{r["type"]}" style="width:32px;height:32px;font-size:15px">{icon}</div>'
        f'<div class="rcard-body">'
        f'<div class="rcard-type">{TYPE_LABELS.get(r["type"],r["type"])}</div>'
        f'<div class="rcard-summary">{r["summary"]}</div>'
        + (f'<div class="rcard-result">{result}</div>' if result else "")
        + f'</div>'
        f'<span class="pill {pill_cls}">{label}</span>'
        f'</div>'
    )


def _dot_class(title):
    tl = title.lower()
    if "ot" in tl or "occupational" in tl: return "d-ot"
    if "pt" in tl or "physical" in tl:     return "d-pt"
    return "d-other"


def _cal_row(event):
    title = event.get("title","Event")
    start = event.get("start","")
    day = mon = time_str = ""
    try:
        if "T" in start:
            dt = datetime.fromisoformat(start.replace("Z","+00:00"))
            day      = dt.strftime("%-d")
            mon      = dt.strftime("%b")
            time_str = dt.strftime("%-I:%M %p")
        else:
            dt       = datetime.strptime(start, "%Y-%m-%d")
            day      = dt.strftime("%-d")
            mon      = dt.strftime("%b")
            time_str = "All day"
    except Exception:
        day, mon, time_str = "—", "", start
    dot = _dot_class(title)
    return (
        f'<div class="cal-event-row">'
        f'<div class="cal-badge"><div class="cal-bday">{day}</div><div class="cal-bmon">{mon}</div></div>'
        f'<div class="cal-dot {dot}"></div>'
        f'<div class="cal-info"><div class="cal-title">{title}</div><div class="cal-time">{time_str}</div></div>'
        f'</div>'
    )


def _build_calendar(cal_events):
    today    = date.today()
    year     = today.year
    month    = today.month
    month_title = today.strftime("%B %Y")

    # Collect days that have events
    event_days = set()
    for e in cal_events:
        start = e.get("start","")
        try:
            if "T" in start:
                dt = datetime.fromisoformat(start.replace("Z","+00:00"))
            else:
                dt = datetime.strptime(start, "%Y-%m-%d")
            if dt.year == year and dt.month == month:
                event_days.add(dt.day)
        except Exception:
            pass

    # Build grid
    cal = calendar.Calendar(firstweekday=6)  # Sunday first
    weeks = cal.monthdayscalendar(year, month)
    cells = ""
    for week in weeks:
        for d in week:
            if d == 0:
                cells += '<div class="cal-cell other-month">·</div>'
            else:
                classes = "cal-cell"
                if d == today.day: classes += " today"
                if d in event_days: classes += " has-event"
                cells += f'<div class="{classes}">{d}</div>'

    return month_title, cells


def _build_summary(pending, cal_events, past):
    today = date.today()
    today_str = today.strftime("%A, %B %-d")
    parts = [f"It's {today_str}."]

    if pending:
        types = list({TYPE_LABELS.get(p["type"], p["type"]) for p in pending})
        parts.append(f"You have {len(pending)} action{'s' if len(pending)>1 else ''} waiting for approval ({', '.join(types)}).")
    else:
        parts.append("No pending approvals — you're all caught up.")

    # Next upcoming event
    upcoming = sorted(
        [e for e in cal_events if e.get("start")],
        key=lambda e: e["start"]
    )
    if upcoming:
        next_e = upcoming[0]
        title  = next_e.get("title","event")
        start  = next_e.get("start","")
        try:
            if "T" in start:
                dt = datetime.fromisoformat(start.replace("Z","+00:00"))
                when = dt.strftime("%A at %-I:%M %p")
            else:
                dt = datetime.strptime(start, "%Y-%m-%d")
                when = dt.strftime("%A %B %-d")
            parts.append(f"Next up: {title} on {when}.")
        except Exception:
            parts.append(f"Next up: {title}.")

    done = sum(1 for r in past if r["status"] == "executed")
    if done:
        parts.append(f"{done} action{'s' if done>1 else ''} completed so far.")

    return " ".join(parts)


def serve(agent, port: int = 8000):
    app = Flask(__name__)

    def render():
        pending = agent.queue.list(status="pending")
        all_q   = agent.queue.list()
        past    = [r for r in all_q if r["status"] != "pending"]
        done_count = sum(1 for r in past if r["status"] == "executed")

        cal_events = []
        try:
            cal_events = agent.connectors["calendar"].fetch_events()
        except Exception:
            pass

        badge = f'<span class="badge">{len(pending)}</span>' if pending else ""
        summary_text = _build_summary(pending, cal_events, past)
        month_title, cal_cells = _build_calendar(cal_events)

        cards  = "".join(_pending_card(p) for p in pending) or \
            '<div class="empty"><div class="empty-icon">✅</div>Nothing waiting on you.</div>'
        recent = "".join(_recent_card(r) for r in past[:20]) or \
            '<div class="empty"><div class="empty-icon">📭</div>No activity yet.</div>'
        cal_list = "".join(_cal_row(e) for e in cal_events[:12]) or \
            '<div style="color:var(--muted);font-size:13px;padding:8px 0">No upcoming events.</div>'

        return PAGE.format(
            badge=badge,
            summary_text=summary_text,
            pending_count=len(pending),
            done_count=done_count,
            upcoming_count=len(cal_events),
            total_count=len(all_q),
            cal_month_title=month_title,
            cal_cells=cal_cells,
            cal_list=cal_list,
            cards=cards,
            recent=recent,
        )

    @app.route("/")
    def index():
        return render()

    @app.route("/decide")
    def decide():
        pid = request.args.get("id")
        ok  = request.args.get("ok") == "1"
        agent.queue.decide(pid, ok)
        if ok:
            agent.execute_approved()
        return redirect("/")

    app.run(host="0.0.0.0", port=port)
