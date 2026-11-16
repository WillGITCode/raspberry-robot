# Raspberry Pi robot

A small 4WD robot on a Raspberry Pi 4: an L298N motor driver, an Xbox 360 pad, a Parallax PING))) on a pan servo, and more parts waiting in `hardware/`. Built for fun and learning.

| Path | What |
|---|---|
| `rover/` | The robot's code: one non-blocking 50 Hz tick loop, modes, safety filters, drivers. See [rover/README.md](rover/README.md). |
| `tests/` | Fast tests on gpiozero's mock pins; no Pi needed. |
| `tools/bench` | Deploy to the bench Pi, read its logs, drive it on the stand, bench camera. |
| `pi/` | The Pi side: setup script, deploy hook, systemd unit, stop script. |
| `docs/` | Checklists for runs on the robot. |
| `hardware/` | Measured specs and requirements for each part, and the wiring record. |
| `legacy/` | The earlier code generations, kept for reference. |

## Tests

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest -q
```

A pass proves logic only, not the robot.
