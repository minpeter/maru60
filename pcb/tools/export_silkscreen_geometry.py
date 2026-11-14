#!/usr/bin/env python3
"""Export native stroke polygons for safe reference-label placement (KiCad 9)."""
import json
import sys
import pcbnew as p

b = p.LoadBoard(sys.argv[1])
out = []
def record(item, ref, kind):
    if item.GetLayerName() not in ("F.Silkscreen", "B.Silkscreen", "F.SilkS", "B.SilkS"):
        return
    if hasattr(item, "IsVisible") and not item.IsVisible():
        return
    shape = p.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(shape, item.GetLayer(), 0, 5000, p.ERROR_OUTSIDE)
    rings = []
    for i in range(shape.OutlineCount()):
        o = shape.Outline(i)
        rings.append([[o.CPoint(j).x/1e6, o.CPoint(j).y/1e6] for j in range(o.PointCount())])
    out.append({"uuid": item.m_Uuid.AsString(), "ref": ref, "kind": kind,
                "layer": item.GetLayerName(), "x": item.GetPosition().x/1e6, "y": item.GetPosition().y/1e6,
                "text": item.GetText() if hasattr(item, "GetText") else None, "poly": rings})
for f in b.GetFootprints():
    record(f.Reference(), f.GetReference(), "reference")
    record(f.Value(), f.GetReference(), "value")
    for item in f.GraphicalItems():
        record(item, f.GetReference(), "graphic")
for item in b.GetDrawings():
    record(item, "", "drawing")
json.dump(out, open(sys.argv[2], "w"))
print(len(out), "silkscreen items")
