# PCB requirements and evidence ledger

| Requirement | Evidence / implementation | Status |
|---|---|---|
| GH60 envelope | Model references 285.0 × 94.6 mm profile, 19.05 mm pitch, and Rule60 frame transform | Draft key-center model; own Edge.Cuts pending |
| RP2350A | QMK fork's `handwired/onekey/rp2350` metadata uses `processor: RP2350` | Target scaffold added; no build |
| USB-C | v7.10 case notch is 12.8 mm wide; existing surveyed 6095 center is photo-scaled ≈18.0 mm GH60 X | Receptacle/board-edge design and physical fit pending |
| MX hot-swap | Required | Socket/footprint and electrical topology pending |
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
- No PH60 or Waffling60 board geometry was copied. No socket footprint geometry is present in the source tree, so no genuine socket collision study has been performed.
