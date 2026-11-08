# Maru60 RP2350A PCB — engineering draft

**Current state: see [CURRENT.md](CURRENT.md)** (V7 baseline and latest prototype). The V7 recovery log is in
[../recovery/README.md](../recovery/README.md). Everything below describes earlier stages (A21/A22 foundation) and is
kept for history.

## Recovered native checkpoints (2026-11-03)

The [A21 checkpoint](checkpoints/a21/README.md) now includes the actual native four-layer board, schematic, project, local libraries and evidence. Its A22 predecessor is retained at `checkpoints/a21/coordinator-evidence/source.kicad_pcb`. Fresh checks and publication limits are in [publication/a21-a22](publication/a21-a22/README.md). A21 still has 21 opens and A22 22; neither is fabrication-ready. The foundation notes below are historical and do not describe the current existence of native CAD.

This independent PCB workstream is kept under `pcb/`; it does not merge or alter housing work.

## Product requirements

GH60-class PCB; RP2350A; USB-C; MX hot-swap; switchable WKL/HHKB physical layouts; 7U spacebar only for PCB v1; split/non-split Backspace and right Shift; stepped Caps; PCB-mount and plate-mount stabilizer support using compatible plates; VIA remapping; per-key RGB and underglow. Wireless/Bluetooth remains undecided; no radio or battery is committed.

WKL and HHKB bottom rows share a common 0U origin and 15U span with a 7U spacebar. WKL has blank 1U Win blockers at centers 2U and 13U. HHKB has blank 1.5U corner blockers and five active centers at 2U, 3.25U, 7.5U, 11.75U and 13U. The physical socket-site union preserves all seven centers [0.75, 2, 3.25, 7.5, 11.75, 13, 14.25]U for both configurations. Opposite-layout blockers overlap some union sites; separate plate/top-shell fit remains unverified. Earlier WK and 6.25U choices were dropped for v1 by user decision.

## Mechanical reference

The branch is based on `main` at `03c92914fb0acad659a554024d689673794ea5a9`. Mechanical fit reference is open PR #1 head `1d89453825131438929ad887e2b0264f8f620cd2`: top case v7.10 and bottom-case draft v0.11. The stored interface spec defines the Rule60 plate frame and board transform:
`X_plate = X_GH60 + 0.4525`, `Y_plate = 101.06775 - Y_GH60`.
The current plate has plate-mount stabilizer cutouts. A PCB-mount option needs a different plate or verified shared cutouts. USB notch and connector clearance must be checked against the selected receptacle and actual CAD.

## Engineering artifacts

- `feasibility/layout_model.json`: two 7U bottom-row definitions compared against independent QMK fixtures, with the WKL/HHKB physical socket union retained, plus split/non-split Backspace and right Shift.
- `feasibility/validate_layout.mjs`: executable validator and SVG generator. Run with `node pcb/feasibility/validate_layout.mjs`.
- `feasibility/validation-report.json`: latest model-case test summary.
- `feasibility/layout-preview.svg` and `layout-preview.png`: WKL/HHKB 7U comparison; gray segments mark blockers; union sites remain modeled separately.
- `firmware/qmk`: RP2350/VIA overlay scaffold pinned to the investigated QMK fork revision.
- `engineering/third_party/MX_V2`: MIT-licensed upstream 1U and 7U MX hot-swap footprints with required notices.
- `engineering/footprint-check.mjs`: geometry-only screening of real switch copper pads and 7U stabilizer drills against the WKL/HHKB bottom-row socket union.
- `engineering/electrical-architecture.md`: RP2350A/USB-C/matrix/RGB design decisions, official reference links, and explicit KiCad/physical-validation blockers.

QMK references: [ANSI Tsangan 60%](https://raw.githubusercontent.com/qmk/qmk_firmware/master/layouts/default/60_ansi_tsangan/info.json) and [HHKB 60%](https://raw.githubusercontent.com/qmk/qmk_firmware/master/layouts/default/60_hhkb/info.json).

## Validation boundary

The Node model checks 12 declared nominal layout/option cases for explicit row widths and key order, nominal switch-center bounds, plate/GH60 coordinate round-trip, and minimum 0.5U modeled center spacing. These are nominal layout cases, not physical PCB compatibility tests. The model does **not** check switch body, hot-swap socket, diode, LED, stabilizer, mounting-hole, plate or case collision. Licensed ai03 1U/7U hot-swap footprint geometry is now vendored and screened; no PCB/plate/case solid collision check has been done. Do not read the passing layout report as clearance proof.

At the original foundation revision, no schematic or routed KiCad PCB had been made. Native WIP CAD is now archived above. KiCad is unavailable in the Windows execution environment; install/approval details and the actual RP2350A power/USB/RGB architecture are documented in `engineering/electrical-architecture.md`. The licensed hot-swap footprint copper screening passes only its narrow geometric checks; it is not DRC or physical fit validation. The Maru60 QMK/VIA overlay compiles in the separate pinned cloud build after prototype USB metadata was added, but VIA GUI remapping/persistence, electrical validation, and physical fit remain unverified. This is not manufacturing-ready.

## License and design provenance

The owner intends open hardware, but has not selected the PCB hardware license. The repository root license is not silently asserted as the PCB license. This draft does not copy third-party PCB CAD. PH60 (CC BY-NC-SA) and Waffling60 (CERN-OHL-S2) were identified during research and are excluded from this design. Record component-datasheet and footprint licenses when parts are selected.
