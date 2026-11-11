# L298N carrier between the decks

Printed part: a carrier that holds the L298N motor driver between the decks, beside the NiMH tray ([spec](spec.md)). Status: `requested`.

## Purpose

Moves the L298N off the top deck (decision 10) and holds it low, so the motor wires stay short and the top deck has room.

## Fit

- Between the decks, in the `deck_gap` of 56 mm, beside the NiMH tray (see `../nimh-battery/requirements.md`). Its fit under the top deck must be measured: the board with its heatsink and standoffs must be shorter than the gap (`l298n_board_height` plus the carrier's base must be below `deck_gap`).
- Holds the board raised on its mounting holes, with screws or standoffs, so the underside does not touch the deck.
- Keep the screw terminals open and reachable: motor outputs to the four TT motors, the supply terminal from the kill switch, GND and the 5 V pin to the breadboard rail, and the six control inputs from BOARD 18, 11, 13, 15, 32 and 33 (`wiring.md`).
- Keep the heatsink free for air.
- Keep clear of the side brackets (`side_bracket_*`) and the motor bolts.
- The 5 V jumper stays reachable (`wiring.md` checklist).

## Mounting points

- Fixes to the lower deck with M3 screws through lower-deck holes or slots (positions TBD, new `lower_deck_mount_positions`), since the existing lower-deck cut-outs are motor-bolt ovals (decision 4 adapted). Not to the top deck.
- Fixed to the part: the L298N, by M3 or M2 screws (hole size TBD).

## Loads

- The L298N's weight (light); driving vibration and a bump.
- Heat from the board.
- Screw terminal wire pull and screwing: the carrier must not twist.

## Parameters

| Parameter | Dimension | Note |
|---|---|---|
| Board length | `l298n_board_length` | TBD |
| Board width | `l298n_board_width` | TBD |
| Board height | `l298n_board_height` | TBD, with heatsink |
| Hole spacing, length | `l298n_hole_spacing_length` | TBD |
| Hole spacing, width | `l298n_hole_spacing_width` | TBD |
| Hole diameter | `l298n_hole_diameter` | TBD |
| Standoff height | `l298n_standoff_height` | TBD |
| Gap between the decks | `deck_gap` | 56 mm |
| Plate thickness | `plate_thickness` | 1 mm |
| Lower deck main width | `lower_deck_main_width` | 110 mm |
| Side bracket width | `side_bracket_width` | TBD |
| Side bracket position | `side_bracket_position` | TBD |
| Lower-deck mounting positions | `lower_deck_mount_positions` | New, TBD: usable holes or slots for the carrier |

## Open questions

- Does the board with its heatsink fit in the 56 mm gap, beside the NiMH tray?
- Which lower-deck holes or slots can carry the carrier's M3 screws?
