import io
import json

import pytest

from rover import guard, manual, ramp, settings
from rover.events import Events
from rover.loop import FakeClock
from rover.main import apply_settings


@pytest.fixture
def restore():
    saved = {n: settings.current(n) for n in settings.TUNABLES}
    yield
    settings.apply({n: v for n, v in saved.items()})


def test_apply_sets_module_constants_used_at_call_time(restore, tmp_path):
    from rover.manual import manual_command
    from rover.pad import PadState

    f = tmp_path / "settings.toml"
    f.write_text("speed_cap = 0.5\ninner_drop = 0.3\naccel_per_s = 8\n")
    out = io.StringIO()
    applied = apply_settings(Events(out, FakeClock()), str(f))
    assert applied == {"speed_cap": 0.5, "inner_drop": 0.3, "accel_per_s": 8.0}
    assert manual.SPEED_CAP == 0.5 and ramp.Ramp().accel == 8.0
    c = manual_command(PadState(lx=-1.0), 0.0)
    assert (c.left, c.right) == pytest.approx((0.35, 0.5))  # inner side at 1 - 0.3
    assert json.loads(out.getvalue())["event"] == "settings"


def test_bad_values_are_faults_and_defaults_stay(restore, tmp_path):
    f = tmp_path / "settings.toml"
    f.write_text('speed_cap = 3.0\nwheel_size = 2\nexplore_speed = "fast"\nguard_slow_m = 0.15\n')
    out = io.StringIO()
    before = (manual.SPEED_CAP, guard.SLOW_M)
    assert apply_settings(Events(out, FakeClock()), str(f)) == {}
    assert (manual.SPEED_CAP, guard.SLOW_M) == before
    faults = [json.loads(x)["error"] for x in out.getvalue().splitlines()]
    assert len(faults) == 4 and any("outside" in e for e in faults) and any("unknown" in e for e in faults)


def test_missing_file_is_defaults_and_a_broken_one_is_a_fault(tmp_path):
    out = io.StringIO()
    assert apply_settings(Events(out, FakeClock()), str(tmp_path / "none.toml")) == {}
    assert out.getvalue() == ""
    broken = tmp_path / "broken.toml"
    broken.write_text("speed_cap = = 1\n")
    apply_settings(Events(out, FakeClock()), str(broken))
    assert "cannot read" in json.loads(out.getvalue())["error"]


def test_merge_cli(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("speed_cap = 0.4\n"))
    assert settings.main(["--merge", "inner_drop=0.25"]) == 0
    assert capsys.readouterr().out == "inner_drop = 0.25\nspeed_cap = 0.4\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert settings.main(["--merge", "speed_cap=9"]) == 2
