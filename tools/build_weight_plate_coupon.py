"""Two-layer overlay coupon of the weight plate: its outline and screw holes, to lay on the real plate.

The sheet is the `back_deco_plate` outline at true size with the four `bottom.weight_plate_holes` cut at the bottom
case's clearance diameter (`DECO_SCREW_HOLE_D`, 3.0 mm). Lay it on the plate's inside face with the edges flush: if
every tapped hole sits inside its coupon hole (an M2 screw goes in through each one), the bottom case's screw holes
fit the plate. Outline and holes are mirror-symmetric, so either face of the coupon works.
Writes to build/weight-plate-coupon/ only; nothing is published.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import manifold3d as md
import shapely.geometry as sg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_bottomcase_draft as b  # noqa: E402
import rule60_spec as spec  # noqa: E402
from maru60.mesh_io import to_trimesh, write_3mf  # noqa: E402

LAYERS = 2
LAYER_H = 0.20  # The owner's 0.20 mm Standard profile; the first layer is 0.20 too


def build(thickness: float) -> md.Manifold:
    pts = spec.outline_points("back_deco_plate", arc_steps=24)
    poly = sg.polygon.orient(sg.Polygon(pts))
    sheet = md.Manifold.extrude(md.CrossSection([list(poly.exterior.coords)[:-1]]), thickness)
    r = b.DECO_SCREW_HOLE_D / 2
    holes = [md.Manifold.cylinder(thickness + 2.0, r, r, 64).translate([x, y, -1.0])
             for x, y in spec.value("bottom.weight_plate_holes")["holes"]]
    coupon = sheet - md.Manifold.batch_boolean(holes, md.OpType.Add)
    return coupon.translate([-b.DECO["bbox"][2] / 2, -b.DECO["bbox"][3] / 2, 0.0])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "build/weight-plate-coupon/maru60-weight-plate-coupon.3mf")
    args = ap.parse_args()
    coupon = build(LAYERS * LAYER_H)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_3mf(args.out, "Maru60 weight-plate overlay coupon", [("WeightPlateCoupon", to_trimesh(coupon))],
              fine_layer_z=None)
    lo, hi = coupon.bounding_box()[:3], coupon.bounding_box()[3:]
    print(f"{args.out.relative_to(ROOT)}: {hi[0] - lo[0]:.2f} x {hi[1] - lo[1]:.2f} x {hi[2] - lo[2]:.2f} mm, "
          f"genus {coupon.genus()}, holes d{b.DECO_SCREW_HOLE_D} at {spec.value('bottom.weight_plate_holes')['holes']}")


if __name__ == "__main__":
    main()
