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

## Bench tool

`tools/bench` works on the Pi through the ssh alias `rover-bench` (set in `~/.ssh/config`; the repo holds no host or key).

- `tools/bench deploy` runs pytest, takes `.bench/deploy.lock` (one deploy at a time), pushes `HEAD` to the Pi's bare repo (`refs/heads/main`, which the `post-receive` hook deploys), waits until `rover.service` is active on that commit, and prints it.
- `tools/bench status` prints the service state, the last `start` event (with the deployed commit) and the last deploy record.
- `tools/bench logs [--since 2m] [--follow-for 10s]` prints the service's JSON event lines and deploy records; `--follow-for` streams for that long and stops.
- `tools/bench stop` runs `rover-stop` on the Pi: every motor pin low. While the service runs it holds the pins, so `rover-stop` fails with "GPIO busy"; then `stop` stops the service (its `ExecStopPost` does the same) and leaves it stopped until the next deploy.
- `tools/bench drive <left> <right> <seconds>` sends the command every 100 ms (the deadman coasts after 300 ms), then stops. It moves the wheels: only with the robot on its stand.
- `tools/bench snap` saves a JPEG from the C920 on the desktop to `.bench/snaps/<time>.jpg` and prints the path. The device is found by name (`/dev/v4l/by-id/*C920*-index0`); it fails if the camera is not on this machine.
- `tools/bench clip <seconds>` records an MP4 to `.bench/clips/<time>.mp4` and one contact-sheet JPEG of 8 frames (4x2) beside it, and prints both paths. Read the sheet as an image.
- `tools/bench --dry-run snap|clip` prints the device glob result and the ffmpeg commands without running them.
