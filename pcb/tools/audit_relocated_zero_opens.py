#!/usr/bin/env python3
"""Comprehensive native geometry, material-graph v2, inner-plane integrity, and reference coverage
audit for the relocated-expansion-block 0-open candidate checkpoint.

Run from the repository root (pcbnew is only available in the pinned KiCad image):

    tools/run_kicad9.sh python3 pcb/tools/audit_relocated_zero_opens.py \
      --candidate-board pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb \
      --candidate-material pcb/experiments/resume-20261109-relocated-expansion-zero-opens/qa/material-graph.json.gz \
      --out-dir .omo/evidence/relocated0-audit-new

The source checkpoint defaults to the preserved header25/U13 seven-open checkpoint. All paths are
resolved from the repository root (the parent of this file's ``pcb/tools`` directory), not from the
current working directory.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path
import pcbnew as p

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "pcb/experiments/resume-20261109-relocated-expansion-zero-opens"
SOURCE_CHECKPOINT = ROOT / "pcb/experiments/resume-20261109-header25-u13-contact-repair"
BLOCK_REFS = {"J3", "U11", "U13", "U12", "R128", "C128", "C129"} | {f"R13{i}" for i in range(6)} | {f"R14{i}" for i in range(6)}
SILK_ONLY_REFS = {"LOGO1"}
RELOCATED_REFS = BLOCK_REFS | SILK_ONLY_REFS
U1_FANOUT_MM = (106.3, 76.8, 115.7, 86.2)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json_or_gz(path: Path) -> dict:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(path.read_text(encoding="utf-8"))


def poly(shape, out: bool = True) -> p.SHAPE_POLY_SET:
    q = p.SHAPE_POLY_SET()
    shape.TransformToPolygon(q, 1, p.ERROR_OUTSIDE if out else p.ERROR_INSIDE)
    q.Simplify()
    return q


def sub(a: p.SHAPE_POLY_SET, b: p.SHAPE_POLY_SET) -> p.SHAPE_POLY_SET:
    q = p.SHAPE_POLY_SET(a)
    q.BooleanSubtract(b)
    return q


def poly_to_rings(ps: p.SHAPE_POLY_SET) -> list[dict]:
    rows = []
    for i in range(ps.OutlineCount()):
        outer = [[ps.COutline(i).CPoint(j).x, ps.COutline(i).CPoint(j).y] for j in range(ps.COutline(i).PointCount())]
        holes = [
            [[ps.CHole(i, h).CPoint(j).x, ps.CHole(i, h).CPoint(j).y] for j in range(ps.CHole(i, h).PointCount())]
            for h in range(ps.HoleCount(i))
        ]
        rows.append({"outer": outer, "holes": holes})
    return rows


def fp_electrical_sig(f: p.FOOTPRINT) -> tuple:
    pads = sorted(
        (
            pd.m_Uuid.AsString(),
            pd.GetNumber(),
            pd.GetPosition().x,
            pd.GetPosition().y,
            round(pd.GetOrientationDegrees(), 4),
            pd.GetSize().x,
            pd.GetSize().y,
            pd.GetDrillSize().x,
            pd.GetDrillSize().y,
            pd.GetNetname(),
        )
        for pd in f.Pads()
    )
    return (
        f.GetReference(),
        f.GetPosition().x,
        f.GetPosition().y,
        round(f.GetOrientationDegrees(), 4),
        f.GetLayer(),
        tuple(pads),
    )


def track_sig(t: p.PCB_TRACK) -> tuple:
    if isinstance(t, p.PCB_VIA):
        return ("VIA", t.GetPosition().x, t.GetPosition().y, t.GetWidth(p.F_Cu), t.GetDrillValue(), t.GetNetname())
    return ("SEG", t.GetLayer(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth(), t.GetNetname())


def compare_material_graphs(src_mg: dict, cand_mg: dict, affected_uuids: set[str], label: str) -> dict:
    pad_inv_eq = src_mg["pad_inventory"] == cand_mg["pad_inventory"]
    splits = []
    merges = []
    cand_parts_by_net = cand_mg["pad_partitions_by_net"]
    for net, old_groups in sorted(src_mg["pad_partitions_by_net"].items()):
        new_groups = cand_parts_by_net.get(net, [])
        new_sets = [set(g) for g in new_groups]
        for og in old_groups:
            oset = set(og)
            if not any(oset <= ns for ns in new_sets):
                splits.append({"net": net, "broken_group": og})
        if len(new_groups) != len(old_groups):
            merges.append({"net": net, "before": len(old_groups), "after": len(new_groups)})

    multi_group_nets_remaining = {
        net: len(groups) for net, groups in cand_parts_by_net.items() if len(groups) > 1
    }

    cand_direct = {
        tuple(sorted((a, b))): {ln: area for ln, area in sup}
        for a, b, sup in cand_mg["direct_edges"]
    }
    checked_unaffected = 0
    missing_direct = []
    reduced_direct = []
    for a, b, sup in src_mg["direct_edges"]:
        if a in affected_uuids or b in affected_uuids:
            continue
        checked_unaffected += 1
        key = tuple(sorted((a, b)))
        if key not in cand_direct:
            missing_direct.append({"pair": list(key), "source_support": sup})
            continue
        csup = cand_direct[key]
        for ln, s_area in sup:
            c_area = csup.get(ln, 0.0)
            if c_area + 1e-15 < s_area:
                reduced_direct.append({"pair": list(key), "layer": ln, "before": s_area, "after": c_area})

    src_barrels = {row["uuid"]: row for row in src_mg["barrel_joins"]}
    cand_barrels = {row["uuid"]: row for row in cand_mg["barrel_joins"]}
    retained_barrel_uuids = sorted(set(src_barrels) & set(cand_barrels))
    retained_barrels_equal = all(cand_barrels[u] == src_barrels[u] for u in retained_barrel_uuids)
    added_barrel_uuids = sorted(set(cand_barrels) - set(src_barrels))
    removed_barrel_uuids = sorted(set(src_barrels) - set(cand_barrels))

    src_empty_uuids = {x["uuid"] for x in src_mg["empty_object_layers"]}
    new_empty = [x for x in cand_mg["empty_object_layers"] if x["uuid"] not in src_empty_uuids]
    src_mult_uuids = {x["uuid"] for x in src_mg["multiple_component_object_layers"]}
    new_mult = [x for x in cand_mg["multiple_component_object_layers"] if x["uuid"] not in src_mult_uuids]

    return {
        "comparison_label": label,
        "source_board_sha256": src_mg["board_sha256"],
        "candidate_board_sha256": cand_mg["board_sha256"],
        "pad_inventory_identical": pad_inv_eq,
        "source_pad_component_splits": splits,
        "merges": merges,
        "merge_component_reduction_sum": sum(m["before"] - m["after"] for m in merges),
        "multi_group_nets_remaining": multi_group_nets_remaining,
        "unchanged_object_direct_contacts_checked": checked_unaffected,
        "missing_direct_contacts": missing_direct,
        "reduced_direct_contacts": reduced_direct,
        "prior_barrel_count": len(src_barrels),
        "candidate_barrel_count": len(cand_barrels),
        "retained_barrel_count": len(retained_barrel_uuids),
        "all_retained_barrel_records_equal_by_UUID": retained_barrels_equal,
        "added_barrel_uuids": added_barrel_uuids,
        "removed_barrel_uuids": removed_barrel_uuids,
        "guard_failures": len(cand_mg["guard_failing_material_edges"]),
        "guard_failing_material_edges": cand_mg["guard_failing_material_edges"],
        "source_empty_object_layers_count": len(src_mg["empty_object_layers"]),
        "candidate_empty_object_layers_count": len(cand_mg["empty_object_layers"]),
        "new_empty_object_layers": new_empty,
        "source_multiple_component_object_layers_count": len(src_mg["multiple_component_object_layers"]),
        "candidate_multiple_component_object_layers_count": len(cand_mg["multiple_component_object_layers"]),
        "new_multiple_component_object_layers": new_mult,
        "native_pairs_without_guarded_positive_copper": cand_mg["native_pairs_without_guarded_positive_copper"],
        "pass": (
            pad_inv_eq
            and not splits
            and not multi_group_nets_remaining
            and not missing_direct
            and not reduced_direct
            and retained_barrels_equal
            and len(cand_mg["guard_failing_material_edges"]) == 0
            and len(new_empty) == 0
            and len(new_mult) == 0
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--candidate-board",
        type=Path,
        default=EXPERIMENT / "pcb/maru60.kicad_pcb",
        help="candidate board (default: the relocated-expansion checkpoint)",
    )
    ap.add_argument(
        "--candidate-material",
        type=Path,
        default=EXPERIMENT / "qa/material-graph.json.gz",
        help="candidate material graph (default: the checkpoint's archived graph)",
    )
    ap.add_argument(
        "--source-board",
        type=Path,
        default=SOURCE_CHECKPOINT / "pcb/maru60.kicad_pcb",
        help="preserved seven-open source board",
    )
    ap.add_argument(
        "--source-material",
        type=Path,
        default=SOURCE_CHECKPOINT / "qa/material-graph.json.gz",
        help="preserved seven-open source material graph",
    )
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    h7_board_path = args.source_board
    h7_mg_path = args.source_material
    cand_board_path = args.candidate_board

    b_src = p.LoadBoard(str(h7_board_path))
    b_cand = p.LoadBoard(str(cand_board_path))

    # 1. Footprint check: 383 total; 363 non-relocated electrically identical; 20 relocated documented
    src_fps = {f.m_Uuid.AsString(): f for f in b_src.GetFootprints()}
    cand_fps = {f.m_Uuid.AsString(): f for f in b_cand.GetFootprints()}
    assert set(src_fps) == set(cand_fps) and len(cand_fps) == 383

    relocated_pad_uuids: set[str] = set()
    relocated_details = []
    unchanged_fp_count = 0
    unexpected_fp_changes = []
    for u, sf in src_fps.items():
        cf = cand_fps[u]
        ref = cf.GetReference()
        if ref in RELOCATED_REFS:
            for pd in cf.Pads():
                relocated_pad_uuids.add(pd.m_Uuid.AsString())
            relocated_details.append({
                "ref": ref,
                "uuid": u,
                "before_mm_deg_layer": [sf.GetPosition().x / 1e6, sf.GetPosition().y / 1e6, sf.GetOrientationDegrees(), b_src.GetLayerName(sf.GetLayer())],
                "after_mm_deg_layer": [cf.GetPosition().x / 1e6, cf.GetPosition().y / 1e6, cf.GetOrientationDegrees(), b_cand.GetLayerName(cf.GetLayer())],
            })
        else:
            if fp_electrical_sig(sf) == fp_electrical_sig(cf):
                unchanged_fp_count += 1
            else:
                unexpected_fp_changes.append(ref)
    assert not unexpected_fp_changes, f"Unexpected non-BLOCK footprint changes: {unexpected_fp_changes}"

    # Track & via diff vs header25-u13-contact-repair
    src_trks = {t.m_Uuid.AsString(): t for t in b_src.GetTracks()}
    cand_trks = {t.m_Uuid.AsString(): t for t in b_cand.GetTracks()}

    added_uuids = sorted(set(cand_trks) - set(src_trks))
    removed_uuids = sorted(set(src_trks) - set(cand_trks))
    modified_uuids = sorted(u for u in (set(src_trks) & set(cand_trks)) if track_sig(src_trks[u]) != track_sig(cand_trks[u]))
    affected_uuids = set(added_uuids) | set(removed_uuids) | set(modified_uuids) | relocated_pad_uuids

    # 2. Material Graph v2 comparison
    src_mg = load_json_or_gz(h7_mg_path)
    cand_mg = load_json_or_gz(args.candidate_material)
    comp_vs_h7 = compare_material_graphs(src_mg, cand_mg, affected_uuids, "vs_header25_u13_7opens")
    (out_dir / "material-comparison.json").write_text(json.dumps(comp_vs_h7, indent=2) + "\n")
    print(
        "Material pass:", comp_vs_h7["pass"],
        "multi_group_nets_remaining:", comp_vs_h7["multi_group_nets_remaining"],
        "guard_failures:", comp_vs_h7["guard_failures"],
        "new_empty_layers:", len(comp_vs_h7["new_empty_object_layers"]),
        "new_mult_layers:", len(comp_vs_h7["new_multiple_component_object_layers"]),
        "rejected_pairs:", len(comp_vs_h7["native_pairs_without_guarded_positive_copper"]),
    )

    # 3. Inner GND plane islands, area, and minimum non-GND via neck width
    cand_items = list(b_cand.GetTracks()) + [pd for f in b_cand.GetFootprints() for pd in f.Pads()]
    src_items = list(b_src.GetTracks()) + [pd for f in b_src.GetFootprints() for pd in f.Pads()]
    cand_holes = [(q.m_Uuid.AsString(), poly(q.GetEffectiveHoleShape(), True)) for q in cand_items if isinstance(q, (p.PAD, p.PCB_VIA)) and q.HasHole()]
    src_holes = [(q.m_Uuid.AsString(), poly(q.GetEffectiveHoleShape(), True)) for q in src_items if isinstance(q, (p.PAD, p.PCB_VIA)) and q.HasHole()]

    cand_planes = {}
    src_planes = {}
    plane_summary = {}
    for lid in (p.In1_Cu, p.In2_Cu):
        ln = b_cand.GetLayerName(lid)
        gc = p.SHAPE_POLY_SET()
        for z in b_cand.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() == "GND" and z.IsOnLayer(lid):
                gc.BooleanAdd(z.GetFilledPolysList(lid))
        gc.Simplify()
        gs = p.SHAPE_POLY_SET()
        for z in b_src.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() == "GND" and z.IsOnLayer(lid):
                gs.BooleanAdd(z.GetFilledPolysList(lid))
        gs.Simplify()
        cand_planes[lid] = gc
        src_planes[lid] = gs
        plane_summary[ln] = {
            "islands_source": gs.OutlineCount(),
            "islands_candidate": gc.OutlineCount(),
            "area_source_mm2": round(gs.Area() / 1e12, 4),
            "area_candidate_mm2": round(gc.Area() / 1e12, 4),
            "delta_mm2": round((gc.Area() - gs.Area()) / 1e12, 4),
        }

    added_vias_set = {u for u in added_uuids if isinstance(cand_trks[u], p.PCB_VIA)}
    added_via_records = []
    cand_vias_by_net: dict[str, list] = {}
    for t in b_cand.GetTracks():
        if isinstance(t, p.PCB_VIA):
            cand_vias_by_net.setdefault(t.GetNetname(), []).append(t)
            if t.m_Uuid.AsString() in added_vias_set:
                added_via_records.append({
                    "uuid": t.m_Uuid.AsString(),
                    "net": t.GetNetname(),
                    "xy_nm": [t.GetPosition().x, t.GetPosition().y],
                    "xy_mm": [t.GetPosition().x / 1e6, t.GetPosition().y / 1e6],
                    "width_nm": t.GetWidth(p.F_Cu),
                    "drill_nm": t.GetDrillValue(),
                })

    gnd_thermal_gap = 500000
    gnd_min_thick = 250000
    for z in b_cand.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == "GND" and z.IsOnLayer(p.In1_Cu):
            gnd_thermal_gap = max(gnd_thermal_gap, z.GetThermalReliefGap())
            gnd_min_thick = max(gnd_min_thick, z.GetMinThickness())

    non_gnd_antipads = []
    all_drill_antipad_shapes: list[tuple[p.BOX2I, p.SHAPE_POLY_SET]] = []
    for q in cand_items:
        if isinstance(q, p.PCB_VIA):
            if q.GetNetname() != "GND":
                rad = q.GetWidth(p.In1_Cu) // 2 + 200000
                non_gnd_antipads.append((q.m_Uuid.AsString(), q.GetNetname(), q.GetPosition().x, q.GetPosition().y, rad))
                wpoly = poly(p.SHAPE_CIRCLE(q.GetPosition(), rad + 5000), True)
            else:
                rad = q.GetWidth(p.In1_Cu) // 2 + gnd_thermal_gap
                wpoly = poly(p.SHAPE_CIRCLE(q.GetPosition(), rad + 5000), True)
            all_drill_antipad_shapes.append((wpoly.BBox(), wpoly))
        elif isinstance(q, p.PAD) and q.HasHole():
            if q.GetNetname() not in ("", "GND"):
                bb = q.GetEffectiveShape(p.In1_Cu).BBox() if q.IsOnLayer(p.In1_Cu) else q.GetEffectiveHoleShape().BBox()
                rad = max(bb.GetWidth(), bb.GetHeight()) // 2 + 200000
                non_gnd_antipads.append((q.m_Uuid.AsString(), q.GetNetname(), q.GetPosition().x, q.GetPosition().y, rad))
                wpoly = poly(p.SHAPE_CIRCLE(q.GetPosition(), rad + 5000), True)
            elif q.GetNetname() == "GND":
                bb = q.GetEffectiveShape(p.In1_Cu).BBox() if q.IsOnLayer(p.In1_Cu) else q.GetEffectiveHoleShape().BBox()
                rad = max(bb.GetWidth(), bb.GetHeight()) // 2 + gnd_thermal_gap
                wpoly = poly(p.SHAPE_CIRCLE(q.GetPosition(), rad + 5000), True)
            else:
                hbb = q.GetEffectiveHoleShape().BBox()
                hrad = max(hbb.GetWidth(), hbb.GetHeight()) // 2 + 255000
                wpoly = poly(p.SHAPE_CIRCLE(q.GetPosition(), hrad), True)
            all_drill_antipad_shapes.append((wpoly.BBox(), wpoly))

    def local_antipad_envelope(query_bb: p.BOX2I) -> p.SHAPE_POLY_SET:
        pad = gnd_min_thick + 50000
        eb = p.BOX2I(p.VECTOR2I(query_bb.GetX() - pad, query_bb.GetY() - pad), p.VECTOR2I(query_bb.GetWidth() + 2 * pad, query_bb.GetHeight() + 2 * pad))
        loc = p.SHAPE_POLY_SET()
        for wbb, wpoly in all_drill_antipad_shapes:
            if eb.Intersects(wbb):
                loc.BooleanAdd(wpoly)
        loc.Simplify()
        if loc.OutlineCount() > 0:
            loc.Inflate(gnd_min_thick // 2 + 25000, p.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, 5000)
            loc.Inflate(- (gnd_min_thick // 2), p.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, 5000)
            loc.Simplify()
        return loc

    min_neck_mm = 999.0
    min_neck_pair = None
    min_diff_net_neck_mm = 999.0
    min_diff_net_neck_pair = None
    sub_20_pairs = []
    sub_15_same_net_pairs = []
    sub_15_diff_net_pairs = []
    seen_neck_keys: set[tuple[str, str]] = set()
    for u1, n1, x1, y1, r1 in non_gnd_antipads:
        if u1 not in added_vias_set:
            continue
        for u2, n2, x2, y2, r2 in non_gnd_antipads:
            if u1 == u2:
                continue
            pkey = tuple(sorted((u1, u2)))
            if pkey in seen_neck_keys:
                continue
            seen_neck_keys.add(pkey)
            d_nm = math.hypot(x1 - x2, y1 - y2)
            neck_mm = (d_nm - r1 - r2) / 1e6
            entry = {"via_a": u1, "net_a": n1, "obj_b": u2, "net_b": n2, "center_dist_mm": round(d_nm / 1e6, 4), "neck_mm": round(neck_mm, 4)}
            if neck_mm < min_neck_mm:
                min_neck_mm = neck_mm
                min_neck_pair = entry
            if n1 != n2 and neck_mm < min_diff_net_neck_mm:
                min_diff_net_neck_mm = neck_mm
                min_diff_net_neck_pair = entry
            if neck_mm < 0.20 - 1e-6:
                sub_20_pairs.append(entry)
            if neck_mm < 0.15 - 1e-6:
                if n1 == n2:
                    sub_15_same_net_pairs.append(entry)
                else:
                    sub_15_diff_net_pairs.append(entry)

    # 4. Reference coverage audit for all added + modified outer non-GND tracks
    u1_box = p.SHAPE_POLY_SET()
    u1_box.NewOutline()
    ex0, ey0, ex1, ey1 = (int(v * 1e6) for v in U1_FANOUT_MM)
    for x, y in ((ex0, ey0), (ex1, ey0), (ex1, ey1), (ex0, ey1)):
        u1_box.Append(x, y)

    cand_holes_by_net: dict[str, list] = {}
    for q in cand_items:
        if isinstance(q, p.PAD) and q.HasHole() and q.GetNetname():
            cand_holes_by_net.setdefault(q.GetNetname(), []).append(q)

    check_track_ids = {u for u in (set(added_uuids) | set(modified_uuids)) if not isinstance(cand_trks[u], p.PCB_VIA)}
    ref_rows = []
    uncovered_outside_own_and_u1 = []
    uncovered_outside_indiv_antipads_and_u1 = []
    uncovered_outside_envelope_and_u1 = []
    exempt_u1_rows = 0

    for uid in sorted(check_track_ids):
        q = cand_trks[uid]
        if q.GetNetname() in ("", "GND"):
            continue
        lid = q.GetLayer()
        if lid not in (p.F_Cu, p.B_Cu):
            continue
        copper = poly(q.GetEffectiveShape(lid), True)
        cbb = copper.BBox()
        for _, h in cand_holes:
            if cbb.Intersects(h.BBox()):
                copper.BooleanSubtract(h)
        own_windows = []
        for via in cand_vias_by_net.get(q.GetNetname(), []):
            win = poly(p.SHAPE_CIRCLE(via.GetPosition(), via.GetWidth(p.F_Cu) // 2 + 205000), True)
            if cbb.Intersects(win.BBox()):
                own_windows.append(win)
        for hpad in cand_holes_by_net.get(q.GetNetname(), []):
            win = poly(p.SHAPE_CIRCLE(hpad.GetPosition(), 705000), True)
            if cbb.Intersects(win.BBox()):
                own_windows.append(win)
        nearby_antipads = [wpoly for wbb, wpoly in all_drill_antipad_shapes if cbb.Intersects(wbb)]

        for pl_lid, ground in cand_planes.items():
            missing = sub(copper, ground)
            outside_trans = p.SHAPE_POLY_SET(missing)
            for win in own_windows:
                outside_trans.BooleanSubtract(win)
            outside_u1 = sub(outside_trans, u1_box)
            outside_indiv = p.SHAPE_POLY_SET(outside_u1)
            for wpoly in nearby_antipads:
                if outside_indiv.OutlineCount() == 0:
                    break
                outside_indiv.BooleanSubtract(wpoly)
            outside_env = sub(outside_indiv, local_antipad_envelope(outside_indiv.BBox())) if outside_indiv.OutlineCount() > 0 and outside_indiv.Area() > 1e6 else outside_indiv
            if outside_trans.OutlineCount() > 0 and outside_u1.Area() <= 1e6:
                exempt_u1_rows += 1
            row = {
                "uuid": uid,
                "net": q.GetNetname(),
                "track_layer": b_cand.GetLayerName(lid),
                "reference": b_cand.GetLayerName(pl_lid),
                "raw_uncovered_mm2": round(missing.Area() / 1e12, 6),
                "outside_own_transition_mm2": round(outside_trans.Area() / 1e12, 6),
                "outside_own_and_u1_mm2": round(outside_u1.Area() / 1e12, 6),
                "outside_individual_antipads_and_u1_mm2": round(outside_indiv.Area() / 1e12, 6),
                "outside_zone_antipad_envelope_and_u1_mm2": round(outside_env.Area() / 1e12, 6),
            }
            ref_rows.append(row)
            if outside_u1.OutlineCount() > 0 and outside_u1.Area() > 1e6:
                bb = outside_u1.BBox()
                uncovered_outside_own_and_u1.append({**row, "at_mm": [round(bb.Centre().x / 1e6, 3), round(bb.Centre().y / 1e6, 3)]})
            if outside_indiv.OutlineCount() > 0 and outside_indiv.Area() > 1e6:
                bb = outside_indiv.BBox()
                uncovered_outside_indiv_antipads_and_u1.append({**row, "at_mm": [round(bb.Centre().x / 1e6, 3), round(bb.Centre().y / 1e6, 3)]})
            if outside_env.OutlineCount() > 0 and outside_env.Area() > 1e6:
                bb = outside_env.BBox()
                uncovered_outside_envelope_and_u1.append({**row, "at_mm": [round(bb.Centre().x / 1e6, 3), round(bb.Centre().y / 1e6, 3)]})

    # Also check retained outer tracks near added vias
    new_via_windows = [
        (
            nv["xy_nm"],
            poly(
                p.SHAPE_CIRCLE(
                    p.VECTOR2I(*nv["xy_nm"]),
                    nv["width_nm"] // 2 + (gnd_thermal_gap + 5000 if nv["net"] == "GND" else 205000),
                ),
                True,
            ),
        )
        for nv in added_via_records
    ]
    flagged_retained_src = []
    flagged_retained_cand = []
    retained_antipad_crescents = []
    retained_outside_declared_windows = []
    for uid, q in cand_trks.items():
        if isinstance(q, p.PCB_VIA) or uid in check_track_ids or q.GetNetname() in ("", "GND"):
            continue
        lid = q.GetLayer()
        if lid not in (p.F_Cu, p.B_Cu):
            continue
        qbb = q.GetBoundingBox()
        near_nv = [
            wpoly
            for (vx, vy), wpoly in new_via_windows
            if qbb.GetX() - 800000 <= vx <= qbb.GetRight() + 800000
            and qbb.GetY() - 800000 <= vy <= qbb.GetBottom() + 800000
        ]
        if not near_nv:
            continue
        c_cu = poly(q.GetEffectiveShape(lid), True)
        s_cu = poly(src_trks[uid].GetEffectiveShape(lid), True)
        flagged_retained_cand.append({"uuid": uid, "net": q.GetNetname(), "layer": b_cand.GetLayerName(lid), "polygons": poly_to_rings(c_cu)})
        flagged_retained_src.append({"uuid": uid, "net": q.GetNetname(), "layer": b_src.GetLayerName(lid), "polygons": poly_to_rings(s_cu)})
        for _, h in cand_holes:
            if c_cu.BBox().Intersects(h.BBox()):
                c_cu.BooleanSubtract(h)
        for _, h in src_holes:
            if s_cu.BBox().Intersects(h.BBox()):
                s_cu.BooleanSubtract(h)
        for pl_lid in (p.In1_Cu, p.In2_Cu):
            old_miss = sub(s_cu, src_planes[pl_lid])
            new_miss = sub(c_cu, cand_planes[pl_lid])
            added_miss = sub(new_miss, old_miss)
            if added_miss.Area() > 1e6:
                retained_antipad_crescents.append({
                    "uuid": uid,
                    "net": q.GetNetname(),
                    "reference": b_cand.GetLayerName(pl_lid),
                    "antipad_crescent_mm2": round(added_miss.Area() / 1e12, 6),
                })
                outside_nv = sub(added_miss, local_antipad_envelope(added_miss.BBox()))
                if outside_nv.Area() > 1e6:
                    retained_outside_declared_windows.append({
                        "uuid": uid,
                        "net": q.GetNetname(),
                        "reference": b_cand.GetLayerName(pl_lid),
                        "outside_declared_windows_mm2": round(outside_nv.Area() / 1e12, 6),
                    })

    summary = {
        "footprints": {
            "total": 383,
            "unchanged_electrical_count": unchanged_fp_count,
            "relocated_expansion_block_count": len(BLOCK_REFS),
            "relocated_silkscreen_only_count": len(SILK_ONLY_REFS),
            "relocated_details": sorted(relocated_details, key=lambda x: x["ref"]),
        },
        "copper_diff_vs_header7": {
            "added_tracks_and_vias": len(added_uuids),
            "added_vias": len(added_via_records),
            "added_non_gnd_vias": sum(1 for v in added_via_records if v["net"] != "GND"),
            "added_gnd_fanout_vias": sum(1 for v in added_via_records if v["net"] == "GND"),
            "removed_tracks_and_vias": len(removed_uuids),
            "modified_tracks_and_vias": len(modified_uuids),
        },
        "inner_gnd_planes": plane_summary,
        "inner_plane_via_necks": {
            "min_different_net_neck_mm": round(min_diff_net_neck_mm, 4) if min_diff_net_neck_mm < 900 else None,
            "min_different_net_neck_pair": min_diff_net_neck_pair,
            "min_all_neck_mm": round(min_neck_mm, 4) if min_neck_mm < 900 else None,
            "min_all_neck_pair": min_neck_pair,
            "sub_015mm_different_net_pairs": sub_15_diff_net_pairs,
            "sub_015mm_same_net_pairs": sub_15_same_net_pairs,
            "sub_020mm_pairs_count": len(sub_20_pairs),
            "sub_020mm_pairs": sub_20_pairs,
        },
        "reference_coverage": {
            "checked_track_plane_rows": len(ref_rows),
            "u1_fanout_box_mm": list(U1_FANOUT_MM),
            "zone_thermal_gap_mm": gnd_thermal_gap / 1e6,
            "zone_min_thickness_mm": gnd_min_thick / 1e6,
            "u1_fanout_exempt_rows": exempt_u1_rows,
            "adjacent_antipad_crescent_rows_count": len(uncovered_outside_own_and_u1),
            "min_thickness_cusp_fillet_rows_count": len(uncovered_outside_indiv_antipads_and_u1),
            "uncovered_outside_zone_antipad_envelope_and_u1_count": len(uncovered_outside_envelope_and_u1),
            "uncovered_outside_zone_antipad_envelope_and_u1": uncovered_outside_envelope_and_u1[:20],
            "retained_tracks_antipad_crescent_count": len(retained_antipad_crescents),
            "retained_tracks_new_unsupported_outside_declared_windows": retained_outside_declared_windows,
        },
        "material_graph_pass": comp_vs_h7["pass"],
        "pass": (
            comp_vs_h7["pass"]
            and all(v["islands_candidate"] <= v["islands_source"] for v in plane_summary.values())
            and not sub_15_diff_net_pairs
            and not uncovered_outside_envelope_and_u1
            and not retained_outside_declared_windows
        ),
    }
    (out_dir / "audit-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out_dir / "routing-scope.json").write_text(
        json.dumps(
            {
                "source_header7_sha256": sha256_file(h7_board_path),
                "candidate_sha256": sha256_file(cand_board_path),
                "relocated_footprints": sorted(relocated_details, key=lambda x: x["ref"]),
                "added_uuids": added_uuids,
                "removed_uuids": removed_uuids,
                "modified_uuids": modified_uuids,
                "added_vias": added_via_records,
            },
            indent=2,
        )
        + "\n"
    )

    # Export exact-native-plane-inputs.json for GEOS + exact Q^2 inner-plane replay
    declared_windows = []
    for nv in added_via_records:
        vx, vy = nv["xy_nm"]
        rad = nv["width_nm"] // 2 + (gnd_thermal_gap + 5000 if nv["net"] == "GND" else 205000)
        declared_windows.append({"uuid": nv["uuid"], "net": nv["net"], "xy_nm": [vx, vy], "radius_nm": rad})
    # Also include any relocated through-hole pads (e.g. J3 PTH/NPTH holes moved to new location!)
    for ref in BLOCK_REFS:
        f_c = b_cand.FindFootprintByReference(ref)
        for pd in f_c.Pads():
            if pd.HasHole():
                bb = pd.GetEffectiveShape(p.In1_Cu).BBox() if pd.IsOnLayer(p.In1_Cu) else pd.GetEffectiveHoleShape().BBox()
                rad = int(math.hypot(bb.GetWidth(), bb.GetHeight()) // 2) + 210000
                declared_windows.append({"uuid": pd.m_Uuid.AsString(), "net": pd.GetNetname(), "xy_nm": [pd.GetPosition().x, pd.GetPosition().y], "radius_nm": rad})

    plane_inputs = {
        "source": {
            "planes": {b_src.GetLayerName(lid): poly_to_rings(src_planes[lid]) for lid in (p.In1_Cu, p.In2_Cu)},
            "holes": [{"uuid": u, "polygons": poly_to_rings(h)} for u, h in src_holes],
            "flagged_retained_shadows": flagged_retained_src,
        },
        "candidate": {
            "planes": {b_cand.GetLayerName(lid): poly_to_rings(cand_planes[lid]) for lid in (p.In1_Cu, p.In2_Cu)},
            "holes": [{"uuid": u, "polygons": poly_to_rings(h)} for u, h in cand_holes],
            "flagged_retained_shadows": flagged_retained_cand,
        },
        "windows": declared_windows,
    }
    (out_dir / "exact-native-plane-inputs.json").write_text(json.dumps(plane_inputs) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "footprints"}, indent=2))


if __name__ == "__main__":
    main()
