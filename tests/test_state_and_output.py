# tests/test_state_and_output.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import HealthReading, Threshold, evaluate
from run import render


# ---------- state vocabulary ----------

def _readings(**values):
    return [HealthReading(k, v, k) for k, v in values.items()]


def test_ok_state():
    r = evaluate(_readings(cpu_temp=50, memory_usage=60))
    assert r.state == "OK"
    assert r.state_code == 0
    assert r.healthy


def test_warn_state():
    r = evaluate(_readings(cpu_temp=80))          # > 75 -> warning
    assert r.state == "WARN"
    assert r.state_code == 1
    assert not r.healthy


def test_crit_state():
    r = evaluate(_readings(cpu_temp=95))          # > 90 -> critical
    assert r.state == "CRIT"
    assert r.state_code == 2


def test_stale_state_when_unreachable():
    r = evaluate(_readings(cpu_temp=10), reachable=False)
    assert r.state == "STALE"
    assert r.state_code == 3
    assert not r.healthy                          # missing host is never healthy


def test_stale_trumps_warnings():
    # Even readings that look fine must not read healthy if the host was unreachable.
    r = evaluate([], reachable=False)
    assert r.state == "STALE"
    assert r.worst_severity == "stale"


# ---------- rendering ----------

def test_render_text():
    r = evaluate(_readings(cpu_temp=80))
    txt = render(r, "text")
    assert "WARN" in txt
    assert "cpu_temp" in txt


def test_render_json_roundtrip():
    import json
    r = evaluate(_readings(cpu_temp=95))
    payload = json.loads(render(r, "json"))
    assert payload["state"] == "CRIT"
    assert payload["state_code"] == 2
    assert any(a["severity"] == "critical" for a in payload["alerts"])


def test_render_csv_columns():
    r = evaluate(_readings(cpu_temp=50))
    csv_out = render(r, "csv")
    header = csv_out.splitlines()[0]
    assert header == "host,state,state_code,metric,value,label"
    assert "cpu_temp" in csv_out
