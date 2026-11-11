# USB SSD holder

Printed part: a holder for the USB SSD in its enclosure ([spec](spec.md)). Status: `requested`.

## Purpose

Holds the Pi's boot SSD on the top deck, near the Pi case, so it does not slide or tug on its cable.

## Fit

- Top deck, near the Pi case; position TBD (`ssd_position`).
- Holds the enclosure by a cradle with a strap or retaining lip; the enclosure's own shape decides which (model TBD).
- Keep the connector end open and clear so the USB 3 cable reaches a Pi USB 3 port on the case's right end with a bend that does not strain the plug (`wiring.md`, SSD supply). Cable length is `ssd_cable_length`.
- Do not block the case's right-end ports or the fins' airflow.
- Keep clear of the power bank holder and the breadboard ribbons.

## Mounting points

- Bolts to the top deck with M3 screws through the deck slots in Parameters (which slots are TBD, decision 4).
- Fixed to the part: the SSD enclosure, by the cradle and strap.

## Loads

- Carries one SSD enclosure (light); driving vibration and a bump.
- The SSD must stay seated: a shifting drive can drop out the boot disk.
- Cable pull when the USB 3 plug is connected or removed.

## Parameters

| Parameter | Dimension | Note |
|---|---|---|
| Enclosure length | `ssd_enclosure_length` | TBD |
| Enclosure width | `ssd_enclosure_width` | TBD |
| Enclosure height | `ssd_enclosure_height` | TBD |
| Cable length | `ssd_cable_length` | TBD |
| Connector position on the enclosure | `ssd_port_position` | New, TBD: which end and where the USB port sits |
| Position on the deck | `ssd_position` | TBD |
| Edge slot size | `top_deck_edge_slot_size` | TBD |
| Edge slot positions | `top_deck_edge_slot_positions` | TBD |
| Deck thickness | `plate_thickness` | 1 mm |

## Open questions

- Which SSD enclosure model? Boss may give it.
- Which top-deck slots are free for the holder?
