"""Orchestrator: watchers -> reasoner -> planner -> approval queue -> execute.

The execute step ONLY runs actions that have been approved. In the prototype,
execution of outbound/paid actions is gated behind the human approval queue.
"""
import json

from agent.approvals import ApprovalQueue
from agent.memory import Memory
from agent.llm import Reasoner
from agent.connectors.gmail import GmailConnector
from agent.connectors.calendar import CalendarConnector
from agent.connectors.web_monitor import WebMonitor


class Agent:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.memory = Memory(cfg.get("family", {}))
        self.reasoner = Reasoner(cfg)
        self.queue = ApprovalQueue(
            auto_approve_types=cfg.get("approvals", {}).get("auto_approve_types", [])
        )
        # Connectors keyed by name; planner routes approved actions to them.
        self.connectors = {
            "gmail": GmailConnector(cfg),
            "calendar": CalendarConnector(cfg),
            "web_monitor": WebMonitor(cfg),
        }

    # 1) WATCH ----------------------------------------------------------------
    def gather_events(self) -> list:
        if self.cfg.get("mode") == "demo":
            return [{"source": "demo", "text": "Karate school: please confirm Digby for this week."}]
        events = []
        events += self.connectors["gmail"].fetch_events()
        events += self.connectors["calendar"].fetch_events()
        events += self.connectors["web_monitor"].fetch_events()
        return events

    # 2-3) REASON + PLAN ------------------------------------------------------
    def run_cycle(self) -> list:
        events = self.gather_events()
        for e in events:
            self.memory.remember_event(e.get("source", "?"), e.get("text", ""))

        actions = self.reasoner.propose_actions(events, self.memory)

        proposed = []
        for a in actions:
            row = self.queue.propose(a)
            proposed.append(row)

        # Execute anything already approved (e.g. auto-approved read actions).
        self.execute_approved()
        return proposed

    # 4) EXECUTE (approved only) ---------------------------------------------
    def execute_approved(self) -> None:
        for row in self.queue.list(status="approved"):
            connector = self.connectors.get(row.get("connector"))
            if connector is None:
                self.queue.mark_executed(row["id"], "no connector (logged only)")
                continue
            payload = row.get("payload", {})
            if isinstance(payload, str):
                payload = json.loads(payload) if payload else {}
            result = connector.execute(row["type"], payload)
            self.queue.mark_executed(row["id"], result)
