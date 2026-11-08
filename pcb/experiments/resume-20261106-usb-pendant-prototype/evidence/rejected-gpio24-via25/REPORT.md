# GPIO24 via relocation / GPIO25 closure: rejected prototypes

## Decision

No candidate is selected. Native routing improves 9 opens to 8, but the primary prototype has genuine remote represented-plane loss outside the frozen transition envelopes. No area tolerance, fill editing or window enlargement is used to accept that loss. The source remains unchanged.

Primary candidate: candidate/pcb/maru60.kicad_pcb
Source SHA256: 88fbac1d15c3ad320bcdd8af3a6f7c8293da39342bb8869d71cfed406ce44d5e
Primary candidate SHA256: 42bfe0e9f19637b1e6a65c6887e5455d70419ced716f6df60064d7f6c8c73239
Source commit: fa96a7c8b334f0f496ab7cdb4de9b18cf9276966.

## Exact edit scope

- Move GPIO24 through-via79e90551-63f2-4d3a-82a7-9d5d6259c3d6 from(105.8,37.5) to(105.7,37.525). Diameter0.50mm on all four copper layers; drill0.25mm, preserved and natively asserted.
- F.Cu track b9d330ac-1b1c-42cf-989e-7a81dbfe810a retains its exact original launch from(104.35,38.0) to(105.51,37.6), then a new0.15mm segment reaches the moved via.
- B.Cu track27d5bab5-97b2-409f-970d-ef67b5e0bc6a retains its exact original launch from(106.275,36.9) to(105.99,37.26), then a new0.15mm segment reaches the moved via.
- New GPIO25 vias at(93.925,40.175) and(98.15,40.6), both0.50/0.25mm;0.15mm trace route joins J3.6 to U11.15 through B/F/B layers. Full path is in qa/FROZEN_SCOPE.json.
- No pad/component moves, rule/width changes, other foreign-net edits, or copper deletion. Raw parsed scope proves exactly3 modified source objects and19 additions; all other source geometry and all57 companion files are identical.

## Passing checks on primary prototype

- Native DRC first gate:9→8 opens; all39 warning records exactly unchanged; no new shorts/clearances; parity0.
- Fresh corrected all-through-hole material graph: only intended U11.15/J3.6 GPIO25 pad-component merger; U13.11 remains separate. GPIO24 J3.5/U11.16 stays connected.
- Every unchanged material node remains present; no retained material-root split; no retained positive material-contact edge lost.
- Both external contacts of modified GPIO24 scope remain positive. The F.Cu opposite-end guarded overlap remains exactly0.01767886605mm²; B.Cu remains positive at0.017732740211mm² (source0.017732655183mm²).
- All pad-net identities match; raw/native/load/connectivity net identity checks pass across1,064 schematic nodes.
- ERC0; all58 cold-refilled unit files byte-identical.
- Source51 guarded-contact diagnostics are exactly unchanged, not native warnings and not resolved.

## Rejecting exact remote-plane witnesses

A native plane-difference screen shows five contours outside the frozen455µm transition disks on each inner plane, totaling8.1866e-08mm² per plane. Every physical through-hole was checked: none intersects these remote residuals.

Native Boolean subtraction can create artifacts, so the final rejection does not rely on that area alone. Exact Fraction-based ray classification against the source and candidate's serialized native filled contours finds four strict sample points per plane that are inside source copper and outside candidate copper. All four are also explicitly off both source and candidate boundaries. Thus genuine represented loss exists on both In1.Cu and In2.Cu. One of the five Boolean contours has a centroid outside both fills and is not counted as a genuine-loss witness.

Strict witness coordinates in integer-nanometre rational units:
- (275772281/3,113703281/3)
- (195288289/2,75336641/2)
- (206488289/2,75336641/2)
- (277542856/3,111982885/3)

See qa/rational-loss-strict.json and qa/outside-loss-allholes.json. These are remote from all declared old/new transitions. Their small size does not waive rejection. No claim is made that the Boolean total is the exact area of genuine loss.

## Transition-envelope audit and limitation

Before saving, fixed455000nm radius windows were declared separately for the old/new GPIO24 transition and the two new GPIO25 transitions. Source settings were asserted: via radius250000nm, inner-plane local clearance200000nm and native maximum polygon error5000nm. No window was subsequently enlarged.

The455µm radius was a conservative declared envelope, not an independently proved exact native-antipad union. The requested stricter450µm comparison was run and preserved in qa/outside-loss-allholes-450.json. It leaves0.0128161460585mm² /8 contours per plane, including the real local antipad overhang and the remote differences.

Observed native fill coordinates match the native outside polygon for radius450500nm at5000nm error, e.g.(450500,59309) relative to the via center. This explains why the ideal450µm circle is not an exact boundary of actual generated antipads. However, replacing the windows with the union of those reconstructed native polygons still leaves small local integer-contour residuals as well as the remote losses (qa/outside-native-antipads.json). Therefore this packet does NOT assert complete exact attribution of every450–455µm residual or an exact-antipad acceptance proof. The primary candidate is rejected independently for strict remote losses, so that incomplete attribution cannot confer acceptance.

## Reference-scan status

The exhaustive full-plane/all-outer-track script and the earlier full source-projection script did not produce completed reports. After rejection, the running analyses were interrupted and returned exit 130. They are incomplete, not passing. See qa/INCOMPLETE_SCANS.json. No all-track area/contour pass is claimed. Any future accepted candidate still requires every area AND contour row to be asserted, not a summary or area epsilon.

## Return-transition geometric witnesses

Nearest rooted GND through-via center distances:
- Moved GPIO24 transition:1.475847mm.
- J3 GPIO25 transition:0.778621mm.
- Bridge GPIO25 transition:3.651370mm.

The candidate material roots connect each listed nearest GND via to247 GND pads and the inner GND plane roots. This is a connectivity/distance witness, not a proof of signal integrity, impedance, return-current quality, EMI, crosstalk or hardware stability. The bridge transition's relatively long distance remains relevant for future review.

## Bounded follow-up variants

Two isolated25µm placement variants preserve all original departure lines and the entire GPIO25 route:
- variants/via24-left025: GPIO24 via(105.675,37.525), hash c80ac9a2b6462826f42ea08cdcec925336c947bdb0a77f2ca1383d272a73689f.
- variants/via24-down025: GPIO24 via(105.7,37.55), hash356776dfd5e50205572837e5dcaa4005996875ce04b0469dbdb1f5139b7df26b.

Each has its own frozen scope and native-gate evidence. The left025 variant passes native DRC but has four strict remote-loss witnesses per plane. The down025 variant fails native DRC with three new GPIO24-via-to-GPIO25 clearance errors (0.1288,0.1346,0.1318mm versus0.15mm required); no later plane gate is run for it. Full expensive material/ERC/cold/reference reruns are intentionally not warranted for a variant rejected at the remote-plane gate. Consult DECISION.json for the final per-variant status.

No rejected candidate was selected. All failed geometry and negative evidence are preserved separately from the current prototype. No external publication, manufacturing or flashing occurred.
