# Maru60 RP2350A PCB — engineering draft

**Current state: see [CURRENT.md](CURRENT.md)** (V7 baseline and latest prototype). The V7 recovery log is in
[../recovery/README.md](../recovery/README.md). Everything below describes earlier stages (A21/A22 foundation) and is
kept for history.

## Current artifacts (2026-11-11)

The relocated-expansion 0/0 prototype now has a reproducible evidence set and a
draft fabrication package. None of it is a manufacturing release.

| Artifact | What it is |
| --- | --- |
| [fabrication/](fabrication/README.md) | Draft BOM (382 rows), CPL (370 SMD), Gerbers/drill/IPC-D-356/STEP, `PROVENANCE.json`, `VERIFICATION.json`. 374/382 BOM rows still lack an MPN. |
| [experiments/resume-20261109-relocated-expansion-zero-opens/REPRODUCE.md](experiments/resume-20261109-relocated-expansion-zero-opens/REPRODUCE.md) | Full native/portable/material/audit/GEOS reproduction sequence with expected numbers. |
| [experiments/resume-20261109-relocated-expansion-zero-opens/qa/strict-promotion/REPORT.md](experiments/resume-20261109-relocated-expansion-zero-opens/qa/strict-promotion/REPORT.md) | Strict-baseline promotion decision: **PROMOTE_UNDER_AMENDED_POLICY**. The amended pair-capsule window covers the 26 designed fillet cusps (0.507 mm²); the residual is 9 single-antipad crescents (0.0426 mm²) + 1,802 Clipper2 keyhole slivers (0.00128 mm²) = 0.0439 mm². |
| [experiments/resume-20261109-relocated-expansion-zero-opens/qa/mechanical-fit/REPORT.md](experiments/resume-20261109-relocated-expansion-zero-opens/qa/mechanical-fit/REPORT.md) | CAD fit after the variant fixes: relocated block 19 pass / 0 tight (J3 0.85 mm); USB-C J1-centred 14.75 mm notch passes (1.20 mm); 7U PCB-mount stabilizer passes the new plate variant (0.40 mm). See [FIXES.md](experiments/resume-20261109-relocated-expansion-zero-opens/qa/mechanical-fit/FIXES.md). |
| [models/rule60-v3-hhkb-gas-plate-pcb-mount.dxf](models/rule60-v3-hhkb-gas-plate-pcb-mount.dxf) | PCB-mount 7U plate variant (enlarged cutout); the original plate-mount DXF is unchanged. |
| [models/maru60-hhkb-topcase-right-usb-14p75-j1centred.3mf](models/maru60-hhkb-topcase-right-usb-14p75-j1centred.3mf) | Right top-case half with the 14.75 mm USB-C notch centred on J1. |
| [models/maru60-hhkb-bottomcase-j3-relief-left.3mf](models/maru60-hhkb-bottomcase-j3-relief-left.3mf) | Left bottom-case half with the local J3 relief pocket (0.85 mm clearance). |
| [experiments/resume-20261109-relocated-expansion-zero-opens/qa/power-review/REPORT.md](experiments/resume-20261109-relocated-expansion-zero-opens/qa/power-review/REPORT.md) | Power analysis: 5.8 µF vs TI 10 µF typical (5.336 µF effective at 5 V); inrush 1.16 mA; LED full-white 1.14 A vs 173.7–233.9 mA limiter — full white is not supported. |
| [experiments/resume-20261109-relocated-expansion-zero-opens/qa/power-sim/REPORT.md](experiments/resume-20261109-relocated-expansion-zero-opens/qa/power-sim/REPORT.md) | Transient simulation: eFuse 25 ms ramp / 1.07 mA inrush; 4 V startup monotonic; UVLO/OVLO 3.987/3.621 V and 5.738/5.212 V; **0.76 mA/ch LED cap is at the limiter edge (0.22% margin) and latches if the load is present at enable — sequence the LED load after the rail is up, or cap at ≤0.70 mA/ch**. |
| [experiments/resume-20261109-relocated-expansion-zero-opens/qa/thermal-sim/REPORT.md](experiments/resume-20261109-relocated-expansion-zero-opens/qa/thermal-sim/REPORT.md) | Lumped thermal network: U2 is the limit (needs θJA ≤78.4 °C/W at 5 V input / 85 °C; as-built screening 120 °C/W); U18/U7 are not the limit; LED full-white 4.56 W. |
| [experiments/resume-20261109-relocated-expansion-zero-opens/qa/usb-si-sim/REPORT.md](experiments/resume-20261109-relocated-expansion-zero-opens/qa/usb-si-sim/REPORT.md) | USB 2.0 SI: 167 mm D+/D- route, 5.28 mm intra-pair skew; 0.25 mm pair is **112.8 Ω** differential (not 90 Ω; ~0.40 mm needed); HS eye 299 mV / 0.53 UI at the template edge. |
| [LICENSE-DECISION.md](LICENSE-DECISION.md) | PCB license options and recommendation (CERN-OHL-S-2.0); owner decides. |
| [USB-ID-DECISION.md](USB-ID-DECISION.md) | VID/PID options and recommendation (pid.codes 0x1209); owner decides. |

The promoted tools are `pcb/tools/audit_relocated_zero_opens.py`,
`geos_witness_zero_opens.py`, `analyze_strict_promotion.py`,
`check_mechanical_fit.py`, `analyze_power.py` and `export_fabrication.py`; see
[pcb/tools/README.md](tools/README.md).

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
