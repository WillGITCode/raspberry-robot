# Motor-control layer

`rover/drivetrain.py` (speed control), `rover/move.py` (moves), `rover/encoders.py` (spike filter).

**Commands are target speeds.** Pad, explore, bench drive and moves all give `left`/`right` as a fraction of top speed (-1..1). The loop filters them as before (deadman, obstacle guard, ramp); the drivetrain then turns each side's target into a motor duty. The guards and the stop latch come first and are untouched.

- **With encoders** (`ROVER_ENCODERS=1`): duty = target (feed-forward) + a PI correction from the side's measured speed (edges/s over 0.3 s x metres per edge). The correction is limited to `pi_max_correction`, the duty to `duty_max` (unless commanded higher), so a bad reading cannot run a wheel away.
- **Without encoders:** duty = target, with `trim` (right x(1+trim), left x(1-trim)). Default 0; about +0.025 cures the bench drift right.
- **Spike rejection:** an edge closer than `min_edge_ms` (3) to the last one on its side is dropped (kernel timestamps). The service reads the encoders once every tick, first thing.
- **Encoder fault:** a side commanded at least `fault_duty` with no edge for `fault_window_s`, or more than `max_edge_hz` edges/s, raises `encoder_fault` (event + fault): the motors coast and the pad is latched (Start re-arms, event `encoder_rearm`; with no pad, restart the service). A wheel jammed against a wall looks the same; that stop is wanted too.

**Moves** (`Mover`): `drive(speed, turn, seconds, metres)`, `distance(m)`, `turn(deg)`. Turn is counter-clockwise positive. Every move ends at `move_max_s` (10 s) or `move_max_m` (3 m), whichever comes first, with a reason (`distance`, `angle`, `time`, `distance_cap`) in the `move` event. `turn` needs a heading (gyro, or odometry with a track); without one it ends at the time cap. Bench: `tools/bench move distance 0.5`, `move turn 90`, `move drive 0.3 0.1 2`. Explore builds its commands with `rover.move.mix`.

**Calibrate on the robot** (`tools/bench tune`): `edge_m_left`, `edge_m_right` (drive 1 m, divide by the edge count), `max_speed_mps` (from the stand check), `pi_kp`, `pi_ki`. Run `tools/stand_check_drivetrain.py --yes-wheels-clear` with the wheels off the ground (service stopped; `--fake` for a dry run). All values: `python -m rover.settings --list`.

Not yet seen on the robot: the numbers above are defaults from the bench facts; the layer is tested on fake GPIO and the sim only.
