# tests/test_core.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import HealthReading, Threshold, evaluate, DEFAULT_THRESHOLDS


def test_healthy_no_alerts():
    readings = [
        HealthReading("cpu_temp", 50, "CPU Temperature"),
        HealthReading("memory_usage", 60, "Memory Usage"),
        HealthReading("raid_status", 1.0, "RAID Array Status"),
        HealthReading("psu", 1.0, "PSU Status"),
    ]
    result = evaluate(readings, host="r720")
    assert result.healthy
    assert result.worst_severity == "info"


def test_cpu_temp_warning_and_critical():
    readings = [HealthReading("cpu_temp", 80, "CPU Temperature")]
    result = evaluate(readings)
    assert not result.healthy
    assert len(result.alerts) == 1
    assert result.alerts[0]["severity"] == "warning"


def test_cpu_temp_critical_tier():
    readings = [HealthReading("cpu_temp", 95, "CPU Temperature")]
    result = evaluate(readings)
    assert result.worst_severity == "critical"


def test_raid_failure_detected():
    readings = [HealthReading("raid_status", 0.0, "RAID Array Status")]
    result = evaluate(readings)
    assert result.alerts[0]["severity"] == "critical"
    assert result.alerts[0]["direction"] == "below"


def test_custom_thresholds():
    custom = [Threshold("cpu_temp", 60, "above", "warning", "CPU")]
    readings = [HealthReading("cpu_temp", 65, "CPU")]
    result = evaluate(readings, thresholds=custom)
    assert len(result.alerts) == 1


def test_multiple_metrics_multiple_alerts():
    readings = [
        HealthReading("cpu_temp", 95, "CPU"),   # triggers BOTH warning (75) and critical (90) tiers
        HealthReading("psu", 0.0, "PSU"),       # triggers critical
    ]
    result = evaluate(readings)
    # 3 alerts: cpu warning + cpu critical + psu critical (severity escalation is intended)
    assert len(result.alerts) == 3
    assert result.worst_severity == "critical"


def test_default_thresholds_shape():
    metrics = {t.metric for t in DEFAULT_THRESHOLDS}
    assert "cpu_temp" in metrics
    assert "raid_status" in metrics
    assert "psu" in metrics
