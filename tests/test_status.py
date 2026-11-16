import json
import time
import urllib.request

from rover.health import Health, throttle_flags
from rover.status import StatusServer


class Log:
    def __init__(self):
        self.items = []

    def emit(self, event, **f):
        self.items.append((event, f))


def get(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=2) as r:
        return r.status, r.headers.get("Content-Type"), r.read()


def test_state_page_and_events():
    srv = StatusServer(host="127.0.0.1", port=0)
    try:
        srv.publish({"mode": "manual", "guard": {"state": "clear"}})
        code, ctype, body = get(srv.port, "/state")
        assert code == 200 and ctype == "application/json"
        assert json.loads(body) == {"mode": "manual", "guard": {"state": "clear"}}
        code, ctype, body = get(srv.port, "/")
        assert code == 200 and b"EventSource" in body
        with urllib.request.urlopen(f"http://127.0.0.1:{srv.port}/events", timeout=2) as r:
            assert r.headers.get("Content-Type") == "text/event-stream"
            line = r.readline()
            assert line.startswith(b"data: ") and json.loads(line[6:])["mode"] == "manual"
    finally:
        srv.close()


def test_publish_never_waits_for_readers():
    srv = StatusServer(host="127.0.0.1", port=0)
    try:
        t0 = time.perf_counter()
        for i in range(10_000):
            srv.publish({"i": i})
        assert time.perf_counter() - t0 < 0.05
    finally:
        srv.close()


def test_health_event_every_period(tmp_path):
    temp = tmp_path / "temp"
    temp.write_text("48250\n")

    class Throttle:
        value = 0x50005

    log = Log()
    h = Health(log, Throttle(), temp_path=str(temp), every=5.0, extras=[lambda: {"pings": 7}])
    for i in range(300):  # 6 s at 50 Hz
        h.tick_done(0.001 if i % 100 else 0.015)
        h.maybe_emit(i * 0.02)
    assert len(log.items) == 1
    event, f = log.items[0]
    assert event == "health" and f["cpu_temp"] == 48.25 and f["throttled"] == "0x50005"
    assert f["throttle_flags"] == ["under_voltage", "throttled", "under_voltage_seen", "throttled_seen"]
    assert f["tick_ms_max"] == 15.0 and f["tick_ms_p50"] == 1.0 and f["pings"] == 7


def test_throttle_flags_none_and_zero():
    assert throttle_flags(None) == [] and throttle_flags(0) == []
