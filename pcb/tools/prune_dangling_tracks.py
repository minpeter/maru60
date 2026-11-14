#!/usr/bin/env python3
"""Trim or remove the dangling track stubs reported by a KiCad DRC JSON report.

usage: prune_dangling_tracks.py BOARD.kicad_pcb DRC.json [--nets GND,+4V_LED] [--max-length 6.0]

A stub is only ever shortened back to the last point where another item of the
same net joins it (a T-junction part-way along is kept), and removed only when
nothing else touches it beyond its connected end.  Tracks on other nets or
longer than --max-length abort the run.  Re-run DRC afterwards and repeat.
"""
import json
import math
import sys

import pcbnew


def main():
    board_path, drc_path = sys.argv[1], sys.argv[2]
    nets = sys.argv[sys.argv.index("--nets") + 1].split(",") if "--nets" in sys.argv else ["GND", "+4V_LED"]
    max_len = float(sys.argv[sys.argv.index("--max-length") + 1]) if "--max-length" in sys.argv else 6.0
    with open(drc_path) as report:
        drc = json.load(report)
    b = pcbnew.LoadBoard(board_path)
    mm = pcbnew.ToMM
    recs = []
    anchors = {}   # net -> list of (x, y, owner index or None)
    for t in b.GetTracks():
        net = t.GetNetname()
        if t.Type() == pcbnew.PCB_TRACE_T:
            layer = t.GetLayerName()
            i = len(recs)
            s, e = (mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y))
            recs.append({"t": t, "net": net, "layer": layer, "w": mm(t.GetWidth()), "s": s, "e": e})
            anchors.setdefault((net, layer), []).extend([(s[0], s[1], i), (e[0], e[1], i)])
        elif t.Type() == pcbnew.PCB_VIA_T:
            for layer in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"):
                anchors.setdefault((net, layer), []).append((mm(t.GetPosition().x), mm(t.GetPosition().y), None))
    for f in b.GetFootprints():
        for p in f.Pads():
            for layer, lid in (("F.Cu", pcbnew.F_Cu), ("B.Cu", pcbnew.B_Cu)):
                if p.IsOnLayer(lid):
                    anchors.setdefault((p.GetNetname(), layer), []).append((mm(p.GetPosition().x), mm(p.GetPosition().y), None))
    removed = trimmed = 0
    done = set()
    for v in drc["violations"]:
        if v["type"] != "track_dangling":
            continue
        pos = v["items"][0]["pos"]
        uuid = v["items"][0].get("uuid")
        for i, r in enumerate(recs):
            if i in done or r["t"].m_Uuid.AsString() != uuid:
                continue

            def lonely(pt):
                if any(owner != i and owner not in done and math.hypot(ax - pt[0], ay - pt[1]) <= r["w"] / 2 + 1e-6
                       for ax, ay, owner in anchors.get((r["net"], r["layer"]), [])):
                    return False
                # A track endpoint can meet the middle of another segment.
                # Endpoint-only anchors miss that T-junction and may delete
                # its short branch before trimming the real overhang.
                for j, other in enumerate(recs):
                    if j == i or j in done or (other["net"], other["layer"]) != (r["net"], r["layer"]):
                        continue
                    ax, ay = other["s"]; bx, by = other["e"]
                    ll = (bx-ax)**2+(by-ay)**2
                    u = max(0, min(1, ((pt[0]-ax)*(bx-ax)+(pt[1]-ay)*(by-ay))/ll)) if ll else 0
                    if math.hypot(pt[0]-(ax+u*(bx-ax)), pt[1]-(ay+u*(by-ay))) <= (r["w"]+other["w"])/2+1e-6:
                        return False
                return True

            ls, le = lonely(r["s"]), lonely(r["e"])
            if not ls and not le:
                continue  # no geometrically proved dangling end to remove
            if ls != le:
                ds, de = (0.0, 1.0) if ls else (1.0, 0.0)
            else:
                ds = math.hypot(r["s"][0] - pos["x"], r["s"][1] - pos["y"])
                de = math.hypot(r["e"][0] - pos["x"], r["e"][1] - pos["y"])
            # C = connected end, D = dangling end
            c, d = (r["e"], r["s"]) if ds < de else (r["s"], r["e"])
            L = math.hypot(d[0] - c[0], d[1] - c[1])
            if r["net"] not in nets or L > max_len:
                raise SystemExit(f"refusing to touch {r['net']} track of {L:.3f} mm at {pos}")
            tmax = 0.0
            if L > 1e-9:
                ux, uy = (d[0] - c[0]) / L, (d[1] - c[1]) / L
                for ax, ay, owner in anchors.get((r["net"], r["layer"]), []):
                    if owner == i or owner in done:
                        continue
                    t = (ax - c[0]) * ux + (ay - c[1]) * uy
                    if t < -r["w"] / 2 or t > L + r["w"] / 2:
                        continue
                    tc = min(max(t, 0.0), L)
                    if math.hypot(ax - (c[0] + ux * tc), ay - (c[1] + uy * tc)) <= r["w"] / 2 + 1e-6:
                        tmax = max(tmax, tc)
            done.add(i)
            if tmax <= r["w"] / 2 + 1e-6:
                b.Remove(r["t"])
                removed += 1
            elif tmax < L - 1e-6:
                nd = pcbnew.VECTOR2I(pcbnew.FromMM(c[0] + ux * tmax), pcbnew.FromMM(c[1] + uy * tmax))
                if ds < de:
                    r["t"].SetStart(nd)
                else:
                    r["t"].SetEnd(nd)
                trimmed += 1
            break
    if removed or trimmed:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        pcbnew.SaveBoard(board_path, b)
    print(json.dumps({"removed": removed, "trimmed": trimmed}))


if __name__ == "__main__":
    main()
