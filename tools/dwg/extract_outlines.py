"""Extract the Rule 60 V3 plate outlines, top-mount holes and loose parts from INKC STUDIO's rule60-v3.dwg.

Usage:
    bun tools/dwg/dwg_to_json.mjs third_party/inkc-rule60-v3/rule60-v3.dwg /tmp/rule60-v3.json
    uv run tools/dwg/extract_outlines.py third_party/inkc-rule60-v3/rule60-v3.dwg /tmp/rule60-v3.json \
        spec/rule60-v3-outlines.json

Output frame ("plate frame", mm, X right, Y back, seen from the keycap side): origin at the bounding-box lower-left of
the `rule 60-6095(top)` plate. The `6095(gas)` plate is placed by aligning its Esc switch cutout with the top plate's,
which puts it at (0, +1.018). This is the plate frame of build_topcase_draft.py. Vertices are `[x, y, bulge]` with the
DWG LWPOLYLINE bulge (tan(theta/4), positive = counter-clockwise) on the segment from vertex i to i+1, wrapping when
`closed`. Loose parts the drawing does not place are written in their own bounding-box lower-left frame.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

Ent = dict[str, Any]

if len(sys.argv) != 4:
    raise SystemExit(__doc__)
DWG, SRC, OUT = map(Path, sys.argv[1:])

ents = json.loads(SRC.read_text())["entities"]
by_handle = {e["handle"]: e for e in ents}


def closed(e: Ent) -> bool:
    return bool(e["flag"] & 512 or e["flag"] & 1)  # libredwg LWPOLYLINE flag: 512 = closed, 16 = has bulges


def bulge_points(p0, p1, b, step=math.pi / 90):
    if abs(b) < 1e-12:
        return [p0, p1]
    th = 4 * math.atan(b)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    chord = math.hypot(dx, dy)
    r = chord / (2 * math.sin(th / 2))
    d = r * math.cos(th / 2)
    cx = (p0[0] + p1[0]) / 2 - dy / chord * d
    cy = (p0[1] + p1[1]) / 2 + dx / chord * d
    a0 = math.atan2(p0[1] - cy, p0[0] - cx)
    n = max(2, int(abs(th) / step) + 1)
    return [(cx + abs(r) * math.cos(a0 + th * i / n), cy + abs(r) * math.sin(a0 + th * i / n)) for i in range(n + 1)]


def bbox(e: Ent) -> tuple[float, float, float, float]:
    v = e["vertices"]
    pts = []
    for i in range(len(v) if closed(e) else len(v) - 1):
        a, b = v[i], v[(i + 1) % len(v)]
        pts += bulge_points((a["x"], a["y"]), (b["x"], b["y"]), a.get("bulge", 0) or 0)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def inside(inner, outer, m=0.01):
    return outer[0] - m <= inner[0] and inner[2] <= outer[2] + m and outer[1] - m <= inner[1] and inner[3] <= outer[3] + m


def esc_centre(plate_handle: str):
    """Centre of the left-most 14 x 14 switch cutout in the back row inside the plate."""
    pb = bbox(by_handle[plate_handle])
    sq = []
    for e in ents:
        if e["type"] != "LWPOLYLINE" or e["handle"] == plate_handle or len(e["vertices"]) > 12:
            continue
        b = bbox(e)
        if abs(b[2] - b[0] - 14) < 0.05 and abs(b[3] - b[1] - 14) < 0.05 and inside(b, pb):
            sq.append(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))
    top_y = max(y for _, y in sq)
    return min((x, y) for x, y in sq if abs(y - top_y) < 0.1)


def find_text(text: str) -> Ent:
    for e in ents:
        if e["type"] == "TEXT" and e["text"] == text:
            return e
    raise SystemExit(f"label {text!r} not found")


def plate_below(label: Ent, nverts: int) -> Ent:
    """Plate LWPOLYLINE whose bounding-box top-left is closest below the label insertion point."""
    lx, ly = label["startPoint"]["x"], label["startPoint"]["y"]
    best = None
    for e in ents:
        if e["type"] == "LWPOLYLINE" and len(e["vertices"]) == nverts:
            b = bbox(e)
            if b[3] < ly:
                d = math.hypot(b[0] - lx, b[3] - ly)
                if best is None or d < best[0]:
                    best = (d, e)
    assert best is not None, label["text"]
    return best[1]


def poly_record(name: str, e: Ent, dx: float, dy: float, extra: dict[str, Any]) -> dict[str, Any]:
    b = bbox(e)
    return {
        "name": name,
        "handle": e["handle"],
        "layer": e["layer"],
        "closed": closed(e),
        "bbox": [round(b[0] + dx, 4), round(b[1] + dy, 4), round(b[2] + dx, 4), round(b[3] + dy, 4)],
        "verts": [[round(v["x"] + dx, 4), round(v["y"] + dy, 4), round(v.get("bulge", 0) or 0, 6)] for v in e["vertices"]],
        **extra,
    }


def own_frame(e: Ent) -> tuple[float, float]:
    b = bbox(e)
    return -b[0], -b[1]


def piece(e: Ent) -> list[list[float]]:
    """Vertices [x, y, bulge] of an open LWPOLYLINE or LINE; the last vertex's bulge is unused."""
    if e["type"] == "LINE":
        return [[e["startPoint"]["x"], e["startPoint"]["y"], 0.0], [e["endPoint"]["x"], e["endPoint"]["y"], 0.0]]
    return [[v["x"], v["y"], v.get("bulge", 0) or 0.0] for v in e["vertices"]]


