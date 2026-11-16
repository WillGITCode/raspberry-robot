# rover

The robot's code: one 50 Hz tick loop that never blocks, on an injected clock. Motors on gpiozero, the ping on gpiod, the servo on lgpio, and a small 2D sim. Tests need no Pi.

## Layout

One tick (`rover/robot.py`, `Robot.tick`), in order:

1. **Inputs**: the drive socket (`rover/drive_input.py`: bench drives and bench modes) and the pad (`rover/pad.py`).
2. **Arbiter** (`rover/control.py`): who drives this tick, by one priority rule. Stop first (Back or a lost pad latches idle). Then people: the pad's mode, manual or one they started, such as explore. Then agents: today the bench, a bench mode or a socket drive, only while people give no command. Voice and agent control over MCP plug in here, each at its place in that order.
3. **Sensors**: the scanner (`rover/scanner.py`), with its pattern picked by the active mode.
4. **Safety chain and motors** (`rover/loop.py`): deadman (coast on a command older than 300 ms), then the obstacle guard, then the ramp. This is the only code that moves the motors.
5. **Odometry** (off until wired) and **telemetry**: events, the status page snapshot, health.

`rover/main.py` builds the parts and runs `serve()`: the timing, the systemd watchdog and the overrun check. Modes (`rover/modes.py`, `rover/explore.py`) only return drive commands. They never touch hardware, and the arbiter never does either.

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest -q
```

The tests set `GPIOZERO_PIN_FACTORY=mock` and `GPIOZERO_MOCK_PIN_CLASS=mockpwmpin` themselves. A pass proves logic only, not the robot.

## Service

`python -m rover.main` runs the tick loop at 50 Hz with the real clock. Under systemd (`pi/rover.service`, `Type=notify`) it sends `READY=1` once and `WATCHDOG=1` every tick; `WatchdogSec=1` kills a loop that hangs. `ExecStopPost=` runs `pi/rover-stop` (`rover/stop.py`), which drives every enable and direction pin low after any exit.

Events are JSON lines on stdout: `start` (with commit), `drive` (left, right, source), `mode_change`, `obstacle_limit` (state, distance, limit), `deadman_stop`, `tick_overrun`, `health`, `fault`, `stop`. The commit comes from `$ROVER_COMMIT` or `git rev-parse HEAD`.

Drive commands arrive on a Unix datagram socket (`$ROVER_DRIVE_SOCKET`, default `/run/rover/drive.sock`) as `"<left> <right>"` text, or `"mode <name> [seconds]"` to run a mode for the bench; the bench tool feeds it. A command older than 300 ms coasts the motors.

## Sensors and the obstacle guard

- `rover/ping.py`: the Parallax PING))) on BOARD 16 (GPIO 23), one pin for trigger and echo, read with gpiod 2 edge events on kernel timestamps. One tick triggers; later ticks collect the echo without waiting. The echo's start must be a rising edge 650-900 us after the trigger. On the bench it always came at 752-759 us. With the motors at full speed, noise adds many short spikes, which the kernel names "falling". The end is the first falling edge at least 100 us later. No start in that window (`lost_start`), no echo within 30 ms or a pulse out of range gives `distance=None` with an `error`, never "clear" and never a guess. It never triggers while the pin is high. `/debug/ping` on the status server serves the raw edges of the last 40 pings.
- **Motor noise:** at full speed, some pings lose their start, and some hear a farther target while the robot shakes. On the stand the guard's nearest-of-0.2 s still saw the 26 cm object in about 87% of windows. Half speed reads cleanly. The fix is hardware: 0.1 uF across each motor (`hardware/wiring.md`). Until then, don't use the full-speed boost near obstacles.
- `rover/servo.py`: the pan servo on BOARD 5 (GPIO 3), driven by lgpio `tx_servo` with microsecond pulses: `400 + angle * 100/9` us (the old code's formula), 10 to 170 degrees, ahead at 95. The old code's comments put 10 on the left. It is relaxed only when the service closes.
- `rover/scanner.py`: owns both. The servo holds actively the whole time the service runs. On the stand at full speed, vibration back-drove an unpowered servo about 90 degrees, and the guard read 3 m "clear" with an obstacle at 26 cm. Pattern `ahead` holds 95 degrees and pings at 25 Hz; `sweep` steps 10 -> 170 -> 10 by 20 degrees (about 3 s a round); `fan` steps 95, 65, 95, 125 (about 0.7 s a round) to catch walls met at a shallow angle. Each reading keeps its angle and time. A mode picks the pattern with a `scan` attribute (default `ahead`).
- `rover/guard.py`: limits forward speed (the mean of the two sides) by the nearest valid reading within 20 degrees of ahead over the last 0.2 s (the cone often sees two surfaces; the closer wins, and a failed ping never hides the valid ones before it): zero at about 24 cm or less (a limit under 0.1 snaps to zero), full from 60 cm. `obstacle_limit` is logged only while there is forward motion to limit, once a new state holds 0.15 s ("stop" at once). Turning and reverse are never limited, so the robot can back off or spin away. With no valid reading in the last 0.5 s, forward speed is capped at 0.3 (no boost), and a close reading from the last 2 s still counts. If the sensors cannot start, the service runs on with a `fault` event and the guard stays blind (capped).

## Sim runner (develop modes without the robot)

`python -m rover.simrun` runs the real loop (modes, arbiter, guard, ramp, scanner) in a simulated room, with the mode as a bench mode:

- `python -m rover.simrun`: explore in a 5 x 4 m room, live, with the status page on `http://127.0.0.1:8090/` showing a top-down view of the room, the robot and its ping rays.
- `python -m rover.simrun --headless --minutes 5 --furniture --seed 3`: as fast as possible, with 2 or 3 boxes in the room. It prints one line of metrics (closest approach, path, bumps, looks, stucks, guard stops, faults) and exits non-zero on a bump. Run a few seeds after any change to a mode, the guard or the scanner.
- `--room 3x3`, `--speed 4` (live, 4x real time) and `--max-speed` (metres per second at full command, a guess until measured).

