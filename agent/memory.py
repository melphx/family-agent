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
