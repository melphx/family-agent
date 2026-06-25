"""Google Calendar connector (stub).

Phase 1 wiring: same Google project as Gmail; enable Calendar API; add scope
calendar.events. Reading events is safe; creating/changing events is an action
and goes through the approval queue.
"""
from agent.connectors.base import Connector


class CalendarConnector(Connector):
    name = "calendar"

    def fetch_events(self) -> list:
        if not self.cfg.get("connectors", {}).get("calendar", {}).get("enabled"):
            return []
        # TODO(live): list upcoming events; return normalized dicts.
        return []

    def execute(self, action_type: str, payload: dict) -> str:
        if action_type == "create_event":
            # TODO(live): events().insert(...)
            return f"[stub] would create event '{payload.get('title')}' at {payload.get('when')}"
        return f"[calendar] unsupported action: {action_type}"
