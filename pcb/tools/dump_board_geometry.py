"""Dump board geometry to JSON (run inside the KiCad container)."""
import pcbnew, json, sys
b = pcbnew.LoadBoard(sys.argv[1])
mm = 1e-6
def poly(sps):
    out = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i)
        out.append([[o.CPoint(j).x*mm, o.CPoint(j).y*mm] for j in range(o.PointCount())])
    return out
d = {"fps": [], "tracks": [], "vias": [], "zones": [], "edges": [], "drawings": []}
for f in b.GetFootprints():
    bb = f.GetBoundingBox(False, False) if hasattr(f, 'GetBoundingBox') else None
    fp = {"ref": f.GetReference(), "value": f.GetValue(), "fpid": str(f.GetFPID().GetUniStringLibId()),
          "x": f.GetPosition().x*mm, "y": f.GetPosition().y*mm, "rot": f.GetOrientationDegrees(),
          "layer": f.GetLayerName(), "attr": f.GetAttributes(), "pads": [], "dnp": f.IsDNP(),
          "bbox": [bb.GetX()*mm, bb.GetY()*mm, bb.GetWidth()*mm, bb.GetHeight()*mm]}
    try:
        f.BuildCourtyardCaches()
        cy = f.GetCourtyard(pcbnew.F_CrtYd if f.GetLayer()==pcbnew.F_Cu else pcbnew.B_CrtYd)
        fp["courtyard"] = poly(cy)
    except Exception as e:
        fp["courtyard"] = []
    for p in f.Pads():
        lay = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        sps = pcbnew.SHAPE_POLY_SET()
        p.TransformShapeToPolygon(sps, lay, 0, 5000, pcbnew.ERROR_INSIDE)
        fp["pads"].append({"num": p.GetNumber(), "net": p.GetNetname(), "x": p.GetPosition().x*mm, "y": p.GetPosition().y*mm,
                           "sx": p.GetSize(lay).x*mm, "sy": p.GetSize(lay).y*mm, "shape": p.GetShape(lay),
                           "drill": [p.GetDrillSize().x*mm, p.GetDrillSize().y*mm], "attr": p.GetAttribute(),
                           "layers": [b.GetLayerName(l) for l in p.GetLayerSet().Seq()], "poly": poly(sps),
                           "rot": p.GetOrientationDegrees(), "lx": p.GetFPRelativePosition().x*mm, "ly": p.GetFPRelativePosition().y*mm,
                           "pinfn": p.GetPinFunction()})
    d["fps"].append(fp)
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        d["vias"].append({"x": t.GetPosition().x*mm, "y": t.GetPosition().y*mm, "d": t.GetWidth(pcbnew.F_Cu)*mm, "drill": t.GetDrill()*mm, "net": t.GetNetname()})
    elif t.Type() == pcbnew.PCB_ARC_T:
        d["tracks"].append({"x1": t.GetStart().x*mm, "y1": t.GetStart().y*mm, "x2": t.GetEnd().x*mm, "y2": t.GetEnd().y*mm, "w": t.GetWidth()*mm, "layer": t.GetLayerName(), "net": t.GetNetname(), "arc": [t.GetMid().x*mm, t.GetMid().y*mm]})
    else:
        d["tracks"].append({"x1": t.GetStart().x*mm, "y1": t.GetStart().y*mm, "x2": t.GetEnd().x*mm, "y2": t.GetEnd().y*mm, "w": t.GetWidth()*mm, "layer": t.GetLayerName(), "net": t.GetNetname()})
for z in b.Zones():
    zz = {"net": z.GetNetname(), "name": z.GetZoneName(), "layers": [b.GetLayerName(l) for l in z.GetLayerSet().Seq()], "keepout": z.GetIsRuleArea(),
          "outline": poly(z.Outline()), "fill": {}}
    for l in z.GetLayerSet().Seq():
        try:
            zz["fill"][b.GetLayerName(l)] = [[[[p.x*mm, p.y*mm] for p in [o.CPoint(j) for j in range(o.PointCount())]] for o in [fp_.Outline(i)] + [fp_.Hole(i, h) for h in range(fp_.HoleCount(i))]] for fp_ in [z.GetFilledPolysList(l)] for i in range(fp_.OutlineCount())]
        except Exception as e:
            zz["fill"][b.GetLayerName(l)] = []
    d["zones"].append(zz)
edge_items = list(b.GetDrawings()) + [item for fp in b.GetFootprints() for item in fp.GraphicalItems() if item.GetLayerName() == "Edge.Cuts"]
for dr in edge_items:
    if dr.GetLayerName() == "Edge.Cuts" and dr.Type() == pcbnew.PCB_SHAPE_T:
        d["edges"].append({"shape": dr.GetShape(), "x1": dr.GetStart().x*mm, "y1": dr.GetStart().y*mm, "x2": dr.GetEnd().x*mm, "y2": dr.GetEnd().y*mm, "w": dr.GetWidth()*mm,
                           "c": [dr.GetCenter().x*mm, dr.GetCenter().y*mm] if dr.GetShape() in (pcbnew.SHAPE_T_ARC, pcbnew.SHAPE_T_CIRCLE) else None, "r": dr.GetRadius()*mm if dr.GetShape() in (pcbnew.SHAPE_T_ARC, pcbnew.SHAPE_T_CIRCLE) else None,
                           "mid": [dr.GetArcMid().x*mm, dr.GetArcMid().y*mm] if dr.GetShape() == pcbnew.SHAPE_T_ARC else None})
    elif dr.Type() in (pcbnew.PCB_TEXT_T,):
        d["drawings"].append({"text": dr.GetText(), "layer": dr.GetLayerName(), "x": dr.GetPosition().x*mm, "y": dr.GetPosition().y*mm})
# Native board material, including rounded outside corners and every internal
# Edge.Cuts aperture. Consumers must retain the holes instead of using a bbox.
outline = pcbnew.SHAPE_POLY_SET()
if not b.GetBoardPolygonOutlines(outline):
    raise RuntimeError("Invalid board outline; cannot safely export routing geometry")
d["board_material"] = [
    [[[o.CPoint(j).x*mm, o.CPoint(j).y*mm] for j in range(o.PointCount())]
     for o in [outline.Outline(i)] + [outline.Hole(i, h) for h in range(outline.HoleCount(i))]]
    for i in range(outline.OutlineCount())]
json.dump(d, open(sys.argv[2], "w"))
print(len(d["fps"]), len(d["tracks"]), len(d["vias"]), len(d["zones"]), len(d["edges"]))
