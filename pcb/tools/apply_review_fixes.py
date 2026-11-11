#!/usr/bin/env python3
"""Apply the footprint/layout corrections from the 2026-11-11 datasheet review (KiCad 9 pcbnew).

usage: apply_review_fixes.py BOARD.kicad_pcb

1. U13 TPD6E05U06 (RVZ-14): pads 0.30 x 0.65 mm with full paste -> TI land pattern
   4221500/A: 0.20 x 0.50 mm on the same 0.5 mm pitch, same outer pad edge.
2. L1 (RP2350 core-regulator inductor): copper-pour keep-out on B.Cu between the
   pads, as RP2350 datasheet section 6.3.8.1 asks ("cut away any extra copper
   underneath the inductor").
3. C102 (VREG_VIN capacitor): back to the Raspberry Pi reference position
   (0.18 mm further from C103; the full 0.23 mm would violate clearance to the
   +1V1 track on its other side), widening the +3V3 / +1V1 pad gap from 0.24 to 0.42 mm.
"""
import json
import sys

import pcbnew

mm = pcbnew.FromMM


def main():
    path = sys.argv[1]
    b = pcbnew.LoadBoard(path)
    out = {}

    u13 = b.FindFootprintByReference("U13")
    c = u13.GetPosition()
    n = 0
    for p in u13.Pads():
        layer = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
        sz = p.GetSize(layer)
        long_, short = max(sz.x, sz.y), min(sz.x, sz.y)
        if abs(pcbnew.ToMM(long_) - 0.65) > 1e-3 or abs(pcbnew.ToMM(short) - 0.30) > 1e-3:
            raise SystemExit(f"U13 pad {p.GetNumber()} is {pcbnew.ToMM(sz.x)} x {pcbnew.ToMM(sz.y)}, not the expected 0.30 x 0.65")
        horizontal = sz.x > sz.y           # pad long axis in board coordinates
        p.SetSize(layer, pcbnew.VECTOR2I(mm(0.50), mm(0.20)) if horizontal else pcbnew.VECTOR2I(mm(0.20), mm(0.50)))
        pos = p.GetPosition()
        d = mm(0.075)                      # keep the outer edge: centre moves out by (0.65 - 0.50) / 2
        if horizontal:
            pos.x += d if pos.x > c.x else -d
        else:
            pos.y += d if pos.y > c.y else -d
        p.SetPosition(pos)
        n += 1
    out["u13_pads"] = n

    l1 = b.FindFootprintByReference("L1")
    pads = sorted(l1.Pads(), key=lambda p: (p.GetPosition().y, p.GetPosition().x))
    bb0, bb1 = pads[0].GetBoundingBox(), pads[-1].GetBoundingBox()
    x0 = min(bb0.GetLeft(), bb1.GetLeft()) - mm(0.05)
    x1 = max(bb0.GetRight(), bb1.GetRight()) + mm(0.05)
    y0, y1 = bb0.GetBottom() + mm(0.02), bb1.GetTop() - mm(0.02)
    if y1 <= y0:    # pads side by side in x
        pads = sorted(l1.Pads(), key=lambda p: p.GetPosition().x)
        bb0, bb1 = pads[0].GetBoundingBox(), pads[-1].GetBoundingBox()
        y0 = min(bb0.GetTop(), bb1.GetTop()) - mm(0.05)
        y1 = max(bb0.GetBottom(), bb1.GetBottom()) + mm(0.05)
        x0, x1 = bb0.GetRight() + mm(0.02), bb1.GetLeft() - mm(0.02)
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowTracks(False)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetLayer(l1.GetLayer())
    z.SetZoneName("RP2350 L1 body: no copper pour between the inductor pads (datasheet 6.3.8.1)")
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(x, y)
    b.Add(z)
    out["l1_keepout_mm"] = [pcbnew.ToMM(v) for v in (x0, y0, x1, y1)]

    c102 = b.FindFootprintByReference("C102")
    c103 = b.FindFootprintByReference("C103")
    pos = c102.GetPosition()
    gap = pcbnew.ToMM(c103.GetPosition().x - pos.x)
    if abs(gap - 0.71) > 0.02:
        raise SystemExit(f"C102/C103 spacing is {gap}, expected about 0.71 mm before the fix")
    pos.x -= mm(0.18)   # 0.23 would leave only 0.127 mm to the +1V1 track on its other side
    c102.SetPosition(pos)
    out["c102_x_mm"] = pcbnew.ToMM(pos.x)

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    pcbnew.SaveBoard(path, b)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
