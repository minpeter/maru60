MARU60: GPIO27 header, GPIO24 ground stitch and reference-label checkpoint

Candidate PCB SHA256:
9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed

This is a reversible development candidate, not strict geometric acceptance or fabrication approval. The strict baseline bbf61e6 / 04be04e5 remains preserved with 11 open connection pairs and 51 warnings. The earlier c782123 / 56d66f65 prototype remains preserved with 10 open pairs and 50 warnings.

WHAT CHANGED

The GPIO27 header connection now joins J3.9 to the existing U11.13/U13.8 component. This required a declared local detour of EXT_GPIO10 and a 0.212132 mm move of an existing EXT_GPIO26 via, plus its connected route adjustments. The changes are fully listed in the header evidence. No component, schematic, net, width rule or clearance rule was changed. New signal tracks are 0.15 mm wide; the new signal via is 0.50/0.25 mm.

A 0.50/0.25 mm GND through via was added at (105.65, 36.05), close to the U11-side GPIO24 transition. Its plated annulus connects both inner GND planes and the existing component containing all 247 GND pads. Nearest verified GND-via distance to that signal transition changes from 3.647688 to 1.457738 mm. This is a geometric improvement, not a measured inductance or signal-integrity result.

Four visible back-side references, U13, U11, R135 and R145, were moved and enlarged from 0.75 to 0.80 mm. Their names, layer, mirroring and 0.10 mm stroke were retained. These changes remove exactly eight warnings with none added. Actual rendered ink was checked against mask openings, other silk, Fab geometry, board edge and both raw and cached courtyard geometries; the raw drawn-courtyard envelope gap is at least 0.204523 mm. The labels were visually checked for association with their own parts.

CORRECTION AFTER INDEPENDENT REVIEW

The first combined candidate b1e3b41f is ON HOLD and is not selected. Independent review found 0.0003496908615 mm2 of new GPIO26 F.Cu copper over the unchanged source-via reference void, outside the previously declared moved-via window. The earlier header report incorrectly summarized every affected route as passing. The raw measurement had recorded the exception.

This corrected candidate preserves the original departure direction from (95.075, 40.175) to the exact collinear point (95.765, 40.815), then continues on one new 0.15 mm segment to the moved via (96.65, 41.625). No transition window was enlarged. Independent targeted tests confirm zero new unsupported area on both replacement segments outside the unchanged permitted window, and the original source-via contact patch is exactly restored. Other far-end contacts are explicitly remapped and remain positive; their patches are not claimed identical. The full-board verification now asserts every tested return-area result, instead of relying on a prose summary of an array.

VERIFIED ON THIS EXACT COMBINED FILE

- Native KiCad 9.0.2+dfsg-1: 9 open pairs, 42 warnings, no other DRC errors, zero schematic-parity errors, ERC 0.
- All 1,064 electrical pin bindings match the unchanged schematic netlist; raw names and native loaded/built names match across 12,135 conductive objects.
- All 58 CAD files remain byte-identical after a separate cold load, connectivity build, zone refill and save.
- Corrected material graph: 9,773 segments, 923 vias, 383 footprints. All existing physical endpoint components remain intact except the intended GPIO27 merge. The nine remaining complete open-component pairs match; native ratsnest representative UUIDs are not required to stay identical.
- Both inner GND planes remain single components. For the header refactor, no full-board plane loss occurs outside the three declared signal-transition windows, and no unrelated old signal shadow loses reference. New GPIO27 and replacement GPIO10 tracks retain adjacent reference outside their own signal transitions.
- Adding the GND stitch and labels to the header candidate preserves every old direct/zone contact area and every old non-zone object material node. All serialized zone forms stay exact. Physical inner-plane area changes only by the actual new drill, 0.049087681002 mm2 per plane. No old signal shadow is removed by this composition. The final departure-angle correction leaves all serialized fills exact; only one existing track endpoint and one new track change.

STRICT DIAGNOSTICS ARE NOT WAIVED

The c782123 source already has a real, independently bounded remote +4V_LED reference-shadow difference of 2.7676778318142192e-08 mm2 per plane. Its exact no-loss diagnostic remains FAIL. The new header deliberately changes old geometry and contact patches, so unchanged-geometry identity is not claimed. Three retired GPIO10 UUID contacts are exact physical remaps to the new terminal segment. At its deliberately reshaped start junction, total overlap grows, but a native Boolean old-minus-new difference of 1.37825e-08 mm2 across 26 tiny outlines remains recorded. No broad numerical tolerance was used to erase these results.

The corrected material graph also retains 51 inherited guarded-contact proof failures. These are a separate conservative geometry diagnostic, not the 42 native DRC warnings. They are not silently converted to a full-board electrical certification.

POWER MODEL WORK

The actual unchanged part names and pin nets confirm 49.7 uF of nominal capacitance directly on +4V_REG: C100 4.7 uF, C120 1 uF, C140 and C141 22 uF each. The original decks remain bound to PCB56d66f65. Final PCB9d787421 has independently verified identical values and pin nets for these four parts; see simulation/PROVENANCE_NOTE.txt and qa/power-envelope-applicability.json. Eighteen new synthetic charge-balance cases use that basis and independently check simulator endpoints against the finite-ramp analytical equation. All finish with finite waveforms and less than 10 uV endpoint difference. Independent replay reproduced all 18 saved waveforms exactly; an independent all-sample analytic comparison has maximum error 1.006039 uV.

These are illustrative passive sensitivities, not an extracted current-board or active stability simulation. Assumed effective fractions of 100%, 50% and 20%, assumed 20 milliohm ESR, a 0.2 A load step and 10/50/100 us fixed-current intervals are not measured bounds or actual regulator behavior. Real effective capacitance, ESR/ESL, control loop, current limits, layout parasitics and loads remain unknown. Official active-model compatibility gaps remain; no startup, fault, brownout, thermal or stability qualification is claimed. The earlier 14 frozen passive/behavioral replays also remain qualified as sensitivities/control tests, not a full current-board model.

REMAINING WORK

Three header pairs remain: GPIO24 to U13, and two GPIO25 component pairs. All six MCU-side pairs remain. The 42 warnings are 15 text-height, 13 mask/silk clipping, 10 silk-overlap and 4 dangling-track warnings. No warning was suppressed. The separate MCU GPIO27 escape C is REJECTED: its shifted +1V1 rail introduces four clearance errors against LED_FAULT_N, with 0.1050 and 0.1223 mm gaps where 0.1500 mm is required. Positive connectivity/reference findings do not override these errors. Its bounded continuation search also found no complete route. No MCU experiment is in this checkpoint.

Full ARM/QMK builds, active power validation, SI/EMI, stackup/part validation, mechanical fit and physical tests remain unfinished. LED qualification stays OFF. No public push, manufacturing order or flashing was performed.

REPRODUCING CHECKS

Use the exact native KiCad build and its Python pcbnew module. From this directory, run /usr/bin/python3 VERIFY.py for fresh DRC, ERC, net identity and a byte-stable cold-copy check. Add --material to recompute the corrected material graph and compare physical open-component pairs and contacts; that option takes several minutes. Outputs go into a new verification-* folder. The original CAD is never overwritten. A different native build must be re-reviewed, not silently treated as identical.

The concise decision, complete warning register, original source-bound evidence and final native images accompany the checkpoint. The master delivery manifest covers delivered files; older nested manifests describe their specifically named historical source packets, not the whole delivery.
