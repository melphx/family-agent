"""LLM wrapper. Uses OpenAI when a key is present and mode is 'live'; otherwise
returns canned proposals so the whole loop is demoable with no credentials.

Model-agnostic by design: to move to a local model later (Qwen/Llama/Hermes via
Ollama), implement a sibling class with the same .propose_actions() signature and
swap it in core.py. Nothing else changes.
"""
import os
import json


class Reasoner:
    def __init__(self, cfg: dict):
        self.cfg = cfg.get("llm", {})
        self.mode = cfg.get("mode", "demo")
        self.api_key = self.cfg.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
        self._client = None
        if self.mode == "live" and self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception as e:  # pragma: no cover
                print(f"[llm] OpenAI unavailable ({e}); falling back to demo proposals.")

    def propose_actions(self, events: list, memory) -> list:
        """Return a list of proposed actions given new events + memory."""
        if self._client is None:
            return self._demo_proposals(events)
        return self._live_proposals(events, memory)

    # --- demo path: no network, deterministic --------------------------------
    def _demo_proposals(self, events: list) -> list:
        out = []
        for e in events:
            if "karate" in e.get("text", "").lower():
                out.append({
                    "type": "send_email",
                    "connector": "gmail",
                    "summary": "Draft reply to karate school confirming Digby for this week's class",
                    "payload": {
                        "to": "frontdesk@example-karate-school.com",
                        "subject": "Digby - class this week",
                        "body": "Hi! Confirming Digby for this week's class. Thanks!",
                    },
                })
                out.append({
                    "type": "create_event",
                    "connector": "calendar",
                    "summary": "Add 'Digby karate' to the family calendar (Sat 10:00am)",
                    "payload": {"title": "Digby karate", "when": "Saturday 10:00", "duration_min": 60},
                })
        return out

    # --- live path: real model, still only PROPOSES --------------------------
    def _live_proposals(self, events: list, memory) -> list:
        family = memory.data.get("family", {})
        system = (
            "You are a household operations assistant for the Wills family. "
            "You never take actions directly — you only propose them for human approval.\n\n"
            "Family context:\n"
            f"{json.dumps(family, indent=2)}\n\n"
            "What to watch for in every email:\n\n"
            "APPOINTMENTS & SCHEDULES\n"
            "- Digby has PT and OT at Kids Care Pediatric PT & OT Services, Latham NY, "
            "(518) 786-1665. Must rebook every 2-3 months. When last appointment is within "
            "6 weeks, propose a place_call to schedule more.\n"
            "- Any email with dates/times for appointments, classes, activities, school events, "
            "sports, recitals, or meetings → propose create_event for each one.\n\n"
            "BILLING & PAYMENTS\n"
            "- Invoices, bills, payment due notices, account statements, past-due reminders → "
            "summarize in a send_email or flag as a reminder. Note the amount, due date, and who it's from.\n"
            "- Payment confirmations or receipts → create_event for the record if significant.\n\n"
            "ACTION REQUESTS\n"
            "- Emails asking to confirm attendance, RSVP, sign a form, or reply → "
            "propose send_email with a draft reply using only the sender's real email address.\n"
            "- Emails asking to call or schedule → propose place_call with the number from the email.\n\n"
            "GENERAL FAMILY\n"
            "- School newsletters, permission slips, event notices → create_event or flag for review.\n"
            "- Subscription renewals, insurance notices, HOA communications → flag for review.\n"
            "- Ignore: pure marketing emails, spam, social media notifications, automated security "
            "alerts (Google sign-in notices, 2FA codes), and newsletters with no action needed.\n\n"
            "STRICT RULES — never break these:\n"
            "1. NEVER invent or guess email addresses, phone numbers, or URLs. "
            "Only use contact details that appear verbatim in the email content provided. "
            "If you cannot find a reply-to address in the email, do NOT propose send_email.\n"
            "2. For send_email, the 'to' field must be copied exactly from the sender's address "
            "in the email — do not construct or guess it.\n"
            "3. For create_event, derive all dates and times from the actual email content. "
            "Do not invent dates.\n"
            "4. If an email requires no action (security alerts, newsletters, receipts), "
            "return {\"actions\": []}.\n\n"
            "Return a JSON object with key 'actions': a list of objects with keys: "
            "type, connector, summary, payload.\n"
            "Allowed types: send_email, create_event, check_website, order_item, place_call.\n"
            "For create_event payloads include: title, start_datetime (ISO 8601), "
            "end_datetime (ISO 8601), description, location, timezone.\n"
            "For place_call payloads include: to, phone, reason, suggested_script.\n"
            "Be conservative — only propose actions when clearly warranted. "
            "Return {\"actions\": []} if nothing needs doing."
        )
        user = json.dumps({"events": events, "obligations": memory.obligations()})
        resp = self._client.chat.completions.create(
            model=self.cfg.get("model", "gpt-4o"),
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            response_format={"type": "json_object"},
        )
        try:
            data = json.loads(resp.choices[0].message.content)
            return data if isinstance(data, list) else data.get("actions", [])
        except Exception:
            return []

    def summarize(self, pending: list, cal_events: list, past: list, memory) -> str:
        """Generate a natural-language AI summary of the current family state."""
        if self._client is None:
            return "Running in demo mode — connect OpenAI for AI summaries."
        family = memory.data.get("family", {})
        state = {
            "pending_actions": [{"type": p["type"], "summary": p["summary"]} for p in pending],
            "upcoming_calendar": [{"title": e.get("title"), "start": e.get("start")} for e in cal_events[:10]],
            "recent_activity": [{"type": r["type"], "summary": r["summary"], "status": r["status"]} for r in past[:10]],
            "family": family,
        }
        system = (
            "You are a helpful family assistant for the Wills family. "
            "Given the current state of the family agent, write a warm, concise 2-3 sentence "
            "summary of what's going on today. Mention pending items needing attention, "
            "upcoming appointments, and anything noteworthy. Be specific and practical. "
            "Write in plain English as if talking to a busy parent."
        )
        try:
            resp = self._client.chat.completions.create(
                model=self.cfg.get("model", "gpt-4o"),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(state)},
                ],
                max_completion_tokens=200,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"Summary unavailable: {e}"

    def chat(self, message: str, pending: list, cal_events: list, memory) -> str:
        """Answer a question about the family's current state."""
        if self._client is None:
            return "Running in demo mode — connect OpenAI for chat."
        family = memory.data.get("family", {})
        context = {
            "pending_actions": [{"type": p["type"], "summary": p["summary"], "payload": p.get("payload")} for p in pending],
            "upcoming_calendar": [{"title": e.get("title"), "start": e.get("start")} for e in cal_events[:15]],
            "family": family,
        }
        system = (
            "You are a helpful family assistant for the Wills family. "
            "Answer questions about the family's schedule, appointments, pending actions, "
            "and anything in the provided context. Be concise and direct. "
            "If you don't know something, say so honestly."
        )
        try:
            resp = self._client.chat.completions.create(
                model=self.cfg.get("model", "gpt-4o"),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Context: {json.dumps(context)}\n\nQuestion: {message}"},
                ],
                max_completion_tokens=300,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"Sorry, I couldn't process that: {e}"
