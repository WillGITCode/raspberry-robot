# rover

The robot's code: one 50 Hz tick loop that never blocks, on an injected clock. Each tick reads the drive inputs and the pad, lets the active mode ask for motion, runs the scanner, then the chain that alone moves the motors: deadman (coast on a command older than 300 ms), obstacle guard, ramp. Motors on gpiozero; the ping on gpiod; the servo on lgpio; a small 2D sim. Tests need no Pi.

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest -q
```

The tests set `GPIOZERO_PIN_FACTORY=mock` and `GPIOZERO_MOCK_PIN_CLASS=mockpwmpin` themselves. A pass proves logic only, not the robot.

## Service

`python -m rover.main` runs the tick loop at 50 Hz with the real clock. Under systemd (`pi/rover.service`, `Type=notify`) it sends `READY=1` once and `WATCHDOG=1` every tick; `WatchdogSec=1` kills a loop that hangs. `ExecStopPost=` runs `pi/rover-stop` (`rover/stop.py`), which drives every enable and direction pin low after any exit.

Events are JSON lines on stdout: `start` (with commit), `drive` (left, right, source), `mode_change`, `obstacle_limit` (state, distance, limit), `deadman_stop`, `tick_overrun`, `health`, `fault`, `stop`. The commit comes from `$ROVER_COMMIT` or `git rev-parse HEAD`.

Drive commands arrive on a Unix datagram socket (`$ROVER_DRIVE_SOCKET`, default `/run/rover/drive.sock`) as `"<left> <right>"` text; the bench tool feeds it. A command older than 300 ms coasts the motors.

## Sensors and the obstacle guard

- `rover/ping.py`: the Parallax PING))) on BOARD 16 (GPIO 23), one pin for trigger and echo, read with gpiod 2 edge events on kernel timestamps. One tick triggers; later ticks collect the echo without waiting. No echo within 30 ms, a missed rise or a pulse out of range gives a reading with `distance=None` and an `error`, never "clear". It never triggers while the pin is high. Bench: the pin flips from trigger to input in about 150 us (max 370 us seen), well inside the sensor's 750 us hold-off.
- `rover/servo.py`: the pan servo on BOARD 5 (GPIO 3), driven by lgpio `tx_servo` with microsecond pulses: `400 + angle * 100/9` us (the old code's formula), 10 to 170 degrees, ahead at 95. The old code's comments put 10 on the left.
- `rover/scanner.py`: owns both. Pattern `ahead` holds 95 degrees and pings at 25 Hz, relaxing the servo once still; `sweep` steps 10 -> 170 -> 10 by 20 degrees (about 3 s a round). Each reading keeps its angle and time. A mode picks the pattern with a `scan` attribute (default `ahead`).
- `rover/guard.py`: limits forward speed (the mean of the two sides) by the freshest valid reading within 20 degrees of ahead: zero at 20 cm or less, full from 60 cm. Turning and reverse are never limited, so the robot can back off or spin away. With no valid reading in the last 0.5 s, forward speed is capped at 0.3 (no boost), and a close reading from the last 2 s still counts. If the sensors cannot start, the service runs on with a `fault` event and the guard stays blind (capped).

## Odometry (ready, not wired)

- `rover/encoders.py`: the two front 10-slot encoders, counted with gpiod edge events (both edges, kernel debounce 300 us): about 10.2 mm per edge on the 65 mm wheels. Single channel, so each count takes its sign from that side's motor output.
- `rover/imu.py`: the GY-521 (MPU-6050) gyro over I2C with smbus2: the yaw rate, with its bias measured while the motors coast at start.
- `rover/odometry.py`: the pose (x, y, heading, distance, speed per side), with heading from the gyro (on a 4WD skid-steer robot, wheel heading slips) and distance from the encoders. It shows on the status page as `pose`.
- Off by default: the encoder pins (BOARD 29/31) and moving the servo off the I2C pin (to BOARD 12) are proposals in `hardware/wiring.md`, waiting on Boss. Once wired, set `ROVER_ENCODERS=1` and/or `ROVER_IMU=1` for the service (a systemd drop-in) after a bench check.

## Health and the status page

- `rover/health.py`: a `health` event every 5 s with the CPU temperature, the throttle flags (`vcgencmd get_throttled`, read on a background thread; `under_voltage` means the supply sagged), tick time p50/p99/max, and ping counts and errors.
- `rover/status.py`: a read-only page on port 8080 (`$ROVER_STATUS_PORT`): `/` shows the mode, the command and motor output, the guard, a radar of the ping readings and health; `/state` is the snapshot as JSON; `/events` streams it 10 times a second. Open `http://<pi>:8080/` on the desktop or a phone. Nothing on it can move the robot.

