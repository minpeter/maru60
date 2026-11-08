# MCU northern escape: rejected partial C, continuation paused

**No MCU pair was closed. C is unselected and rejected by native clearance checks.** Its material and adjacent-reference results are useful bounded evidence, but they do not override four hard DRC errors. No SI, EMI, active power-stability, manufacturing or hardware pass is claimed.

## Source and frozen files

- Prototype source: `source/pcb/`, copied from `../../combined-trial/pcb/`.
- Source PCB SHA256: `56d66f65bb1f30d6ec7860f398cfd4f2399f3a9d305ef80d4bebab721d2571d9`.
- Frozen rejected C: `frozen-C/pcb/`; working equivalent: `north-escape-c/pcb/`.
- C PCB SHA256: `ebf7bdb8556158df3f6c6c63ed985dec18a34ca709a6175d69efbde93389e634`.
- Earlier failed partial A: `north-escape/pcb/`, SHA `30aa174b1083c0b166daafaa831a7dd8986a0852b94eb18b69aba82c1d25533c`.
- Earlier failed correction B: `north-escape-b/pcb/`, SHA `c7d3bac1e8c77ee4e48f4d753ae3b9e982fa9572f7a1d78b143ac7518a33c4da`.

The c782 prototype source, stricter 04be baseline, previous wide10b rejection and other experiment branches remain unchanged. This MCU partial was not merged into the newer header/stitch/label checkpoint.

## C native result: FAIL

- 10 open pairs remain, exactly the source count.
- 51 warnings: the original 50 plus an intentional single-layer MCU_GPIO27 launch-via warning.
- **4 hard clearance errors**, all between the shifted +1V1 rail and existing LED_FAULT_N tracks. Required clearance is 0.1500 mm; measured gaps are 0.1050 mm on three reports and 0.1223 mm on one.
- Affected LED_FAULT_N tracks: `b995c2c7-f443-497b-bb80-da0d3312d10d` and `f6f5406e-c528-4d4f-a9d3-6a7ddc1ae774`, around (110.8,75.45–76.05).
- Schematic parity: 0. Fresh ERC: 0.
- Raw/native Load/Build net identities and all 1,064 schematic XML pin bindings match.
- Cold refill is byte-identical. All 57 companion files remain exact.

C’s hard-error severity breakdown was identified during final aggregation after the read-only continuation screen. No long-route PCB was produced. Future variants must pass a full severity/category count before deeper return-path or continuation work; any new electrical or clearance error is reported immediately. Do not interpret passing material/reference checks below as a native DRC pass.

## Declared changes

This experiment tried MCU_GPIO27’s north-side escape rather than repeating the failed GPIO10 entry.

- Move the existing COL5 through-via from (112.35,76.80) to (112.175,76.30), retaining its UUID, net, 0.50 mm diameter and 0.25 mm drill.
- Adjust three incident COL5 tracks and add one B.Cu link plus a 0.175 mm In1.Cu link. Signal width stays 0.15 mm. No new In2 signal is added.
- Add a 0.15 mm B.Cu launch from U1 pad41 at (112.2,78.05) to a new MCU_GPIO27 through-via at (112.16,77.0), diameter 0.50 mm / drill 0.25 mm. There is no F.Cu continuation or connection to the expansion component.
- Refactor one +1V1 F.Cu rail: retain both original endpoint vias at (111.4,75.7) and (111.4,79.3505), retain 0.60 mm width, and move the middle to x111.28 with short endpoint legs. This 0.12 mm shift fixes the rail’s reference deficit but introduces the clearance errors above.

C has 9,763 tracks, 922 vias, 383 footprints and 13,204.538596839022 mm summed track length. Relative to source: five added tracks, one added via and 1.561303022128 mm added summed length. Five source objects change, all declared; all other raw source objects and footprints remain exact.

The +1V1 path changes from 3.6505 to 3.749911254969543 mm, a 0.099411254969543 mm increase. Its physical copper union removes 0.3977095282385 mm² and adds 0.4534838452705 mm². No impedance, current-capacity or stability inference is made from these numbers.

## Material and power-branch checks

The corrected all-through-drill material exporter completed on C’s actual file.

- All named pad partitions are unchanged, including all ten +1V1 pad bindings: TP5, C110, L1, C103, C108, C109 and U1 pins 6/23/39/50.
- All 247 original GND pads retain J1’s material root.
- No unmodified object material changes or unmodified-root splits occur.
- No unrelated accepted edge or witness changes occur.
- One old COL5 incident edge is retired and replaced by the new link; five declared incident witnesses change. The 51 inherited guarded-contact rejections remain unchanged.
- The two power endpoint vias retain their geometry and identity. New 0.60 mm endpoint capsules are centered exactly on the unchanged 0.60 mm via disks, preserving full annular coverage by primitive containment. Separately polygonized union calculations report tiny 4.78795e-08 and 5.6933e-08 mm² differences; these raw diagnostics are retained rather than described as byte-exact contact witnesses.

