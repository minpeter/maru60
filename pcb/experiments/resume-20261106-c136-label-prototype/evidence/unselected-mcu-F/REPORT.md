# LED staircase repair F: checked partial launch, unselected

**The local rail-clearance/reference conflict is repaired in this one candidate. No complete MCU pair is connected. F is not selected or merged.** Nine open pairs remain; a full GPIO27 route, its eventual layer-transition return and independent review remain absent. This is nominal geometry evidence, not SI, power-stability, current-capacity, hardware or manufacturing approval.

## Exact source and frozen candidate

- Source: `source/pcb/maru60.kicad_pcb`, SHA256 `9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed`.
- Candidate: `candidate-F/pcb/maru60.kicad_pcb`, SHA256 `fb227c9af1b2c520452fee6815fdfecf6c44f7a42f090d432e5293fd3538d434`.
- All 58 original checkpoint files remain unchanged. Rejected C, D and E hashes were rechecked and remain unchanged. F was reconstructed from the immutable source plus explicit changes, not made by overwriting a rejected board.

## Read-only assessment and concrete repair

A source-bound inventory covers x109.7–111.9/y74.7–76.8, including 40 nearby track/pad/via objects and all actual filled zones. Nearby foreign copper includes RUN on F.Cu, the +1V1 through-via at (111.4,75.7), C110/C113 on B.Cu and +3V3 B.Cu routing. F.GND fill has 0.15 mm clearance; the adjacent In1 GND zone has 0.20 mm clearance. F.GND fill was not assumed immutable or harmless to remove.

Three intermediate LED_FAULT_N staircase vertices shift left exactly 0.10 mm. Four existing 0.15 mm F.Cu tracks are retargeted; their outer endpoints remain fixed:

- (110.9,75.35) → (110.7,75.45)
- (110.7,75.45) → (110.7,75.95)
- (110.7,75.95) → (110.6,76.05)
- (110.6,76.05) → (110.7,76.149999)

The prospective fixed-copper clearance screen found a minimum 0.205343124445 mm gap to the E-shaped rail, versus the 0.15 mm rule; all four new LED segments had complete In1 coverage. Native checks below then used the actual saved/refilled candidate.

The 0.60 mm +1V1 rail retains both original endpoint vias at (111.4,75.7) and (111.4,79.3505), with its upper jog ending at (111.28,76.17), middle at x111.28, and short lower endpoint leg. All decoupler/pad branches and component positions are unchanged.

The candidate also contains the declared partial-launch experiment: relocate the 0.50/0.25 mm COL5 via from (112.35,76.8) to (112.175,76.3), adjust three incident COL5 tracks, add a 0.175 mm In1 link and one B.Cu link, and add a 0.15 mm B.Cu MCU_GPIO27 launch from U1 pad41 (112.2,78.05) to a new 0.50/0.25 mm via at (112.16,77.0). There is no new In2 signal corridor and no F.Cu continuation.

## Native and identity gates

Full native DRC severity/category checks ran before deeper tests:

- **9 open pairs, 43 warnings, zero other hard errors, parity 0.** No clearance/short error remains.
- Warnings: 15 text-height, 13 silk-over-copper, 10 silk-overlap, 4 dangling-track, 1 dangling-via. The source's 42 warnings are exactly retained; the new warning is the intentionally unfinished MCU_GPIO27 launch via.
- Fresh ERC: 0. Raw/load/build net identities pass for 12,141 conductive objects and all 1,064 schematic pin bindings.
- Cold load, connectivity build, refill and save preserve all 58 candidate files byte-for-byte; refill approximately 2.67 seconds.
- Nine existing conductive objects change, all declared. Five tracks and one via are added. All other raw source objects are exact apart from recomputed fills; no footprints, netlist or rules change.

## Full material and contact checks

The corrected all-through-hole material exporter completed on F's exact file.

- Complete pad inventory and every named pad partition are unchanged. The nine physical open-component pairs exactly match the source.
- All 247 GND pads remain on the J1 material root; all ten +1V1 pad bindings remain on one root.
- No unmodified object material changes, unmodified-root splits, unrelated accepted-edge loss or unrelated witness changes occur.
- Two declared incident source edges retire: the COL5 connection remapped through its new link and a redundant LED same-net shortcut. Fourteen declared incident witnesses change. This is an intentional refactor, not exact old-contact identity.
- Both fixed LED terminal contacts remain positive after 2 nm inward guards. Their total overlap increases, but raw old-minus-new patch differences of 2.35845e-08 and 9.5165e-09 mm² remain recorded. The removed redundant LED shortcut previously had 0.000287564968 mm² overlap; its net's pad partition is unchanged.
- The original power endpoint vias keep their geometry. Exact integer endpoints and equal 0.60 mm capsule/via diameters establish full annular containment by primitive geometry. Separately polygonized overlap diagnostics retain 2.70661e-07 and 5.6933e-08 mm² old-patch differences; they are not erased or called byte-identical contacts.
- All 51 inherited guarded-contact diagnostic failures remain exactly unchanged. They are distinct from the 43 native warnings and preclude calling this full electrical certification.

## Actual reference, plane changes and local returns

All physical through-holes are subtracted; no Unfracture is used. All 12,876 source signal-layer shadows were checked. Actual adjacent references are F.Cu→In1 and B.Cu→In2; the short COL5 In1 segment is checked against In2.

