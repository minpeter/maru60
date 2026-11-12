#!/usr/bin/env python3
"""Apply a list of layout operations to a board (run with KiCad 9 pcbnew).

usage: apply_layout_ops.py BOARD.kicad_pcb OPS.json

OPS.json is {"ops": [...]}; operations run in order.  The board is edited in
place (use a checkpoint copy) and every zone is refilled at the end.

  {"op": "remove_tracks", "tracks": [{x1,y1,x2,y2,layer,net}, ...]}
  {"op": "add_tracks", "tracks": [{x1,y1,x2,y2,w,layer,net}, ...]}
  {"op": "add_vias", "vias": [{x,y,net}, ...]}                      0.5 / 0.25 mm through vias
  {"op": "remove_vias", "vias": [{x,y,net}, ...]}
  {"op": "move_vias", "moves": [{"net", "from": [x, y], "to": [x, y]}]}
  {"op": "set_ref_text", "min_height": 1.0, "min_thickness": 0.15}       visible silkscreen reference fields
  {"op": "move_ref_text", "ref", "x", "y"}                           reference text of one footprint, absolute position
  {"op": "move_track_points", "moves": [{"layer", "net", "from": [x, y], "to": [x, y]}]}   every track end at `from`
  {"op": "remove_footprint", "ref": "C142"}
  {"op": "replace_footprint", "ref", "lib_dir", "name", "fpid", "side": "F.Cu"|"B.Cu",
        "x", "y", "rot", "value", "pad_nets": {"1": "NET", ...}, "expect_pads": {"1": [x, y]}}
  {"op": "add_footprint", "ref", "lib_dir", "name", "fpid", "side", "x", "y", "rot", "value", "pad_nets", "path", "sheetname", "sheetfile"}
  {"op": "set_pad_net", "ref", "pad", "net"}
  {"op": "move_footprint", "ref", "x", "y", "rot"}
  {"op": "add_pads", "ref", "pads": [{"num", "x", "y", "side", "sx", "sy", "like": pad number to copy net/function from}]}
  {"op": "set_pad_geometry", "ref", "pads": {"1": {"x", "y", "sx_local", "sy_local"}, ...}}   absolute position, size in the pad's own frame
  {"op": "reshape_pads", "ref", "pads": [{"at": [x, y], "to": [x, y], "sx_local", "sy_local"}]}   the pad(s) at a position
  {"op": "remove_graphics", "fpid" | "refs", "layer_re", "shapes": ["Polygon"]}   shapes of footprints on matching layers (texts stay);
                                                                     "shapes" (optional) limits it to these kinds (Line, Arc, Circle, Polygon, Rect)
  {"op": "set_drill", "refs_re", "from", "to"}                       NPTH pads: drill and pad size
  {"op": "add_circles", "items": [{"ref", "x", "y", "r", "layer", "fill": true, "w": 0.1}]}   footprint graphics
  {"op": "set_fpid", "refs": [...], "fpid": "nick:name"}
  {"op": "set_field", "ref", "name", "value"}
  {"op": "set_dnp", "ref", "dnp": true|false}
"""
import json
import math
import re
import sys

import pcbnew

mm = pcbnew.FromMM


