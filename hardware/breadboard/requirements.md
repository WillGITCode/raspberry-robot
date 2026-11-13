# Breadboard holder with hold-down

Printed part: a holder with a hold-down for the breadboard ([spec](spec.md)). Status: `requested`.

## Purpose

Holds the wiring breadboard on the top deck and presses it down so jumpers do not shake loose while driving (decision 5).

## Fit

- Top deck; position TBD (`breadboard_position`), near the Pi case so the Dupont ribbon strips from the header reach it (`wiring.md`, Breadboard layout).
- The holder cradles the board; the hold-down is a bar or clips across the board's edges, leaving every hole row free that `wiring.md` uses (the rails, strips A to E, and the empty GY-521 strips F to I).
- Keep the long edges and rail ends open for jumpers; short jumpers are cut to length, so no wall is higher than the board's pins.
- Leave room for the ribbons to the header, the L298N 5 V lead, and the servo, PING and encoder leads.
- The board choice (full, half or mini) decides the size; hold the board by its edges.

## Mounting points

- Bolts to the top deck with M3 screws through the deck slots in Parameters (which slots are TBD, decision 4).
- Fixed to the part: the breadboard, by the cradle and hold-down. The hold-down fixes to the holder (screw or snap, designer's choice).

## Loads

- Carries a breadboard with its jumpers (light).
- Driving vibration and a bump; the hold-down keeps the board seated.
- Pushing wires in and pulling them out must not lift or slide the board.

## Parameters

| Parameter | Dimension | Note |
|---|---|---|
| Board length | `breadboard_length` | TBD |
| Board width | `breadboard_width` | TBD |
| Board height | `breadboard_height` | TBD, pins to top face |
| Hole pitch | `breadboard_hole_pitch` | TBD |
| Position on the deck | `breadboard_position` | TBD |
| Edge slot size | `top_deck_edge_slot_size` | TBD |
| Edge slot positions | `top_deck_edge_slot_positions` | TBD |
| Deck thickness | `plate_thickness` | 1 mm |

## Open questions

- Which breadboard (full, half or mini)? It decides the holder size.
- Which top-deck slots are free for the holder?
