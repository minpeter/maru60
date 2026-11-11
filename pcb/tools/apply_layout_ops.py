#!/usr/bin/env python3
"""Apply a list of layout operations to a board (run with KiCad 9 pcbnew).

usage: apply_layout_ops.py BOARD.kicad_pcb OPS.json

OPS.json is {"ops": [...]}; operations run in order.  The board is edited in
place (use a checkpoint copy) and every zone is refilled at the end.

  {"op": "remove_tracks", "tracks": [{x1,y1,x2,y2,layer,net}, ...]}
  {"op": "add_tracks", "tracks": [{x1,y1,x2,y2,w,layer,net}, ...]}
  {"op": "add_vias", "vias": [{x,y,net}, ...]}                      0.5 / 0.25 mm through vias
  {"op": "remove_vias", "vias": [{x,y,net}, ...]}
  {"op": "remove_footprint", "ref": "C142"}
  {"op": "replace_footprint", "ref", "lib_dir", "name", "fpid", "side": "F.Cu"|"B.Cu",
        "x", "y", "rot", "value", "pad_nets": {"1": "NET", ...}, "expect_pads": {"1": [x, y]}}
  {"op": "move_footprint", "ref", "x", "y", "rot"}
  {"op": "add_pads", "ref", "pads": [{"num", "x", "y", "side", "sx", "sy", "like": pad number to copy net/function from}]}
  {"op": "set_pad_geometry", "ref", "pads": {"1": {"x", "y", "sx", "sy"}, ...}}   absolute position, board-frame size
  {"op": "set_drill", "refs_re", "from", "to"}                       NPTH pads: drill and pad size
  {"op": "add_circles", "items": [{"ref", "x", "y", "r", "layer", "fill": true, "w": 0.1}]}   footprint graphics
  {"op": "set_fpid", "refs": [...], "fpid": "nick:name"}
  {"op": "set_field", "ref", "name", "value"}
  {"op": "set_dnp", "ref", "dnp": true|false}
"""
import json
import re
import sys

import pcbnew

mm = pcbnew.FromMM


def P(x, y):
    return pcbnew.VECTOR2I(mm(float(x)), mm(float(y)))


