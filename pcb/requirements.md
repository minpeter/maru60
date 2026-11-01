# PCB requirements and evidence ledger

| Requirement | Evidence / implementation | Status |
|---|---|---|
| GH60 envelope | Model references 285.0 × 94.6 mm profile, 19.05 mm pitch, and Rule60 frame transform | Draft key-center model; own Edge.Cuts pending |
| RP2350A | QMK fork's `handwired/onekey/rp2350` metadata uses `processor: RP2350` | Target scaffold added; no build |
| USB-C | v7.10 case notch is 12.8 mm wide; existing surveyed 6095 center is photo-scaled ≈18.0 mm GH60 X | Receptacle/board-edge design and physical fit pending |
| MX hot-swap | Required | Socket/footprint and electrical topology pending |
| WK / WKL / HHKB | Six named bottom-row width definitions in `layout_model.json` | Nominal keycap/switch-center model only |
| 6.25U / 7U | Both defined for WK, WKL, HHKB | Width checks pass; PCB/plate fit pending |
| Split/non-split Backspace and right Shift | Both site variants modeled independently | Coordinate checks pass; actual footprint/site clearance pending |
| Stepped/non-stepped Caps Lock | Both variants modeled; stepped switch is offset +0.25U | Offset is provisional; plate/keycap check pending |
| PCB-mount and plate-mount stabilizers | Both retained as requirements; current case plate is plate-mount style | Footprints and compatible plate variants pending; no clearance claim |
| VIA | QMK fork pinned in firmware manifest; `VIA_ENABLE = yes` scaffold | QMK build and VIA layout/GUI/persistence test pending |
| Per-key RGB + underglow | Both are mandatory product requirements | LED count/topology, control zones, pins and power budget pending |
| Wireless/Bluetooth | Explicitly undecided | No battery or radio committed |
| Open hardware license | Intent recorded | Exact license and provenance review pending |

## Model test result

`node pcb/feasibility/validate_layout.mjs` passes 48 **declared layout/option cases**: six explicit bottom-row definitions crossed with split/non-split Backspace, split/non-split right Shift, and stepped/non-stepped Caps. The checks confirm the named row widths/order, modeled switch-center bounds, plate↔GH60 transform round-trip, and minimum modeled same-row spacing. This does not validate 48 physical PCB combinations.

The standard WK 6.25U definition is eight positions: 1.25U Ctrl, Win, Alt; 6.25U Space; 1.25U Alt, Win, Menu/Fn, Ctrl = 15U. Other modeled totals: WK 7U 15U; WKL 6.25U 15.25U; WKL 7U 15U; HHKB 6.25U 14.25U; HHKB 7U 14U. Split spacebar is not included.

## Mechanical provenance

- Base: repository `main` `03c92914fb0acad659a554024d689673794ea5a9`.
- Case reference: open PR #1 head `1d89453825131438929ad887e2b0264f8f620cd2` (top v7.10, bottom draft v0.11).
- GH60 frame and Rule60 plate transform: existing `spec/rule60-v3.json`, `spec/boards.json`, and `spec/rule60-v3-outlines.json`.
- No PH60 or Waffling60 board geometry was copied. No socket footprint geometry is present in the source tree, so no genuine socket collision study has been performed.
