# GPIO24 bounded local-reroute trial

**Status: HOLD / UNSELECTED pending the parent’s explicit development decision.** Native connectivity improves. The unrelated old-shadow change has now been classified as a genuine, sub-1 nm serialized boundary difference; strict exact preservation does not pass. No tolerance, warning suppression, electrical release, SI claim or manufacturing approval is implied. The independently accepted local GPIO26 checkpoint `frozen26b` is preserved unchanged.

## Files and identity

- Exact parent: `frozen26b/pcb`, PCB SHA256 `04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99`.
- Trial: `frozen24move/pcb/maru60.kicad_pro`, complete 58-file companion directory.
- Trial PCB SHA256 `2bacda8824b543df9be08628cd8ac14b2ed6628d7ee3e221626b869da74787d4`.
- Original recovered source remains `2b5787cc27e7fea92dff2ad483185fccfab1d2d27bf07662395de26f7ab14d69` at HEAD `321785ad9af76405c23ca6f6b215b1a07f8ae948`.
- Manifest: `qa24move/MANIFEST.json`. Native full-board SVG/PNG and local F.Cu/B.Cu views: `images24move/`. The views were visually checked. Gray copper in the detail views is not necessarily GND.

## Declared edit, relative to26b

Six 0.15 mm EXT_GPIO24 track segments and two 0.50/0.25 mm through vias are added. No inner signal layer is used.

- B.Cu: J3 pad5 (92.5,39.0) → (92.35,37.75), new through via.
- B.Cu: U11 pad16 (107.1,36.675) → (106.275,36.9) → (105.8,37.5), new through via.
- F.Cu: (92.35,37.75) → (97.225,38.0) → (104.35,38.0) → (105.8,37.5).
- Exactly one existing object is repositioned: EXT_GPIO3 via `976a7de4-489f-4261-a64f-3551037e01df`, (97.25,37.55) → (97.25,37.45). Its dimensions, drill, span, net and UUID are unchanged. No old track coordinate is edited. Its physical incident contact areas are intentionally rechecked rather than assumed unchanged.
- All other existing raw conductive objects, footprint placements, circuit sources and rules are unchanged. Only inner GND fill polygons change as a consequence.
- Added length relative to26b: **16.419553005737 mm**. Relative to original: **20.021843801633 mm**.
- Trial total: **9,758 track segments, 922 vias, 383 footprints**, total track length **13,204.477293816894 mm**. Relative to original this is eight added tracks and three added vias, plus the one declared existing-via relocation.

The held route-only predecessor `frozen24` clipped two existing reference voids. The 0.10 mm via move plus 0.025 mm F.Cu route shift removes those new-route reference gaps without moving a component or using an inner layer.

## Native results

- Fresh DRC: **10 opens, 51 warning records identical to the original, zero other hard errors, explicit parity0**. `qa24move/drc-clean.json` is a repeat clean-log DRC; the initial report also succeeded but logged a temporary global CLI-lock cleanup message. Later runs use a private TMPDIR as well as private XDG directories.
- Fresh ERC: **0**.
- Native source identity: all **12,119 raw conductive objects** match Load/Build net names; all **1,064 XML electrical pin bindings** match.
- Normal isolated cold BuildConnectivity/refill/save: PCB and all **58 files byte-identical**, net names stable; 2.93 seconds.
- EXT_GPIO26 remains closed. EXT_GPIO24's J3 and U11 components now merge; U13 is still open. Thus the experimental native count is12→10 overall, not a claim that all expansion wiring is complete.
- Four short header pairs remain: GPIO24 U13, two GPIO25 pairs and GPIO27 J3; the six long MCU opens remain outside this worker's edits.
- `qa24move/{drc-comparison,CONTACT_AND_OPEN_SUMMARY}.json` preserves full before/after pair lists and pad partitions. Native representative pair descriptions can change after a component merger, so removed-record count is not itself closure count.

## Material contacts and affected circuit

The corrected reviewed material exporter ran on the absolute frozen trial with a distinct output and all asserted through drills subtracted. No Unfracture was used.

- All **21,775 original direct contacts remain present**, with14 additional positive direct contacts; six old witness areas change, all on EXT_GPIO3 incident geometry. None is lost or reduced to unproved contact.
- All **733 original zone contacts remain present**. Two GND witness areas increase from0.147260768066 to0.147260768161 mm²; these are explicitly recorded, not called byte-identical.
- All246 pad-net inventories remain. Only EXT_GPIO26 and EXT_GPIO24 pad partitions merge. EXT_GPIO3 and GND pad partitions are unchanged.
- All51 inherited guarded-contact rejections and native unproved candidate-pair sets are identical. All plated barrel proofs remain valid.
- Only two old track material nodes change area because the relocated through drill changes the copper removed from them: F.Cu `183b381d-42a3-49f4-a8cb-abf824d7658b` and B.Cu `48e89f5e-c7ba-4a20-a4a3-4d002c478a59`, both EXT_GPIO3. The existing via's material is translated as explicitly declared; equal area is not a claim of equal geometry.
- Full witness values and node changes are in `qa24move/{material-comparison,changed-old-material-nodes}.json`.

## Return geometry and explicit remaining issue

