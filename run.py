"""Entrypoint: run one agent cycle, then serve the approval page.

Demo mode needs no credentials. See README.md.
"""
import os
import yaml

from agent.core import Agent
from agent.web.approval_app import serve


def load_config(path: str = "config.yaml") -> dict:
    if not os.path.exists(path):
        path = "config.example.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def main() -> None:
    cfg = load_config()
    agent = Agent(cfg)

    print(f"[run] mode={cfg.get('mode')}  running one cycle...")
    proposals = agent.run_cycle()
    print(f"[run] cycle produced {len(proposals)} proposed action(s).")
    for p in proposals:
        print(f"       - [{p['status']}] {p['type']}: {p['summary']}")

    port = cfg.get("approvals", {}).get("web_port", 8000)
    print(f"[run] approval page -> http://localhost:{port}  (Ctrl+C to stop)")
    serve(agent, port=port)


if __name__ == "__main__":
    main()
