# rackpulse/run.py - scheduled health checks
"""
Run via:
  python run.py --once            # single check, text report
  python run.py --once --json     # machine-readable (monitoring source)
  python run.py --once --csv      # tabular output
  python run.py --interval 300    # loop every 300s

Exit codes: 0 OK, 1 WARN, 2 CRIT, 3 STALE (host unreachable).
"""

import argparse
import csv
import io
import json
import os
import sys
import time

try:
    from dotenv import load_dotenv
except ImportError:                      # CI/test envs without python-dotenv
    def load_dotenv(*args, **kwargs):
        pass

from core import evaluate

load_dotenv()


def render(result, fmt="text"):
    """Render a HealthCheckResult as text, JSON, or CSV. Pure function."""
    if fmt == "json":
        payload = {
            "host": result.host,
            "state": result.state,
            "state_code": result.state_code,
            "readings": [
                {"metric": r.metric, "value": r.value, "label": r.label}
                for r in result.readings
            ],
            "alerts": result.alerts,
        }
        return json.dumps(payload, indent=2)
    if fmt == "csv":
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["host", "state", "state_code", "metric", "value", "label"])
        for r in result.readings:
            w.writerow([result.host, result.state, result.state_code,
                        r.metric, r.value, r.label])
        return out.getvalue()
    lines = [
        f"{result.host} - {result.state} ({len(result.readings)} readings)"
    ]
    for r in result.readings:
        lines.append(f"  {r.metric:<16} {r.value:>8}  {r.label}")
    for a in result.alerts:
        lines.append(f"  [{a['severity'].upper()}] {a['label']}: "
                     f"{a['value']} (threshold {a['threshold']}, {a['direction']})")
    return "\n".join(lines)


def run_once():
    # Lazy import: esxi.py pulls pyVmomi, which is only needed for live checks.
    from esxi import health_check

    host = os.getenv("ESXI_HOST", "")
    user = os.getenv("ESXI_USER", "root")
    password = os.getenv("ESXI_PASSWORD", "")
    if not host:
        print("Set ESXI_HOST in .env (see .env.example)")
        return None

    try:
        readings = health_check(host, user, password, host)
        reachable = True
    except Exception as e:
        print(f"[rackpulse] host unreachable: {e}")
        readings, reachable = [], False
    result = evaluate(readings, host=host, reachable=reachable)
    if not result.healthy:
        from alerts import dispatch
        config = {
            "webhook_url": os.getenv("ALERT_WEBHOOK_URL", ""),
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        }
        dispatch(result, config)
    return result


def main():
    parser = argparse.ArgumentParser(description="rackpulse - legacy Dell/ESXi health monitoring")
    parser.add_argument("--once", action="store_true", help="run a single check")
    parser.add_argument("--interval", type=int, default=300,
                        help="seconds between checks (default 300)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--csv", action="store_true", help="CSV output")
    args = parser.parse_args()

    fmt = "json" if args.json else ("csv" if args.csv else "text")

    if args.once:
        result = run_once()
        if result is None:
            sys.exit(3)
        print(render(result, fmt))
        sys.exit(result.state_code)

    print(f"🔄 rackpulse monitoring every {args.interval}s (Ctrl+C to stop)")
    while True:
        try:
            result = run_once()
            if result is not None:
                print(render(result, fmt))
        except Exception as e:
            print(f"[rackpulse] check failed: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
