# Legacy code

The robot's first four code generations, kept for reference. Nothing here runs on the robot any more, and nothing imports it. `rover/` replaced all of it.

| Folder | What it was | Replaced by |
|---|---|---|
| `FirstTry/` | First script: Xbox pad (the `inputs` library), RPi.GPIO motors, the ping and servo tests | `rover/pad.py`, `rover/motors.py` |
| `2ndTry/` | State-machine experiments with blinking LEDs | `rover/modes.py` |
| `modules/` | Controller, motor and ping classes; `pocketFlow/` LLM experiments (Ollama on the Pi) | `rover/`; LLM work belongs on the desktop |
| `src/` | The last generation: a state machine with idle, remote control and obstacle avoidance; `ServoController(5)`, `PingSensor(16)`, `MotorController([18, 11, 13, 15], [32, 33])` | `rover/` (the pins come from here) |
| `sensorTests/` | One-off sensor, servo, keyboard, pygame and speech-to-text tests | `tools/bench` checks |

Known faults, for anyone lifting code from here (ticket 12 and research 05): blocking `while` loops and `sleep`s in the control path, a ping that returns `inf` ("clear") on any error and waits with no timeout, a pad that keeps its last stick value when it drops, and a stop that hides its own failure.
