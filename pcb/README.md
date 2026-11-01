# Maru60 RP2350A PCB — engineering draft

This independent PCB workstream is kept under `pcb/`; it does not merge or alter housing work.

## Product requirements

GH60-class PCB; RP2350A; USB-C; MX hot-swap; switchable WK/WKL/HHKB physical layouts; 6.25U and 7U space bars; split/non-split Backspace and right Shift; stepped Caps; PCB-mount and plate-mount stabilizer support using compatible plates; VIA remapping; per-key RGB and underglow. Wireless/Bluetooth remains undecided; no radio or battery is committed.

## Mechanical reference

The branch is based on `main` at `03c92914fb0acad659a554024d689673794ea5a9`. Mechanical fit reference is open PR #1 head `1d89453825131438929ad887e2b0264f8f620cd2`: top case v7.10 and bottom-case draft v0.11. The stored interface spec defines the Rule60 plate frame and board transform:
`X_plate = X_GH60 + 0.4525`, `Y_plate = 101.06775 - Y_GH60`.
The current plate has plate-mount stabilizer cutouts. A PCB-mount option needs a different plate or verified shared cutouts. USB notch and connector clearance must be checked against the selected receptacle and actual CAD.

## Engineering artifacts

- `feasibility/layout_model.json`: explicit draft key envelopes and switch-center transforms for WK, WKL, and HHKB; 6.25U/7U; split-space, split/non-split Backspace, split/non-split right Shift, and stepped/non-stepped Caps.
- `feasibility/validate_layout.mjs`: executable validator and SVG generator. Run with `node pcb/feasibility/validate_layout.mjs`.
- `feasibility/validation-report.json`: latest run summary.
- `feasibility/layout-preview.svg` and `layout-preview.png`: WK 6.25U visual draft. It shows keycap envelopes and switch centers only.
- `firmware/qmk`: minimal RP2350/VIA overlay scaffold pinned to the investigated QMK fork revision.

## Validation boundary

The Node model checks 96 combinations for switch-center bounds, plate/GH60 coordinate round-trip, minimum 0.5U center spacing, and nominal row envelope width. It does **not** check switch body, hot-swap socket, diode, LED, stabilizer, mounting-hole, plate or case collision. No licensed socket footprint geometry or PCB/plate/case solids are in this workstream yet. Do not read the passing layout report as clearance proof.

No schematic or KiCad PCB has been made. KiCad is unavailable in the current execution environment. Firmware scaffold, QMK compilation, VIA GUI remapping/persistence, electrical validation, and physical fit remain unverified. This is not manufacturing-ready.

## License and design provenance

The owner intends open hardware, but has not selected the PCB hardware license. The repository root license is not silently asserted as the PCB license. This draft does not copy third-party PCB CAD. PH60 (CC BY-NC-SA) and Waffling60 (CERN-OHL-S2) were identified during research and are excluded from this design. Record component-datasheet and footprint licenses when parts are selected.
