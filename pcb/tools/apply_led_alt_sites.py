#!/usr/bin/env python3
"""Give option-position key LEDs a second land site (run with KiCad 9 pcbnew).

usage: apply_led_alt_sites.py BOARD.kicad_pcb SPEC.json

SPEC.json holds two lists:

  "top_sites":     entries written by plan_led_alt_sites.py: four extra F.Cu pads
                   for the same footprint in a gap between housings, with the
                   F.Cu tracks and GND via that connect them.
  "bottom_relays": hand-specified entries.  The footprint is flipped to B.Cu at
                   "relay" (this becomes its placement site), four F.Cu pads are
                   left at the old window position, and the listed vias and
                   tracks connect the two sites.

Every LED keeps its reference, nets and position in the chain; only the number
of places it may be soldered changes.  Exactly one site per LED is populated.
"""
import json
import sys

import pcbnew


def mm(v):
    return pcbnew.FromMM(float(v))


def add_track(b, nets, a):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(mm(a["x1"]), mm(a["y1"])))
    t.SetEnd(pcbnew.VECTOR2I(mm(a["x2"]), mm(a["y2"])))
    t.SetWidth(mm(a["w"]))
    t.SetLayer(b.GetLayerID(a["layer"]))
    t.SetNet(nets[a["net"]])
    b.Add(t)


def main():
    board_path, spec_path = sys.argv[1], sys.argv[2]
    spec = json.load(open(spec_path))
    b = pcbnew.LoadBoard(board_path)
    nets = b.GetNetsByName()
    proto = next(t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and abs(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) - 0.5) < 1e-6
                 and abs(pcbnew.ToMM(t.GetDrill()) - 0.25) < 1e-6)

    def add_via(v):
        via = proto.Duplicate()
        via.SetPosition(pcbnew.VECTOR2I(mm(v["x"]), mm(v["y"])))
        via.SetNet(nets[v["net"]])
        b.Add(via)

    report = []
    for s in spec.get("top_sites", []):
        fp = b.FindFootprintByReference(s["ref"])
        by_num = {p.GetNumber(): p for p in fp.Pads()}
        for num, (x, y) in s["alt_pads"].items():
            src = by_num[num]
            p = pcbnew.PAD(fp)
            p.ImportSettingsFrom(src)
            p.SetNumber(num)
            p.SetNet(src.GetNet())
            p.SetPinFunction(src.GetPinFunction())
            p.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            fp.Add(p)
        for t in s["add_tracks"]:
            add_track(b, nets, t)
        for v in s["add_vias"]:
            add_via(v)
        report.append({"ref": s["ref"], "kind": "top", "alt_site": s["alt_site"]})

    for s in spec.get("bottom_relays", []):
        fp = b.FindFootprintByReference(s["ref"])
        old = [(p.GetNumber(), p.GetPosition().x, p.GetPosition().y, p.GetNet(), p.GetPinFunction()) for p in fp.Pads()]
        template = b.FindFootprintByReference(s["template"])   # an untouched F.Cu LED: source of F.Cu pad settings
        tpads = {p.GetNumber(): p for p in template.Pads()}
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetPosition(pcbnew.VECTOR2I(mm(s["relay"][0]), mm(s["relay"][1])))
        fp.SetOrientationDegrees(s.get("relay_rotation", 0))
        got = {p.GetNumber(): [round(pcbnew.ToMM(p.GetPosition().x), 4), round(pcbnew.ToMM(p.GetPosition().y), 4)] for p in fp.Pads()}
        if "expect_pads" in s and any(abs(got[k][0] - v[0]) > 1e-3 or abs(got[k][1] - v[1]) > 1e-3 for k, v in s["expect_pads"].items()):
            raise SystemExit(f"{s['ref']}: flipped pads are at {got}, expected {s['expect_pads']}")
        for num, x, y, net, fn in old:
            p = pcbnew.PAD(fp)
            p.ImportSettingsFrom(tpads[num])
            p.SetNumber(num)
            p.SetNet(net)
            p.SetPinFunction(fn)
            p.SetPosition(pcbnew.VECTOR2I(x, y))
            fp.Add(p)
        for v in s["add_vias"]:
            add_via(v)
        for t in s["add_tracks"]:
            add_track(b, nets, t)
        report.append({"ref": s["ref"], "kind": "bottom", "relay": s["relay"], "relay_pads": got})
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    pcbnew.SaveBoard(board_path, b)
    print(json.dumps(report))


if __name__ == "__main__":
    main()
