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
