# NiMH tray between the decks

Printed part: a tray that holds the NiMH pack between the decks ([spec](spec.md)). Status: `requested`.

## Purpose

Carries the Zeee 7.2 V pack low between the decks (decision 7), where it is out of the way and keeps the centre of mass low.

## Fit

- Between the decks, in the `deck_gap` of 56 mm, beside the L298N carrier (see `../l298n/requirements.md`). The pack's height (`battery_height`) plus the tray's base must be below `deck_gap`.
- Holds the pack with a tray and a strap or lip that retains it against a bump; the pack must slide out for charging.
- The EC5 lead runs from the pack to the kill switch and then the L298N motor supply terminal (`wiring.md`, Motor supply); it hangs near the rear motors today (`spec.md`). Keep the lead's exit open (`battery_lead_length`) with a bend that does not strain it.
- Keep clear of the side brackets and the motor bolts.

## Mounting points

- Fixes to the lower deck with M3 screws through lower-deck holes or slots (positions TBD, new `lower_deck_mount_positions`). Not to the top deck.
- Fixed to the part: the pack, by the tray and strap.

## Loads

- The pack is the heaviest part of the robot (weight not recorded): it must hold through driving vibration and a bump without shifting.
- Plug and unplug of the EC5 connector; lead pull.
- Removal for charging.

## Parameters

| Parameter | Dimension | Note |
|---|---|---|
| Pack length | `battery_length` | TBD |
| Pack width | `battery_width` | TBD |
| Pack height | `battery_height` | TBD |
| Lead length | `battery_lead_length` | TBD |
| Position | `battery_position` | TBD |
| Gap between the decks | `deck_gap` | 56 mm |
| Plate thickness | `plate_thickness` | 1 mm |
| Lower deck main width | `lower_deck_main_width` | 110 mm |
| Side bracket width | `side_bracket_width` | TBD |
| Side bracket position | `side_bracket_position` | TBD |
| Lower-deck mounting positions | `lower_deck_mount_positions` | New, TBD |

## Open questions

- Does the pack fit in the 56 mm gap beside the L298N carrier?
- How should the pack be retained: strap, lip or both?
