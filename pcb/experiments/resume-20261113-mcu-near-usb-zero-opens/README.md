# MCU near USB — routed candidate, 2026-11-13

**Routing and manufacturing-CAD checks are complete. Physical-fit hold remains.**
Open the [KiCad project](pcb/maru60.kicad_pro), [board](pcb/maru60.kicad_pcb),
or [fabrication and assembly package](order/README.md).
Board SHA256: `2cc544c8e6eb00bd3f53fa480a0167dcb8e14dac687f7eb2af0c85946bda5584`.
This supersedes the incomplete MCU-relocation checkpoint for further development;
it does not replace the historical `pcb/order` selection or approve fabrication.

## Completed design

U1 is at board XY (26, 35) mm beside USB-C; U3 flash is at (10, 35) mm.
The crystal, regulator and core decoupling parts follow the MCU. The inherited
2U/split Backspace sites, selected plate-mount 7U spacebar, connectors and outline
are retained. All relocated signal, power and ground connections are routed.

The final cleanup separates the QSPI clock/select vias, connects COL13 and C114
ground, detours GPIO25 around the COL13 via, and removes abandoned branches.
C199's supply via and C113 move clear of solder openings. Two +1V1 segments
meet the recommended hole clearance, and D16's left silk edge clears the
adjacent switch hole while retaining its cathode mark.

Two added 100Ω resistors, **R192 and R193**, damp the relocated key-LED paths.
R193 is before the branch to both exclusive Caps Lock LED sites. **R115 is now
150Ω**. The three formerly failing modeled paths pass all 24 targeted
strong/weak/load conditions on their actual routed geometry. See the
[recorded damping checks](qa/signal-integrity/led-damping/results.json).

## Saved verification

| Check | Result and scope |
| --- | --- |
| [Native KiCad 9.0.2](qa/native/RESULT.json) | 0 opens, 0 errors, 0 warnings, ERC 0, schematic parity 0. Cold refill leaves all 81 CAD files identical. |
| [Copper connectivity](qa/native/material-summary.json) | All 274 nets have one connected pad partition. The graph retains 1,601 rejected individual contacts and 231 native pairs without a guarded contact; no strict-baseline promotion is claimed. |
| [JLCPCB DFM](qa/dfm-per-rule.json) | All 32 rules: 0 findings. [Geometry checks](qa/dfm-geometry.json) find no via drill holes overlapping SMD lands. |
| [Gerber readback](qa/gerber-readback.json) | All 24 checks pass with an independent parser. |
| [Assembly export](order/PROVENANCE.json) | 412 footprints; 336 automated placements, 136 top / 200 bottom; 55 LCSC parts. LED14/LED15 and the six Backspace receptacles are hand-fitted. |
| [Case envelopes](qa/mechanical-fit/selected-assembly.json) | 50 relocated/expansion component envelopes pass, minimum 0.85 mm at J3, with assumed heights and gasket travel. USB notch passes. Raw report remains `ATTENTION`; see below. |
| [Backspace envelopes](qa/backspace-fit.json) | Three resistors and ten swept hardware envelopes pass under the recorded assumptions. |
| [Signal models](qa/signal-integrity/REPORT.md) | Final-board USB, LED, matrix, crystal and miscellaneous signal results, with model and numerical limits. |
| [Power distribution](qa/pdn/README.md) | Corrected routed-copper model: VBUS U8→U18 about 124 mV at assumed 0.5 A, and +3V3 U2→U1.49 about 78 mV at assumed 0.15 A / 20 °C. Maximum tested LED drop at 60 °C: 28.55 mV. No regulator transient or thermal requalification. |
| [Firmware reuse](qa/firmware-reuse.json) | MCU pin bindings match; all original net/pin bindings and LED order match after contracting only the added R192/R193. R115 changes to 150Ω; both UF2 hashes verified. No new build or hardware flash. |

Supplier inventory is the **2026-11-11 snapshot**, not a live availability check.
R115 now uses **C25082 / 0402WGF1500TCE, 150Ω ±1%**: its library identity was
checked on 2026-11-13; current JLCPCB stock and basic/extended class remain unverified.
335 placements fit supplier footprints; nonpolarised R123 retains the previous
placement convention. Review the recorded land-pattern differences and supplier
assembly preview before ordering. Preserve the existing LED power limit and
bring-up procedures; no full-white power or production qualification is implied.

## Fit gates before fabrication

The selected 7U hardware is **Designer Studio Stabilizer (For Plate)** with a
7U wire and the [plate-mount / 2U Backspace plate](../../../models/maru60-hhkb-plate-7u-plate-mount-2u-backspace.dxf).
The raw mechanical check tests PCB-mount 7U holes against this plate and reports
a failure. Those holes are intentionally unused by the selected hardware; the
raw failure is preserved, and it does not establish the selected product's fit.

Do not fabricate until these inherited fit gates are resolved:

1. Select the exact Mill-Max 3305 receptacle and verify its drawing against
   **1.70 mm finished holes / 2.50 mm lands**. Test actual switch pins, seating,
   retention and soldering on a coupon. The present dimensions are study geometry.
2. Verify Designer Studio 7U clip retention and plate thickness, wire/housing
   clearance to the PCB and case, and free travel. Nominal plate thickness is
   1.5 mm; 1.6 mm FR4 is not automatically interchangeable.
3. Verify the separate PCB-mount **2U Backspace stabilizer**, fasteners, switch
   and keycap. The model assumes at most 2 mm projection below the PCB, an upper
   housing of 7.75 × 14 mm with 0.25 mm allowance, and 0.8 mm gasket travel.
   Minimum plate outer-edge margin at the opening is only 1.1378 mm.
4. Fit exactly one site of LED14 and one of LED15 for the chosen switch layout.
   Check switch-body and solder clearance. Never populate central 2U and split
   switches simultaneously. Follow [the assembly table](order/README.md#backspace-assembly).

No physical fit, USB electrical compliance, crystal startup measurement or
powered hardware qualification has been performed. Prior license/USB-ID
decisions and the earlier candidate's other qualification boundaries still apply.
The [previous fit investigation](../resume-20261112-backspace-2u/README.md#fit-gates-before-fabrication)
contains the product evidence and assumptions.

## Reproduce and review

[REPRODUCE.md](REPRODUCE.md) gives commands for the delivered CAD.
[qa/status.json](qa/status.json) records the candidate's exact acceptance scope.
`MANIFEST.json` binds the delivered files and tools; it is not release approval.
Reports with ignored `build/` source paths retain their actual source hashes.
The final R193 silk-only correction is bound to the electrical results by
[byte-identical geometry and the exact one-line CAD edit](qa/geometry-equivalence.json).
The geometry and full copper graph are compressed without changing their bytes.
[Selected construction records](qa/design-operations/README.md) explain final edits
but are not a complete replay of every historic routing intermediate.
