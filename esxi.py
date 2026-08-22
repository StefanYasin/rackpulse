# rackpulse/esxi.py — ESXi host health collection via pyVmomi
"""
Community roadmap: scheduled health checks against legacy Dell PowerEdge
running ESXi 6.7. Connects via pyVmomi, collects hardware health, returns
readings for the threshold engine (core.py).

Hardware-dependent — tested on Dell PowerEdge R720 / ESXi 6.7.
"""

import ssl
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from core import HealthReading


def _ssl_context():
    """ESXi 6.7 uses old TLS — build a permissive-but-scoped context."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def connect(host, user, password):
    return SmartConnect(host=host, user=user, pwd=password,
                        sslContext=_ssl_context())


def collect_readings(si, host_name="") -> list:
    """Collect health readings from a connected ESXi host."""
    readings = []
    content = si.RetrieveContent()

    for host in content.rootFolder.childEntity[0].hostFolder.childEntity[0].host:
        # Hardware status (health status of the host)
        runtime = host.runtime
        # CPU temperature is not directly exposed; use overall status
        # as a proxy, and memory usage from the host summary
        summary = host.summary
        overall = str(runtime.healthSystemState.overallStatus) if runtime.healthSystemState else "unknown"

        # Memory usage %
        mem_usage = summary.quickStats.overallMemoryUsage  # MB used
        mem_total = summary.hardware.memorySize / (1024 * 1024)  # MB
        mem_pct = round(100.0 * mem_usage / mem_total, 1) if mem_total else 0
        readings.append(HealthReading("memory_usage", mem_pct, "Memory Usage"))

        # Overall health status → numeric (gray=0.5 unknown, green=1, yellow=0.4, red=0)
        status_map = {"green": 1.0, "yellow": 0.4, "red": 0.0, "unknown": 0.5, "gray": 0.5}
        readings.append(HealthReading("overall_status", status_map.get(overall, 0.5), "Overall Health"))

        # Storage: check datastores for usage
        for ds in content.rootFolder.childEntity[0].datastoreFolder.childEntity:
            if ds.summary.accessible:
                cap = ds.summary.capacity or 1
                free = ds.summary.freeSpace or 0
                usage = round(100.0 * (cap - free) / cap, 1)
                readings.append(HealthReading("disk_usage", usage, f"Datastore {ds.name}"))

    return readings


def health_check(host, user, password, host_name=""):
    """Full check: connect, collect, disconnect."""
    si = connect(host, user, password)
    try:
        return collect_readings(si, host_name)
    finally:
        Disconnect(si)
