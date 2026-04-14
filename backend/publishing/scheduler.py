"""
Scheduler: runs RSS monitor and X monitor on a schedule.
Run this as a background process alongside the FastAPI server.

Usage:
    python backend/publishing/scheduler.py charubak
    
Or import and call run_scheduled() in your deployment.
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime
from pathlib import Path


def load_client_config(client_id: str, base_path: str = "voices") -> dict:
    """Loads client config (pillars, keywords, watch accounts)."""
    config_file = Path(base_path) / client_id / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)

    # Default config — reads pillars from voice document if available
    return {
        "pillars": [
            "What founders get wrong about growth marketing",
            "DeFi growth tactics that move TVL and users",
            "The real state of Web3 marketing vs the hype",
            "Building AI tools with Python and the Anthropic API",
            "How a mainnet launch actually works"
        ],
        "keywords": None,      # Uses defaults from x_monitor
        "watch_accounts": [],  # X accounts to watch
        "rss_interval_hours": 6,
        "x_interval_hours": 2,
        "auto_schedule_approved": True,
    }


def save_client_config(client_id: str, config: dict, base_path: str = "voices"):
    """Saves client config."""
    config_dir = Path(base_path) / client_id
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(config_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)


def run_rss_cycle(client_id: str, config: dict, base_path: str = "voices"):
    """Runs one RSS monitor cycle."""
    try:
        from inputs.rss_monitor import run_monitor
        run_monitor(client_id, config["pillars"], base_path=base_path)
    except Exception as e:
        print(f"[RSS] Error: {e}")


def run_x_cycle(client_id: str, config: dict, base_path: str = "voices"):
    """Runs one X monitor cycle."""
    try:
        from inputs.x_monitor import run_x_monitor
        run_x_monitor(
            client_id,
            config["pillars"],
            keywords=config.get("keywords"),
            watch_accounts=config.get("watch_accounts", []),
            base_path=base_path
        )
    except Exception as e:
        print(f"[X Monitor] Error: {e}")


def run_scheduling_cycle(client_id: str, base_path: str = "voices"):
    """Schedules any newly approved posts."""
    try:
        from publishing.buffer_publisher import schedule_all_approved
        results = schedule_all_approved(client_id, base_path=base_path)
        if results:
            print(f"[Buffer] Scheduled {len(results)} posts for {client_id}")
    except Exception as e:
        print(f"[Buffer] Error: {e}")


def run_all_clients(base_path: str = "voices"):
    """Runs monitor cycle for all configured clients."""
    voices_dir = Path(base_path)
    if not voices_dir.exists():
        return

    for client_dir in voices_dir.iterdir():
        if not client_dir.is_dir():
            continue
        client_id = client_dir.name
        if client_id == "demo":
            continue

        config = load_client_config(client_id, base_path)
        print(f"\n--- Running cycle for {client_id} ---")
        run_rss_cycle(client_id, config, base_path)
        run_x_cycle(client_id, config, base_path)
        run_scheduling_cycle(client_id, base_path)


def run_scheduled(
    client_ids: list[str] = None,
    base_path: str = "voices",
    run_once: bool = False
):
    """
    Main scheduler loop.
    client_ids: specific clients to monitor. None = all clients.
    run_once: if True, runs once and exits (useful for cron).
    """
    print(f"[Scheduler] Starting — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    last_rss = {}
    last_x = {}
    RSS_INTERVAL = 6 * 3600   # 6 hours
    X_INTERVAL = 2 * 3600     # 2 hours

    while True:
        now = time.time()

        if client_ids:
            targets = client_ids
        else:
            targets = [
                d.name for d in Path(base_path).iterdir()
                if d.is_dir() and d.name != "demo"
            ]

        for client_id in targets:
            config = load_client_config(client_id, base_path)

            # RSS check
            rss_interval = config.get("rss_interval_hours", 6) * 3600
            if now - last_rss.get(client_id, 0) >= rss_interval:
                run_rss_cycle(client_id, config, base_path)
                last_rss[client_id] = now

            # X check
            x_interval = config.get("x_interval_hours", 2) * 3600
            if now - last_x.get(client_id, 0) >= x_interval:
                run_x_cycle(client_id, config, base_path)
                last_x[client_id] = now

            # Auto-schedule approved posts
            if config.get("auto_schedule_approved"):
                run_scheduling_cycle(client_id, base_path)

        if run_once:
            print("[Scheduler] Run complete (run_once mode)")
            break

        sleep_minutes = 30
        print(f"[Scheduler] Next check in {sleep_minutes} minutes...")
        time.sleep(sleep_minutes * 60)


if __name__ == "__main__":
    client_id = sys.argv[1] if len(sys.argv) > 1 else None
    run_once = "--once" in sys.argv

    clients = [client_id] if client_id else None
    run_scheduled(clients, run_once=run_once)
