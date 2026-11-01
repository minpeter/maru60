# PCB requirements and evidence ledger

| Requirement | Evidence / implementation | Status |
|---|---|---|
| GH60 envelope | Model references 285.0 × 94.6 mm profile and 19.05 mm pitch | Draft key-center model; own Edge.Cuts pending |
| RP2350A | QMK fork's `handwired/onekey/rp2350` metadata uses `processor: RP2350` | Target scaffold added; no build |
| USB-C | v7.10 case notch is 12.8 mm wide; existing surveyed 6095 center is photo-scaled ≈18.0 mm GH60 X | Receptacle/board-edge design and physical fit pending |
| MX hot-swap | Required | Socket/footprint and electrical topology pending |
| WK / WKL / HHKB | `layout_model.json` enumerates each | Nominal switch/keycap envelopes only |
| 6.25U / 7U | Model enumerates both for each layout | Envelope checks pass; plate check pending |
| Split/non-split Backspace and right Shift | Model enumerates both choices | Envelope checks pass; actual switch/socket sites pending |
| Stepped/non-stepped Caps Lock | Model enumerates both choices | Offset is provisional; plate/keycap check pending |
| PCB-mount and plate-mount stabilizers | Both retained as requirements; current case plate is plate-mount style | Footprints and compatible plate variants pending; no clearance claim |
| VIA | QMK fork pinned in firmware manifest; `VIA_ENABLE = yes` scaffold | QMK build and VIA layout/GUI/persistence test pending |
| Per-key RGB + underglow | Both are mandatory product requirements | LED count/topology, separate control zones, pins and power budget pending |
| Wireless/Bluetooth | Explicitly undecided | No battery or radio committed |
| Open hardware license | Intent recorded | Exact license and provenance review pending |

## Model test result

`node pcb/feasibility/validate_layout.mjs` checked 96 combinations. It confirms only: key switch centers are inside the nominal board envelope, the plate↔GH60 transform round-trips, adjacent switch centers in each modeled row are at least 0.5U apart, and modeled row width stays within 15.05U.

## Mechanical provenance

- Base: repository `main` `03c92914fb0acad659a554024d689673794ea5a9`.
- Case reference: open PR #1 head `1d89453825131438929ad887e2b0264f8f620cd2` (top v7.10, bottom draft v0.11).
- GH60 frame and Rule60 plate transform: existing `spec/rule60-v3.json`, `spec/boards.json`, and `spec/rule60-v3-outlines.json`.
- No PH60 or Waffling60 board geometry was copied. No socket footprint geometry is present in the source tree, so no genuine socket collision study has been performed.
