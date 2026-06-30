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
            "Key obligations to watch for:\n"
            "- Digby has PT (physical therapy) and OT (occupational therapy) appointments at "
            "Kids Care Pediatric PT & OT Services in Latham NY (711 Troy-Schenectady Rd, Suite 214). "
            "Phone: (518) 786-1665. Appointments must be rebooked every 2-3 months as they "
            "don't schedule further out. When the last known appointment is within 6 weeks, "
            "propose a place_call action to schedule the next block.\n"
            "- When an email contains an appointment schedule, propose create_event actions "
            "for each appointment.\n\n"
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
