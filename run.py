# rackpulse/run.py — scheduled health checks
"""
Community roadmap: scheduled health checks (not one-shot). Run via:
  python run.py --once            # single check
  python run.py --interval 300    # loop every 300s
"""

import argparse
import os
import time

from dotenv import load_dotenv

from core import evaluate
from alerts import dispatch
from esxi import health_check

load_dotenv()


def run_once():
    host = os.getenv("ESXI_HOST", "")
    user = os.getenv("ESXI_USER", "root")
    password = os.getenv("ESXI_PASSWORD", "")
    if not host:
        print("Set ESXI_HOST in .env (see .env.example)")
        return

    print(f"🔍 rackpulse — checking {host}")
    readings = health_check(host, user, password, host)
    result = evaluate(readings, host=host)
    if result.healthy:
        print(f"✅ {host} healthy ({len(readings)} readings)")
    else:
        config = {
            "webhook_url": os.getenv("ALERT_WEBHOOK_URL", ""),
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        }
        dispatch(result, config)
    return result


def main():
    parser = argparse.ArgumentParser(description="rackpulse — legacy Dell/ESXi health monitoring")
    parser.add_argument("--once", action="store_true", help="run a single check")
    parser.add_argument("--interval", type=int, default=300,
                        help="seconds between checks (default 300)")
    args = parser.parse_args()

    if args.once:
        run_once()
        return

    print(f"🔄 rackpulse monitoring every {args.interval}s (Ctrl+C to stop)")
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[rackpulse] check failed: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
