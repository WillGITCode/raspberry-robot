# Power bank holder

Printed part: a holder for the Aukey power bank ([spec](spec.md)). Status: `requested`.

## Purpose

Holds the Aukey bank on the top deck, where Boss can reach it for charging, so it feeds the Pi over USB-C (decisions 3 and 7).

## Fit

- Top deck; position TBD (`bank_position`). The bank must be reachable for charging, so no part sits over its ports, and the ports face the edge of the deck.
- Holds the bank by a cradle with a strap or lip; the bank's size is TBD.
- Leave a path for the USB-C cable to the Pi's USB-C on the rear face of the case (`bank_cable_length`), with a bend that does not strain either plug (`wiring.md`, Pi supply).
- Keep the bank's ports (USB-A, USB-C, USB-A QC) open and its on-bank button or LEDs visible.
- Keep clear of the rear mast, the breadboard and the SSD holder.

## Mounting points

- Bolts to the top deck with M3 screws through the deck slots in Parameters (which slots are TBD, decision 4).
- Fixed to the part: the bank, by the cradle and strap.

## Loads

- The heaviest top-deck part after the Pi case; it must resist driving vibration and a bump without shifting.
- Plugging and unplugging the charging cable in place.
- Cable pull on the USB-C lead to the Pi.

## Parameters

| Parameter | Dimension | Note |
|---|---|---|
| Body length | `bank_length` | TBD |
| Body width | `bank_width` | TBD |
| Body height | `bank_height` | TBD |
| Cable length | `bank_cable_length` | TBD |
| Port positions on the bank | `bank_port_positions` | New, TBD: which face carries each port and the button |
| Position on the deck | `bank_position` | TBD |
| Edge slot size | `top_deck_edge_slot_size` | TBD |
| Edge slot positions | `top_deck_edge_slot_positions` | TBD |
| Deck thickness | `plate_thickness` | 1 mm |

## Open questions

- Where on the top deck should the bank sit, and on which side should Boss charge it?
- Which top-deck slots are free for the holder?