def reverse(p: list[list[float]]) -> list[list[float]]:
    """The same path walked backwards: segment i of the result is segment n-2-i of `p` with its bulge negated."""
    n = len(p)
    return [[p[n - 1 - i][0], p[n - 1 - i][1], -p[n - 2 - i][2] if i < n - 1 else 0.0] for i in range(n)]


def cutouts(plate: Ent) -> list[list[list[float]]]:
    """Closed cutout loops inside a plate outline. Some cutouts are drawn as open polylines plus LINEs: those are
    chained end to end; zero-length LINEs and LINEs lying on an existing cutout edge are dropped."""
    pb, tol = bbox(plate), 1e-3
    loops, open_pieces = [], []
    for e in ents:
        if e["handle"] == plate["handle"] or e["type"] not in ("LWPOLYLINE", "LINE") or not inside(bbox_any(e), pb):
            continue
        if e["type"] == "LWPOLYLINE" and closed(e):
            loops.append(piece(e))
        elif e["type"] == "LWPOLYLINE" or math.dist(piece(e)[0][:2], piece(e)[1][:2]) > tol:
            open_pieces.append(piece(e))
    leftovers = []
    while open_pieces:
        cur = open_pieces.pop(0)
        while math.dist(cur[0][:2], cur[-1][:2]) > tol:
            for i, p in enumerate(open_pieces):
                if math.dist(p[0][:2], cur[-1][:2]) < tol or math.dist(p[-1][:2], cur[-1][:2]) < tol:
                    nxt = open_pieces.pop(i)
                    nxt = nxt if math.dist(nxt[0][:2], cur[-1][:2]) < tol else reverse(nxt)
                    cur = cur[:-1] + [[cur[-1][0], cur[-1][1], nxt[0][2]]] + nxt[1:]
                    break
            else:
                break
        if math.dist(cur[0][:2], cur[-1][:2]) < tol:
            loops.append(cur[:-1])  # the last vertex repeats the first
        else:
            leftovers.append(cur)
    edges = [((a[0], a[1]), (b[0], b[1])) for lp in loops for a, b in zip(lp, lp[1:] + lp[:1])]
    for p in leftovers:  # a stray LINE drawn over a cutout edge
        assert len(p) == 2 and any(on_segment(p[0][:2], s) and on_segment(p[1][:2], s) for s in edges), p
    return loops


def on_segment(q, seg, tol=0.01) -> bool:
    (ax, ay), (bx, by) = seg
    if not (min(ax, bx) - tol <= q[0] <= max(ax, bx) + tol and min(ay, by) - tol <= q[1] <= max(ay, by) + tol):
        return False
    return abs((bx - ax) * (q[1] - ay) - (by - ay) * (q[0] - ax)) / max(math.dist((ax, ay), (bx, by)), 1e-9) < tol


def bbox_any(e: Ent) -> tuple[float, float, float, float]:
    if e["type"] == "LWPOLYLINE":
        return bbox(e)
    (ax, ay, _), (bx, by, _) = piece(e)
    return min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)


def frame_verts(loop: list[list[float]], dx: float, dy: float) -> list[list[float]]:
    return [[round(x + dx, 4), round(y + dy, 4), round(b, 6)] for x, y, b in loop]