The sim's robot is a point with one ping ray and no inertia. Results there are logic, not floor behaviour.

## Settings (tuning without a deploy)

`rover/settings.py` lists the tunables: speed cap and boost, steering `inner_drop`, deadzone, ramp, the guard's distances and blind cap, and explore's speeds and distances. Each one has a safe range. At start the service applies `/etc/rover/settings.toml` (or `$ROVER_SETTINGS`) and logs a `settings` event. A bad value is a `fault`, and that value keeps its default. On the desktop:

- `tools/bench tune --list`: every tunable with its default and range.
- `tools/bench tune`: the robot's settings file.
- `tools/bench tune inner_drop=0.35 speed_cap=0.4`: checks the values here, merges them into the file on the Pi and restarts the service (about 2 s; press Start again).
- `tools/bench tune --reset`: back to the defaults.

## Modes

One mode at a time, in `rover/modes.py`; a mode returns a drive command and never touches hardware. It reads the pad and `Sense` (the guard's reading ahead and the newest reading at each angle), and picks the scanner's pattern with its `scan` attribute.

- `idle`: no motion. The start state, and where Back or a lost pad lands (latched: only Start re-arms).
- `manual`: the pad drives (see Pad). Start switches here from any mode.
- `explore` (`rover/explore.py`): press Y (once armed). It cruises at 0.3 with the sensor fanning 30 degrees either side, veering away from a side closer than 40 cm. With something within 40 cm ahead, or within 25 cm at 30 degrees, it stops, sweeps 10-170, and spins toward the widest open gap (neighbouring angles all 70 cm or more, not one "far" reading, which may be an angled surface that sent the echo away) until ahead has stayed open for 0.3 s, then cruises on. Blocked again within 1 s of a turn, that "open" was false: it backs off before looking again. If the reading ahead (under 2.5 m) changes by less than 5 cm for 3 s while it cruises, it is pushing on something the ping can't see (or stalled): it backs off for 0.8 s, then looks. With no valid reading for 1 s it stands still. Blind for 5 s, or three failed turns or re-blocks with no 2 s of progress between them, it gives up to `idle`. Moving a stick takes manual control at once (people beat the robot); Back stops it. Its steps are logged as `explore` events and shown on the status page next to the mode. In the sim it explores rooms of 2-6 m for minutes without coming within 21 cm of a wall. It drives as source `robot`, and the obstacle guard still limits every command.

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
- `tools/bench timeline [--since 15m]` turns the journal into one row per thing the robot did, with wall-clock times: mode changes, explore steps, bench modes, guard states, deadman stops, faults, starts, stops and deploys. Runs of one drive command fold into a row; health shows only when something is off (power flags, ping errors, slow ticks), with a summary at the end. Use it right after a floor test.
- `tools/bench status` prints the service state, the last `start` event (with the deployed commit) and the last deploy record.
- `tools/bench logs [--since 2m] [--follow-for 10s]` prints the service's JSON event lines and deploy records; `--follow-for` streams for that long and stops.
- `tools/bench stop` stops `rover.service` (its `ExecStopPost` runs `rover-stop` once the pins are free), then runs `rover-stop` again for the case where the service was not running: every motor pin low either way. `rover-stop` alone fails "GPIO busy" while the service runs. The service stays stopped until the next deploy.
- `tools/bench mode <name> <seconds>` (stand only) runs a mode, such as `explore`, for the bench while the pad is idle: the service ends it at the deadline (at most 120 s) even if ssh drops, and any pad input, Back, a bench drive or `mode idle` ends it sooner. The status page shows it as `bench:<name>`, and `bench_mode` events log its start and end. On the stand the wheels can't move the robot, so explore walks through cruise, stuck, back, look and turn.
- `tools/bench drive <left> <right> <seconds>` sends the command every 100 ms (the deadman coasts after 300 ms), then `0 0`, and leaves the service running (so the pad works afterwards). It moves the wheels: only with the robot on its stand.
- `tools/bench ping-check [seconds]` runs `rover/ping.py` on the Pi on its own (not through the service) and prints distances, errors and the pin flip time. If `rover.service` already owns the ping, it prints the service's `/state` instead. No motion.
- `tools/bench servo-check` pans the servo to 95, 10, 95, 170, 95. `tools/bench scan-check` copies `rover/` to a temporary folder on the Pi and prints one full sweep per angle. Servo only, never the wheels; both fail if `rover.service` owns the servo.
- `tools/bench snap` saves a JPEG from the C920 on the desktop to `.bench/snaps/<time>.jpg` and prints the path. The device is found by name (`/dev/v4l/by-id/*C920*-index0`); it fails if the camera is not on this machine.
- `tools/bench clip <seconds>` records an MP4 to `.bench/clips/<time>.mp4` and one contact-sheet JPEG of 8 frames (4x2) beside it, and prints both paths. Read the sheet as an image.
- `tools/bench --dry-run snap|clip` prints the device glob result and the ffmpeg commands without running them.
- `tools/bench check-stops` is the scripted stop check, for the robot **on its stand, wheels off the ground** (it spins the wheels at 0.5 for at most 2 s per drive). It needs the Pi over ssh and the C920 on this machine. Each step prints `pass:` or `fail:`: (1) snap; (2) drive both sides forward at 0.5 for 2 s while a 4 s clip records, then snap, and check the log has the drive 0.5 0.5 command and the stop after it; (3) drive and stop sending, and check `deadman_stop` follows the last command by at most 0.32 s (300 ms deadman plus one 20 ms tick); (4) drive and `kill -9` the service's main process (`--kill-whom=main`: a plain `systemctl kill` also kills the `ExecStopPost` stop script), and check `rover-stop` logged "motor pins low (coast)"; (5) drive, then `tools/bench stop`, and check the same line and that the service is stopped. Open the clip's contact sheet to see the wheels turning, then still. However the run ends (a failed step, an error, Ctrl-C) an exit trap runs `tools/bench stop`. `tools/bench --dry-run check-stops` prints every command and checks nothing. A pass is a result on the stand, not proof of floor behaviour.

## Pad

`rover/pad.py` reads the Xbox 360 pad with python-evdev, polled once per tick (no thread): deadzone 0.1, sticks normalised to -1..1; a missing or vanished device gives zeros and `lost=True`. `rover/manual.py` maps it to a `DriveCommand` (source `person`). The left stick drives like a car: forward/back is the throttle, and sideways arcs the robot, with the inner side slowing to 30% of the outer side at full deflection (`INNER_DROP` 0.7; it was 0.5 until Boss asked for sharper turns). Pushed sideways alone, it arcs forward at the push's speed; pulled back, only the stick's Y sets reverse speed. The right stick's X spins in place. The speed cap `SPEED_CAP` is 0.6 (0.3 for the first floor runs; Boss: the gearing is low, faster is safe), and the right trigger raises it to 1.0. Both are tunable (Settings). Wired into `main.py` through the `ModeManager`; when the active mode gives no command (idle, pad lost) the drive socket (`tools/bench drive`) drives, and Back clears it.
