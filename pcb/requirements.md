# PCB requirements and evidence ledger

| Requirement | Evidence / implementation | Status |
|---|---|---|
| GH60 envelope | Model references 285.0 × 94.6 mm profile, 19.05 mm pitch, and Rule60 frame transform | Draft key-center model; own Edge.Cuts pending |
| RP2350A | QMK fork's `handwired/onekey/rp2350` metadata uses `processor: RP2350` | Target scaffold added; no build |
| USB-C | v7.10 case notch is 12.8 mm wide; existing surveyed 6095 center is photo-scaled ≈18.0 mm GH60 X | Receptacle/board-edge design and physical fit pending |
| MX hot-swap | ai03 MX_V2 MIT 1U/7U footprints vendored with license; copper pad geometry screened against seven bottom-row sites | Diodes, full layout, face transform, DRC and physical fit pending |
| WKL / HHKB | Two independent 7U bottom-row fixtures; blocker intervals plus union socket sites | Nominal keycap/switch-center model only |
| Spacebar size | 7U only for PCB v1 | Selected by user; earlier 6.25U option removed |
| Split/non-split Backspace and right Shift | Both site variants modeled independently | Coordinate checks pass; actual footprint/site clearance pending |
| Stepped Caps Lock | Stem-center candidate -0.25U kept distinct from keycap outline | Unvalidated; selected manufacturer footprint/keycap/plate needed |
| PCB-mount and plate-mount stabilizers | Both retained as requirements; current case plate is plate-mount style | Footprints and compatible plate variants pending; no clearance claim |
| VIA | QMK fork pinned in firmware manifest; `VIA_ENABLE = yes` scaffold | QMK build and VIA layout/GUI/persistence test pending |
| Per-key RGB + underglow | Both are mandatory product requirements | LED count/topology, control zones, pins and power budget pending |
| Wireless/Bluetooth | Explicitly undecided | No battery or radio committed |
| Open hardware license | Intent recorded | Exact license and provenance review pending |

## Model test result

`node pcb/feasibility/validate_layout.mjs` passes 8 **declared nominal layout/option cases**: WKL and HHKB QMK-fixture-anchored 7U rows crossed with split/non-split Backspace and right Shift. These are not physical PCB compatibility tests. The validator compares against separate fixtures transcribed from [QMK ANSI Tsangan 60%](https://raw.githubusercontent.com/qmk/qmk_firmware/master/layouts/default/60_ansi_tsangan/info.json) and [QMK HHKB 60%](https://raw.githubusercontent.com/qmk/qmk_firmware/master/layouts/default/60_hhkb/info.json).

WKL and HHKB are the only v1 layouts and span 15U from the same origin. Nominal segment centers are 0.75, 2, 3.25, 7.5, 11.75, 13 and 14.25U. WKL has blank 1U Win segments at 2U and 13U; HHKB has 1.5U corner blockers and five active centers at 2, 3.25, 7.5, 11.75 and 13U. Their physical union retains all seven switch sites needed across both layouts. Opposite-layout blocker/socket overlap is a clearance risk still to measure. Their fixture GH60 X centers are 13.91, 37.7225, 61.535, 142.4975, 223.46, 247.2725 and 271.085 mm; HHKB uses the interior five only.

**Decision history:** WK and 6.25U alternatives were considered earlier, then removed from v1; the user selected WKL and HHKB with 7U only. They are absent from layout data, firmware seed, validator and preview.

Stepped Caps is excluded from passing cases. The -0.25U leftward stem-center offset is a candidate; it still needs confirmation against the selected manufacturer footprint, keycap and plate. The keycap outline stays centered independently. Split spacebar is not included.

## Mechanical provenance

- Base: repository `main` `03c92914fb0acad659a554024d689673794ea5a9`.
- Case reference: open PR #1 head `1d89453825131438929ad887e2b0264f8f620cd2` (top v7.10, bottom draft v0.11).
- GH60 frame and Rule60 plate transform: existing `spec/rule60-v3.json`, `spec/boards.json`, and `spec/rule60-v3-outlines.json`.
- No PH60 or Waffling60 board geometry was copied. A narrow copper-pad footprint screening now uses geometry extracted from MIT-licensed ai03 MX_V2 files; it does not model switch body, plate, stabilizer housings, case, or transformed board side.


## Electrical and footprint progress (2026-11-01)

- Vendored ai03 MX_V2 `MX-Hotswap-1U` and `MX-Hotswap-7U` from upstream commit `0b379eebbeb66c7fd6e82e400b47958ad695614e` under its included MIT license. The project-wide PCB hardware license remains unselected.
- `node pcb/engineering/footprint-check.mjs`: PASS_GEOMETRY_ONLY. It parsed two copper pads per 1U socket, checked all seven WKL/HHKB union sites for cross-socket copper AABB intersections (0), and checked four wide 7U stabilizer NPTH drills against socket copper (positive calculated clearance). See `engineering/footprint-check-report.json` for exact results and limitations.
- This is not KiCad DRC or physical/plate/case validation. The source footprint side/orientation must be set as specified by upstream and inspected in KiCad before PCB placement.
- Bare RP2350A requires external QSPI flash and its integrated switching regulator block must follow the Raspberry Pi RP2350A Minimal reference; details and unresolved USB-C, matrix, RGB-power selections are in `engineering/electrical-architecture.md`.
- The KiCad native schematic/board are still absent because KiCad 10.0.8 and `kicad-cli` are not installed in this environment; the official installer/approval boundary is documented. Do not treat reference data or a geometry report as a completed design.
- Parent-provided cloud build: pinned emolitor QMK RP2350 `via_ci` baseline and Maru60 `via` target compiled/linked to UF2 after adding prototype USB ID metadata. This does not validate a physical PCB or VIA GUI/persistence. Build run provenance is external to the local Windows workspace.