top = plate_below(find_text("rule 60-6095(top)"), 80)
gas = plate_below(find_text("rule 60-6095(gas)"), 88)
tb = bbox(top)
T_DX, T_DY = -tb[0], -tb[1]
et, eg = esc_centre(top["handle"]), esc_centre(gas["handle"])
G_DX, G_DY = T_DX + et[0] - eg[0], T_DY + et[1] - eg[1]
# HHKB plate: the gas outline with split-backspace, 7u, plate-mount-stabilizer cutouts and no flex cuts. Its outline is
# vertex-identical to plate_gas, so it is placed by its bounding box and checked on the Esc cutout.
hhkb_label = "rule 60-6095(gas)--7u非左移+分裂退格"
hhkb = plate_below(find_text(hhkb_label), 88)
hb, gb = bbox(hhkb), bbox(gas)
H_DX, H_DY = G_DX + gb[0] - hb[0], G_DY + gb[1] - hb[1]
eh = esc_centre(hhkb["handle"])
assert math.dist((eh[0] + H_DX, eh[1] + H_DY), (et[0] + T_DX, et[1] + T_DY)) < 0.02, "HHKB plate Esc off the frame"
hhkb_cuts = sorted(cutouts(hhkb), key=lambda lp: (round(min(v[1] for v in lp), 1), min(v[0] for v in lp)))

holes = sorted(
    ({"name": "top_mount_hole", "handle": e["handle"], "layer": e["layer"],
      "c": [round(e["center"]["x"] + T_DX, 4), round(e["center"]["y"] + T_DY, 4)], "d": round(2 * e["radius"], 4)}
     for e in ents
     if e["type"] == "CIRCLE" and inside((e["center"]["x"], e["center"]["y"]) * 2, tb)),
    key=lambda h: (h["c"][1], h["c"][0]),
)

# The 19 labelled plate variants share these two outlines (vertex-identical) and differ only in their key cutouts.
variants = []
for t in (e for e in ents if e["type"] == "TEXT" and e["text"].startswith("rule 60-6095(")):
    for nv, kind in ((88, "gas"), (80, "top")):
        if f"({kind})" in t["text"]:
            variants.append({"label": t["text"], "label_handle": t["handle"], "plate": kind,
                             "outline_handle": plate_below(t, nv)["handle"]})

inner, outer = by_handle["2AF2"], by_handle["2AF3"]  # labels 2AE6 `内配 厚度4.5MM`, 2AE7 `外配装饰板 厚度3mm`
out: dict[str, Any] = {
    "format": "rule60-outlines/1",
    "units": "mm",
    "source": {
        "file": f"third_party/inkc-rule60-v3/{DWG.name}",
        "sha256": hashlib.sha256(DWG.read_bytes()).hexdigest(),
        "author": "INKC STUDIO",
        "converter": "@mlightcad/libredwg-web 0.8.2 via tools/dwg/dwg_to_json.mjs (libredwg code 4, non-fatal)",
        "extractor": "tools/dwg/extract_outlines.py",
    },
    "frame": {"name": "plate", "origin": "bbox lower-left of the 6095(top) plate", "x": "right",
              "y": "back (away from the typist)",
              "dwg_to_frame": {"top": [round(T_DX, 4), round(T_DY, 4)], "gas": [round(G_DX, 4), round(G_DY, 4)]}},
    "points": {"esc_switch_centre": [round(et[0] + T_DX, 4), round(et[1] + T_DY, 4)], "switch_pitch": 19.05},
    "outlines": [
        poly_record("plate_gas", gas, G_DX, G_DY, {"thickness": 1.5, "label": "rule 60-6095(gas)"}),
        poly_record("plate_gas_hhkb", hhkb, H_DX, H_DY,
                    {"thickness": 1.5, "label": hhkb_label,
                     "note": "HHKB plate (split backspace, 7u, plate-mount stabilizers, no flex cuts): plate_gas outline "
                             "placed on plate_gas, Esc cutout on points.esc_switch_centre",
                     "cutouts": [frame_verts(lp, H_DX, H_DY) for lp in hhkb_cuts]}),
        poly_record("plate_top", top, T_DX, T_DY, {"thickness": 1.5, "label": "rule 60-6095(top)"}),
        poly_record("battery_bay_filler", inner, *own_frame(inner),
                    {"thickness": 4.5, "label": "rule60v3  内配  厚度4.5MM", "placed": False,
                     "note": "filler for the 140 x 45 x 4.5 mm R2 battery bay (inference); not placed in the drawing"}),
        poly_record("back_deco_plate", outer, *own_frame(outer),
                    {"thickness": 3.0, "label": "rule60v3  外配装饰板   厚度3mm", "placed": False,
                     "note": "3 mm back decoration plate (acrylic UV / brushed steel option, inference); not placed"}),
    ],
    "circles": holes,
    "variants": variants,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
print(f"wrote {OUT}: {len(out['outlines'])} outlines, {len(holes)} holes, {len(variants)} variant labels")
for o in out["outlines"]:
    b = o["bbox"]
    print(f"  {o['name']:20s} {o['handle']} {len(o['verts'])} verts, {b[2] - b[0]:.3f} x {b[3] - b[1]:.3f}")
