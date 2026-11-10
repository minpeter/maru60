# Current baseline and development prototype

Machine-readable entrypoint: [`current.json`](current.json). It pins the primary
KiCad project, board and root schematic for each selection with repository-relative
paths and SHA256 hashes. Both selections are **not manufacturing-ready**.
Run `uv run tools/check_pcb_current.py` from the repository root to check file
identity and path containment. This read-only check does not replay DRC, cold
refill, electrical checks or qualification, and does not inventory every CAD
dependency. Diagnostic counts in the manifest are saved observations.

| Selection | Primary project | Recorded open pairs / warnings |
| --- | --- | --- |
| Strict geometry baseline | [Open project](experiments/resume-20261105-ext-gpio26/pcb/maru60.kicad_pro) | 11 / 51 |
| Bounded development prototype | [Open project](experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pro) | 0 / 0 |

The strict baseline remains PCB `04be04e5`, commit `bbf61e6`.
The latest development prototype is PCB `cb7b5b29`: following the selected `B.Cu`
expansion-block relocation, the 19-footprint GPIO expansion/isolation block
(`J3`, `U11`, `U13`, `U12`, `R128`, `C128`, `C129`, `R130..R135`, `R140..R145`) is
placed adjacent to `U1` below the spacebar row (`x = 71..97 mm`, `y = 77..92 mm`),
except the side-entry expansion connector `J3` and its ESD array `U13`, which sit at
`(44.25, 75.0) mm` and `(47.1, 79.5) mm` so the JST SH plug has a clear 3.5 mm
insertion corridor under the board (verified against the bottom case at full gasket
travel), silkscreen-only `LOGO1` moves into the vacated upper area at `(100.0, 35.0) mm`,
all other 363 footprints remain electrically identical, and all remaining open nets
are routed octilinearly across `F.Cu` and `B.Cu`.
Design rules are unchanged from the source checkpoint (minimum connection width
0.15 mm) and no reference designator is hidden; the former warnings were cleared by
fixing their causes (stub removal, a `SWDIO` reroute that widens a `+3V3` pour neck,
and legible reference repositioning).
Fresh native checks report **0 opens, 0 warnings, no other DRC errors, ERC zero,
parity zero and 58 byte-identical cold-refilled CAD files**. All prior named-pad
components remain connected without splits, and all seven remaining multi-group nets
(`EXT_GPIO25`, `MCU_GPIO10`, `MCU_GPIO24`, `MCU_GPIO25`, `MCU_GPIO26`, `MCU_GPIO27`,
`MCU_GPIO3`) merge to single components (`multi_group_nets_remaining = {}`). All 754
retained barrel records remain equal by UUID (`910` total barrels including `156`
added vias), and all 17,701 unaffected direct contacts remain present without
reduced overlap. Both inner `GND` planes remain single connected islands with net
area gain (`In1.Cu` `+43.408 mm²`, `In2.Cu` `+20.5404 mm²`), minimum different-net
non-GND inner-plane via neck is `0.1512 mm` (`3` same-net pairs `< 0.15 mm`), and
unsupported outer-track channel copper outside drill antipads, `GND` thermal rings,
`0.25 mm` `zone_min_thickness` fillets and the `U1` QFN60 fanout window is zero.
See the [checkpoint](experiments/resume-20261109-relocated-expansion-zero-opens/README.md)
and [reproduction instructions](../docs/pcb-validation.md).

Zero open pairs and **zero** `2 nm` guarded-contact failures (`guard_failures = 0`)
are recorded on the recomputed Material Graph v2, with zero new empty object layers
and zero new multi-component object layers. Independent GEOS 3.13.1 and exact
$\mathbb{Q}^2$ replay (`qa/geos-audit.json`, `qa/geos-rational-witnesses.json`)
records `0.2704 mm²` (`In1.Cu`) and `0.2806 mm²` (`In2.Cu`) outside individual
circular windows from `0.25 mm` `zone_min_thickness` fillets between adjacent new
vias and Clipper2 integer keyhole chords, without tolerance waiver. Physical
bottom-case clearance for relocated `B.Cu` parts, inherited strict-baseline
differences and manufacturing/hardware qualification remain open.

The power audit checks 13 components and 32 pin assignments, with conditional
feedback and soft-start calculations; its arithmetic replay passes 519 assertions.
Input nominal 5.8 uF versus typical 10 uF guidance remains a review flag rather
than proven instability. Effective component parameters, actual source/load data,
active-loop models and measurements remain open. USB SI/EMI, thermal, fit and
hardware qualification are outstanding. LED qualification stays OFF.

Fresh full ARM/QMK builds pass for both WKL `via` and HHKB `via_hhkb` against the
pinned upstream, recursive submodules and both patches. All six LED translation
units confirm qualification zero. [Logs, ELF/UF2 files and hashes](experiments/resume-20261109-silk-height/qa/qmk-build/RESULT.json)
are retained; no flashing or hardware operation is claimed.

## 2026-11-11 review artifacts

The 0/0 result is now reproducible from the tracked repository, and the open
gates have dedicated evidence:

- [REPRODUCE.md](experiments/resume-20261109-relocated-expansion-zero-opens/REPRODUCE.md)
  and the promoted `pcb/tools/audit_relocated_zero_opens.py` /
  `geos_witness_zero_opens.py`; `tools/check_pcb_native.py` now asserts
  `--expected-warnings` (default 0) and records its command in `RESULT.json`.
- [Strict-promotion decision](experiments/resume-20261109-relocated-expansion-zero-opens/qa/strict-promotion/REPORT.md):
  **CONDITIONAL**. The 0.551 mm² outside-window area is 92.0% designed 0.25 mm
  fillet cusp, 7.7% single-antipad crescent and 0.23% Clipper2 keyhole-chord
  artifact; it is a tolerance-policy artifact, not a physical defect. Promotion
  needs a documented window-policy amendment (or cusp waiver) and resolution of
  the keyhole-chord slivers.
- [Mechanical fit](experiments/resume-20261109-relocated-expansion-zero-opens/qa/mechanical-fit/REPORT.md):
  relocated block 18 pass / 1 tight (J3 0.33 mm); the stock 12.8 mm USB-C notch
  fails a 12.35 mm plug while the printed 14.75 mm notch passes; the 7U
  PCB-mount stabilizer fails the current plate cutout (plate-mount is unaffected).
- [Power review](experiments/resume-20261109-relocated-expansion-zero-opens/qa/power-review/REPORT.md):
  5.8 µF nominal / 5.336 µF effective at 5 V vs TI 10 µF typical; inrush
  1.16 mA; **LED full-white 1.14 A vs 173.7–233.9 mA limiter — full white is not
  supported** and needs a firmware brightness cap or a different limiter/source.
- [Fabrication draft](fabrication/README.md): BOM 382 rows (374 missing MPN),
  CPL 370 SMD, Gerbers/drill/IPC-D-356/STEP, provenance and 23 verification
  checks. Not an assembly approval.
- [License](LICENSE-DECISION.md) and [USB ID](USB-ID-DECISION.md) decision
  documents; both remain the owner's choice.

Earlier prototypes `df21164e` (7/26), `41f82c80` (9/38), `88fbac1d` (9/39),
`2e532c1a` (9/40), `9d787421` (9/42) and `56d66f65` (10/50) remain preserved. This
selection is not strict baseline promotion or manufacturing release. Return to the
[PCB overview](README.md) or [project overview](../README.md).
