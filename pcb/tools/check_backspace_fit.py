#!/usr/bin/env python3
"""Nominal case clearance for the 2U Backspace changes (not a physical fit test)."""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import trimesh
import check_mechanical_fit as fit


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("board", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    raw = args.board.read_bytes()
    fps = fit.parse_footprints(raw.decode())
    by_ref = {f["ref"]: f for f in fps}
    meshes = fit.load_case_meshes("maru60-hhkb-bottomcase-j3-relief", fit.BOTTOMCASE_DRAFT, "bottom")
    fit.RELOCATED_REFS = ["R189", "R190", "R191"]
    resistors = fit.check_relocated(fps, meshes, 9)["parts"]
    hardware = []
    # A deliberately conservative 2 mm below-board envelope for receptacle
    # tails and stabilizer fasteners. Supplier dimensions remain a fit gate.
    for ref in ("SW14", "SW15"):
        f = by_ref[ref]
        for pad in fit.blocks(f["block"], "pad"):
            if not re.search(r'\(pad "[12]" thru_hole', pad):
                continue
            at = re.search(r'\(at ([-\d.]+) ([-\d.]+)', pad)
            dx, dy = fit.rotate_xy(float(at[1]), float(at[2]), f["rot"])
            hardware.append((f"{ref} receptacle", f["x"]+dx, f["y"]+dy, 1.25))
    assert len(hardware) == 6, "expected six receptacle lands"
    for x in (254.3845, 278.2605):
        for y in (2.21375, 17.45375):
            hardware.append(("stabilizer fastener envelope", x, y, 2.5))
    rows = []
    for label, x, y, radius in hardware:
        wx, wy = fit.sample_rect_world(x-radius, y-radius, x+radius, y+radius, 9)
        surf, hit = fit.ray_surface_zp(meshes, wx, wy)
        free = float(np.min(surf[hit])) - (fit.BOARD_BOTTOM_ZP + fit.GASKET_TRAVEL) if hit.any() else None
        # A missing downward ray can be a case opening, not a collision.
        # Test the complete swept solid, including 0.5 mm clearance on its
        # sides and below, against both case halves instead of waiving misses.
        ex, ey = fit.sample_rect_world(x-radius-.5, y-radius-.5, x+radius+.5, y+radius+.5, 2)
        z0 = fit.BOARD_BOTTOM_ZP
        z1 = z0 + fit.GASKET_TRAVEL + 2.0 + .5
        box = trimesh.creation.box(extents=[np.ptp(ex), np.ptp(ey), z1-z0])
        box.apply_translation([np.mean(ex), np.mean(ey), (z0+z1)/2])
        volumes = []
        for entry in meshes:
            transformed = box.copy()
            transformed.vertices = box.vertices @ fit.bc.TO_PRINT[:3, :3].T + fit.bc.TO_PRINT[:3, 3] + entry["tbed"]
            overlap = trimesh.boolean.intersection([transformed, entry["mesh"]], engine="manifold")
            volumes.append(float(abs(overlap.volume)))
        collision_volume = sum(volumes)
        rows.append({"item": label, "board_mm": [x, y], "assumed_below_board_mm": 2.0,
                     "sample_box_half_size_mm": radius, "hit_fraction": float(hit.mean()),
                     "clearance_mm": round(free-2.0, 4) if free is not None else None,
                     "clearance_envelope_intersection_mm3": collision_volume,
                     "pass": collision_volume < 1e-6 and (free is None or free-2.0 >= .5)})
    report = {"board": str(args.board), "board_sha256": hashlib.sha256(raw).hexdigest(),
              "scope": "Nominal swept-solid clearance over 0.8 mm gasket travel, with 0.5 mm side/bottom margin; no hardware measurements",
              "case": "models/maru60-hhkb-bottomcase-j3-relief-{left,right}.3mf",
              "resistors": resistors, "hardware_envelopes": rows,
              "pass": all(r["status"] == "pass" for r in resistors) and all(r["pass"] for r in rows),
              "limitations": "Receptacle fit, switch seating and actual stabilizer/fastener dimensions require a physical coupon. The 2 mm protrusion envelope is an assumption, not a Mill-Max specification."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"pass": report["pass"], "resistors": len(resistors), "hardware_envelopes": len(rows)}, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
