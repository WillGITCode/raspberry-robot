# Pi 4 case mount

Printed part: a mount for the Pi 4 in its finned case ([spec](spec.md)). Status: `requested`.

## Purpose

Fixes the Pi 4 case to the top deck, rear right, so it can be unbolted and swapped alone. Replaces today's unrecorded fixing.

## Fit

- Top deck, rear right, case USB-C, micro-HDMI and audio side facing rearward, USB and Ethernet end facing right (`spec.md`).
- Holds the case on its base (the case, not the bare board), with the screws or a clip set by the case, which is not yet known.
- Keep the rear face clear for the USB-C and micro-HDMI plugs and the right end clear for USB and Ethernet cables. The USB 3 cable to the SSD (`wiring.md`, SSD supply) leaves from the right end.
- Keep the fins free for airflow: no wall over the fins.
- Leave room for the Dupont ribbon strips from the 40-pin header to the breadboard (`wiring.md`, Breadboard layout). The side of the case that the header faces is TBD.

## Mounting points

- Bolts to the top deck with M3 screws through the deck slots listed in Parameters (which slots are TBD, decision 4).
- Fixed to the part: the Pi case, by the means in Open questions.

## Loads

- Carries the case and Pi (light), plus driving vibration and a bump.
- Plugging and unplugging USB, Ethernet and HDMI pulls on the case: it must not shift or crack.
- Cable pull from the SSD and C920 USB cables.

## Parameters

| Parameter | Dimension | Note |
|---|---|---|
| Case length | `pi4_case_length` | TBD |
| Case width | `pi4_case_width` | TBD |
| Case height | `pi4_case_height` | TBD; includes the fins |
| Board length | `pi4_board_length` | 85 mm, for the board inside the case |
| Board width | `pi4_board_width` | 56 mm |
| Board hole spacing, length | `pi4_hole_spacing_length` | 58 mm, if the board is fixed directly |
| Board hole spacing, width | `pi4_hole_spacing_width` | 49 mm |
| Board hole edge offset | `pi4_hole_edge_offset` | 3.5 mm |
| Board hole diameter | `pi4_hole_diameter` | TBD |
| Tallest component | `pi4_tallest_component_height` | 16 mm, USB and Ethernet connectors |
| Position from rear | `pi4_case_position_from_rear` | TBD |
| Position from right | `pi4_case_position_from_right` | TBD |
| Edge slot size | `top_deck_edge_slot_size` | TBD, for the slots the mount uses |
| Edge slot positions | `top_deck_edge_slot_positions` | TBD |
| Deck thickness | `plate_thickness` | 1 mm |

## Open questions

- How is the case fixed today, and should the mount hold the case by its base holes, a clip or a tray?
- Which top-deck slots lie under the case's rear-right position?
