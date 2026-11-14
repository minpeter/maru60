#!/usr/bin/env python3
"""Create the reverse-LED CAD candidate from a pinned baseline (KiCad 9).

This performs placement and pin-function conversion, not autorouting. The
baseline is never written. Pass --reset-board to rebuild the candidate board.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import pcbnew as p

OLD_NEW = {"1": "2", "2": "3", "3": "4", "4": "1"}
FUNCTION = {"1": "GND", "2": "DIN", "3": "VDD", "4": "DOUT"}
BASE = "LED_SK6812MINI_E_012_Reverse_Window4x3p6"
VALUE = "SK6812MINI-E-012"
URL = "https://datasheet.lcsc.com/datasheet/pdf/0907a34a701b4aef568078003f6e9eae.pdf"


def children(s):
    depth = 0
    quoted = escaped = False
    start = None
    rows = []
    for i, c in enumerate(s):
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
            continue
        if c == '"':
            quoted = True
        elif c == "(":
            depth += 1
            if depth == 2:
                start = i
        elif c == ")":
            if depth == 2:
                rows.append((start, i+1, s[start:i+1]))
            depth -= 1
    assert depth == 0 and not quoted
    return rows


def head(s):
    return re.match(r"\(\s*([^\s()]+)", s)[1]


def prop(s, name, value):
    pattern = r'(\(property "'+re.escape(name)+r'" )"(?:\\.|[^"\\])*"'
    s, n = re.subn(pattern, lambda m: m[1]+json.dumps(value), s, count=1)
    if not n:
        s = s[:-1]+f' (property "{name}" {json.dumps(value)} (at 0 0 0) (effects (font (size 1 1)) (hide yes))))'
    return s


def rot(q, angle):
    a = math.radians(angle)
    return (q[0]*math.cos(a)-q[1]*math.sin(a), q[0]*math.sin(a)+q[1]*math.cos(a))


def fmt(q):
    return " ".join(f"{v:.6f}" for v in q)


def make_footprint(name, sites):
    first = sites[0]
    x0, y0 = first["center_mm"]
    a0 = first["axis_degrees"]
    out = [f'(footprint "{name}" (version 20241229) (generator "pcbnew") (layer "F.Cu")',
           '(descr "Reverse mount; pinned 2025-11-22 MINI-E-012 numbering; custom outward lands; engineering only")',
           '(attr smd)',
           f'(property "Reference" "REF**" (at 0 -2.8 0) (layer "F.SilkS") (hide yes) (effects (font (size 1 1) (thickness .15))))',
           f'(property "Value" "{VALUE}" (at 0 2.8 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness .15))))']
    for site in sites:
        dx, dy = rot((site["center_mm"][0]-x0, site["center_mm"][1]-y0), -a0)
        delta = site["axis_degrees"]-a0
        def local(q):
            rx, ry = rot(q, -delta)
            return rx+dx, ry-dy
        def line(a, b, layer, w):
            out.append(f'(fp_line (start {fmt(local(a))}) (end {fmt(local(b))}) (stroke (width {w}) (type solid)) (layer "{layer}"))')
        # F.Cu library view sees the rear of a reverse-mounted LED. B.Cu
        # placement at 0 degrees therefore has DIN bottom-left, VDD bottom-right.
        pins = {"1": (-3.2, .75), "2": (-3.2, -.75), "3": (3.2, -.75), "4": (3.2, .75)}
        for num, q in pins.items():
            out.append(f'(pad "{num}" smd roundrect (at {fmt(local(q))} {delta}) (size 1.8 .9) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio .15))')
        for layer, x, y, w in (("F.CrtYd", 4.25, 2.05, .05), ("F.Fab", 1.6, 1.4, .1)):
            corners = [(-x, -y), (x, -y), (x, y), (-x, y)]
            for a, b in zip(corners, corners[1:]+corners[:1]):
                line(a, b, layer, w)
        # Actual routed internal contour: 4.0 x 3.6, R0.5. The four arcs are
        # native Edge.Cuts arcs, not a fake rectangular drill or silkscreen.
        for a, b in [((-1.5, -1.8), (1.5, -1.8)), ((2, -1.3), (2, 1.3)),
                     ((1.5, 1.8), (-1.5, 1.8)), ((-2, 1.3), (-2, -1.3))]:
            line(a, b, "Edge.Cuts", .05)
        for cx, cy, start in ((1.5, -1.3, -90), (1.5, 1.3, 0), (-1.5, 1.3, 90), (-1.5, -1.3, 180)):
            q = [local((cx+.5*math.cos(math.radians(a)), cy+.5*math.sin(math.radians(a)))) for a in (start, start+45, start+90)]
            out.append(f'(fp_arc (start {fmt(q[0])}) (mid {fmt(q[1])}) (end {fmt(q[2])}) (stroke (width .05) (type solid)) (layer "Edge.Cuts"))')
        # Pin 1 orientation mark outside the aperture and paste lands.
        q = local((-3.2, 1.62))
        e = local((-3.08, 1.62))
        out.append(f'(fp_circle (center {fmt(q)}) (end {fmt(e)}) (stroke (width .12) (type solid)) (fill solid) (layer "F.SilkS"))')
    return "\n".join(out)+"\n)\n"


def schematic(baseline, destination, names):
    path = baseline/"maru60-lighting.kicad_sch"
    s = path.read_text()
    lib_span = next((a, z, t) for a, z, t in children(s) if head(t) == "lib_symbols")
    old = next(t for _, _, t in children(lib_span[2]) if t.startswith('(symbol "Maru60:SK6805_EC15_001"'))
    new = old.replace("SK6805_EC15_001", "SK6812MINI_E_012")
    new = re.sub(r'\(number "([1-4])"', lambda m: '(number "'+OLD_NEW[m[1]]+'"', new)
    new = prop(new, "Value", VALUE)
    new = prop(new, "Footprint", "Maru60:"+BASE)
    new = prop(new, "Datasheet", URL)
    new = prop(new, "Description", "Reverse RGB LED; 2025-11-22 numbering 1=GND 2=DIN 3=VDD 4=DOUT")
    new = prop(new, "ki_fp_filters", "LED_SK6812MINI_E_012_Reverse*")
    changes = [(lib_span[0], lib_span[1], lib_span[2][:-1]+"\n"+new+")")]
    found = set()
    for a, z, t in children(s):
        if head(t) != "symbol":
            continue
        m = re.search(r'\(property "Reference" "([^"]+)"', t)
        if not m or m[1] not in names:
            continue
        ref = m[1]
        found.add(ref)
        t = t.replace('(lib_id "Maru60:SK6805_EC15_001")', '(lib_id "Maru60:SK6812MINI_E_012")')
        t = prop(t, "Value", VALUE)
        t = prop(t, "Footprint", "Maru60:"+names[ref])
        t = prop(t, "Datasheet", URL)
        t = prop(t, "LCSC", "C5149201")
        # Pin instances, when present, carry the revised pin numbers too.
        t = re.sub(r'\(pin "([1-4])"', lambda m: '(pin "'+OLD_NEW[m[1]]+'"', t)
        changes.append((a, z, t))
    assert found == set(names), (found, set(names))
    for a, z, t in sorted(changes, reverse=True):
        s = s[:a]+t+s[z:]
    (destination/path.name).write_text(s)
    sym = (baseline/"Maru60.kicad_sym").read_text()
    sym = sym.rstrip()[:-1]+"\n"+new.replace('(symbol "Maru60:SK6812MINI_E_012"', '(symbol "SK6812MINI_E_012"', 1)+"\n)\n"
    (destination/"Maru60.kicad_sym").write_text(sym)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--reset-board", action="store_true")
    args = ap.parse_args()
    src, dst = args.baseline/"pcb", args.candidate/"pcb"
    baseline = src/"maru60.kicad_pcb"
    before = hashlib.sha256(baseline.read_bytes()).hexdigest()
    plan = json.loads((args.candidate/"design/bottom-assembly-plan.json").read_text())
    target = dst/"maru60.kicad_pcb"
    if not args.reset_board and target.read_bytes() != baseline.read_bytes():
        raise SystemExit("Candidate is already edited; explicit --reset-board required to rebuild")
    b = p.LoadBoard(str(baseline))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    grouped = {}
    for site in plan["sites"]:
        grouped.setdefault(site["ref"], []).append(site)
    names, log, remove = {}, [], []
    for ref, sites in grouped.items():
        name = BASE+("_"+ref+"_Exclusive" if len(sites) > 1 else "")
        names[ref] = name
        text = make_footprint(name, sites)
        (dst/"Maru60.pretty"/(name+".kicad_mod")).write_text(text)
        new = p.FootprintLoad(str(dst/"Maru60.pretty"), name)
        assert new is not None
        old = fps[ref]
        nets = {OLD_NEW[pad.GetNumber()]: pad.GetNet() for pad in old.Pads()}
        for num, net in list(nets.items()):
            if net.GetNetname().startswith("unconnected-("):
                newname = re.sub(r"-Pad[1-4]\)$", "-Pad"+num+")", net.GetNetname())
                if newname != net.GetNetname():
                    replacement = p.NETINFO_ITEM(b, newname)
                    b.Add(replacement)
                    for t in b.GetTracks():
                        if t.GetNetCode() == net.GetNetCode():
                            t.SetNet(replacement)
                    nets[num] = replacement
        new.SetFPID(p.LIB_ID("Maru60", name))
        new.SetReference(ref)
        new.SetValue(VALUE)
        new.SetPath(old.GetPath())
        new.SetSheetname(old.GetSheetname())
        new.SetSheetfile(old.GetSheetfile())
        b.Add(new)
        new.SetPosition(p.VECTOR2I(*(round(v*1e6) for v in sites[0]["center_mm"])))
        new.Flip(new.GetPosition(), p.FLIP_DIRECTION_TOP_BOTTOM)
        new.SetOrientationDegrees(-sites[0]["axis_degrees"])
        for pad in new.Pads():
            pad.SetNet(nets[pad.GetNumber()])
            pad.SetPinFunction(FUNCTION[pad.GetNumber()])
        # Validate each of the physical pad positions, including both backspace
        # options; a reflected numbering mistake must fail before saving.
        expected_pads = []
        pattern = {"1": (-3.2, -.75), "2": (-3.2, .75), "3": (3.2, .75), "4": (3.2, -.75)}
        for site in sites:
            for num, q in pattern.items():
                x, y = rot(q, site["axis_degrees"])
                expected_pads.append((num, site["center_mm"][0]+x, site["center_mm"][1]+y))
        got = [(pad.GetNumber(), p.ToMM(pad.GetPosition().x), p.ToMM(pad.GetPosition().y)) for pad in new.Pads()]
        for num, x, y in expected_pads:
            assert any(n == num and math.hypot(x-xx, y-yy) < .00001 for n, xx, yy in got), (ref, expected_pads, got)
        remove.append(old)
        log.append({"ref": ref, "footprint": name, "side": "B.Cu", "pads": got,
                    "pad_functions": FUNCTION, "sites": len(sites)})
    for old in remove:
        b.Remove(old)
    schematic(src, dst, names)
    p.SaveBoard(str(target), b)
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == before
    (args.candidate/"design/led-cad-conversion.json").write_text(json.dumps({"status": "unrouted placement", "baseline_sha256": before, "refs": log}, indent=2)+"\n")
    print("Converted", len(grouped), "LED references,", len(plan["sites"]), "routed apertures; routing not yet repaired")


if __name__ == "__main__":
    main()
