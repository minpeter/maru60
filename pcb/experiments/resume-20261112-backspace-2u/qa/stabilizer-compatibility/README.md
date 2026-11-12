# 7U plate-mount stabilizer cross-check

The current 7U plate opening has the expected Cherry-family **width and pitch**.
DUROCK and Gateron both offer plate-mount products with 7U wires, in addition
to the selected Designer Studio product. That supports using a common mounting
pattern; it does not establish that every housing clears every corner or that
all clips hold every plate thickness. No physical parts were tested.

| Product | Retrieved evidence | Assessment on this plate |
| --- | --- | --- |
| Cherry MX metal-frame 7U / G99-0379 reference | Manufacturer dimensioned drawing, archived by SparkFun | Main width and pitch are in tolerance; original INKC corner profile differs. Full profile/physical fit unqualified. |
| DUROCK Plate Mount | Kinetic Labs specifies plate mount and choice of 6.25U/7U wire | Same mounting category and correct wire option; no product-specific dimension drawing or clip thickness range in retrieved description. |
| Gateron Plate Mount V2 | Kinetic Labs specifies plate mount and includes a 7U wire | Same mounting category and correct wire option; no product-specific dimension drawing or clip thickness range in retrieved description. |
| Designer Studio Stabilizer (For Plate) | GEONWORKS assembly guide and 6.25U/7U component selection | Correct mounting category; wire below plate. Product-specific dimensions remain unprovided. |

Sources and exact evidence are in [sources.json](sources.json). The supplied
Designer Studio images are archived in [the adjacent source directory](../designer-studio/source.json).

## CAD measurement and reference

[Geometry report](geometry.json) is computed from the **delivered DXF**, whose
SHA256 is recorded. [Cherry PDF](cherry-mx.pdf), PDF page 3 / printed 10-4,
gives dimensions in inches:

| Dimension | Current plate | Cherry drawing, converted to mm |
| --- | --- | --- |
| Main housing opening width | 6.6500 mm on both sides | 6.6548 ± 0.1016 mm |
| Housing center-to-center pitch | 114.3000 mm | 114.3000 ± 0.1016 mm |
| Main opening tangent-line span | 12.3000 mm in original INKC data | 12.2936 ± 0.1016 mm |
| Frame thickness | Case design nominal 1.5 mm; actual manufacture not measured | 1.5240 ± 0.1016 mm in the MX metal-frame drawing |

The historical Cherry thickness band includes nominal 1.5 mm and nominal
1.6 mm. It does **not** guarantee a supplier's FR4 thickness tolerance or the
clip ranges of Designer Studio, DUROCK or Gateron. Prefer the case's nominal
1.5 mm stack and confirm the actual manufactured thickness and clip engagement.
A PCB-thickness choice on a PCB-mount stabilizer is a different specification.

## Corner shape finding

The original INKC plate uses rounded routing relief. Cherry's drawing calls
out maximum 0.012 inch (0.3048 mm) corner radii. Placing a 6.65 × 12.3 mm
rounded-rectangle aperture probe with that radius on the INKC housing tangent
lines leaves about **0.1062 mm² per housing** outside the actual opening.

This is a **screening discrepancy**, not a measured collision: the probe is not
a manufacturer's plastic housing, and the complete Cherry datum/profile was
not reconstructed. It prevents claiming full drawing conformity just because
the width and pitch match. Do not arbitrarily enlarge the whole opening:
that may compromise clip retention. Check the actual housing's corner relief
and clip retention on a plate sample before committing to a production batch.
The PCB and plate were not changed as part of this comparison.

The remaining practical checks are insertion/removal, secure clip engagement,
free return of the 7U key, wire travel, and clearance between housing/wire and
PCB components through gasket movement. These findings apply only to the
**7U spacebar**. The separate 2U Backspace candidate still uses a PCB-mount
stabilizer assumption.

Reproduce the dimensional screen from repository root:

```sh
.venv/bin/python pcb/tools/check_plate_stabilizer_reference.py build/stabilizer-reference.json
```

A zero exit code means the two checked dimensions pass and the original INKC
7U cutout is preserved. It does not mean all brands or the corner probe pass;
`all_products_qualified` remains false.
