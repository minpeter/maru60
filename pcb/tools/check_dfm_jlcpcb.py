#!/usr/bin/env python3
"""JLCPCB manufacturability checks that a DRC rule deck cannot express.

usage: .venv/bin/python pcb/tools/check_dfm_jlcpcb.py BOARD.json OUT.json

BOARD.json is the geometry dump (dump_board_geometry.py).  The rule-deck part of
the check is `qa/dfm-jlcpcb/maru60-jlcpcb.kicad_dru`, run with kicad-cli on a
copy of the project.  This script adds:

  a  via holes inside SMD pads (solder wicking)
  b  solder-mask web between neighbouring pads of the fine-pitch parts (the
     board's mask expansion is 0, so the web equals the copper gap)
  c  stencil area ratio of every paste aperture for 0.10 and 0.12 mm foils
     (aperture taken as the pad size)
  h  assembled parts closer to the board edge than JLCPCB's 2.5 mm
  i  fiducials and tooling holes present on the board

LIMITS holds the JLCPCB figures with the page each was read from on 2026-11-11.
Everything is computed from the board geometry.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

CAP = "https://jlcpcb.com/capabilities/pcb-capabilities"
ASM_TERMS = "https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service"
ASM_CAP = "https://jlcpcb.com/capabilities/pcb-assembly-capabilities"
TOOLING = "https://jlcpcb.com/help/article/how-to-add-tooling-holes-for-pcb-assembly-order"
RAILS = "https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order"
FAQ2 = "https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2"

# value (mm unless noted), source. "UNVERIFIED" = not found on a JLCPCB page that could be fetched.
LIMITS = {
    "track_width_min": (0.09, CAP + " (Min track/space, 1 oz, multilayer)"),
    "copper_space_min": (0.09, CAP + " (same row)"),
    "pad_to_track_min": (0.10, CAP + " (Pad to track clearance, 1 oz)"),
    "smd_pad_to_pad_min": (0.15, CAP + " (SMD pad to pad, different nets)"),
    "smd_pad_min": (0.25, CAP + " (Min SMD pad 0.25 x 0.25 mm)"),
    "same_net_gap": (0.25, CAP + " (Same-net track spacing)"),
    "via_hole_min": (0.15, CAP + " (Min via, multilayer)"),
    "via_hole_pref": (0.20, CAP + " (Preferred min via hole)"),
    "via_dia_min": (0.25, CAP + " (Min via diameter)"),
    "via_dia_no_surcharge": (0.45, CAP + " (0.2/0.25 mm hole with via diameter < 0.45 mm costs more)"),
    "via_annular_min": (0.05, CAP + " (Via diameter 0.1 mm larger than hole)"),
    "via_annular_pref": (0.075, CAP + " (0.15 mm preferred)"),
    "pth_annular_min": (0.15, CAP + " (PTH annular ring, multilayer 1 oz, absolute min)"),
    "pth_annular_rec": (0.20, CAP + " (same row, recommended)"),
    "pth_hole_rec": (0.50, CAP + " (Recommended min PTH size)"),
    "pth_tol": ("+0.13/-0.08", CAP + " (PTH hole tolerance)"),
    "npth_min": (0.50, CAP + " (Min non-plated holes)"),
    "npth_tol": ("+/-0.05 UNVERIFIED", "not stated on " + CAP + " on 2026-11-11; value is the long-standing JLC figure"),
    "plated_slot_min": (0.35, CAP + " (Min plated slot width, multilayer; remark on the page says 0.5)"),
    "plated_slot_rec": (0.50, CAP + " (remark of the same row)"),
    "plated_slot_len_ratio": (2.0, CAP + " (slot length >= 2 x width)"),
    "npth_slot_min": (1.0, CAP + " (Min non-plated slot width)"),
    "via_hole_to_copper": (0.20, CAP + " (Via hole to track)"),
    "pth_hole_to_copper_min": (0.28, CAP + " (PTH to track, minimum)"),
    "pth_hole_to_copper_rec": (0.35, CAP + " (PTH to track, recommended)"),
    "npth_to_copper": (0.20, CAP + " (NPTH to track)"),
    "inner_via_hole_to_copper": (0.20, CAP + " (Inner layer via hole to copper)"),
    "inner_pth_hole_to_copper": (0.30, CAP + " (Inner layer PTH pad hole to copper)"),
    "via_hole_to_hole": (0.20, CAP + " (Via hole-to-hole spacing)"),
    "pad_hole_to_hole": (0.45, CAP + " (Pad hole-to-hole spacing)"),
    "copper_to_edge_min": (0.20, CAP + " (Routed: copper clearance from edge / slots)"),
    "copper_to_edge_rec": (0.30, FAQ2 + " (traces and components > 0.3 mm from the edge; routing tolerance 0.2 mm)"),
    "outline_tol": (0.20, CAP + " (Routed edge tolerance, regular)"),
    "mask_dam_min": (0.10, CAP + " (Soldermask bridge, 1 oz, green/red/yellow/blue/purple: min pad spacing)"),
    "mask_dam_min_black_white": (0.13, CAP + " (same row, black/white)"),
    "mask_opening_to_trace": (0.09, CAP + " (Soldermask expansion remark)"),
    "plugged_via_to_opening": (0.35, CAP + " (Plugged vias: clearance from other mask openings)"),
    "silk_line_min": (0.15, CAP + " (Legend minimum line width)"),
    "silk_text_height_min": (1.0, CAP + " (Legend minimum text height 40 mil)"),
    "silk_to_pad": (0.15, CAP + " (Pad to silkscreen)"),
    "asm_body_to_edge": (2.5, ASM_TERMS + " (component body to board edge >= 2.5 mm; otherwise edge rails)"),
    "asm_rail_width": (5.0, RAILS + " (edge rails at least 5 mm)"),
    "asm_body_to_body": (0.3, "UNVERIFIED as a rule: JLCPCB blog figure only; " + ASM_TERMS + " says only 'IPC-7351B medium/low density, no overlap or very small gap'"),
    "asm_min_pitch_standard": (0.35, ASM_CAP + " (Standard PCBA minimum IC pin spacing)"),
    "asm_min_package_standard": ("01005", ASM_CAP),
    "asm_board_min": ("70 x 70", ASM_CAP + " (Standard PCBA single PCB 70x70 - 460x500 mm)"),
    "asm_board_max": ("460 x 500", ASM_CAP),
    "tooling_hole": (1.152, TOOLING + " (2-3 NPTH 1.152 mm, mask expansion 0.148 mm, opposite corners)"),
    "fiducial": (1.0, RAILS + " (1 mm copper, 2 mm mask opening, >= 3.35 mm from edge incl. keep-out, 3-4 pcs)"),
    "fiducial_edge": (3.35, RAILS),
    "stencil_thickness": ("0.10 / 0.12", "UNVERIFIED: JLCPCB does not publish the foil thickness used for PCBA; both evaluated"),
    "area_ratio_min": (0.66, "IPC-7525 guideline (not a JLCPCB number); 0.60 is commonly quoted for electroformed/nano-coated foils"),
    "aspect_ratio_min": (1.5, "IPC-7525 guideline (not a JLCPCB number)"),
}
L = {k: v[0] for k, v in LIMITS.items()}
FINE = ("U1", "U13", "U8", "U18", "U2", "U11", "J1", "J3", "U10")


def thermal_barrels(d):
    """Guard the specific thermal-pad classification used by the DRC deck.

    Only the nine ground barrels within U1's exposed pad qualify. Component
    lead holes retain the PTH recommendations, including other pads of U1.
    """
    fp = next(f for f in d["fps"] if f["ref"] == "U1")
    pads = [p for p in fp["pads"] if p["num"] == "61"]
    ep = unary_union([Polygon(poly) for p in pads if not p["drill"][0]
                      for poly in p["poly"] if len(poly) >= 3])
    barrels = [p for p in pads if p["drill"][0]]
    rows = []
    for p in barrels:
        drill = max(p["drill"])
        ring = (min(p["sx"], p["sy"]) - drill) / 2
        inside = ep.covers(Point(p["x"], p["y"]).buffer(drill / 2))
        ok = (p["net"] == "GND" and abs(p["drill"][0] - p["drill"][1]) < 1e-6
              and 0.20 <= drill <= 0.30 and ring >= L["via_annular_pref"]
              and inside and all(layer in p["layers"] for layer in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")))
        rows.append({"at_mm": [p["x"], p["y"]], "drill_mm": drill,
                     "annular_mm": round(ring, 4), "inside_exposed_pad": inside, "pass": ok})
    return {"classification": "U1.61 plated thermal barrels; no inserted component leads",
            "expected_count": 9, "count": len(rows), "barrels": rows,
            "pass": len(rows) == 9 and all(r["pass"] for r in rows)}


def main():
    d = json.loads(Path(sys.argv[1]).read_text())
    res = {"limits": {k: {"value": v[0], "source": v[1]} for k, v in LIMITS.items()}}
    res["thermal_barrels"] = thermal_barrels(d)
    xs = [e["x1"] for e in d["edges"]] + [e["x2"] for e in d["edges"]]
    ys = [e["y1"] for e in d["edges"]] + [e["y2"] for e in d["edges"]]
    outline = box(min(xs), min(ys), max(xs), max(ys))
    smd = [(f["ref"], p["num"], p["net"], Polygon(p["poly"][0]), "F" if "F.Cu" in p["layers"] else "B", p) for f in d["fps"] for p in f["pads"]
           if p["drill"][0] == 0 and p["poly"] and any(l.endswith(".Cu") for l in p["layers"])]
    # a
    vip = []
    for v in d["vias"]:
        pt = Point(v["x"], v["y"])
        for ref, num, net, g, side, p in smd:
            if abs(p["x"] - v["x"]) < 4 and abs(p["y"] - v["y"]) < 4 and g.distance(pt) < v["drill"] / 2:
                vip.append({"pad": f"{ref}.{num}", "side": side, "via": [round(v["x"], 3), round(v["y"], 3)], "hole_inside_pad": g.contains(pt)})
    res["via_holes_in_smd_pads"] = vip
    # b
    web = {}
    for ref in FINE:
        pads = [(num, g) for r, num, net, g, side, p in smd if r == ref]
        best = None
        for i in range(len(pads)):
            for j in range(i + 1, len(pads)):
                gap = pads[i][1].distance(pads[j][1])
                if gap > 1e-6 and (best is None or gap < best[0]):
                    best = (round(gap, 4), pads[i][0], pads[j][0])
        if best:
            web[ref] = {"min_mask_web_mm": best[0], "between": [best[1], best[2]], "limit_mm": L["mask_dam_min"], "pass": best[0] >= L["mask_dam_min"]}
    res["mask_web_fine_pitch"] = web
    # c
    ar = []
    for ref, num, net, g, side, p in smd:
        if not any("Paste" in l for l in p["layers"]):
            continue
        a, per = g.area, g.length
        ar.append((a / (per * 0.10), a / (per * 0.12), f"{ref}.{num}", round(min(p["sx"], p["sy"]), 3), round(max(p["sx"], p["sy"]), 3)))
    ar.sort()
    low = {}
    for r10, r12, name, w, h in ar:
        key = (name.split(".")[0].rstrip("0123456789"), w, h)
        low.setdefault(key, {"example": name, "aperture_mm": [w, h], "area_ratio_0.10": round(r10, 2), "area_ratio_0.12": round(r12, 2), "count": 0})["count"] += 1
    res["stencil_area_ratio_lowest"] = sorted(low.values(), key=lambda v: v["area_ratio_0.12"])[:8]
    res["stencil_area_ratio_guideline"] = L["area_ratio_min"]
    # h
    edge = []
    for f in d["fps"]:
        if not f["pads"] or f["ref"].startswith(("TP", "STAB", "LOGO")) or f["dnp"]:
            continue
        if f["ref"].startswith("SW") and f["ref"] not in ("SW100", "SW101"):
            continue
        cy = [Polygon(c) for c in f["courtyard"] if len(c) >= 3]
        g = unary_union(cy) if cy else unary_union([Polygon(p["poly"][0]) for p in f["pads"] if p["poly"]])
        dist = outline.exterior.distance(g)
        if dist < L["asm_body_to_edge"]:
            edge.append({"ref": f["ref"], "side": f["layer"], "courtyard_to_edge_mm": round(dist, 2)})
    res["assembled_parts_within_2p5mm_of_edge"] = sorted(edge, key=lambda e: e["courtyard_to_edge_mm"])
    # i
    res["fiducials_on_board"] = [f["ref"] for f in d["fps"] if "fiducial" in f["fpid"].lower() or f["ref"].startswith("FID")]
    res["tooling_holes_1p152mm"] = sum(1 for f in d["fps"] for p in f["pads"] if abs(p["drill"][0] - 1.152) < 0.01)
    Path(sys.argv[2]).write_text(json.dumps(res, indent=1) + "\n")
    if not res["thermal_barrels"]["pass"]:
        raise SystemExit("U1 thermal-barrel classification/geometry failed; inspect before using the thermal DRC rules")
    print("via holes in SMD pads:", len(vip), [v["pad"] for v in vip][:12])
    for k, v in web.items():
        print("mask web", k, v["min_mask_web_mm"], "PASS" if v["pass"] else "FAIL")
    for v in res["stencil_area_ratio_lowest"]:
        print("stencil", v)
    print("parts within 2.5 mm of the edge:", len(edge), [(e["ref"], e["courtyard_to_edge_mm"]) for e in res["assembled_parts_within_2p5mm_of_edge"]][:20])
    print("fiducials:", res["fiducials_on_board"], "tooling holes:", res["tooling_holes_1p152mm"])


if __name__ == "__main__":
    main()
