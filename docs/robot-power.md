# Robot Pi power: Boss's checklist

Decision 8 (pad driving): on the robot the Pi runs from the Aukey power bank and boots from an SD card, with no SSD fitted. The bank ran the Pi alone for hours; the SSD was what it could not carry (`hardware/wiring.md`, power paths). The NiMH pack feeds only the motors and the L298N's 5 V output.

This slice stays open until Boss reports below. Nothing here has been run on the robot.

The bench Pi already boots from SD on Wi-Fi (`docs/bench-setup.md`, root `/dev/mmcblk0p2`). If you move that same SD card to the robot Pi, steps 1 and 4 are already done: skip them and keep the alias `rover-bench`. Use a second card only if the bench Pi must keep its own.

## Steps

Boss's result goes on the line after each step.

- [ ] 1. Prepare the SD card with Imager, the same settings as the bench: Pi OS Lite 64-bit (trixie), user `rover` with your key, NOPASSWD sudo, Wi-Fi configured for the network the robot will be on. Result:
- [ ] 2. Fit the Pi on the robot, powered from the Aukey bank only, with no SSD on the USB ports. The pad receiver goes in a USB port. Result:
- [ ] 3. Boot it and read its Wi-Fi address (router list, or `ping` the hostname). Result:
- [ ] 4. Add the host alias in the desktop's `~/.ssh/config`. `tools/bench` and `pi/provision.sh` both call the alias `rover-bench` by name, so for the robot Pi either point `rover-bench` at it (while the bench Pi is off) or ask for the scripts to take a host name. Check `ssh rover-bench true` from a plain command (not chained or piped, which runs sandboxed). Result:
- [ ] 5. From the repo root run `pi/provision.sh`. It ends with `changes: N`; a rerun prints `changes: 0`. Reboot once for the watchdog (`ssh rover-bench 'sudo systemctl reboot'`). Result:
- [ ] 6. Deploy: `tools/bench deploy`, then `tools/bench status`. Result:

## The check

Wheels off the ground, on the stand, NiMH connected, kill switch within reach.

- [ ] 7. Clear the counter: note `ssh rover-bench 'vcgencmd get_throttled'` before the run (a fresh boot should read `throttled=0x0`). Result:
- [ ] 8. Stand run at speed 1.0 for 2 minutes: `tools/bench drive 1.0 1.0 120`. Did the Pi stay up (no reboot, Wi-Fi and `tools/bench status` still answer)? Result:
- [ ] 9. Straight after, `ssh rover-bench 'vcgencmd get_throttled'`. Paste the output. `throttled=0x0` means no undervoltage; any set bit, in particular bit 0 (under-voltage now) or bit 16 (under-voltage has occurred), counts as a fail. Result:
- [ ] 10. Stall the motors for 3 s: with the wheels held or blocked, run `tools/bench drive 1.0 1.0 3`, then release. Did the Pi stay up? Result:
- [ ] 11. `ssh rover-bench 'vcgencmd get_throttled'` again. Paste the output. Result:

If the Pi resets or `get_throttled` shows undervoltage, report it as it is: the bank does not carry this load, and the plan needs a different power source (a buck from the NiMH, a stronger bank, or the PD trigger on hand).
