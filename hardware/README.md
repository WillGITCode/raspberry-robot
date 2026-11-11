# Hardware specs

Measured specs of the robot's parts, one folder per component, for CAD to read. Each folder holds a `spec.md` in a fixed format: Purpose, Fit and position, Mounting points, a Measurements table (`Dimension | Value | Unit | Source | Note`) and Open questions. Text and tables only; no photos.

## Source tags

| Tag | Meaning |
|---|---|
| measured | Measured on the robot or part by Boss |
| datasheet | From the maker's datasheet, URL in Note; exact confirmed models only |
| photo estimate | Read off a photo |
| `TBD` | Not known yet; listed in `CHECKLIST.md` |

Photo estimates are never used for fit.

## Standing requirement for CAD

CAD models must be fully parametric and editable by a human: every sketch, body and model is driven by named parameters (a spreadsheet or variables), with no dead imported geometry for parts we define. The `Dimension` names in each spec are those parameters, so TBD values can be filled in later without remodelling. A published model may be referenced only for parts we don't define.

## Index

| Folder | Status | TBD count |
|---|---|---|
| [chassis](chassis/spec.md) | as built | 25 |
| [tt-motor](tt-motor/spec.md) | as built | 10 |
| [wheel](wheel/spec.md) | as built | 5 |
| [wheel-encoder](wheel-encoder/spec.md) | as built | 7 |
| [l298n](l298n/spec.md) | as built | 9 |
| [pi4-case](pi4-case/spec.md) | as built | 6 |
| [ping-sensor](ping-sensor/spec.md) | as built | 7 |
| [pan-servo](pan-servo/spec.md) | as built | 6 |
| [kill-switch](kill-switch/spec.md) | as built | 8 |
| [nimh-battery](nimh-battery/spec.md) | as built | 5 |
| [power-bank](power-bank/spec.md) | as built | 6 |
| [gy-521](gy-521/spec.md) | planned | 5 |
| [c920](c920/spec.md) | planned | 6 |
| [phone-s7](phone-s7/spec.md) | planned | 5 |
| [speaker](speaker/spec.md) | planned | 5 |
| [lidar-ld06](lidar-ld06/spec.md) | planned | 5 |
| [usb-ssd](usb-ssd/spec.md) | planned | 5 |
| [breadboard](breadboard/spec.md) | planned | 5 |

## Wiring

[wiring.md](wiring.md) records the power paths, the pin table, the breadboard layout and Boss's wiring checklist. Rows carry a source of `repo`, `Boss` or `proposed`; nothing `proposed` is wired.