def main():
    path, ops_path = sys.argv[1], sys.argv[2]
    ops = json.load(open(ops_path))["ops"]
    b = pcbnew.LoadBoard(path)
    nets = b.GetNetsByName()
    proto = next(t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and abs(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) - 0.5) < 1e-6
                 and abs(pcbnew.ToMM(t.GetDrill()) - 0.25) < 1e-6)
    log = []
    # pcbnew's Python wrappers misbehave after BOARD.Remove(), so everything is looked up first
    # and every removal happens in one pass after all other operations.
    live = [(t, t.GetLayerName(), t.GetNetname(), pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y), pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y))
            for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
    vias = [(t, t.GetNetname(), pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y)) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    doomed_tracks, doomed_items = [], []
    for op in ops:
        kind = op["op"]
        if kind == "remove_tracks":
            for r in op["tracks"]:
                hit = [rec for rec in live if rec[1] == r["layer"] and rec[2] == r["net"] and rec not in doomed_tracks and (
                    max(abs(rec[3] - r["x1"]), abs(rec[4] - r["y1"]), abs(rec[5] - r["x2"]), abs(rec[6] - r["y2"])) < 1e-4 or
                    max(abs(rec[3] - r["x2"]), abs(rec[4] - r["y2"]), abs(rec[5] - r["x1"]), abs(rec[6] - r["y1"])) < 1e-4)]
                if not hit:
                    raise SystemExit(f"track to remove not found: {r}")
                doomed_tracks.append(hit[0])
        elif kind == "add_tracks":
            for a in op["tracks"]:
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(P(a["x1"], a["y1"]))
                t.SetEnd(P(a["x2"], a["y2"]))
                t.SetWidth(mm(a["w"]))
                t.SetLayer(b.GetLayerID(a["layer"]))
                t.SetNet(nets[a["net"]])
                b.Add(t)
        elif kind == "add_vias":
            for v in op["vias"]:
                via = proto.Duplicate()
                via.SetPosition(P(v["x"], v["y"]))
                via.SetNet(nets[v["net"]])
                b.Add(via)
        elif kind == "remove_vias":
            for v in op["vias"]:
                hit = [rec for rec in vias if rec[1] == v["net"] and abs(rec[2] - v["x"]) < 1e-3 and abs(rec[3] - v["y"]) < 1e-3]
                if len(hit) != 1:
                    raise SystemExit(f"via to remove not found: {v}")
                doomed_items.append(hit[0][0])
        elif kind == "remove_footprint":
            doomed_items.append(fps[op["ref"]])
        elif kind == "replace_footprint":
            old = fps[op["ref"]]
            new = pcbnew.FootprintLoad(op["lib_dir"], op["name"])
            if new is None:
                raise SystemExit(f"footprint {op['name']} not found in {op['lib_dir']}")
            nick, name = op["fpid"].split(":")
            new.SetFPID(pcbnew.LIB_ID(nick, name))
            new.SetReference(op["ref"])
            new.SetValue(op["value"])
            new.SetPath(old.GetPath())
            new.SetSheetname(old.GetSheetname())
            new.SetSheetfile(old.GetSheetfile())
            b.Add(new)
            new.SetPosition(P(op["x"], op["y"]))
            if op["side"] == "B.Cu":
                new.Flip(new.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            new.SetOrientationDegrees(op.get("rot", 0))
            for p in new.Pads():
                net = op["pad_nets"].get(p.GetNumber())
                if net:
                    if net not in nets:
                        b.Add(pcbnew.NETINFO_ITEM(b, net))
                        nets = b.GetNetsByName()
                    p.SetNet(nets[net])
            got = {p.GetNumber(): [round(pcbnew.ToMM(p.GetPosition().x), 4), round(pcbnew.ToMM(p.GetPosition().y), 4)] for p in new.Pads()}
            for k, v in op.get("expect_pads", {}).items():
                if abs(got[k][0] - v[0]) > 2e-3 or abs(got[k][1] - v[1]) > 2e-3:
                    raise SystemExit(f"{op['ref']}: pads are at {got}, expected {op['expect_pads']}")
            doomed_items.append(old)
            fps[op["ref"]] = new
            log.append({"replace": op["ref"], "pads": got})
        elif kind == "move_footprint":
            fp = fps[op["ref"]]
            fp.SetPosition(P(op["x"], op["y"]))
            if "rot" in op:
                fp.SetOrientationDegrees(op["rot"])
        elif kind == "add_pads":
            fp = fps[op["ref"]]
            by_num = {p.GetNumber(): p for p in fp.Pads()}
            for a in op["pads"]:
                src = by_num[a["like"]]
                layer = pcbnew.B_Cu if a["side"] == "B.Cu" else pcbnew.F_Cu
                p = pcbnew.PAD(fp)
                p.SetNumber(a["num"])
                p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
                ls = pcbnew.LSET()
                for L in ((pcbnew.B_Cu, pcbnew.B_Paste, pcbnew.B_Mask) if a["side"] == "B.Cu" else (pcbnew.F_Cu, pcbnew.F_Paste, pcbnew.F_Mask)):
                    ls.AddLayer(L)
                p.SetLayerSet(ls)
                p.SetShape(layer, pcbnew.PAD_SHAPE_ROUNDRECT)
                p.SetRoundRectRadiusRatio(layer, 0.25)
                p.SetSize(layer, pcbnew.VECTOR2I(mm(a["sx"]), mm(a["sy"])))
                p.SetNet(src.GetNet())
                p.SetPinFunction(src.GetPinFunction())
                p.SetPosition(P(a["x"], a["y"]))
                fp.Add(p)
        elif kind == "set_pad_geometry":
            fp = fps[op["ref"]]
            for p in fp.Pads():
                g = op["pads"].get(p.GetNumber())
                if not g:
                    continue
                layer = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) else pcbnew.F_Cu
                cur = p.GetSize(layer)
                bb = p.GetBoundingBox()
                horizontal_now = bb.GetWidth() >= bb.GetHeight()
                want_horizontal = g["sx"] >= g["sy"]
                long_, short = max(g["sx"], g["sy"]), min(g["sx"], g["sy"])
                cur_long_is_x = cur.x >= cur.y
                # keep the pad's own orientation: put the long side on whichever local axis is currently long
                if horizontal_now == want_horizontal:
                    p.SetSize(layer, pcbnew.VECTOR2I(mm(long_), mm(short)) if cur_long_is_x else pcbnew.VECTOR2I(mm(short), mm(long_)))
                else:
                    p.SetSize(layer, pcbnew.VECTOR2I(mm(short), mm(long_)) if cur_long_is_x else pcbnew.VECTOR2I(mm(long_), mm(short)))
                p.SetPosition(P(g["x"], g["y"]))
        elif kind == "set_drill":
            n = 0
            for ref, fp in fps.items():
                if not re.search(op["refs_re"], ref):
                    continue
                for p in fp.Pads():
                    d = p.GetDrillSize()
                    if abs(pcbnew.ToMM(d.x) - op["from"]) < 1e-4 and abs(pcbnew.ToMM(d.y) - op["from"]) < 1e-4:
                        p.SetDrillSize(pcbnew.VECTOR2I(mm(op["to"]), mm(op["to"])))
                        p.SetSize(pcbnew.F_Cu, pcbnew.VECTOR2I(mm(op["to"]), mm(op["to"])))
                        n += 1
            log.append({"set_drill": n})
        elif kind == "add_circles":
            for a in op["items"]:
                fp = fps[a["ref"]]
                s = pcbnew.PCB_SHAPE(fp)
                s.SetShape(pcbnew.SHAPE_T_CIRCLE)
                s.SetCenter(P(a["x"], a["y"]))
                s.SetEnd(P(a["x"] + a["r"], a["y"]))
                s.SetLayer(b.GetLayerID(a["layer"]))
                s.SetWidth(mm(a.get("w", 0.1)))
                s.SetFilled(bool(a.get("fill", True)))
                fp.Add(s)
        elif kind == "set_fpid":
            nick, name = op["fpid"].split(":")
            for ref in op["refs"]:
                fps[ref].SetFPID(pcbnew.LIB_ID(nick, name))
        elif kind == "set_field":
            fp = fps[op["ref"]]
            if op["name"] == "Value":
                fp.SetValue(op["value"])
            else:
                fp.SetField(op["name"], op["value"])
        elif kind == "set_dnp":
            fp = fps[op["ref"]]
            fp.SetDNP(bool(op["dnp"]))
            fp.SetExcludedFromBOM(bool(op["dnp"]))
            fp.SetExcludedFromPosFiles(bool(op["dnp"]))
        else:
            raise SystemExit(f"unknown op {kind}")
    for rec in doomed_tracks:
        b.Remove(rec[0])
    for item in doomed_items:
        b.Remove(item)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    pcbnew.SaveBoard(path, b)
    print(json.dumps({"ops": len(ops), "log": log}))


if __name__ == "__main__":
    main()
