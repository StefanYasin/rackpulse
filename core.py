# rackpulse/core.py — threshold engine + health evaluation (pure, testable)
"""
Threshold evaluation for rackpulse. Pure logic, no ESXi dependency —
this is the part that's unit-testable without hardware.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class HealthReading:
    """One health metric reading from a host."""
    metric: str          # e.g. "cpu_temp", "raid_status", "psu"
    value: float         # numeric value (0-100 for %, 0/1 for status)
    label: str = ""      # human label, e.g. "CPU Temp", "PSU 0"


@dataclass
class Threshold:
    """A threshold rule. value is the boundary; 'direction' says which side is bad."""
    metric: str
    value: float
    direction: str = "above"   # "above" = bad when value > threshold; "below" = bad when <
    severity: str = "warning"  # warning | critical
    label: str = ""


@dataclass
class HealthCheckResult:
    """Result of evaluating readings against thresholds."""
    host: str = ""
    readings: List[HealthReading] = field(default_factory=list)
    alerts: List[Dict] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return len(self.alerts) == 0

    @property
    def worst_severity(self) -> str:
        ranks = {"info": 0, "warning": 1, "critical": 2}
        return max((a["severity"] for a in self.alerts), key=lambda s: ranks.get(s, 0), default="info")


DEFAULT_THRESHOLDS = [
    Threshold("cpu_temp", 75, "above", "warning", "CPU Temperature"),
    Threshold("cpu_temp", 90, "above", "critical", "CPU Temperature"),
    Threshold("raid_status", 0.5, "below", "critical", "RAID Array Status"),
    Threshold("psu", 0.5, "below", "critical", "PSU Status"),
    Threshold("memory_usage", 95, "above", "warning", "Memory Usage"),
    Threshold("disk_usage", 90, "above", "warning", "Disk Usage"),
]


def evaluate(readings: List[HealthReading], thresholds: Optional[List[Threshold]] = None,
             host: str = "") -> HealthCheckResult:
    """Evaluate readings against thresholds. Pure function — unit-testable."""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    result = HealthCheckResult(host=host, readings=readings)
    for reading in readings:
        for t in thresholds:
            if t.metric != reading.metric:
                continue
            bad = reading.value > t.value if t.direction == "above" else reading.value < t.value
            if bad:
                result.alerts.append({
                    "host": host,
                    "metric": reading.metric,
                    "label": t.label or reading.label,
                    "value": reading.value,
                    "threshold": t.value,
                    "direction": t.direction,
                    "severity": t.severity,
                })
    return result
