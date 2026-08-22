# rackpulse/alerts.py — alert dispatch (console / webhook / telegram)
"""
Community roadmap #1: threshold alerts to Telegram/email when a legacy
PowerEdge crosses health thresholds.
"""

import requests


def send_console(result, message):
    print(f"[{result.worst_severity.upper()}] {message}")


def send_webhook(url, payload, timeout=5):
    try:
        requests.post(url, json=payload, timeout=timeout)
    except Exception as e:
        print(f"[alerts] webhook failed: {e}")


def send_telegram(bot_token, chat_id, message, timeout=5):
    try:
        if not bot_token or not chat_id:
            print("[alerts] telegram not configured (bot_token/chat_id missing)")
            return
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": f"🚨 rackpulse: {message}"}, timeout=timeout)
    except Exception as e:
        print(f"[alerts] telegram failed: {e}")


def dispatch(result, config=None):
    """Send alerts for a HealthCheckResult via all enabled channels."""
    config = config or {}
    if result.healthy:
        return
    for alert in result.alerts:
        msg = (f"{alert['label']} on {alert['host']}: {alert['value']} "
               f"({alert['direction']} threshold {alert['threshold']}) — {alert['severity']}")
        send_console(result, msg)
        send_webhook(config.get("webhook_url", ""), {"text": msg})
        send_telegram(config.get("bot_token", ""), config.get("chat_id", ""), msg)
