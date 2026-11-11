# Wiring record

Power paths, pin table, breadboard layout and Boss's wiring checklist. Documents only: **nothing is wired from this file, and nothing marked `proposed` is wired until Boss confirms it.**

## Source tags

| Tag | Meaning |
|---|---|
| `repo` | Read from the code in this repo |
| `Boss` | Boss said so |
| `proposed` | A worker proposal, not yet confirmed by Boss. Not wired. |

An unknown value is `TBD` and is on the checklist at the end. Header pin numbers are BOARD numbering (`GPIO.setmode(GPIO.BOARD)`).

## Power paths

| Path | From | To | Source | Note |
|---|---|---|---|---|
| Pi supply | Aukey power bank, USB-C | Pi 4 | Boss | Decision 3. The bank ran the Pi for hours before. Load with the SSD is unverified (checklist). |
| SSD supply | Pi 4 USB 3 port | USB SSD in its enclosure | Boss | The Pi boots from the SSD. The Pi's USB ports share a limited current (about 1.2 A, from memory, not fetched), so the SSD may draw much of it. |
| Motor supply | NiMH pack, EC5 | kill switch, then L298N motor supply terminal | Boss | The NiMH feeds only the motors and the L298N's 5 V output. |
| 5 V rail | L298N 5 V output | breadboard 5 V rail | Boss | Needs the L298N's 5 V regulator and jumper (unverified). May sag when the NiMH sags under motor load. The rail is dead while the kill switch is off. |
| Servo and PING supply | breadboard 5 V rail | pan servo, PING))) | Boss | Keeps servo spikes off the Pi and SSD supply. |
| Common ground | Pi GND, L298N GND, breadboard ground rail | one shared ground | Boss | Needed so the Pi's signals and the 5 V rail share a reference. |

The L298N's logic supply and the servo supply were not recorded anywhere before this file; the rows above are Boss's decisions, not readings of the existing wiring.

## Pin table

BOARD pins in use today come from `src/state/robot_state_machine.py:12-16`. BOARD 3 and 5 are the I2C pins (SDA1, SCL1; from memory of the Pi pinout) and stay free for the GY-521.

| BOARD pin | Use | Direction | Source | Note |
|---|---|---|---|---|
| 1 | 3.3 V supply for both encoders | power | proposed | Only if the encoder boards work at 3.3 V (checklist). |
| 3 | reserved: I2C SDA1 for the GY-521 | reserved | Boss | Keep free. |
| 5 | reserved: I2C SCL1 for the GY-521 | reserved | Boss | The servo is on this pin today (`ServoController(5)`, `repo`) and moves to BOARD 12 (below). |
| 6 | ground for the encoders and the breadboard ground rail | ground | proposed | Any Pi GND pin would do; this one is next to nothing else in use. |
| 11 | motor driver input (second in the motor list) | output | repo | `MotorController([18, 11, 13, 15], ...)` |
| 12 | pan servo signal (moved from BOARD 5) | output | proposed | BOARD 12 is GPIO 18, the Pi's hardware PWM pin. |
| 13 | motor driver input (third) | output | repo | |
| 15 | motor driver input (fourth) | output | repo | |
| 16 | PING))) signal, through the series resistor | in/out | repo | `PingSensor(16)`: triggers and reads on one pin. |
| 18 | motor driver input (first) | output | repo | |
| 29 | front-left encoder output | input | proposed | A plain GPIO (GPIO 5), no other duty. Which encoder is left or right is Boss's to confirm. |
| 31 | front-right encoder output | input | proposed | A plain GPIO (GPIO 6). |
| 32 | motor driver enable (first) | output | repo | `[32, 33]` |
| 33 | motor driver enable (second) | output | repo | |

The code does not say which of the four drive pins is which L298N input; the L298N side is not recorded here (`TBD`, read it off the jumpers).

## PING series resistor (proposed)

**Proposed value: 1 kΩ, in series on the PING signal wire, on the breadboard between the PING and BOARD 16.** Not wired until Boss confirms.

