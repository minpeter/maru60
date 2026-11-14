"""Routed-geometry helpers for the signal-integrity checks.

Reads the JSON written by pcb/tools/dump_board_geometry.py (all values in mm)
and answers, per net:
  * copper length per (layer, width), via count
  * the pad-to-pad path (shortest route through the copper graph) and every
    branch that hangs off it (stubs)
  * which other nets run beside it (edge-to-edge gap, coupled length)
  * whether the adjacent inner plane (In1 under F.Cu, In2 over B.Cu) is solid
    copper under every sample of the route

Nothing here writes to the board.
"""
from __future__ import annotations

import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union, nearest_points
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[3]
# written by run_all.py from the board file (pcb/tools/dump_board_geometry.py in the KiCad container)
DEFAULT_GEOMETRY = ROOT / "build" / "si" / "board.json"
PLANE_FOR = {"F.Cu": "In1.Cu", "B.Cu": "In2.Cu"}
Q = 1e-3  # snapping grid, mm


def _k(x, y):
    return (round(x / Q), round(y / Q))


class Board:
    def __init__(self, path=DEFAULT_GEOMETRY):
        d = json.loads(Path(path).read_text())
        self.raw = d
        self.fps = {f["ref"]: f for f in d["fps"]}
        self.tracks = d["tracks"]
        self.vias = d["vias"]
        self.by_net = defaultdict(list)
        for t in self.tracks:
            self.by_net[t["net"]].append(t)
        self.vias_by_net = defaultdict(list)
        for v in self.vias:
            self.vias_by_net[v["net"]].append(v)
        self.pads_by_net = defaultdict(list)
        for f in d["fps"]:
            for p in f["pads"]:
                q = dict(p)
                q["ref"] = f["ref"]
                self.pads_by_net[p["net"]].append(q)
        # plane fills
        self.plane = {}
        for layer in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"):
            polys = []
            for z in d["zones"]:
                if z["keepout"] or z["net"] != "GND":
                    continue
                for rings in z["fill"].get(layer, []):
                    if len(rings[0]) >= 3:
                        polys.append(Polygon(rings[0], [h for h in rings[1:] if len(h) >= 3]))
            self.plane[layer] = unary_union(polys) if polys else None
        # spatial index of all track segments per layer
        self._seg = {}
        for layer in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"):
            segs = [t for t in self.tracks if t["layer"] == layer]
            geoms = [LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]) for t in segs]
            self._seg[layer] = (segs, geoms, STRtree(geoms) if geoms else None)
        pads, pg = defaultdict(list), defaultdict(list)
        for f in d["fps"]:
            for p in f["pads"]:
                if not p["poly"] or len(p["poly"][0]) < 3:
                    continue
                poly = Polygon(p["poly"][0])
                for layer in ("F.Cu", "B.Cu"):
                    if layer in p["layers"] or p["drill"][0] > 0:
                        q = dict(p)
                        q["ref"] = f["ref"]
                        pads[layer].append(q)
                        pg[layer].append(poly)
        self._pad = {l: (pads[l], pg[l], STRtree(pg[l])) for l in pads}

    # ---- basic statistics -------------------------------------------------
    def net_stats(self, net):
        by = defaultdict(float)
        for t in self.by_net[net]:
            by[(t["layer"], round(t["w"], 3))] += math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"])
        return {
            "length_mm": round(sum(by.values()), 3),
            "by_layer_width": {f"{l}:{w}": round(v, 3) for (l, w), v in sorted(by.items())},
            "vias": len(self.vias_by_net[net]),
            "pads": sorted(f"{p['ref']}.{p['num']}" for p in self.pads_by_net[net]),
        }

    # ---- copper graph -----------------------------------------------------
    def graph(self, net):
        """Nodes are (layer, xq, yq) or ('pad', ref, num, index). Edges carry length, layer, width."""
        segs = self.by_net[net]
        # split segments where another endpoint of the same net/layer lies on them
        ends = defaultdict(set)
        radii = defaultdict(dict)
        for t in segs:
            ends[t["layer"]].add((t["x1"], t["y1"]))
            ends[t["layer"]].add((t["x2"], t["y2"]))
            for xy in [(t["x1"],t["y1"]),(t["x2"],t["y2"])]:
                radii[t["layer"]][xy] = max(radii[t["layer"]].get(xy,0),t["w"]/2)
        for v in self.vias_by_net[net]:
            for layer in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"):
                ends[layer].add((v["x"], v["y"]))
                radii[layer][(v["x"],v["y"])] = max(radii[layer].get((v["x"],v["y"]),0),v["d"]/2)
        adj = defaultdict(list)

        def link(a, b, length, layer, w, kind="track"):
            adj[a].append((b, length, layer, w, kind))
            adj[b].append((a, length, layer, w, kind))

        for t in segs:
            a, b = (t["x1"], t["y1"]), (t["x2"], t["y2"])
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            cuts = [0.0, 1.0]
            if L > 0:
                line = LineString([a,b])
                for i,p in enumerate(self.pads_by_net[net]):
                    if not p['poly'] or not (t['layer'] in p['layers'] or p['drill'][0]>0):
                        continue
                    shape = unary_union([Polygon(ring) for ring in p['poly'] if len(ring)>=3])
                    if line.distance(shape) < t['w']/2-1e-6:
                        contact = nearest_points(line,shape)[0]
                        u = line.project(contact)/L
                        cuts.append(u)
                        link(('pad',p['ref'],p['num'],i),(t['layer'],)+_k(contact.x,contact.y),0.,t['layer'],0.,'pad')
                for p in ends[t["layer"]]:
                    u = max(0.,min(1.,((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / (L * L)))
                    px, py = a[0] + u * (b[0] - a[0]), a[1] + u * (b[1] - a[1])
                    off = math.hypot(px - p[0], py - p[1])
                    if off < t['w']/2+radii[t['layer']].get(p,0)-1e-6:
                        cuts.append(u)
                        if _k(px,py)!=_k(*p):
                            link((t["layer"],) + _k(px, py), (t["layer"],) + _k(*p), off, t["layer"], t["w"])
            cuts = sorted(set(cuts))
            for u0, u1 in zip(cuts, cuts[1:]):
                p0 = (a[0] + u0 * (b[0] - a[0]), a[1] + u0 * (b[1] - a[1]))
                p1 = (a[0] + u1 * (b[0] - a[0]), a[1] + u1 * (b[1] - a[1]))
                link((t["layer"],) + _k(*p0), (t["layer"],) + _k(*p1), (u1 - u0) * L, t["layer"], t["w"])
        for v in self.vias_by_net[net]:
            k = _k(v["x"], v["y"])
            layers = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
            for l0, l1 in zip(layers, layers[1:]):
                link((l0,) + k, (l1,) + k, 0.0, "via", v["d"], "via")
        # A trace may terminate inside a via land without ending exactly at
        # its drill center. Native copper connectivity accepts this contact;
        # omitting it here incorrectly splits otherwise connected SI routes.
        # Stay conservative: the endpoint itself must lie inside the land,
        # not merely within a trace-width tolerance of it.
        nodes = list(adj)
        for v in self.vias_by_net[net]:
            k = _k(v["x"], v["y"])
            for n in nodes:
                if n[0] not in PLANE_FOR:
                    continue
                distance = math.hypot(n[1] * Q - v["x"], n[2] * Q - v["y"])
                if 2 * Q < distance < v["d"] / 2 - Q:
                    link((n[0],) + k, n, distance, n[0], 0.15)
        # pads: connect every track node that lies inside the pad polygon
        nodes = list(adj.keys())
        for i, p in enumerate(self.pads_by_net[net]):
            if not p["poly"]:
                continue
            poly = Polygon(p["poly"][0]).buffer(0.01)
            pid = ("pad", p["ref"], p["num"], i)
            adj[pid]  # make sure it exists
            for n in nodes:
                if n[0] == "pad":
                    continue
                if (n[0] in p["layers"] or p["drill"][0] > 0) and poly.contains(Point(n[1] * Q, n[2] * Q)):
                    link(pid, n, 0.0, n[0], 0.0, "pad")
        return adj

    def pad_nodes(self, adj, ref, num=None, layer=None, net=None):
        """Pad instances of ref/num; `layer` picks one site of a footprint that has two."""
        out = []
        for n in adj:
            if n[0] == "pad" and n[1] == ref and (num is None or n[2] == num):
                if layer is not None and net is not None and layer not in self.pads_by_net[net][n[3]]["layers"]:
                    continue
                out.append(n)
        return out

    @staticmethod
    def shortest(adj, src, dst):
        dist, prev = {src: 0.0}, {}
        pq = [(0.0, 0, src)]
        c = 0
        while pq:
            d, _, n = heapq.heappop(pq)
            if n == dst:
                break
            if d > dist.get(n, 1e99):
                continue
            for m, L, layer, w, kind in adj[n]:
                nd = d + L
                if nd < dist.get(m, 1e99):
                    dist[m] = nd
                    prev[m] = (n, L, layer, w, kind)
                    c += 1
                    heapq.heappush(pq, (nd, c, m))
        if dst not in dist:
            return None
        path, n = [], dst
        while n != src:
            p, L, layer, w, kind = prev[n]
            path.append((p, n, L, layer, w, kind))
            n = p
        return path[::-1]

    def route(self, net, src, dst, pick=None):
        """src/dst are (ref, num) pads.

        A footprint with two land sites has two pads of the same number; `pick`
        is an optional callable(pad_dict) -> bool that selects the fitted site.
        Without it the pad instances that give the shortest path are used.
        """
        adj = self.graph(net)
        best = None
        ok = (lambda n: True) if pick is None else (lambda n: pick(self.pads_by_net[net][n[3]]))
        for a in filter(ok, self.pad_nodes(adj, *src)):
            for b in filter(ok, self.pad_nodes(adj, *dst)):
                p = self.shortest(adj, a, b)
                if p is not None:
                    L = sum(e[2] for e in p)
                    if best is None or L < best[0]:
                        best = (L, p, a, b)
        if best is None:
            return None
        L, path, a, b = best
        on_path = {a, b}
        for e in path:
            on_path.add(e[0]); on_path.add(e[1])
        by = defaultdict(float)
        for e in path:
            if e[5] == "track":
                by[(e[3], round(e[4], 3))] += e[2]
        # A B.Cu <-> In2.Cu route also uses a physical through barrel.
        # Count each barrel once, even when the path crosses several of its
        # layer interfaces. The lumped model includes the full barrel (and
        # therefore conservatively retains its unused section).
        via_sites = {e[0][1:] for e in path if e[5] == "via"}
        vias = len(via_sites)
        # distance of every path node from the source, and the path as ordered elements
        pos, run, elements = {a: 0.0}, 0.0, []
        emitted_vias = set()
        for e in path:
            run += e[2]
            pos[e[1]] = run
            if e[5] == "track" and e[2] > 0:
                if elements and elements[-1][0] == "track" and elements[-1][1] == e[3] and abs(elements[-1][2] - e[4]) < 1e-6:
                    elements[-1][3] += e[2]
                else:
                    elements.append(["track", e[3], round(e[4], 3), e[2]])
            elif e[5] == "via" and e[0][1:] not in emitted_vias:
                elements.append(["via", run])
                emitted_vias.add(e[0][1:])
        # stubs: connected copper not on the path
        stubs = []
        seen = set(on_path)
        # Assign off-path copper in source-to-destination order. Iterating
        # the set changes branch ownership (and even measured stub length)
        # with Python's hash seed when a branch touches several path nodes.
        for n in [a] + [edge[1] for edge in path]:
            for m, Ledge, layer, w, kind in adj[n]:
                if m in seen:
                    continue
                # explore branch
                stack, total, pads, bl = [m], Ledge, set(), defaultdict(float)
                branch_vias = {n[1:]} if kind == "via" else set()
                bl[layer] += Ledge
                seen.add(m)
                while stack:
                    x = stack.pop()
                    if x[0] == "pad":
                        pads.add(f"{x[1]}.{x[2]}")
                    for y, L2, layer2, w2, kind2 in adj[x]:
                        if y in seen:
                            continue
                        seen.add(y)
                        total += L2
                        if kind2 == "track":
                            bl[layer2] += L2
                        if kind2 == "via":
                            branch_vias.add(x[1:])
                        stack.append(y)
                if total > 1e-6 or pads:
                    at = pos.get(n, 0.0)
                    stubs.append({"length_mm": round(total, 3), "pads": sorted(pads), "vias": len(branch_vias - via_sites),
                                  "from_src_mm": round(at, 2),
                                  "layers": {k: round(v, 3) for k, v in bl.items() if k != "via" and v > 0}})
        pts = []
        for e in path:
            if e[5] == "track":
                pts.append(((e[0][1] * Q, e[0][2] * Q), (e[1][1] * Q, e[1][2] * Q), e[3], e[4]))
        return {
            "length_mm": round(L, 3),
            "by_layer_width": {f"{l}:{w}": round(v, 3) for (l, w), v in sorted(by.items())},
            "vias": vias,
            "stubs": stubs,
            "stub_total_mm": round(sum(s["length_mm"] for s in stubs), 3),
            "elements": elements,
            "segments": pts,
        }

    # ---- reference plane --------------------------------------------------
    def plane_gaps(self, segments, step=0.1, margin=0.0):
        """Return samples of the route that have no copper on the adjacent inner plane."""
        out = []
        for a, b, layer, w in segments:
            ref = self.plane.get(PLANE_FOR.get(layer, ""))
            if ref is None:
                continue
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            n = max(1, int(L / step))
            for i in range(n + 1):
                x = a[0] + (b[0] - a[0]) * i / n
                y = a[1] + (b[1] - a[1]) * i / n
                pt = Point(x, y)
                ok = ref.contains(pt) if margin == 0 else ref.contains(pt.buffer(margin))
                if not ok:
                    out.append((round(x, 3), round(y, 3), layer))
        return out

    # ---- neighbours -------------------------------------------------------
    def neighbours(self, net, segments=None, reach=0.6, step=0.1):
        """Other-net tracks on the same layer within `reach` mm (edge to edge).

        Returns {aggressor: {"min_gap", "len_le_0p2", "len_le_0p35", "len_le_0p6"}}.
        """
        if segments is None:
            segments = [((t["x1"], t["y1"]), (t["x2"], t["y2"]), t["layer"], t["w"]) for t in self.by_net[net]]
        res = defaultdict(lambda: {"min_gap": 1e9, "len_le_0p2": 0.0, "len_le_0p35": 0.0, "len_le_0p6": 0.0})
        for a, b, layer, w in segments:
            segs, geoms, tree = self._seg[layer]
            if tree is None:
                continue
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            n = max(1, int(round(L / step)))
            dl = L / n
            for i in range(n):
                x = a[0] + (b[0] - a[0]) * (i + 0.5) / n
                y = a[1] + (b[1] - a[1]) * (i + 0.5) / n
                pt = Point(x, y)
                best = {}
                for j in tree.query(pt.buffer(reach + w / 2 + 0.6)):
                    t = segs[j]
                    if t["net"] == net:
                        continue
                    gap = geoms[j].distance(pt) - w / 2 - t["w"] / 2
                    if gap <= reach and gap < best.get(t["net"], 1e9):
                        best[t["net"]] = gap
                for other, gap in best.items():
                    r = res[other]
                    r["min_gap"] = min(r["min_gap"], gap)
                    if gap <= 0.2:
                        r["len_le_0p2"] += dl
                    if gap <= 0.35:
                        r["len_le_0p35"] += dl
                    r["len_le_0p6"] += dl
        return {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in sorted(res.items(), key=lambda kv: -kv[1]["len_le_0p6"])}

    def pads_near(self, segments, nets, reach=1.0):
        """Shortest distance from the route to any pad of the given nets (same layer)."""
        out = {}
        for a, b, layer, w in segments:
            if layer not in self._pad:
                continue
            pads, geoms, tree = self._pad[layer]
            ln = LineString([a, b])
            for j in tree.query(ln.buffer(reach + w / 2)):
                p = pads[j]
                if p["net"] in nets:
                    g = geoms[j].distance(ln) - w / 2
                    key = f"{p['ref']}.{p['num']}:{p['net']}"
                    if g <= reach and g < out.get(key, 1e9):
                        out[key] = round(g, 3)
        return out

    def net_pad_area(self, net):
        """Pad copper area per layer (mm^2) and through-hole count."""
        area, tht = defaultdict(float), 0
        for p in self.pads_by_net[net]:
            if not p["poly"] or len(p["poly"][0]) < 3:
                continue
            a = Polygon(p["poly"][0]).area
            if p["drill"][0] > 0:
                tht += 1
                area["F.Cu"] += a
                area["B.Cu"] += a
            else:
                for l in ("F.Cu", "B.Cu"):
                    if l in p["layers"]:
                        area[l] += a
        return dict(area), tht