- No retained, unmodified source conductor loses its nearest reference.
- Every one of the 13 new/modified track checks has zero uncovered adjacent-plane area outside its own unchanged transition envelopes. The four moved LED tracks have zero uncovered area even before an exception.
- Full-board physical zone changes are retained, including outer layers:
  - F.Cu GND: loss 1.0707921261125 / gain 0.352935532797 mm²; 9 components remain 9.
  - In1 GND: loss 0.4863510432655 / gain 0.130372431028 mm²; 1 component remains 1.
  - In2 GND: loss 0.733131710302 / gain 0.129225117366 mm²; 1 component remains 1.
  - Main B.Cu +3V3 pour: loss 0.923284476239 / gain 7.5305e-09 mm²; 6 components remain 6. Original power tracks and pad partitions remain preserved, but this is not a current-capacity qualification.
  - Other source filled zones have no physical area changes.

**Real inner-plane web loss remains.** Outside the two nominal 0.455 mm transition windows, In1 loses 0.038611251318 mm² and In2 loses 0.0370067392085 mm². These include a remote 4.586e-08 mm² boundary difference, preserved without waiver. The smallest local In2 clip loses a shortcut; wider clips retain an alternate route. A global one-component count is not substituted for local analysis.

Five representative existing-ground corridors were freshly reconstructed on F and independently checked using native outside-rounded capsules wholly within actual drilled copper, with positive 2 nm guarded overlap onto GND annuli whose roots match J1:

- GPIO27 B-reference: 2.400000 mm long, verified width 0.15 mm, measured minimum available path corridor 0.199000 mm.
- COL5 B-reference: 2.061396 mm, width 0.15 mm, available corridor 0.193964 mm.
- COL5 In1-reference through In2: 2.344239 mm, width 0.20 mm, available corridor 0.242441 mm.
- Modified +1V1 F-reference: 3.263173 mm, width 0.20 mm, available corridor 0.213342 mm.
- Modified LED F-reference: 2.275000 mm, width 0.20 mm, available corridor 0.242441 mm.

These are chosen continuous-metal witnesses, not measured current paths, globally widest webs or SI/power qualification. The nearest existing GND-via center distances are 2.767418 mm from the GPIO27 launch and 2.996352 mm from relocated COL5. An eventual F/B signal transition and its return are still unqualified.

## Length and copper accounting

- +1V1: 3.650500 → 3.715282940910 mm (+0.064782940910); width 0.60 mm. Copper removed/added: 0.385220973305 / 0.4220951058185 mm².
- Four LED tracks: 0.882841712475 → 1.006448803120 mm (+0.123607090645); width 0.15 mm. Copper removed/added: 0.062057239332 / 0.079270660434 mm².
- Candidate: 9,778 tracks, 924 vias, 383 footprints, 13,212.459481491958 mm summed track length. Relative to source: +5 tracks, +1 via and +1.650281798713 mm; no component placement change.

## Evidence and acceptance limits

`FINAL.json` is the asserted validation ledger. `qa/read-only-assessment.json` and `read-only-local-zones.json` preserve the preflight inventory. The `qa/candidate-F-*` files contain native checks, raw net identity, material graph/comparison, all-zone changes, nearest-reference analysis, exact modified LED/power contacts, local neck topology and native corridor witnesses. `scripts/` preserves executable checks. An initial unbounded read-only geometry scan was interrupted and replaced with a conservative native-bounding-box prefilter; it did not save any PCB or produce an acceptance result.

The checks above support only a bounded partial-launch experiment with declared geometry/contact/pour changes. Strict unchanged-geometry and exact no-plane-loss acceptance are not claimed. All six MCU pairs remain open, along with one EXT_GPIO24 and two EXT_GPIO25 header pairs. No independent reviewer has accepted F, and no selection or merge has occurred. No install, external push, purchase, fabrication or flashing occurred.

## Read-only next-route assessment: F does not open the former pocket

A bounded static comparison, with **no route search or CAD mutation**, compares rejected C with F inside the former reached bounding box x111.81–116.06/y76.5–78.5. Using the prior screen parameters, the F/B obstacle and reference-mask geometries are exactly identical within this box. All 3,526 sampled cells per layer at 0.05 mm spacing have unchanged track and via masks. The diagonal LED_FAULT_N barrier from (111.9,75.25) to (113.7,77.05), nearby GND vias at (114.85,77.65)/(115.9,78.4), and the actual plane boundaries remain unchanged there.

There are 20 screened via sites within the bounding box in both C and F, concentrated at x115.46–116.06/y76.50–76.60. They are not newly created by F and were not reached in C's prior search. A bounding box includes disconnected pockets; these 20 sites do not contradict the prior zero **reachable** via-site result. Exact sites are recorded in `qa/read-only-old-pocket-assessment.json`.

F therefore repairs the power/LED conflict but supplies no evidence of a new exit. A materially different next step would inspect the previously unsearched exterior south of y78.5, or examine access across/around the unchanged eastern LED staircase toward those northern transition sites, with the ground-via and crystal-plane constraints rechecked. No such reroute, southern search or additional candidate was attempted. This is not a claim that an unbounded route is impossible. F remains based on 9d787421 and is not composed into the newer C136-only checkpoint.
