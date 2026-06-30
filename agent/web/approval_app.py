"""Family Agent — approval + dashboard + chat web UI."""
import json
import calendar
from datetime import datetime, date, timezone
from flask import Flask, request, redirect, jsonify

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
  --r:14px;--sh:0 2px 10px rgba(0,0,0,.07);
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}

/* HEADER */
header{{background:linear-gradient(135deg,#0f2444 0%,#1d4ed8 100%);color:#fff;padding:0 24px}}
.header-inner{{max-width:1200px;margin:0 auto;padding:14px 0;display:flex;align-items:center;gap:14px}}
.logo{{font-size:26px}}
.header-text h1{{font-size:18px;font-weight:700}}
.header-text p{{font-size:11px;opacity:.6;margin-top:1px}}
.header-actions{{margin-left:auto;display:flex;align-items:center;gap:10px}}
.badge{{background:#ef4444;color:#fff;font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.65}}}}
.btn-refresh{{background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.25);border-radius:8px;padding:7px 14px;font-size:13px;font-weight:600;text-decoration:none;display:flex;align-items:center;gap:6px;transition:background .15s}}
.btn-refresh:hover{{background:rgba(255,255,255,.25)}}
.btn-refresh.loading{{opacity:.6;pointer-events:none}}

/* SUMMARY */
.summary-bar{{background:linear-gradient(135deg,#1a3a6e,#1d4ed8);color:#fff;padding:0 24px}}
.summary-inner{{max-width:1200px;margin:0 auto;padding:14px 0}}
.summary-label{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;opacity:.55;margin-bottom:5px}}
.summary-text{{font-size:14px;line-height:1.65;opacity:.9;min-height:40px}}
.summary-text.loading{{opacity:.4;font-style:italic}}

/* STATS */
.stats-bar{{background:var(--surface);border-bottom:1px solid var(--border);padding:0 24px}}
.stats-inner{{max-width:1200px;margin:0 auto;display:flex}}
.stat{{padding:12px 28px 12px 0;display:flex;align-items:center;gap:10px;border-right:1px solid var(--border);margin-right:28px}}
.stat:last-child{{border-right:none}}
.stat-num{{font-size:22px;font-weight:800;line-height:1}}
.stat-label{{font-size:11px;color:var(--muted);margin-top:1px}}
.sn-red{{color:var(--red)}} .sn-green{{color:var(--green)}} .sn-blue{{color:var(--blue)}} .sn-purple{{color:var(--purple)}}

/* LAYOUT */
.layout{{max-width:1200px;margin:0 auto;padding:20px 24px 60px;display:grid;grid-template-columns:300px 1fr 320px;gap:20px}}
@media(max-width:900px){{.layout{{grid-template-columns:1fr}}}}

/* SECTION */
.stitle{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:0 0 10px;display:flex;align-items:center;gap:6px}}
.stitle::after{{content:"";flex:1;height:1px;background:var(--border)}}

/* CARD BASE */
.card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:16px;margin-bottom:10px;box-shadow:var(--sh)}}

/* CALENDAR */
.cal-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}}
.cal-month-title{{font-size:14px;font-weight:700}}
.cal-grid{{display:grid;grid-template-columns:repeat(7,1fr);gap:2px;text-align:center}}
.cal-dow{{font-size:9px;font-weight:700;color:var(--muted);padding:3px 0;text-transform:uppercase}}
.cal-cell{{aspect-ratio:1;display:flex;flex-direction:column;align-items:center;justify-content:center;border-radius:7px;font-size:11px;font-weight:500;position:relative}}
.cal-cell.other-month{{color:#d1d5db}}
.cal-cell.today{{background:var(--blue);color:#fff;font-weight:800}}
.cal-cell.has-event::after{{content:"";position:absolute;bottom:2px;width:4px;height:4px;border-radius:50%;background:var(--green)}}
.cal-cell.today.has-event::after{{background:#fff}}
.cal-divider{{border:none;border-top:1px solid var(--border);margin:10px 0}}
.cal-upcoming-title{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:7px}}
.cal-event-row{{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--border)}}
.cal-event-row:last-child{{border-bottom:none}}
.cal-badge{{min-width:32px;text-align:center}}
.cal-bday{{font-size:15px;font-weight:800;line-height:1}}
.cal-bmon{{font-size:9px;color:var(--muted);text-transform:uppercase}}
.cal-dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0}}
.d-ot{{background:var(--purple)}} .d-pt{{background:var(--blue)}} .d-other{{background:var(--green)}}
.cal-title{{font-size:12px;font-weight:600;line-height:1.3}}
.cal-time{{font-size:11px;color:var(--muted)}}

/* PENDING */
.pcard{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:15px;margin-bottom:10px;box-shadow:var(--sh)}}
.pcard-top{{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px}}
.type-icon{{width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0}}
.ti-send_email{{background:var(--blue-bg)}} .ti-create_event{{background:var(--green-bg)}}
.ti-place_call{{background:var(--yellow-bg)}} .ti-check_website{{background:var(--purple-bg)}}
.ti-order_item{{background:var(--orange-bg)}}
.pcard-type{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}}
.pcard-summary{{font-size:13px;font-weight:600;line-height:1.4;margin-top:2px}}
.payload{{background:var(--light);border-radius:8px;padding:9px;font-size:11px;color:#374151;line-height:1.7;margin-bottom:10px}}
.pr{{display:grid;grid-template-columns:76px 1fr;gap:2px}}
.pk{{color:var(--muted)}} .pv{{word-break:break-word}}
.actions{{display:flex;gap:8px}}
.btn{{display:inline-flex;align-items:center;justify-content:center;gap:5px;padding:9px 0;border-radius:9px;font-size:13px;font-weight:600;text-decoration:none;flex:1;transition:filter .15s}}
.btn:active{{filter:brightness(.88)}}
.btn-ok{{background:var(--green);color:#fff}}
.btn-no{{background:var(--light);color:var(--text);border:1px solid var(--border)}}

/* RECENT */
.rcard{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:13px;margin-bottom:8px;box-shadow:var(--sh);display:flex;align-items:flex-start;gap:9px}}
.rcard-body{{flex:1;min-width:0}}
.rcard-type{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}}
.rcard-summary{{font-size:12px;font-weight:600;margin-top:2px;line-height:1.4}}
.rcard-result{{font-size:11px;color:var(--muted);margin-top:3px}}
.pill{{display:inline-flex;align-items:center;font-size:10px;font-weight:700;padding:2px 7px;border-radius:999px;text-transform:uppercase;flex-shrink:0}}
.p-executed{{background:var(--green-bg);color:var(--green)}}
.p-denied{{background:var(--red-bg);color:var(--red)}}
.p-approved{{background:var(--blue-bg);color:var(--blue)}}

/* CHAT */
.chat-wrap{{display:flex;flex-direction:column;height:100%}}
.chat-messages{{flex:1;overflow-y:auto;max-height:480px;padding:4px 0;margin-bottom:10px;display:flex;flex-direction:column;gap:8px}}
.msg{{padding:10px 13px;border-radius:12px;font-size:13px;line-height:1.55;max-width:92%}}
.msg-user{{background:var(--blue);color:#fff;align-self:flex-end;border-bottom-right-radius:4px}}
.msg-agent{{background:var(--light);color:var(--text);align-self:flex-start;border:1px solid var(--border);border-bottom-left-radius:4px}}
.msg-thinking{{color:var(--muted);font-style:italic;background:var(--light);border:1px solid var(--border)}}
.chat-form{{display:flex;gap:8px}}
.chat-input{{flex:1;border:1px solid var(--border);border-radius:10px;padding:10px 13px;font-size:13px;outline:none;font-family:inherit}}
.chat-input:focus{{border-color:var(--blue);box-shadow:0 0 0 3px rgba(37,99,235,.1)}}
.chat-send{{background:var(--blue);color:#fff;border:none;border-radius:10px;padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer;transition:filter .15s}}
.chat-send:hover{{filter:brightness(1.1)}}
.chat-send:active{{filter:brightness(.9)}}

.empty{{text-align:center;padding:24px;color:var(--muted);font-size:13px}}
.empty-icon{{font-size:26px;margin-bottom:6px}}
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
    <div class="header-actions">
      {badge}
      <a class="btn-refresh" href="/refresh" id="refreshBtn">↻ Check emails</a>
    </div>
  </div>
</header>

<div class="summary-bar">
  <div class="summary-inner">
    <div class="summary-label">AI Summary</div>
    <div class="summary-text" id="summaryText">{summary_text}</div>
  </div>
</div>

<div class="stats-bar">
  <div class="stats-inner">
    <div class="stat"><div><div class="stat-num sn-red">{pending_count}</div><div class="stat-label">Pending</div></div></div>
    <div class="stat"><div><div class="stat-num sn-green">{done_count}</div><div class="stat-label">Completed</div></div></div>
    <div class="stat"><div><div class="stat-num sn-blue">{upcoming_count}</div><div class="stat-label">Upcoming</div></div></div>
    <div class="stat"><div><div class="stat-num sn-purple">{total_count}</div><div class="stat-label">All time</div></div></div>
  </div>
</div>

<div class="layout">

  <!-- LEFT: CALENDAR -->
  <div>
    <div class="stitle">Calendar</div>
    <div class="card">
      <div class="cal-header"><div class="cal-month-title">{cal_month_title}</div></div>
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

  <!-- MIDDLE: APPROVALS + ACTIVITY -->
  <div>
    <div class="stitle">Needs your approval</div>
    {cards}
    <div class="stitle" style="margin-top:20px">Recent activity</div>
    {recent}
  </div>

  <!-- RIGHT: CHAT -->
  <div>
    <div class="stitle">Ask the agent</div>
    <div class="card chat-wrap">
      <div class="chat-messages" id="chatMessages">
        <div class="msg msg-agent">Hi! I'm your family agent. Ask me about upcoming appointments, pending actions, or anything about the family schedule.</div>
      </div>
      <div class="chat-form">
        <input class="chat-input" id="chatInput" type="text" placeholder="Ask anything..." autocomplete="off">
        <button class="chat-send" id="chatSend">Send</button>
      </div>
    </div>
  </div>

</div>

<script>
// Refresh button
document.getElementById('refreshBtn').addEventListener('click', function(e) {{
  e.preventDefault();
  this.classList.add('loading');
  this.textContent = '↻ Checking…';
  window.location.href = '/refresh';
}});

// Chat
const input = document.getElementById('chatInput');
const send  = document.getElementById('chatSend');
const msgs  = document.getElementById('chatMessages');

function addMsg(text, cls) {{
  const d = document.createElement('div');
  d.className = 'msg ' + cls;
  d.textContent = text;
  msgs.appendChild(d);
  msgs.scrollTop = msgs.scrollHeight;
  return d;
}}

async function sendChat() {{
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  addMsg(text, 'msg-user');
  const thinking = addMsg('Thinking…', 'msg-agent msg-thinking');
  send.disabled = true;

  try {{
    const res  = await fetch('/chat', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{message: text}})}});
    const data = await res.json();
    thinking.remove();
    addMsg(data.reply, 'msg-agent');
  }} catch(e) {{
    thinking.remove();
    addMsg('Sorry, something went wrong.', 'msg-agent');
  }} finally {{
    send.disabled = false;
    input.focus();
  }}
}}

send.addEventListener('click', sendChat);
input.addEventListener('keydown', e => {{ if (e.key === 'Enter') sendChat(); }});
</script>
</body>
</html>"""

TYPE_ICONS  = {"send_email":"✉️","create_event":"📅","place_call":"📞","check_website":"🔍","order_item":"📦"}
TYPE_LABELS = {"send_email":"Send Email","create_event":"Add to Calendar","place_call":"Place Call","check_website":"Check Website","order_item":"Order Item"}


def _payload_html(raw):
    if isinstance(raw, str):
        try: p = json.loads(raw) if raw else {}
        except: return f'<div class="pv">{raw}</div>'
    else: p = raw or {}
    return "".join(f'<div class="pr"><span class="pk">{k}</span><span class="pv">{v}</span></div>' for k,v in p.items())


def _pending_card(p):
    icon = TYPE_ICONS.get(p["type"],"⚡"); label = TYPE_LABELS.get(p["type"],p["type"])
    return (f'<div class="pcard"><div class="pcard-top"><div class="type-icon ti-{p["type"]}">{icon}</div>'
            f'<div><div class="pcard-type">{label} · {p["connector"]}</div>'
            f'<div class="pcard-summary">{p["summary"]}</div></div></div>'
            f'<div class="payload">{_payload_html(p["payload"])}</div>'
            f'<div class="actions">'
            f'<a class="btn btn-ok" href="/decide?id={p["id"]}&ok=1">✓ Approve</a>'
            f'<a class="btn btn-no" href="/decide?id={p["id"]}&ok=0">✕ Deny</a>'
            f'</div></div>')


def _recent_card(r):
    icon = TYPE_ICONS.get(r["type"],"⚡"); status = r["status"]
    pill_cls = {"executed":"p-executed","denied":"p-denied","approved":"p-approved"}.get(status,"p-approved")
    label    = {"executed":"✓ Done","denied":"✕ Denied","approved":"Approved"}.get(status,status)
    result   = r.get("result") or ""
    return (f'<div class="rcard"><div class="type-icon ti-{r["type"]}" style="width:32px;height:32px;font-size:14px">{icon}</div>'
            f'<div class="rcard-body"><div class="rcard-type">{TYPE_LABELS.get(r["type"],r["type"])}</div>'
            f'<div class="rcard-summary">{r["summary"]}</div>'
            + (f'<div class="rcard-result">{result}</div>' if result else "")
            + f'</div><span class="pill {pill_cls}">{label}</span></div>')


def _dot_class(title):
    tl = title.lower()
    if "ot" in tl or "occupational" in tl: return "d-ot"
    if "pt" in tl or "physical" in tl:     return "d-pt"
    return "d-other"


def _cal_row(event):
    title = event.get("title","Event"); start = event.get("start","")
    day = mon = time_str = ""
    try:
        if "T" in start:
            dt = datetime.fromisoformat(start.replace("Z","+00:00"))
            day = dt.strftime("%-d"); mon = dt.strftime("%b"); time_str = dt.strftime("%-I:%M %p")
        else:
            dt = datetime.strptime(start,"%Y-%m-%d")
            day = dt.strftime("%-d"); mon = dt.strftime("%b"); time_str = "All day"
    except: day,mon,time_str = "—","",start
    dot = _dot_class(title)
    return (f'<div class="cal-event-row">'
            f'<div class="cal-badge"><div class="cal-bday">{day}</div><div class="cal-bmon">{mon}</div></div>'
            f'<div class="cal-dot {dot}"></div>'
            f'<div><div class="cal-title">{title}</div><div class="cal-time">{time_str}</div></div>'
            f'</div>')


def _build_calendar(cal_events):
    today = date.today()
    event_days = set()
    for e in cal_events:
        start = e.get("start","")
        try:
            dt = datetime.fromisoformat(start.replace("Z","+00:00")) if "T" in start else datetime.strptime(start,"%Y-%m-%d")
            if dt.year == today.year and dt.month == today.month: event_days.add(dt.day)
        except: pass
    cal_obj = calendar.Calendar(firstweekday=6)
    cells = ""
    for week in cal_obj.monthdayscalendar(today.year, today.month):
        for d in week:
            if d == 0: cells += '<div class="cal-cell other-month">·</div>'
            else:
                cls = "cal-cell"
                if d == today.day: cls += " today"
                if d in event_days: cls += " has-event"
                cells += f'<div class="{cls}">{d}</div>'
    return today.strftime("%B %Y"), cells


def serve(agent, port: int = 8000):
    app = Flask(__name__)

    def _get_state():
        pending    = agent.queue.list(status="pending")
        all_q      = agent.queue.list()
        past       = [r for r in all_q if r["status"] != "pending"]
        done_count = sum(1 for r in past if r["status"] == "executed")
        cal_events = []
        try: cal_events = agent.connectors["calendar"].fetch_events()
        except: pass
        return pending, all_q, past, done_count, cal_events

    def render():
        pending, all_q, past, done_count, cal_events = _get_state()
        summary = agent.reasoner.summarize(pending, cal_events, past, agent.memory)
        badge   = f'<span class="badge">{len(pending)}</span>' if pending else ""
        month_title, cal_cells = _build_calendar(cal_events)
        now_str = datetime.now().strftime("%a %b %-d, %-I:%M %p")

        cards  = "".join(_pending_card(p) for p in pending) or \
            '<div class="empty"><div class="empty-icon">✅</div>Nothing waiting on you.</div>'
        recent = "".join(_recent_card(r) for r in past[:15]) or \
            '<div class="empty"><div class="empty-icon">📭</div>No activity yet.</div>'
        cal_list = "".join(_cal_row(e) for e in cal_events[:12]) or \
            '<div style="color:var(--muted);font-size:12px;padding:6px 0">No upcoming events.</div>'

        return PAGE.format(
            now=now_str, badge=badge, summary_text=summary,
            pending_count=len(pending), done_count=done_count,
            upcoming_count=len(cal_events), total_count=len(all_q),
            cal_month_title=month_title, cal_cells=cal_cells,
            cal_list=cal_list, cards=cards, recent=recent,
        )

    @app.route("/")
    def index():
        return render()

    @app.route("/refresh")
    def refresh():
        proposals = agent.run_cycle()
        return redirect("/")

    @app.route("/decide")
    def decide():
        pid = request.args.get("id")
        ok  = request.args.get("ok") == "1"
        agent.queue.decide(pid, ok)
        if ok: agent.execute_approved()
        return redirect("/")

    @app.route("/chat", methods=["POST"])
    def chat():
        data    = request.get_json(force=True)
        message = data.get("message","")
        pending, _, _, _, cal_events = _get_state()
        reply = agent.reasoner.chat(message, pending, cal_events, agent.memory)
        return jsonify({"reply": reply})

    app.run(host="0.0.0.0", port=port)
