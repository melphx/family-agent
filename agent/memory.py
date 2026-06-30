"""Readable memory store: who's who, recurring obligations, and an event log.

Kept as a simple JSON file on purpose — easy to inspect, back up, and move onto the
local box. This is the 'shared memory' the agent reasons over.
"""
import os
import json
import time

MEM_PATH = os.path.join("data", "memory.json")


class Memory:
    def __init__(self, family_cfg: dict, path: str = MEM_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        if os.path.exists(path):
            with open(path) as f:
                self.data = json.load(f)
        else:
            self.data = {"family": family_cfg, "obligations": [], "log": []}
            self._save()

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def remember_event(self, source: str, summary: str):
        self.data["log"].append({"t": time.time(), "source": source, "summary": summary})
        self._save()

    def obligations(self) -> list:
        return self.data.get("obligations", [])

    def add_obligation(self, ob: dict):
        self.data["obligations"].append(ob)
        self._save()

    def is_processed(self, event_id: str) -> bool:
        return event_id in self.data.get("processed_ids", [])

    def mark_processed(self, event_id: str):
        if "processed_ids" not in self.data:
            self.data["processed_ids"] = []
        if event_id not in self.data["processed_ids"]:
            self.data["processed_ids"].append(event_id)
            # Keep only last 500 IDs to prevent unbounded growth
            self.data["processed_ids"] = self.data["processed_ids"][-500:]
            self._save()