- Both physical inner GND planes retain one component. The six new GPIO24 tracks, and the inherited GPIO26 tracks, have zero uncovered projection outside their own signal-via transition envelopes in the performed nominal check. This is a geometric finding, not return-current or impedance simulation.
- Relative to the original2b source, the modified EXT_GPIO3 transition adds reference loss of0.000578146491 mm² beneath one F.Cu track and0.000032982482 mm² beneath one B.Cu track on each inner plane. `modified-transition-confinement.json` proves those specific patches are contained in the explicitly moved via's0.455 mm-radius envelope, with zero patch area outside. Actual inner-zone clearance remains0.20 mm; the envelope includes the native polygonal fill extent.
- The original-source plane comparison reports loss2.0138602518735 and gain0.0901006580205 mm² per plane, including the three new signal vias and the moved-via void. It also reports1.02208e-07 mm² of loss outside the declared windows. This nonzero residue is retained, not waived.
- **Exact26b→24move full-board review found an additional +4V_LED B.Cu old-shadow difference:** track `3e0fec9e-6c78-45a5-a2dc-22ae925ad604`, x274.6 mm, y35.25→38.35, width0.25 mm, loses2.3625e-08 mm² in native Boolean output outside the moved-via window. Direct26b plane loss/gain are1.372606853064/0.09010064614 mm² per plane; three outside-window native residues sum to1.02208e-07 mm². Every value remains recorded.
- **Exact raw-boundary classification of the unrelated track case:** rational cell splitting and winding on the unsimplified raw filled polygons, with no Boolean operation, no Unfracture, and no intersecting drill, finds true local raw-zone loss `1189714324905/42986012` nm² = **2.7676778318142192e-08 mm² per plane**. The native Boolean value is therefore not an exact area oracle. The affected source and candidate piecewise-linear boundaries differ by at most `7524735/10746503` nm = **0.700203126543 nm vertically**, below one1 nm serialized coordinate unit. This is a genuine serialized boundary change, not perfect identity and not wholly a false positive. The complete two-flank review also measures raw gain **9.475081994888174e-09 mm² per plane**. Exact nonzero-edge comparison proves that every changed raw boundary crossing the full track bounding box is inside the reviewed rectangle; exact reversed-edge cancellation preserves all genuine holes. See `EXACT_BOUNDARY_CLASSIFICATION.json`, `exact-far-track-complete.json`, `far-track-boundary-bound-complete.json`, and the retained narrower diagnostics.
- The exact track classification is case-specific. It does not turn other plane-only native residues into zero or establish a general numerical tolerance. The full-board parent review finds only three old-shadow objects affected: the two declared EXT_GPIO3 transition objects and this +4V_LED track. All six new GPIO24 tracks and every EXT_GPIO3 track have no new uncovered area outside their respective transitions.
- **Correction to the earlier preliminary summary:** the local crop used for the original-source shadow comparison was not sufficient once nonzero loss outside the edit envelopes appeared. The zero-unrelated-net-loss statement for24move is withdrawn. Direct26b, full-board evidence controls selection; no silent numerical tolerance is introduced.
- Parent full-board diagnostics are preserved in `qa24move/parent-independent-review.json` and `parent-material-review.json`. Worker direct26b contacts/pairs are in `material-comparison-direct26b.json` and `drc-comparison-direct26b.json`; direct26b integer shadow contours are in `exact26b-targeted-difference.json`. These diagnostics supplement the original-source aggregate results.

## Ground-return transition and screened alternatives

Nearest existing grounded through-vias:

- New J3-side GPIO24 via:0.710633520178 mm away, at(91.8,37.3).
- New U11-side GPIO24 via:3.647687623687 mm away, at(103.725,40.5).
- Moved EXT_GPIO3 via:4.257346591482 mm away, at(94.5,40.7). Its return-transfer spacing is not electrically qualified.

A bounded25 µm-grid site screen for a standard0.50/0.25 mm GND stitch found no site within1.0 mm of the new U11-side signal via, and31 sites within1.5 mm at a minimum0.175 mm foreign-copper gap on all four layers. A stronger-margin example is **(105.65,36.05)**: distance1.457737973711 mm, minimum foreign-copper gap0.20 mm. The closest screened site is(105.65,36.075), distance1.432872988091 mm, minimum gap0.175 mm. No stitch has been added. These are placement screens only; a chosen stitch still needs native DRC/refill, material, drill/reference and connectivity checks.

All reported return geometry is nominal. No field solve, measured impedance, edge-rate/EMI assessment, environmental or hardware stability test has been performed. Neither the3.648 mm transition nor a proposed closer stitch is called SI-qualified.

## Recommendation

- **Strict exact-no-loss gate:** do not pass or select this trial under that gate. The +4V_LED old-shadow boundary genuinely changes, and native plane-only residues remain explicit. The modified EXT_GPIO3 transition is also an intentional geometry change, not a preservation identity.
- **Unqualified prototype development:** the bounded local reroute is a defensible candidate for an explicit, case-specific development decision after the parent’s independent review. It closes one more net component, retains every old material connection, preserves all unrelated pad partitions, confines the planned EXT_GPIO3 return change to its moved transition, and removes the new GPIO24 route’s avoidable reference gaps. The unrelated track-boundary shift is quantitatively below one serialized coordinate unit, rather than silently rounded to zero.
- Keep the stitch as a separate next experiment. Its screened site is not yet a fabricated or electrically qualified return path. Preserve26b as the fallback and retain both held predecessors. No additional board change is included in this packet.
