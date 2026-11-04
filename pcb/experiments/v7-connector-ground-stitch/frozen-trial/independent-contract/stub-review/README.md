# Connector ground stub review

Selected board SHA-256: `c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a`.

## Finding

The F.Cu GND segment `bc0a06ab-785a-4a27-a164-9c3256c7f3bd`, from (15.7, 10.75) to (15.7, 9.8), is a 0.95 mm, 0.25 mm wide **grounded copper leaf**. It is neither floating nor a required connection between named GND pads. Keeping it can be a conservative no-change decision, but the available evidence does **not** prove that it is an effective guard, necessary return conductor, or ESD improvement.

## Material evidence

- Corrected R2 graph: `/tmp/v7-gnd-tail-cleanup-aead/qa/material-graph.json`, matching the selected board hash.
- Exact material helper: `pcb-v7-recovery-20261104/pcb/tools/export_material_graph.py`; the earlier wrapper/neighbor-hole models are not used.
- Stub has one positive F.Cu material component, area 0.237499592978 mm² after actual through-drill subtraction.
- Exactly one accepted graph contact: GND via `5a2cb39f-cff7-4876-a0b9-7db4a3b9b0bc` at (15.7, 9.8), diameter 0.5 mm, drill 0.25 mm.
- Contact area is 0.035244191822 mm² before guarding and 0.0352419640185 mm² after each component is independently guarded inward by 2 nm.
- Stub has no zone contact and no failed guard contact. Its material graph degree is one.
- Anchor via has a proved intact through barrel and accepted In1.Cu / In2.Cu GND-zone contacts, each with guarded overlap 0.1472558792225 mm². There is no accepted F.Cu or B.Cu zone contact at that via in this graph.
- Root is `object:0000af93-3d00-42f8-97ba-dc35153f7a15:0:0`, the common root containing all 247 named GND pads, including the connector and U10 protection IC.
- An explicit graph-only deletion of the stub's sole vertex leaves every material vertex of all 247 GND pads reachable. This is a topological counterfactual, not a changed/refilled board validation.

## Nearby connector/protection geometry

- J1 ground contacts A1/B12 are at (14.8, 7.48), A12/B1 at (21.2, 7.48), with grounded shell pads also on the main GND root.
- The stub lies to the left of the USB D+ and D− routing. It is not a grounded strip between the pair.
- U10 is labelled `TPD2EUSB30DRTR` in the board. Its GND pad 3 is at (18.5, 10.325) on B.Cu, with a separate 0.6 mm long, 0.2 mm wide B.Cu track to GND via (19.1, 10.325).
- Thus the retained stub is not the protection IC's necessary series ground connection. The root via and connected plane material must not be conflated with the leaf segment.

## Disposition

Do not delete this solely to make a generic dead-end warning disappear, and do not explain its retention as a *verified* guard or return-path benefit. Either retain it with the explicit limited rationale above, or assess an isolated removal through the same selected-board DRC, refill, all-hole material graph, and intended signal/ground checks. Nothing in this review establishes a mandatory reason to retain the **segment**; preserving a real ground **via/plane connection** is a separate decision.

No CAD edits were made. No electromagnetic, impedance, current, ESD, fabrication-tolerance or hardware claim is made. The 2 nm material guard is a geometric robustness check, not a manufacturing margin.

## Reproduce

Run `/usr/bin/python3 review_core.py` in this directory. The script verifies the selected board hash, reads R2, reconstructs canonical local copper with every through-hole subtracted, independently checks local F.Cu material contacts, records nearby USB/protection geometry, and writes `report-core.json`. It asserts that the board bytes remain unchanged. An optional exhaustive separation run (`review.py`) was stopped because it was unnecessarily expensive; it produced no result, and no numerical separation claim depends on it.