def P(x, y):
    # round to the nearest nanometre; pcbnew.FromMM truncates
    return pcbnew.VECTOR2I(int(round(float(x) * 1e6)), int(round(float(y) * 1e6)))


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
    doomed_tracks, doomed_items, doomed_graphics = [], [], []
    for op in ops:
        kind = op["op"]
        if kind == "remove_tracks":
            for r in op["tracks"]:
                hit = [rec for rec in live if rec[1] == r["layer"] and rec[2] == r["net"] and not any(rec is x for x in doomed_tracks) and (
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
        elif kind == "move_track_points":
            n = 0
            for m in op["moves"]:
                for rec in live:
                    if rec[1] != m["layer"] or rec[2] != m["net"]:
                        continue
                    if abs(rec[3] - m["from"][0]) < 1e-4 and abs(rec[4] - m["from"][1]) < 1e-4:
                        rec[0].SetStart(P(*m["to"]))
                        n += 1
                    if abs(rec[5] - m["from"][0]) < 1e-4 and abs(rec[6] - m["from"][1]) < 1e-4:
                        rec[0].SetEnd(P(*m["to"]))
                        n += 1
            log.append({"moved_track_ends": n})
        elif kind == "move_vias":
            for m in op["moves"]:
                hit = [rec for rec in vias if rec[1] == m["net"] and abs(rec[2] - m["from"][0]) < 1e-3 and abs(rec[3] - m["from"][1]) < 1e-3]
                if len(hit) != 1:
                    raise SystemExit(f"via to move not found: {m}")
                hit[0][0].SetPosition(P(*m["to"]))
        elif kind == "set_ref_text":
            n = 0
            for ref, fp in fps.items():
                t = fp.Reference()
                if not t.IsVisible() or "Silk" not in t.GetLayerName() or ref in op.get("exclude", []):
                    continue
                if pcbnew.ToMM(t.GetTextHeight()) < op["min_height"] - 1e-6 or pcbnew.ToMM(t.GetTextThickness()) < op["min_thickness"] - 1e-6:
                    t.SetTextHeight(mm(max(op["min_height"], pcbnew.ToMM(t.GetTextHeight()))))
                    t.SetTextWidth(mm(max(op["min_height"], pcbnew.ToMM(t.GetTextWidth()))))
                    t.SetTextThickness(mm(max(op["min_thickness"], pcbnew.ToMM(t.GetTextThickness()))))
                    n += 1
            log.append({"ref_texts_enlarged": n})
        elif kind == "move_ref_text":
            fps[op["ref"]].Reference().SetPosition(P(op["x"], op["y"]))
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
        elif kind == "add_footprint":
            new = pcbnew.FootprintLoad(op["lib_dir"], op["name"])
            nick, name = op["fpid"].split(":")
            new.SetFPID(pcbnew.LIB_ID(nick, name))
            new.SetReference(op["ref"])
            new.SetValue(op["value"])
            new.SetPath(pcbnew.KIID_PATH(op["path"]))
            new.SetSheetname(op["sheetname"])
            new.SetSheetfile(op["sheetfile"])
            b.Add(new)
            new.SetPosition(P(op["x"], op["y"]))
            if op["side"] == "B.Cu":
                new.Flip(new.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            new.SetOrientationDegrees(op.get("rot", 0))
            for p in new.Pads():
                net = op["pad_nets"][p.GetNumber()]
                if net not in nets:
                    b.Add(pcbnew.NETINFO_ITEM(b, net))
                    nets = b.GetNetsByName()
                p.SetNet(nets[net])
            got = {p.GetNumber(): [round(pcbnew.ToMM(p.GetPosition().x), 4), round(pcbnew.ToMM(p.GetPosition().y), 4)] for p in new.Pads()}
            for k, v in op.get("expect_pads", {}).items():
                if abs(got[k][0] - v[0]) > 2e-3 or abs(got[k][1] - v[1]) > 2e-3:
                    raise SystemExit(f"{op['ref']}: pads are at {got}, expected {op['expect_pads']}")
            fps[op["ref"]] = new
            log.append({"add": op["ref"], "pads": got})
        elif kind == "set_pad_net":
            net = op["net"]
            if net not in nets:
                b.Add(pcbnew.NETINFO_ITEM(b, net))
                nets = b.GetNetsByName()
            for p in fps[op["ref"]].Pads():
                if p.GetNumber() == op["pad"]:
                    p.SetNet(nets[net])
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
                p.SetSize(layer, pcbnew.VECTOR2I(mm(g["sx_local"]), mm(g["sy_local"])))
                p.SetPosition(P(g["x"], g["y"]))
        elif kind == "reshape_pads":
            fp = fps[op["ref"]]
            for g in op["pads"]:
                hit = [p for p in fp.Pads() if abs(pcbnew.ToMM(p.GetPosition().x) - g["at"][0]) < 1e-3 and abs(pcbnew.ToMM(p.GetPosition().y) - g["at"][1]) < 1e-3]
                if not hit:
                    raise SystemExit(f"{op['ref']}: pad at {g['at']} not found")
                for p in hit:                  # connectors stack two pad numbers on one land
                    layer = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) else pcbnew.F_Cu
                    p.SetSize(layer, pcbnew.VECTOR2I(int(round(g["sx_local"] * 1e6)), int(round(g["sy_local"] * 1e6))))
                    p.SetPosition(P(*g["to"]))
        elif kind == "remove_graphics":
            n = 0
            for ref, fp in fps.items():
                if ("fpid" in op and fp.GetFPID().GetUniStringLibId() != op["fpid"]) or ("refs" in op and ref not in op["refs"]):
                    continue
                for item in fp.GraphicalItems():
                    if item.Type() == pcbnew.PCB_SHAPE_T and re.search(op["layer_re"], item.GetLayerName()) \
                            and ("shapes" not in op or item.ShowShape() in op["shapes"]):
                        doomed_graphics.append((fp, item))
                        n += 1
            log.append({"graphics_removed": n})
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
                # the radius point lies on the footprint's own +x axis, so every instance matches the library copy
                th = math.radians(fp.GetOrientationDegrees())
                s.SetEnd(P(a["x"] + a["r"] * math.cos(th), a["y"] - a["r"] * math.sin(th)))
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
    for fp, item in doomed_graphics:
        fp.Remove(item)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    pcbnew.SaveBoard(path, b)
    print(json.dumps({"ops": len(ops), "log": log}))


if __name__ == "__main__":
    main()
