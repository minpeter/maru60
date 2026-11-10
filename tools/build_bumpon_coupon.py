"""Fit coupon for the 3M Bumpon SJ5012 pockets of both cases, at the design diameter and two tighter trials.

Top row: pockets open upward, as in the top case (wrist-rest pads face up on the print bed's far side). Bottom row:
pockets open on the bed face, as in the bottom case (printed desk face down), so they see elephant-foot compensation
and a bridged pocket floor. Columns from left: design diameter minus 0.6 / minus 0.3 / design (`POCKET_D`), marked by
one, two and three notches on the front face. All pockets are `POCKET_DEPTH` deep. Writes to build/bumpon-coupon/.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

import manifold3d as md

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_topcase_draft as top  # noqa: E402
from maru60.mesh_io import to_trimesh, write_3mf  # noqa: E402

PITCH = 18.0
EDGE = 3.0
THICK = 4.0
NOTCH_W, NOTCH_D, NOTCH_GAP = 1.0, 0.8, 1.0
DIAMETERS = [round(top.POCKET_D - 0.6, 2), round(top.POCKET_D - 0.3, 2), top.POCKET_D]


def pocket(d: float) -> md.Manifold:
    r = d / 2 / math.cos(math.pi / 72)
    return md.Manifold.cylinder(top.POCKET_DEPTH + 1.0, r, r, 72)


def build() -> md.Manifold:
    w, h = 3 * PITCH + 2 * EDGE, 2 * PITCH + 2 * EDGE
    block = md.Manifold.cube([w, h, THICK])
    cuts = []
    for i, d in enumerate(DIAMETERS):
        cx = EDGE + PITCH * (i + 0.5)
        cuts.append(pocket(d).translate([cx, EDGE + PITCH * 0.5, -1.0]))
        cuts.append(pocket(d).translate([cx, EDGE + PITCH * 1.5, THICK - top.POCKET_DEPTH]))
        for k in range(i + 1):
            x = cx + (k - i / 2) * (NOTCH_W + NOTCH_GAP) - NOTCH_W / 2
            cuts.append(md.Manifold.cube([NOTCH_W, NOTCH_D + 1.0, THICK + 2.0]).translate([x, -1.0, -1.0]))
    return block - md.Manifold.batch_boolean(cuts, md.OpType.Add)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "build/bumpon-coupon/maru60-bumpon-coupon.3mf")
    args = ap.parse_args()
    coupon = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_3mf(args.out, "Maru60 SJ5012 bumpon pocket coupon", [("BumponCoupon", to_trimesh(coupon))], fine_layer_z=None)
    b = coupon.bounding_box()
    print(f"{args.out.relative_to(ROOT)}: {b[3] - b[0]:.1f} x {b[4] - b[1]:.1f} x {b[5] - b[2]:.1f} mm, "
          f"pockets d{DIAMETERS} x {top.POCKET_DEPTH} deep, genus {coupon.genus()}")


if __name__ == "__main__":
    main()
