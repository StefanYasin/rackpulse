<div align="center">

[![Stars](https://img.shields.io/github/stars/StefanYasin/rackpulse?style=flat)]
[![License](https://img.shields.io/github/license/StefanYasin/rackpulse?style=flat)]
[![Issues](https://img.shields.io/github/issues/StefanYasin/rackpulse?style=flat)]
[![Last commit](https://img.shields.io/github/last-commit/StefanYasin/rackpulse?style=flat)]
[![Language](https://img.shields.io/github/languages/top/StefanYasin/rackpulse?style=flat)]

</div>

# 🖥️ rackpulse

**Health monitoring + AI provisioning for legacy Dell PowerEdge servers on VMware ESXi 6.7.**

Backports modern host and hardware health monitoring onto old enterprise gear that would otherwise be left behind — with scheduled checks, threshold alerts, and an experimental AI agent that researches and provisions new services.

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-VMware%20ESXi%206.7-lightgrey)
![Hardware](https://img.shields.io/badge/tested%20on-Dell%20PowerEdge%20R720-darkblue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Why it exists

Most real-world infrastructure is **not** on the newest release. Enterprises routinely run ESXi 6.7-era hosts that modern tooling has abandoned. rackpulse keeps an eye on them:

- **Scheduled health checks** (roadmap #1) — runs every N seconds/minutes, not one-shot
- **Threshold alerts** (roadmap #1) — CPU temp, RAID status, PSU, memory, disk usage → Telegram / webhook / console
- **Severity escalation** — a metric can trip multiple tiers (e.g. CPU 75°C = warning, 90°C = critical)
- **AI provisioning agent** — experimental layer that researches, retrieves, and provisions new services

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in ESXi_HOST / ESXI_USER / ESXI_PASSWORD
python run.py --once           # single health check
python run.py --interval 300   # check every 5 minutes
```

## Architecture

| Module | Purpose |
|---|---|
| `core.py` | Threshold engine — pure, unit-tested, no hardware dependency |
| `esxi.py` | pyVmomi connector — collects host health from ESXi 6.7 |
| `alerts.py` | Dispatch to Telegram / webhook / console |
| `run.py` | CLI + scheduled loop |

## Thresholds

Default rules in `core.py` (`DEFAULT_THRESHOLDS`) — override programmatically:

| Metric | Warning | Critical | Direction |
|---|---|---|---|
| cpu_temp | 75 | 90 | above |
| raid_status | — | 0.5 | below |
| psu | — | 0.5 | below |
| memory_usage | 95 | — | above |
| disk_usage | 90 | — | above |

## Alerts

```env
ALERT_WEBHOOK_URL=        # POST JSON {text: ...}
TELEGRAM_BOT_TOKEN=       # from @BotFather
TELEGRAM_CHAT_ID=         # your chat id
```

## Tests

```bash
python -m pytest tests/ -v   # 7/7 — threshold engine, no hardware needed
```

## Notes

- Built and validated on a **Dell PowerEdge R720** running ESXi 6.7 in a homelab
- ESXi 6.7 uses legacy TLS — the connector builds a scoped permissive SSL context
- The AI provisioning agent requires an OpenAI-compatible API key (optional)

## License

MIT
