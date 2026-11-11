# Pan servo bracket

Printed part: a bracket that holds the pan servo by its mounting tabs ([spec](spec.md)). Status: `requested`.

## Purpose

Replaces the hot glue: holds the SM-S2309S at front centre of the top deck through its tabs, so the servo can be removed and the bracket reprinted alone (decisions 4 and 16).

## Fit

- Top deck, front centre; position `servo_position_from_front`.
- Holds the servo body at the tabs; the servo's horn sits at `servo_horn_height_above_plate` above the deck top face, with its shaft upright so the PING pans left and right.
- Keep the horn's full sweep free (`servo_sweep_angle`): nothing within the PING holder's swept circle.
- Keep the servo lead free to run to the breadboard (signal on Strip B, supply from the 5 V rail; `wiring.md`).
- Keep clear of the deck's central cut-out and diagonal front slots.

## Mounting points

- Bolts to the top deck with M3 screws through the deck slots in Parameters (which slots are TBD, decision 4).
- Fixed to the part: the servo, by screws through its tabs (size TBD).
- Another part fixes above it: the PING holder, on the servo horn (see `../ping-sensor/requirements.md`).

## Loads

- Servo weight plus the PING and its holder; servo torque reaction when it pans.
- Driving vibration and a bump to the front of the robot.
- Cable pull on the servo lead.

## Parameters

| Parameter | Dimension | Note |
|---|---|---|
| Body length | `servo_body_length` | TBD |
| Body width | `servo_body_width` | TBD |
| Body height | `servo_body_height` | TBD, excluding horn |
| Tab span | `servo_tab_span` | TBD |
| Tab hole diameter | `servo_tab_hole_diameter` | New, TBD |
| Horn height above the plate | `servo_horn_height_above_plate` | TBD |
| Position from front | `servo_position_from_front` | TBD |
| Sweep angle | `servo_sweep_angle` | New, TBD: the angle the code pans through; Boss to say |
| Cut-out length | `top_deck_cutout_length` | TBD, bracket stays clear of it |
| Cut-out offset | `top_deck_cutout_offset` | TBD |
| Diagonal slot size | `top_deck_diagonal_slot_size` | TBD |
| Diagonal slot angle | `top_deck_diagonal_slot_angle` | TBD |
| Edge slot size | `top_deck_edge_slot_size` | TBD |
| Edge slot positions | `top_deck_edge_slot_positions` | TBD |
| Deck thickness | `plate_thickness` | 1 mm |

## Open questions

- Which front-centre slots can carry the bracket's M3 screws?
- What servo tab hole size, and what pan angle does the code use?
