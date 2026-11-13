# Pad check on the stand

For Boss. Wheels off the ground, motor power on, the Xbox 360 receiver in the Pi, pad switched on.
Stand only, not floor behaviour.

Deploy, then watch the readings while you press things:

    tools/bench deploy
    tools/bench pad-check        # lists evdev devices, then 20 s of live readings and mode_change events

The Pi needs python-evdev (`sudo apt install python3-evdev` if pad-check says it is missing).

## Codes to confirm
Run `tools/bench pad-check` and move each control. Write the code you actually see next to each guess.

- Left stick: ABS_X (side), ABS_Y (forward is negative): ____
- Right stick: ABS_RX, ABS_RY: ____
- Right trigger: ABS_RZ (0..255 assumed): ____
- Back: BTN_SELECT: ____
- Start: BTN_START: ____

## Checklist
One line per step: what happened.

1. Start (press once; the log shows `mode_change idle -> manual`): ____
2. Left stick forward (both sides forward, about half speed): ____
3. Left stick back (both sides reverse): ____
4. Right stick left/right, left stick centred (spin in place): ____
5. Release the sticks (wheels coast within a tick): ____
6. Back while driving (wheels stop, `mode_change manual -> idle`; sticks do nothing until Start again): ____
7. Start again, then unplug the receiver while driving (wheels stop at once, `mode_change ... pad_lost`; plug back in and press Start to drive again): ____

Tip: `tools/bench logs --since 2m` shows the mode and drive events after each step.
