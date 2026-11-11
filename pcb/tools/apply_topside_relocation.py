#!/usr/bin/env python3
"""Apply a plan from plan_topside_relocation.py to a board (run with KiCad 9 pcbnew).

usage: apply_topside_relocation.py BOARD.kicad_pcb PLAN.json [--dnp REF,REF]

The board is modified in place: use a checkpoint copy.  Footprints are moved,
the stubs that only served the old pad positions are removed, the planned F.Cu
tracks and GND vias are added, and every zone is refilled.
"""
import json
import sys

import pcbnew


def mm(v):
    return pcbnew.FromMM(float(v))


def main():
    board_path, plan_path = sys.argv[1], sys.argv[2]
    dnp = []
    if "--dnp" in sys.argv:
        dnp = [r for r in sys.argv[sys.argv.index("--dnp") + 1].split(",") if r]
    plan = json.load(open(plan_path))
    b = pcbnew.LoadBoard(board_path)
    nets = b.GetNetsByName()
    tracks = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
    gnd_via = next(t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND"
                   and abs(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) - 0.5) < 1e-6 and abs(pcbnew.ToMM(t.GetDrill()) - 0.25) < 1e-6)
    n_moved = n_removed = n_tracks = n_vias = 0
    for e in plan["edits"]:
        if "error" in e:
            continue
        fp = b.FindFootprintByReference(e["ref"])
        x, y, rot = e["to"]
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.SetOrientationDegrees(rot)
        n_moved += 1
        for r in e["remove_tracks"]:
            hit = None
            for t in tracks:
                if t.GetLayerName() != r["layer"] or t.GetNetname() != r["net"]:
                    continue
                a = (pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y), pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y))
                if max(abs(a[0] - r["x1"]), abs(a[1] - r["y1"]), abs(a[2] - r["x2"]), abs(a[3] - r["y2"])) < 1e-4:
                    hit = t
                    break
            if hit is None:
                raise SystemExit(f"{e['ref']}: track to remove not found: {r}")
            tracks.remove(hit)
            b.Remove(hit)
            n_removed += 1
        for a in e["add_tracks"]:
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(mm(a["x1"]), mm(a["y1"])))
            t.SetEnd(pcbnew.VECTOR2I(mm(a["x2"]), mm(a["y2"])))
            t.SetWidth(mm(a["w"]))
            t.SetLayer(b.GetLayerID(a["layer"]))
            t.SetNet(nets[a["net"]])
            b.Add(t)
            n_tracks += 1
        for v in e.get("add_vias", []):
            via = gnd_via.Duplicate()
            via.SetPosition(pcbnew.VECTOR2I(mm(v["x"]), mm(v["y"])))
            b.Add(via)
            n_vias += 1
    for ref in dnp:
        fp = b.FindFootprintByReference(ref)
        fp.SetDNP(True)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    pcbnew.SaveBoard(board_path, b)
    print(json.dumps({"moved": n_moved, "tracks_removed": n_removed, "tracks_added": n_tracks, "vias_added": n_vias, "dnp": dnp}))


if __name__ == "__main__":
    main()