## Bench tool

`tools/bench` works on the Pi through the ssh alias `rover-bench` (set in `~/.ssh/config`; the repo holds no host or key).

- `tools/bench deploy` runs pytest, takes `.bench/deploy.lock` (one deploy at a time), pushes `HEAD` to the Pi's bare repo (`refs/heads/main`, which the `post-receive` hook deploys), waits until `rover.service` is active on that commit, and prints it.
- `tools/bench status` prints the service state, the last `start` event (with the deployed commit) and the last deploy record.
- `tools/bench logs [--since 2m] [--follow-for 10s]` prints the service's JSON event lines and deploy records; `--follow-for` streams for that long and stops.
- `tools/bench stop` stops `rover.service` (its `ExecStopPost` runs `rover-stop` once the pins are free), then runs `rover-stop` again for the case where the service was not running: every motor pin low either way. `rover-stop` alone fails "GPIO busy" while the service runs. The service stays stopped until the next deploy.
- `tools/bench drive <left> <right> <seconds>` sends the command every 100 ms (the deadman coasts after 300 ms), then stops. It moves the wheels: only with the robot on its stand.
- `tools/bench ping-check [seconds]` runs `rover/ping.py` on the Pi on its own (not through the service) and prints distances, errors and the pin flip time. If `rover.service` already owns the ping, it prints the service's `/state` instead. No motion.
- `tools/bench servo-check` pans the servo to 95, 10, 95, 170, 95. `tools/bench scan-check` copies `rover/` to a temporary folder on the Pi and prints one full sweep per angle. Servo only, never the wheels; both fail if `rover.service` owns the servo.
- `tools/bench snap` saves a JPEG from the C920 on the desktop to `.bench/snaps/<time>.jpg` and prints the path. The device is found by name (`/dev/v4l/by-id/*C920*-index0`); it fails if the camera is not on this machine.
- `tools/bench clip <seconds>` records an MP4 to `.bench/clips/<time>.mp4` and one contact-sheet JPEG of 8 frames (4x2) beside it, and prints both paths. Read the sheet as an image.
- `tools/bench --dry-run snap|clip` prints the device glob result and the ffmpeg commands without running them.
- `tools/bench check-stops` is the scripted stop check, for the robot **on its stand, wheels off the ground** (it spins the wheels at 0.5 for at most 2 s per drive). It needs the Pi over ssh and the C920 on this machine. Each step prints `pass:` or `fail:`: (1) snap; (2) drive both sides forward at 0.5 for 2 s while a 4 s clip records, then snap, and check the log has the drive 0.5 0.5 command and the stop after it; (3) drive and stop sending, and check `deadman_stop` follows the last command by at most 0.32 s (300 ms deadman plus one 20 ms tick); (4) drive and `kill -9` the service's main process (`--kill-whom=main`: a plain `systemctl kill` also kills the `ExecStopPost` stop script), and check `rover-stop` logged "motor pins low (coast)"; (5) drive, then `tools/bench stop`, and check the same line and that the service is stopped. Open the clip's contact sheet to see the wheels turning, then still. However the run ends (a failed step, an error, Ctrl-C) an exit trap runs `tools/bench stop`. `tools/bench --dry-run check-stops` prints every command and checks nothing. A pass is a result on the stand, not proof of floor behaviour.

## Pad

`rover/pad.py` reads the Xbox 360 pad with python-evdev, polled once per tick (no thread): deadzone 0.1, sticks normalised to -1..1; a missing or vanished device gives zeros and `lost=True`. `rover/manual.py` maps it to a `DriveCommand` (source `person`). The left stick drives like a car: forward/back is the throttle, and sideways arcs the robot, with the inner side slowing to half the outer side at full deflection (`INNER_DROP`). Pushed sideways alone, it arcs forward at the push's speed; pulled back, only the stick's Y sets reverse speed. The right stick's X spins in place. The speed cap `SPEED_CAP` is 0.3, and the right trigger raises it to 1.0. Wired into `main.py` through the `ModeManager`; when the active mode gives no command (idle, pad lost) the drive socket (`tools/bench drive`) drives, and Back clears it.
