# C920 rear mast

Printed part: a mast at the rear of the robot carrying the Logitech C920 ([spec](spec.md)). Status: `requested`.

## Purpose

Lifts the C920 above the rear of the top deck, facing forward, for a higher and wider view (decision 6). The camera stays on the desktop as the bench camera while p2 needs it.

## Fit

- Top deck, rear; position `c920_position`. Facing forward.
- Height is the parameter `mast_height`, set when Boss fits it.
- Holds the camera by its own clip (`c920_clip_thickness`, `c920_clip_width`), so the mast's top is a lip of that gap, or a flat the clip grips.
- Keep the view forward free of the Pi case, the power bank and the breadboard: the mast sits behind them, and nothing taller than the camera's lens line is in front of it within the lens field.
- Leave the USB lead free to run to a Pi USB port on the case's right end or rear (`wiring.md`; the C920's cable length is not on file).
- Keep clear of the kill switch at the rear.

## Mounting points

- Bolts to the top deck with M3 screws through the deck slots in Parameters (which slots are TBD, decision 4). A wide foot, since the mast is tall.
- Fixed to the part: the C920, by its clip, or by a tripod screw if used (Open questions).

## Loads

- The camera's weight at the top of a lever arm of `mast_height`: bending at the base under driving vibration and a bump.
- The robot is top-heavy with the mast, so it must be stiff.
- Cable pull on the USB lead; plugging the camera in and out.

## Parameters

| Parameter | Dimension | Note |
|---|---|---|
| Mast height | `mast_height` | New, TBD: set when Boss fits it |
| Camera body width | `c920_body_width` | TBD |
| Camera body height | `c920_body_height` | TBD |
| Camera body depth | `c920_body_depth` | TBD |
| Clip thickness | `c920_clip_thickness` | TBD |
| Clip width | `c920_clip_width` | TBD |
| Position | `c920_position` | TBD |
| Edge slot size | `top_deck_edge_slot_size` | TBD |
| Edge slot positions | `top_deck_edge_slot_positions` | TBD |
| Deck thickness | `plate_thickness` | 1 mm |

## Open questions

- Should the mast take the clip, or a tripod screw (the C920 has a threaded socket on some versions, unconfirmed)?
- Which rear top-deck slots carry the mast's M3 screws?
