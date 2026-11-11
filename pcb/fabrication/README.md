# Maru60 fabrication package — DRAFT

**Status: draft, not a manufacturing release and not an assembly approval.**

This package was generated from the frozen development-prototype board:

- Board: `pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb`
- SHA256: `cb7b5b2941bc0e1c4d0a1d10c6dd694f8cf35c4f35665c342dfb747492e10a5d`
- KiCad: 9.0.2 (`maru60-kicad:9.0.2` container, `tools/run_kicad9.sh`)
- Board format: KiCad 9 (`20241229`), generator `pcbnew` 9.0
- Stack: 4 copper layers (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`), 1.6 mm, ENIG
- Nominal outline: 285.0 × 94.6 mm (Edge.Cuts). The Gerber job reports
  285.05 × 94.65 mm because the 0.05 mm edge stroke is included.
- Impedance flag: `ImpedanceControlled: true` in the Gerber job. This is a
  board flag, **not** a fab-qualified stackup or impedance coupon.

## What is included

| File | Contents |
| --- | --- |
| `BOM.csv` | 382 rows, one per non-logo footprint. Columns: Reference, Value, Footprint, Layer, DNP, Manufacturer, MPN, Supplier SKU, Notes, missing_mpn. Rows are sorted by Value then Footprint so identical parts are adjacent; each row is still one reference. |
| `CPL.csv` | 370 rows, SMD placements only. Columns: Ref, Value, Package, Mid X, Mid Y, Rotation, Layer. |
| `gerbers/` | 11 layer Gerbers (4 copper, 2 paste, 2 silkscreen, 2 mask, 1 Edge.Cuts), 1 Excellon drill file, 1 drill map, and the Gerber job file. 14 files total. |
| `maru60.d356` | IPC-D-356 netlist. |
| `maru60.step` | STEP board assembly. Many footprint 3D models are absent from the container; see `export.log`. This is board geometry, not a complete mechanical assembly. |
| `PROVENANCE.json` | Board SHA256, KiCad version, exact commands, UTC timestamp, per-file SHA256, layer count, board size, finish, impedance flag, and verification results. |
| `VERIFICATION.json` | Machine-readable check results and counts. |
| `export.log` | Captured KiCad CLI output, including missing 3D-model warnings. |

The board contains **383 footprint blocks**. `LOGO1` is a board-only silkscreen
logo and is omitted from `BOM.csv`, leaving **382 BOM rows**. The BOM is a full
per-reference inventory, not an approved assembly BOM: it includes the 10 test
points, the DNP through-hole SWD header `J2`, and the board-only stabilizer
`STAB_RS1` so the inventory is complete. `CPL.csv` contains only the 370 SMD
placements; it excludes `LOGO1`, `STAB_RS1`, `TP1`–`TP10` (all marked
`exclude_from_pos_files`), and `J2` (through-hole, DNP).

## CPL convention

- **Mid X / Mid Y**: KiCad footprint origin in millimetres in the board
  coordinate system. No drill/place origin offset is applied.
- **Rotation**: KiCad footprint rotation in degrees counter-clockwise,
  normalised to 0–360. **No JLCPCB part-specific rotation correction is
  applied.** Verify each rotation against the JLC library; bottom-side parts
  may need mirroring or a per-part correction.
- **Layer**: `Top` for `F.Cu`, `Bottom` for `B.Cu`.
- **Package**: KiCad footprint name without the library prefix.
- Coordinates are written with 4 decimal places; rotation with 2.

## What is NOT included / not approved

- **No assembly approval.** There is no approved AVL, supplier quote, assembly
  drawing, or assembly-house DFM review. `BOM.csv` and `CPL.csv` are draft
  inventories only.
- **No license.** The PCB hardware license has not been selected. The
  repository root license is not asserted as the PCB license. Third-party
  footprint licenses (for example the MIT-licensed `MX_V2` footprints) retain
  their own notices and must be preserved.
- **No USB ID.** No USB-IF VID/PID allocation, USB compliance, or USB
  SI/EMI qualification is claimed.
- **No DRC/ERC replay in this package.** The source checkpoint reports zero
  opens and zero warnings, but this export does not re-run DRC, ERC, or cold
  refill.
- **No impedance qualification.** The `ImpedanceControlled` flag is not a
  measured or fab-approved stackup.
- **No complete 3D assembly.** STEP export logs missing models for many
  footprints; do not use it as a mechanical fit authority.
- **No firmware, case, plate, or hardware qualification.**

## Order checklist

1. Confirm the board SHA256 and KiCad version in `PROVENANCE.json`.
2. Review `BOM.csv`; fill MPNs and supplier SKUs, and decide which test
   points, DNP, and mechanical rows to order.
3. Review `CPL.csv` rotations against the JLCPCB library; confirm bottom-side
   corrections and package names.
4. Upload `gerbers/` as a **4-layer, 1.6 mm, ENIG** board. Confirm the
   285.05 × 94.65 mm job outline and the impedance requirement with the fab.
5. Confirm the USB-C receptacle `J1`, fuse `F1`, and `C137` effective
   capacitance before assembly.
6. Do not release assembly until the BOM/CPL are approved and DRC/DFM has
   been reviewed.

## Known gaps before ordering

- **Missing MPNs:** 374 of 382 BOM rows have no MPN (`missing_mpn=yes`).
  Only 8 rows carry a manufacturer/MPN. Supplier SKU is blank for all rows.
- **Candidate parts:**
  - `J1` — USB4105-GF-A (candidate, not approved).
  - `F1` — SF-1206F100-2 (candidate, not approved).
  - `C137` — 4.7 µF 50 V, effective capacitance TBD (not approved).
- **Other open items:** `U1` RP2350A requires A4 production silicon and the
  documented topmark/CHIP_ID check. `L1`, `C102`, `C103`, and `C199` are
  upstream reference candidates, not procurement-approved. `C140`/`C141`
  (22 µF 10 V, effective ≥12 µF TBD), `C125` (1 µF 50 V, effective TBD), and
  `C274`/`C275` (100 nF 10 V X7R candidate) remain open.
- **Mechanical/assembly:** the STEP is incomplete; the board has not been
  through a fab DFM review; the USB-C, fuse, and effective-capacitance choices
  are not frozen.
- **Legal/compliance:** no PCB license, no USB ID, no regulatory or safety
  approval.

## Reproduction

From the repository root, with the project virtualenv (not `uv`):

```sh
.venv/bin/python pcb/tools/export_fabrication.py
```

The script parses the `.kicad_pcb` directly (no `pcbnew` module), writes
`BOM.csv` and `CPL.csv`, runs the KiCad 9 CLI through `tools/run_kicad9.sh`,
and writes `PROVENANCE.json` and `VERIFICATION.json`. It refuses to write
outside `pcb/fabrication/` and never modifies the frozen board.
