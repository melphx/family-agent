"""One-tap approval page for your phone.

Lists pending proposed actions with Approve / Deny buttons. Approving flips the
row to 'approved' and immediately runs the agent's execute step (which only acts
on approved rows). In production, serve this behind HTTPS auth, or email/text the
approve links to yourself.
"""
from flask import Flask, request, redirect

PAGE = """
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Family Agent — Approvals</title>
<style>
 body{{font-family:system-ui,sans-serif;max-width:640px;margin:24px auto;padding:0 16px;color:#1a1a1a}}
 h1{{font-size:20px}} .card{{border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0}}
 .t{{font-size:12px;color:#666;text-transform:uppercase;letter-spacing:.04em}}
 .s{{font-size:16px;margin:6px 0 12px}} .pl{{font-size:13px;color:#444;background:#f6f6f6;border-radius:8px;padding:8px;white-space:pre-wrap}}
 a.btn{{display:inline-block;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:600;margin-right:8px}}
 .ok{{background:#127a3d;color:#fff}} .no{{background:#eee;color:#333}}
 .empty{{color:#666}} .done{{font-size:13px;color:#127a3d}}
</style></head><body>
<h1>Pending approvals</h1>
{cards}
<hr><h1>Recent</h1>{recent}
</body></html>
"""


def serve(agent, port: int = 8000):
    app = Flask(__name__)

    def render():
        pending = agent.queue.list(status="pending")
        if pending:
            cards = "".join(
                f'<div class="card"><div class="t">{p["type"]} · {p["connector"]}</div>'
                f'<div class="s">{p["summary"]}</div>'
                f'<div class="pl">{p["payload"]}</div>'
                f'<a class="btn ok" href="/decide?id={p["id"]}&ok=1">Approve</a>'
                f'<a class="btn no" href="/decide?id={p["id"]}&ok=0">Deny</a></div>'
                for p in pending
            )
        else:
            cards = '<p class="empty">Nothing waiting on you. </p>'
        recent = "".join(
            f'<div class="card"><div class="t">{r["status"]} · {r["type"]}</div>'
            f'<div class="s">{r["summary"]}</div>'
            f'<div class="done">{r.get("result") or ""}</div></div>'
            for r in agent.queue.list() if r["status"] != "pending"
        ) or '<p class="empty">No history yet.</p>'
        return PAGE.format(cards=cards, recent=recent)

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
