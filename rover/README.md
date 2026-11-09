# rover

Motor logic on gpiozero, with a safety filter (coast on a command older than 300 ms), a tick loop on an injected clock, and a small 2D sim. Tests need no Pi.

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest -q
```

The tests set `GPIOZERO_PIN_FACTORY=mock` and `GPIOZERO_MOCK_PIN_CLASS=mockpwmpin` themselves. A pass proves logic only, not the robot.

## Service

`python -m rover.main` runs the tick loop at 50 Hz with the real clock. Under systemd (`pi/rover.service`, `Type=notify`) it sends `READY=1` once and `WATCHDOG=1` every tick; `WatchdogSec=1` kills a loop that hangs. `ExecStopPost=` runs `pi/rover-stop` (`rover/stop.py`), which drives every enable and direction pin low after any exit.

Events are JSON lines on stdout: `start` (with commit), `drive` (left, right, source), `deadman_stop`, `tick_overrun`, `fault`, `stop`. The commit comes from `$ROVER_COMMIT` or `git rev-parse HEAD`.

Drive commands arrive on a Unix datagram socket (`$ROVER_DRIVE_SOCKET`, default `/run/rover/drive.sock`) as `"<left> <right>"` text; the bench tool feeds it. A command older than 300 ms coasts the motors.
