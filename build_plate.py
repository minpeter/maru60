"""INKC Rule60 V3 HHKB gasket plate as fabrication files: Gerbers for a 1.6 mm FR4 plate (JLCPCB-style 2-layer board)
and an R12 DXF for laser or CNC cutting in PC or aluminium.

The geometry is INKC STUDIO's `rule 60-6095(gas)--7u非左移+分裂退格` drawing (spec outline `plate_gas_hhkb`, extracted
from third_party/inkc-rule60-v3/rule60-v3.dwg by tools/dwg/extract_outlines.py), unchanged: the gas outline the Maru60
cases are built around, 62 switch cutouts (the 60 HHKB keys plus the two bottom-row ends under the top-case blockers),
split backspace, 1.75u + 1u right shift, plate-mount stabilizer cutouts for both 2.25u keys and the 7u spacebar, no flex
cuts. Arcs stay true arcs in both files.

Gerbers: board outline; a copper pour on both sides pulled `COPPER_PULLBACK` back from every edge, so the router never
cuts copper and the board reads as an ordinary 2-layer board; solder mask on both sides with no openings (full cover).

Checks (asserted, written to evidence/plate-report.json): outline identical to `plate_gas`; each of the 60 HHKB keys
in its own switch cutout, 14.00 between the clip edges; a stabilizer housing cutout at +-11.938 mm (2.25u) and
+-57.15 mm (7u); every void reachable by a 1.0 mm router bit; copper clear of every edge. Writes
models/rule60-v3-hhkb-gas-plate-fr4-gerber.zip and models/rule60-v3-hhkb-gas-plate.dxf.

Usage:
    uv run build_plate.py
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

import rule60_spec as spec

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
NAME = "rule60-v3-hhkb-gas-plate"
U = 19.05
COPPER_PULLBACK = 0.50  # Copper to every routed edge (JLCPCB minimum 0.3 mm)
ROUTER_BIT = 1.00       # Smallest common routing bit; concave corners below its radius would be left uncut
SWITCH = 14.00          # MX plate cutout
STAB_OFFSETS = {2.25: 11.938, 7.0: 57.15}  # Plate-mount stabilizer housing centres from the switch centre

REC = spec.outline("plate_gas_hhkb")


def hhkb_keys() -> list[tuple[float, float, float]]:
    """(x, y, width in u) of the 60 HHKB keys in the plate frame, from the Esc switch centre on the 19.05 grid. Bottom
    row: 1.5u top-case blocker, 1u, 1.5u, 7u, 1.5u, 1u, 1.5u blocker."""
    ex, ey = spec.point("esc_switch_centre")
    rows = [[1.0] * 15, [1.5] + [1.0] * 12 + [1.5], [1.75] + [1.0] * 11 + [2.25], [2.25] + [1.0] * 10 + [1.75, 1.0],
            [None, 1.0, 1.5, 7.0, 1.5, 1.0, None]]
    keys = []
    for r, widths in enumerate(rows):
        x = 0.0
        for w in widths:
            if w is not None:
                keys.append((ex - U / 2 + (x + w / 2) * U, ey - r * U, w))
            x += 1.5 if w is None else w
    return keys


def check(outer: Polygon, cutouts: list[Polygon], plate: Any, copper: Any) -> dict[str, Any]:
    assert [v[:2] for v in REC["verts"]] == [v[:2] for v in spec.outline("plate_gas")["verts"]], "outline != plate_gas"
    assert plate.is_valid and all(c.within(outer) for c in cutouts), "cutouts must lie inside the outline"
    holes = unary_union(cutouts)
    keys = hhkb_keys()
    assert len(keys) == 60
    owner: dict[tuple[float, float], int] = {}
    wide: list[dict[str, Any]] = []
    stabs: list[dict[str, Any]] = []
    for cx, cy, w in keys:
        hit = [i for i, c in enumerate(cutouts) if c.contains(Point(cx, cy))]
        assert len(hit) == 1 and hit[0] not in owner.values(), (cx, cy, hit)
        owner[(round(cx, 3), round(cy, 3))] = hit[0]
        # Switch section: 14.00 between the clip edges (across the centre line); at least 14.00 along a line 6 mm above
        # the centre (above the 2.25u stabilizer housings). Wider is a shared multi-layout cutout: the clips still hold.
        (_, y0, _, y1) = LineString([(cx, cy - 9.0), (cx, cy + 9.0)]).intersection(cutouts[hit[0]]).bounds
        (x0, _, x1, _) = LineString([(cx - 12.0, cy + 6.0), (cx + 12.0, cy + 6.0)]).intersection(cutouts[hit[0]]).bounds
        assert max(abs(y0 - (cy - SWITCH / 2)), abs(y1 - (cy + SWITCH / 2))) < 0.02, (cx, cy, y0, y1)
        assert x0 <= cx - SWITCH / 2 + 0.02 and x1 >= cx + SWITCH / 2 - 0.02, (cx, cy, x0, x1)
        if x1 - x0 > SWITCH + 0.05:
            wide.append({"key": [round(cx, 2), round(cy, 2), w], "x_from_centre": [round(x0 - cx, 2), round(x1 - cx, 2)]})
    for cx, cy, w in keys:
        if w in STAB_OFFSETS:
            for side in (-1.0, 1.0):
                hx = cx + side * STAB_OFFSETS[w]
                (_, y0, _, y1) = LineString([(hx, cy - 10.0), (hx, cy + 10.0)]).intersection(holes).bounds
                assert y1 - y0 >= 12.3, (w, hx, y0, y1)  # a Cherry-style plate-mount housing is 12.3 mm long
                stabs.append({"key_u": w, "x": round(hx, 3), "y_span_from_centre": [round(y0 - cy, 2), round(y1 - cy, 2)]})
    gauge = Polygon(spec.value("keycaps.hhkb_gauge"))
    spare = [c for i, c in enumerate(cutouts) if i not in owner.values()]
    assert all(not gauge.intersects(c.centroid) for c in spare), "a spare cutout sits inside the HHKB keycap field"
    # Router reach: material a 1.0 mm bit cannot clear in the voids (narrow slots, tight concave corners).
    r = ROUTER_BIT / 2
    voids = [c.difference(c.buffer(-r, quad_segs=32).buffer(r, quad_segs=32)) for c in cutouts]
    voids.append(outer.buffer(r, quad_segs=32).buffer(-r, quad_segs=32).difference(outer))
    uncut = max(v.area for v in voids)
    assert uncut < 0.01, f"{uncut:.3f} mm2 of a void is out of reach of a {ROUTER_BIT} mm bit"
    assert plate.buffer(-(COPPER_PULLBACK - 1e-3)).contains(copper), "copper closer than the pullback to an edge"
    return {
        "outline": "plate_gas (identical vertices): the outline the Maru60 top and bottom cases are verified around",
        "bounds_mm": [round(v, 3) for v in outer.bounds],
        "cutouts": len(cutouts), "hhkb_keys": len(keys), "switch_cutout_mm": SWITCH,
        "spare_cutouts_under_blockers": [[round(v, 2) for v in c.bounds] for c in spare],
        "shared_wider_cutouts": wide,
        "stabilizer_housings": stabs,
        "router_bit_mm": ROUTER_BIT, "max_uncut_void_mm2": round(uncut, 4),
        "copper_pullback_mm": COPPER_PULLBACK, "plate_area_mm2": round(plate.area, 1),
    }


# --- Gerber (RS-274X, mm, 4.6) -------------------------------------------------------------------------------------
def g(v: float) -> str:
    return str(round(v * 1e6))


def gerber(function: str, body: list[str]) -> str:
    head = [f"%TF.FileFunction,{function}*%", "%FSLAX46Y46*%", "%MOMM*%", "%LPD*%", "G75*"]
    return "\n".join(head + body + ["M02*"]) + "\n"


def outline_strokes(loops: list[list[list[float]]]) -> list[str]:
    """Each [x, y, bulge] loop as one closed stroke of a 0.1 mm aperture; bulges become G02/G03 arcs."""
    out = ["%ADD10C,0.100000*%", "D10*"]
    for lp in loops:
        out.append(f"G01*\nX{g(lp[0][0])}Y{g(lp[0][1])}D02*")
        for k, (x0, y0, b) in enumerate(lp):
            x1, y1, _ = lp[(k + 1) % len(lp)]
            if abs(b) < 1e-9:
                out.append(f"G01*\nX{g(x1)}Y{g(y1)}D01*")
            else:
                cx, cy, _, theta = spec.bulge_arc(x0, y0, x1, y1, b)
                out.append(f"{'G03' if theta > 0 else 'G02'}*\nX{g(x1)}Y{g(y1)}I{g(cx - x0)}J{g(cy - y0)}D01*")
    return out


def regions(shape: Any) -> list[str]:
    """Dark region per polygon exterior, then clear regions for its holes."""
    out = []
    for poly in getattr(shape, "geoms", [shape]):
        poly = orient(poly)
        for polarity, ring in [("D", poly.exterior)] + [("C", h) for h in poly.interiors]:
            pts = list(ring.coords)
            out += [f"%LP{polarity}*%", "G36*", f"X{g(pts[0][0])}Y{g(pts[0][1])}D02*"]
            out += [f"G01X{g(x)}Y{g(y)}D01*" for x, y in pts[1:]] + ["G37*"]
    return out + ["%LPD*%"]


# --- DXF R12: closed POLYLINEs with bulges -------------------------------------------------------------------------
def dxf(loops: list[list[list[float]]]) -> str:
    out = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
           "0", "SECTION", "2", "ENTITIES"]
    for lp in loops:
        out += ["0", "POLYLINE", "8", "0", "66", "1", "70", "1"]
        for x, y, b in lp:
            out += ["0", "VERTEX", "8", "0", "10", f"{x:.4f}", "20", f"{y:.4f}", "42", f"{b:.6f}"]
        out += ["0", "SEQEND", "8", "0"]
    return "\n".join(out + ["0", "ENDSEC", "0", "EOF"]) + "\n"


def main() -> None:
    loops = [REC["verts"]] + REC["cutouts"]
    outer = Polygon(spec.verts_points(REC["verts"], 48))
    cutouts = [Polygon(spec.verts_points(c, 48)) for c in REC["cutouts"]]
    plate = outer.difference(unary_union(cutouts))
    copper = plate.buffer(-COPPER_PULLBACK, quad_segs=16)
    report = check(outer, cutouts, plate, copper)

    # Deterministic output (fixed zip timestamps), so the build publishes straight to models/ and evidence/.
    files = {
        f"{NAME}.GKO": gerber("Profile,NP", outline_strokes(loops)),
        f"{NAME}.GTL": gerber("Copper,L1,Top", regions(copper)),
        f"{NAME}.GBL": gerber("Copper,L2,Bot", regions(copper)),
        f"{NAME}.GTS": gerber("Soldermask,Top", []),
        f"{NAME}.GBS": gerber("Soldermask,Bot", []),
    }
    with zipfile.ZipFile(MODELS / f"{NAME}-fr4-gerber.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in files.items():
            z.writestr(zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), text)
    (MODELS / f"{NAME}.dxf").write_text(dxf(loops))
    report["source"] = {"drawing": REC["label"], "handle": REC["handle"], "author": "INKC STUDIO"}
    report["files"] = [f"models/{NAME}-fr4-gerber.zip: " + ", ".join(sorted(files)), f"models/{NAME}.dxf"]
    (ROOT / "evidence" / "plate-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "stabilizer_housings"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
