# Connector GND stitch: frozen prospective contract on c770

## Ready for one isolated candidate, not accepted hardware

The frozen construction contract is **CONSTRUCTION_CONTRACT.json**, SHA256:

`c58baac31c087ddd115fb5ccbe7953ced52d8469c0efe675b2184ea00ff7d7a5`

It permits only one ordinary plated GND through-via at **(17.20, 9.90) mm**, copper diameter **0.50 mm**, drill **0.25 mm**, F.Cu–B.Cu, UUID **cda2df4b-6411-5409-a933-5106751244d8**. No track is added or changed. The selected board and the existing connector stub remain untouched. This packet contains no constructed or adopted candidate.

Exact selected source: **c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a**, commit **094851aa91eb49e40182c9a88657a8ed6e6dcba8**. Paths and hashes for the PCB, project, corrected R2 graph and active all-through-drill helper are pinned in the contract and site results.

## Fresh current-source checks

These results replace reliance on the earlier local/neighbor-hole screening for this construction decision:

| Check | Result |
|---|---:|
| Every existing actual through drill checked | **1,269**: 918 vias, 335 NPTH, 16 PTH |
| Existing object/layer checks | **15,330** |
| Minimum foreign-copper clearance | **0.225 mm**, versus 0.15 mm rule |
| Minimum hole-edge clearance | **1.253330 mm**, versus 0.25 mm rule |
| Minimum current drill-to-old-object shadow distance | **0.350 mm** |
| Minimum historical a9 drill-to-signal-shadow distance | **0.363815 mm** |
| Retired U10 D− shadow distance, UUID 2c517f5c… | **0.600 mm** |
| Annular contact on each actual inner GND material | **0.147260768066 mm²**, no missing annulus |
| Positive overlap after independently guarding both materials inward by 2 nm | **0.1472558792225 mm²** on each plane |
| Planned physical drill loss per inner GND plane | **0.049087681002 mm²** |
| Planned drill loss on all existing outer GND-zone material | **0** |

Hole clearance uses exact rational integer distance-to-capsule-axis comparisons over every physical through hole, independent of pad copper-layer membership. Foreign-copper and original-shadow predicates use native shapes. Both inner plane components were reconstructed with every actual drill removed, exactly area-matched to corrected R2, and bound to the J1.A1 material root. The new via does not yet exist, so these are prospective contact checks, not an actual candidate graph.

The source has no copper graphics, no conflicting via keepout, no custom `.kicad_dru`, and 0.15 mm clearance in every project netclass. The via copper is wholly inside the native board outline; conservative nearest edge clearance is 9.625 mm. Its nominal annular width is 0.125 mm against the project's 0.10 mm minimum. These are project-rule checks, not manufacturer tolerance/process qualification.

## Historical shadow evidence restored narrowly

The exact original a9 PCB was recovered from the **preserved input** member `maru60-tscircuit-full/input/v7/maru60.kicad_pcb` in the already recovered archive. It was not taken from a generated/compatible output. Board hash:

`a9ff40100f8b34cd46b7706eb3264cbbc61508cc4c6895fdcefcb2cce35e7b67`

All **11,905 original non-GND outer shapes** were checked against the proposed drill. The retired U10 D− segment **2c517f5c-8f2d-4a2a-9fea-dc1b7376c3cd** was explicitly present and tested. No new drill intersection was found. The exact original board input is restored for this check; the original full QA/history has **not** been restored. `original_source_provenance.json` records archive and member hashes.

## Retained connector stub

The **0.95 mm**, 0.25 mm-wide F.Cu GND stub **bc0a06ab-785a-4a27-a164-9c3256c7f3bd** runs from (15.7,10.75) to (15.7,9.8).

It is a real grounded leaf, not floating copper: one guarded contact connects it to the via at (15.7,9.8), whose intact barrel contacts both inner planes. It has no surface-pour contact. A graph-only removal leaves all 247 GND pads connected. U10 has its own separate ground route and via. The stub lies to the left of the USB routing, not between D+ and D−.

A local field/capacitance effect is possible, but no guarding, return-inductance or ESD benefit is established. **Retain it to avoid an unmotivated second change**, not because an essential or beneficial guard has been proven. A generic dangling warning is insufficient reason to delete it. The contract explicitly forbids trimming or extending it.

## Exact scope of any future acceptance

The actual inserted candidate must undergo normal native fill, DRC/ERC/parity, corrected all-hole R2 material/root/contact/partition checks, and independent review. All old conductors and holes must remain exact.

The **only permitted physical loss** is the actual new drill disk in the two rooted inner GND planes. Compare actual candidate material with source material minus that exact drill using zero Boolean XOR, not an area-only check. There is **no endpoint mask, no small-area waiver and no 1 nm loss allowance**. The native 1 nm polygon approximation and conservative 2 nm contact guard are representation/robustness mechanisms, not permitted copper loss or manufacturing margins.

All current and a9 historical signal shadows must retain zero new reference loss. All outer GND-zone material and non-GND-zone material must remain exact. If normal fill creates extra outer copper/islands or any other loss, the candidate is outside this contract and must stop for review rather than silently expanding scope. The only new outer copper authorized here is the via annulus.

The prospective nearest return distance for the left D+ via becomes **1.597655 mm** instead of **2.351197 mm**. The right D+ via keeps its existing nearer **1.956559 mm** return. This is only a geometric distance change. **It does not restore the merged-antipad neck or establish signal, impedance, ESD or EMC improvement.**

## Reproduce and review

- `/usr/bin/python3 inspect_site.py`: current-source, all-hole, project-rule, outline and rooted plane-contact screening.
- `/usr/bin/python3 check_legacy_shadow.py`: exact original a9 shadow check, including the retired U10 D− segment.
- Both scripts explicitly reject optimized Python. `fail_closed_controls.json` confirms `-O` fails without modifying existing results.
- `stub-review/`: independent material/contact and graph-counterfactual evidence. Review-requested hardening was applied: optimized-mode rejection, native build pinning, project/netclass binding, board containment and explicit outer-zone zero loss.
- `site_results.json`, `legacy_shadow_results.json` and the frozen contract contain the detailed machine-readable evidence.

The selected source was hash-verified unchanged after all read-only work. The contract is a bounded next experiment, not physical SI/ESD qualification.
