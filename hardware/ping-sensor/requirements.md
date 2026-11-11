# PING holder on the servo horn

Printed part: a holder that fixes the PING))) to the pan servo horn ([spec](spec.md)). Status: `requested`.

## Purpose

Replaces the hot glue between the PING and the servo horn (decision 16), so the sensor pans with the servo and can be removed.

## Fit

- Sits on the servo horn at front centre, the transducers facing forward at rest.
- Holds the PING board by its board mounting hole (`ping_mount_hole_diameter`) or by a pocket around the board; both transducers stay uncovered and unshadowed across the sweep (`servo_sweep_angle`).
- Keep the three wires (ground, 5 V, signal) free to leave the back toward the breadboard, with enough slack for the sweep and no pinch against the bracket (`wiring.md`, Strip A with the 1 kΩ resistor).
- Keep the horn's screw accessible.
- Keep low enough that the sweep clears the top deck and the mast.

## Mounting points

- Fixes to the servo horn by its screw holes (hole spacing TBD, `servo_horn_hole_spacing`), and does not bolt to the deck.
- Fixed to the part: the PING, by an M3 screw (if its hole fits M3, TBD) or a pocket.

## Loads

- The PING's weight (light) swung through the sweep; the holder must be stiff and not wobble.
- Driving vibration and a bump.
- Wire pull as it pans.

## Parameters

| Parameter | Dimension | Note |
|---|---|---|
| Board length | `ping_board_length` | TBD |
| Board width | `ping_board_width` | TBD |
| Board height | `ping_board_height` | TBD, board plus transducers |
| Transducer diameter | `ping_transducer_diameter` | TBD |
| Transducer spacing | `ping_transducer_spacing` | TBD |
| Mounting hole diameter | `ping_mount_hole_diameter` | TBD |
| Offset from horn centre | `ping_glue_offset_from_horn` | TBD |
| Horn height above the plate | `servo_horn_height_above_plate` | TBD |
| Horn length | `servo_horn_length` | New, TBD |
| Horn hole spacing | `servo_horn_hole_spacing` | New, TBD |
| Sweep angle | `servo_sweep_angle` | New, TBD |

## Open questions

- Which horn (single arm, double arm or disc) is on the servo?
- Does the PING's hole take an M3 screw?
