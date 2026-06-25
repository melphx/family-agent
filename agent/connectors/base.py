"""Connector interface. Each connector both senses (fetch_events) and acts
(execute) — but acting only ever happens for actions the queue marked approved.
"""
from abc import ABC, abstractmethod


class Connector(ABC):
    name = "base"

    def __init__(self, cfg: dict):
        self.cfg = cfg

    def fetch_events(self) -> list:
        """Return a list of normalized event dicts: {source, text, ...}."""
        return []

    @abstractmethod
    def execute(self, action_type: str, payload: dict) -> str:
        """Perform an APPROVED action. Return a short result string for the log."""
        raise NotImplementedError