Reasoning (from memory of the Pi and PING behaviour; not fetched):
- The PING returns its echo pulse at 5 V, into a 3.3 V pin.
- A Pi pin has protection diodes to its 3.3 V rail that conduct above about 3.3 V plus a diode drop (about 0.6 V). With 1 kΩ, the worst current is about (5 − 3.9) / 1 kΩ ≈ 1.1 mA, which is well under the few mA usually quoted as safe for one pin.
- A smaller value passes more current; a much larger one slows the pin's edges and could distort the pulse timing. 1 kΩ is a common pick for this.
- The Pi's own 3.3 V trigger pulse still reaches the PING over 1 kΩ, since the PING input needs only about 2 V and draws almost nothing.
- Whether a 1 kΩ resistor is on hand is not recorded (checklist).

> **Warning: this is out of spec for the Pi.** A series resistor limits the current into the diodes but is not a level shift. The pin is still driven above its 3.3 V rating and relies on the clamp diodes. It may work for a long time or it may damage the pin. A BSS138 level shifter is the correct fix (a purchase, not made here).

## Encoder supply (proposed)

Power both front encoders from BOARD 1 (3.3 V), with BOARD 6 as ground, so their outputs are at most 3.3 V and safe for the Pi. This holds only if the encoder boards work at 3.3 V. Their board model, supply voltage and output level are not recorded (`TBD`). If they need 5 V, they take the 5 V rail and the same 1 kΩ series resistor and warning as the PING, one per output.

## Breadboard layout

The board is the printed holder's board (see `breadboard/spec.md`; which one is TBD). Jumpers are short and cut to length. The Pi header reaches the board by Dupont ribbon jumpers kept together in strips; no T-board. Nothing on the board labels the pins, so this table names each strip and what it carries.

| Strip | Carries | Source | Note |
|---|---|---|---|
| Rail 1 (+) | 5 V from the L298N 5 V output; feeds the servo and PING supply | Boss | |
| Rail 2 (−) | common ground: Pi BOARD 6, L298N GND, servo, PING, encoders | Boss | Shared with the Pi and the L298N. |
| Strip A | PING signal: PING wire, 1 kΩ resistor, ribbon to BOARD 16 | proposed | The resistor spans the strip. |
| Strip B | servo signal: servo wire to BOARD 12 | proposed | |
| Strip C | front-left encoder output to BOARD 29 | proposed | |
| Strip D | front-right encoder output to BOARD 31 | proposed | |
| Strip E | encoder 3.3 V from BOARD 1 | proposed | Only if the encoders work at 3.3 V. |
| Strips F, G | spare for the GY-521: BOARD 3 (SDA), BOARD 5 (SCL) | Boss | Kept empty. |
| Strips H, I | spare for the GY-521: 3.3 V or 5 V (module supply TBD) and ground | Boss | Kept empty. Check the GY-521 supply when it is fitted. |

Strip positions on the real board (which column numbers) are TBD until the board is chosen and measured.

## Boss's wiring checklist

Do these before any wiring.

- [ ] Confirm the proposed servo pin: BOARD 12 (moved off BOARD 5).
- [ ] Confirm the proposed encoder pins: BOARD 29 and 31, and which encoder is left or right.
- [ ] Confirm the 1 kΩ PING series resistor (or choose another value), and that one is on hand.
- [ ] Confirm BOARD 1 and BOARD 6 for the encoder supply and ground.
- [ ] Read the encoder board marking and confirm it works at 3.3 V, with a 3.3 V output.
- [ ] Check the L298N's 5 V regulator jumper is fitted.
- [ ] Measure the 5 V rail with a meter while the motors run on the stand (it may sag with the NiMH under load).
- [ ] After a load run on the power bank, run `vcgencmd get_throttled` over SSH and confirm it reports no undervoltage.
- [ ] Note which L298N input each of BOARD 18, 11, 13 and 15 goes to.
- [ ] Confirm the encoder pulse outputs read cleanly once wired (not before).
