"""Web monitor (stub) — watches a page (e.g. Digby's karate schedule) for changes.

Phase 3 wiring: fetch each target URL, hash/diff the relevant content against the
last seen version, and emit an event when it changes. 'check_website' is read-only
and may be auto-approved; any signup it then prepares is a separate action that
must be approved.
"""
from agent.connectors.base import Connector


class WebMonitor(Connector):
    name = "web_monitor"

    def fetch_events(self) -> list:
        cfg = self.cfg.get("connectors", {}).get("web_monitor", {})
        if not cfg.get("enabled"):
            return []
        # TODO(live): requests.get(target['url']) -> bs4 parse -> diff vs stored hash.
        return []

    def execute(self, action_type: str, payload: dict) -> str:
        if action_type == "check_website":
            return f"[stub] would fetch+diff {payload.get('url')}"
        return f"[web_monitor] unsupported action: {action_type}"