## Whole-plane and adjacent-reference checks

All physical through-drills are subtracted, with no Unfracture. All 12,857 source signal-layer projections are examined. Both planes remain one physical component.

- In1: loss 0.4863510432655 mm², gain 0.130372431028 mm².
- In2: loss 0.733131710302 mm², gain 0.129225117366 mm².
- Real loss outside the two nominal 0.455 mm transition envelopes remains: 0.038611251318 mm² on In1 and 0.0370067392085 mm² on In2. Each includes a remote 4.586e-08 mm² boundary difference near x90.58–90.69/y76.60–76.63, recorded without a tolerance waiver.
- No retained source conductor loses its actual adjacent reference: F.Cu→In1, B.Cu→In2. Far-plane-only changes and retired/modified source shadows remain listed separately.
- Every new or modified track has zero uncovered adjacent-plane projection outside its own declared signal-via transitions. The short COL5 In1 segment uses In2 as its reference.

The local web changes are not concealed by the global component count. In the smallest local clip, In2 has two components; analytically restoring only the outside-envelope loss reconnects them. Larger clips remain connected, demonstrating an alternate route around the lost local shortcut, not preservation of that shortcut.

Native capsule witnesses wholly contained in actual existing ground copper establish these alternative corridors:

- MCU_GPIO27 B-reference point (112.175,77.55) to existing GND via (114.85,77.65): 2.40 mm path, verified 0.15 mm corridor width.
- COL5 B-reference point: 2.061396103068 mm path, verified 0.15 mm corridor.
- COL5 In1-reference point: 2.344238815543 mm path, verified 0.20 mm corridor.
- Modified +1V1 F-reference point: 3.263172798365 mm path, verified 0.20 mm corridor.

These are continuous existing-metal witnesses with positive endpoint-annulus overlap after 2 nm inward guards. They are not measured current paths, global maximum web widths, or SI/power qualification. Nearest existing GND-via center distances are 2.767417568781 mm from the MCU launch and 2.996351948620 mm from the relocated COL5 via. A real F.Cu continuation and its transition return are still absent.

## One finite continuation search

On C, the F/B search covered x110.01–140.01 / y32–78.5 at 0.05 mm spacing, using each outer layer’s actual nearest reference. Via screening used a 0.456 mm source-shadow exclusion radius plus a stronger 0.655 mm plane-boundary screen (0.455 mm antipad plus 0.20 mm nominal web). These are screening heuristics, not substituted design rules or proof that native fill is safe.

The search visited 1,842 F.Cu vertices, reached x111.81–116.06 / y76.5–78.5, and reached no B.Cu vertex or expansion pad. Even before the stronger plane-web screen, no sampled second-via site in the reachable F.Cu pocket met the source-shadow screen and both layer masks. The search reaches its southern boundary, so it does not prove impossibility. An identical read-only diagnostic repeat captured the frontier; it was not another geometry variant.

## Specific next layout decision

Do not reuse C unchanged: the +1V1/LED_FAULT_N clearance conflict must be resolved first. The measured interaction is localized around the two LED_FAULT_N tracks listed above; a shaped power-rail jog or bounded LED_FAULT_N reroute must satisfy both clearance and the measured In1 boundary, not merely shift the entire rail farther left.

For continuation, either explore south of y78.5 or redesign the local LED_FAULT_N F.Cu staircase and nearby transition/decoupler corridor. The staircase runs from (113.7,77.05) through (115.1,77.05) toward (116.2,77.55), alongside existing GND vias at (114.85,77.65) and (115.9,78.4), with the actual crystal-related plane keepout nearby. Opening a referenced passage here is a broader local layout task; no successful placement change is asserted.

Further MCU variants and searches are paused. Any later successful route must be composed onto the new frozen source base and rechecked after actual fill. This packet makes no selection, production or firmware change.

## Evidence

`qa/north-escape-c-{drc,erc,net-identity,native-checks,material-comparison,return,power-geometry,power-endpoint-proof,local-neck,ground-corridors,ground-corridors-native}.json` contain the source-bound checks. The full corrected material graph and native logs are retained. `qa/gpio27-continuation-search-initial.json` and `gpio27-continuation-frontier.json` record the finite search. `scripts/` retains the executed implementations; the interrupted first global-shadow diagnostic is explicitly named and has no acceptance result.
