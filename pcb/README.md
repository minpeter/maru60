# Maru60 PCB — RP2350A (engineering draft)

This directory is the independent PCB workstream. It does not change or merge the housing proposal.

## Target

- GH60-class 285.0 × 94.6 mm, 1.6 mm PCB envelope (reference profile: komar007/gh60 rev C as recorded in the mechanical interface data).
- RP2350A MCU; USB-C; QMK with VIA remapping; MX hot-swap; per-key RGB and a separately addressable underglow chain.
- One PCB must provide selectable WK, WKL, and HHKB layouts. The bottom row must provide 6.25U and 7U space bars, and alternate/split Backspace, right Shift, and stepped Caps Lock positions. PCB-mount and plate-mount stabilizers require compatible, separately specified plate cutouts.
- Wireless/Bluetooth is undecided. No battery, radio, or wireless circuitry is committed.

## Mechanical reference and provenance

The work is based on repository `main` at `03c92914fb0acad659a554024d689673794ea5a9`. The case reference is the open PR #1 proposal at `1d89453825131438929ad887e2b0264f8f620cd2` (top case v7.10, bottom case draft v0.11); its plate-frame mapping and USB notch are in `spec/rule60-v3.json`, `spec/boards.json`, and `spec/rule60-v3-outlines.json`. Those files are not copied into this subtree.

The recorded transform is `X_plate = X_GH60 + 0.4525`, `Y_plate = 101.06775 - Y_GH60`. The PR's USB-C notch is 12.8 mm wide and 8.7 mm deep from the lip; the surveyed 6095 connector center is about 18.0 mm in GH60 X (photo-scaled, ±0.3 mm). This is a case-fit reference, not a connector selection for our PCB. Connector body dimensions, shell legs, board-edge position, and cable plug clearance must be checked against the selected part and the actual case CAD before committing the outline.

The current mechanical plate has plate-mount stabilizer cutouts. PCB-mount support therefore requires a second plate variant or verified shared geometry. No switch/socket/LED/stabilizer combination has yet been proven collision-free.

## What exists in this iteration

- `feasibility/layout_model.py`: editable bottom-row position model for the 6.25U and 7U layouts, with split space-bar, split right Shift, split Backspace, and stepped Caps sites. It checks board bounds and generates a labeled SVG preview. Its checks are limited to key-center envelopes; it does not prove switch, socket, LED, stabilizer, screw, or plate clearance.
- `firmware/README.md`: pinned RP2350 QMK/VIA starting point and the required integration/validation steps.

## Next engineering steps

1. Confirm the case mechanical revision and export the plate, PCB seat, USB opening, catch/screw, and interior keep-out geometry to a neutral measured interface file.
2. Replace illustrative layout sites with the chosen GH60 source grid and create actual switch, hot-swap socket, diode, stabilizer, RGB, mounting-hole, and USB-C footprints. Verify every selectable combination against plate and housing solids.
3. Select a USB-C receptacle, ESD protection, power budget, RGB topology, and RP2350A package/pin map. Check USB routing, decoupling, flash, boot/reset access, and thermal/power constraints.
4. Choose a hardware license after provenance review. The repository's root license currently covers the housing source; it is not silently applied as the final PCB hardware license. Do not reuse PH60 (CC BY-NC-SA) or Waffling60 (CERN-OHL-S2) design files in this board without resolving the applicable license and attribution obligations.
5. Run schematic/ERC, PCB/DRC, assembly, QMK build, VIA GUI remap/persistence, then prototype fit and electrical tests. Source-level checks are not physical validation.

This is a draft engineering iteration. It is not routed, electrically complete, validated against the case solids, or ready to fabricate.
