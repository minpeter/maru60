#!/usr/bin/env python3
"""DC resistance network of the power nets, solved from the routed copper.

usage: .venv/bin/python pcb/tools/analyze_pdn.py BOARD.json OUT_DIR [--led-site LED14=1]

BOARD.json is the geometry dump (dump_board_geometry.py).  For each power net the
tracks are cut wherever another track end, via or pad of the same net lands on
them, every piece becomes a resistor R = rho * L / (w * t), vias become barrel
resistors, pads and zone-fill islands are treated as equipotential nodes, and
the node voltages are solved for given source and sink currents.  The two inner
GND planes are not solved. Ground-return resistance, plane necks, and transient
droop require separate analysis; this is a supply-path DC screen.

Everything here is computed from geometry and the stated constants; nothing is
measured.  Track heating uses IPC-2221 external-layer curves for a 10 C rise.
"""
from __future__ import annotations

import json
import argparse
import hashlib
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import nearest_points

RHO20 = 1.72e-5            # ohm*mm, annealed copper at 20 C
TEMPCO = 0.00393
T_OUTER, T_INNER = 0.035, 0.0152
VIA_DRILL, VIA_PLATING, BOARD_T = 0.25, 0.020, 1.6     # plating thickness assumed (JLCPCB states 18 um minimum average)
SNAP = 0.02


def led_supply_pad(footprint, net="+4V_LED", site=0):
    """Select the primary fitted supply land by net, independent of LED pinout.

    Site zero is nearest the footprint origin. Specify a different site for
    an alternate-population load case; only one site per reference is fitted.
    """
    sites = [p for p in footprint["pads"] if p["net"] == net]
    if not sites:
        raise ValueError(f"{footprint['ref']} has no {net} supply land")
    sites.sort(key=lambda p: (math.hypot(p["x"]-footprint["x"], p["y"]-footprint["y"]), p["x"], p["y"]))
    if not 0 <= site < len(sites):
        raise ValueError(f"{footprint['ref']}: invalid supply site {site}; {len(sites)} available")
    return sites[site]


def rho(temp_c):
    return RHO20 * (1 + TEMPCO * (temp_c - 20))


def ipc2221_limit(width_mm, thick_mm, rise_c=10.0, external=True):
    area_mil2 = (width_mm / 0.0254) * (thick_mm / 0.0254)
    return (0.048 if external else 0.024) * rise_c ** 0.44 * area_mil2 ** 0.725


def distribute_current(nodes, amps):
    """Every physical load contributes, including loads sharing a copper node."""
    result = defaultdict(float)
    for node in nodes:
        result[node] += amps / len(nodes)
    return dict(result)


class Net:
    def __init__(self, board, net, temp_c=20.0):
        self.net = net
        self.r = rho(temp_c)
        self.pts = []                      # (layer, x, y)
        self.parent = []
        self.edges = []                    # (a, b, R, meta)
        self.pad_node = {}                 # (ref, num, layer) -> node
        self.pad_sites = []                # retain alternative lands of one pin
        layers = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
        tracks = [t for t in board["tracks"] if t["net"] == net]
        vias = [v for v in board["vias"] if v["net"] == net]
        pads = []
        for f in board["fps"]:
            for p in f["pads"]:
                if p["net"] == net:
                    for layer in layers:
                        if layer in p["layers"] or (p["drill"][0] > 0 and layer in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu")):
                            pads.append((f["ref"], p["num"], layer, p["x"], p["y"], Polygon(p["poly"][0]) if p["poly"] else Point(p["x"], p["y"]).buffer(0.2)))
        zones = []
        for z in board["zones"]:
            if z["net"] == net:
                for layer, isls in z["fill"].items():
                    for isl in isls:
                        if isl and len(isl[0]) >= 3:
                            zones.append((layer, Polygon(isl[0], isl[1:])))
        # anchors per layer
        anchors = defaultdict(list)
        anchor_radius = defaultdict(dict)
        for t in tracks:
            anchors[t["layer"]] += [(t["x1"], t["y1"]), (t["x2"], t["y2"])]
            for xy in [(t["x1"], t["y1"]), (t["x2"], t["y2"])]:
                radii = anchor_radius[t["layer"]]
                radii[xy] = max(radii.get(xy, 0), t["w"] / 2)
        for v in vias:
            for layer in layers:
                anchors[layer].append((v["x"], v["y"]))
                anchor_radius[layer][(v["x"], v["y"])] = max(
                    anchor_radius[layer].get((v["x"], v["y"]), 0), v["d"] / 2)
        for ref, num, layer, x, y, g in pads:
            anchors[layer].append((x, y))
        index = {}

        def node(layer, x, y):
            key = (layer, round(x / SNAP), round(y / SNAP))
            if key not in index:
                index[key] = len(self.pts)
                self.pts.append((layer, x, y))
                self.parent.append(len(self.parent))
            return index[key]

        def find(a):
            while self.parent[a] != a:
                self.parent[a] = self.parent[self.parent[a]]
                a = self.parent[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                self.parent[rb] = ra

        self.find = find
        for t in tracks:
            ax, ay, bx, by = t["x1"], t["y1"], t["x2"], t["y2"]
            L = math.hypot(bx - ax, by - ay)
            thick = T_OUTER if t["layer"] in ("F.Cu", "B.Cu") else T_INNER
            cuts = {0.0, 1.0}
            if L > 1e-9:
                # A pad can land on the middle or edge of a trace without its
                # centre reaching the trace. Preserve that copper contact.
                segment = LineString([(ax, ay), (bx, by)])
                for ref, num, layer, px, py, shape in pads:
                    if layer != t["layer"] or segment.distance(shape) >= t["w"] / 2 - 1e-6:
                        continue
                    contact_point = nearest_points(segment, shape)[0]
                    u = round(segment.project(contact_point) / L, 6)
                    cuts.add(u)
                    union(node(layer, px, py), node(layer, ax + u * (bx-ax), ay + u * (by-ay)))
                for qx, qy in anchors[t["layer"]]:
                    contact = t["w"] / 2 + anchor_radius[t["layer"]].get((qx, qy), 0)
                    if min(ax, bx) - contact <= qx <= max(ax, bx) + contact and min(ay, by) - contact <= qy <= max(ay, by) + contact:
                        u = max(0.0, min(1.0, ((qx - ax) * (bx - ax) + (qy - ay) * (by - ay)) / (L * L)))
                        # Positive copper overlap includes both tracks' round
                        # caps, even when neither center lies in the other.
                        if math.hypot(qx - (ax + u * (bx - ax)), qy - (ay + u * (by - ay))) < contact - 1e-6:
                            cuts.add(round(u, 6))
                            union(node(t["layer"], qx, qy), node(t["layer"], ax + u * (bx - ax), ay + u * (by - ay)))
            cs = sorted(cuts)
            for u0, u1 in zip(cs, cs[1:]):
                a = node(t["layer"], ax + u0 * (bx - ax), ay + u0 * (by - ay))
                b = node(t["layer"], ax + u1 * (bx - ax), ay + u1 * (by - ay))
                seg = L * (u1 - u0)
                if seg > 1e-9:
                    self.edges.append((a, b, self.r * seg / (t["w"] * thick), {"kind": "track", "layer": t["layer"], "w": t["w"], "len": seg,
                                                                               "x": ax + (u0 + u1) / 2 * (bx - ax), "y": ay + (u0 + u1) / 2 * (by - ay)}))
        rvia = self.r * BOARD_T / (math.pi * (VIA_DRILL + VIA_PLATING) * VIA_PLATING)
        for v in vias:
            # A routed endpoint can touch the land without reaching its drill
            # center. The via land is equipotential copper on every layer.
            for layer in layers:
                for qx, qy in anchors[layer]:
                    if math.hypot(qx - v["x"], qy - v["y"]) < v["d"] / 2 - 1e-6:
                        union(node(layer, v["x"], v["y"]), node(layer, qx, qy))
            self.edges.append((node("F.Cu", v["x"], v["y"]), node("B.Cu", v["x"], v["y"]), rvia, {"kind": "via", "x": v["x"], "y": v["y"]}))
            for layer in ("In1.Cu", "In2.Cu"):
                union(node(layer, v["x"], v["y"]), node("F.Cu", v["x"], v["y"]))
        # pads and zone islands are equipotential
        for ref, num, layer, x, y, g in pads:
            n0 = node(layer, x, y)
            self.pad_node[(ref, num, layer)] = n0
            self.pad_sites.append((ref, num, layer, x, y, n0))
            for qx, qy in anchors[layer]:
                if abs(qx - x) < 4 and abs(qy - y) < 4 and g.distance(Point(qx, qy)) < 1e-3:
                    union(n0, node(layer, qx, qy))
        for f in board["fps"]:                       # through-hole pads join the layers
            for p in f["pads"]:
                if p["net"] == net and p["drill"][0] > 0:
                    for layer in ("In1.Cu", "In2.Cu", "B.Cu"):
                        union(node("F.Cu", p["x"], p["y"]), node(layer, p["x"], p["y"]))
        for layer, g in zones:
            inside = [node(layer, qx, qy) for qx, qy in anchors[layer] if g.bounds[0] <= qx <= g.bounds[2] and g.bounds[1] <= qy <= g.bounds[3] and g.contains(Point(qx, qy))]
            inside += [node(lay, x, y) for ref, num, lay, x, y, pg in pads if lay == layer and g.intersects(pg)]
            for n in inside[1:]:
                union(inside[0], n)

    def pad(self, ref, num, layer=None):
        for (r, n, lay), node in self.pad_node.items():
            if r == ref and n == num and (layer is None or lay == layer):
                return self.find(node)
        raise KeyError((ref, num))

    def pad_at(self, ref, num, layer, x, y):
        sites = [(math.hypot(px - x, py - y), node)
                 for r, n, lay, px, py, node in self.pad_sites
                 if r == ref and n == num and lay == layer]
        if not sites:
            raise KeyError((ref, num, layer))
        return self.find(min(sites)[1])

    def solve(self, sources, sinks):
        """sources: {node: None} held at 0 V drop; sinks: {node: amps}. Returns (drop per node dict, edge currents)."""
        adjacent = defaultdict(set)
        for a, b, resistance, _ in self.edges:
            a, b = self.find(a), self.find(b)
            if a != b:
                adjacent[a].add(b)
                adjacent[b].add(a)
        reachable = {self.find(s) for s in sources}
        pending = list(reachable)
        while pending:
            for node in adjacent[pending.pop()]:
                if node not in reachable:
                    reachable.add(node)
                    pending.append(node)
        disconnected = [node for node, amps in sinks.items()
                        if amps and self.find(node) not in reachable]
        if disconnected:
            raise ValueError(f"{self.net}: loaded nodes disconnected from source: {disconnected}")
        # Unloaded floating copper is excluded, never weakly grounded. A weak
        # diagonal tie masks missing source paths as enormous finite voltages.
        roots = sorted(reachable)
        idx = {r: i for i, r in enumerate(roots)}
        n = len(roots)
        G = np.zeros((n, n))
        for a, b, R, meta in self.edges:
            if self.find(a) not in idx or self.find(b) not in idx:
                continue
            ia, ib = idx[self.find(a)], idx[self.find(b)]
            if ia == ib:
                continue
            g = 1.0 / R
            G[ia, ia] += g
            G[ib, ib] += g
            G[ia, ib] -= g
            G[ib, ia] -= g
        I = np.zeros(n)
        for node, amps in sinks.items():
            if amps:
                I[idx[self.find(node)]] -= amps
        fixed = sorted({idx[self.find(s)] for s in sources})
        free = [i for i in range(n) if i not in set(fixed)]
        A = G[np.ix_(free, free)]
        v = np.zeros(n)
        v[free] = np.linalg.solve(A, I[free])
        if not np.isfinite(v).all() or not np.allclose(A @ v[free], I[free], atol=1e-8, rtol=1e-7):
            raise ValueError(f"{self.net}: invalid resistance-network solution")
        cur = []
        for a, b, R, meta in self.edges:
            if self.find(a) not in idx or self.find(b) not in idx:
                continue
            ia, ib = idx[self.find(a)], idx[self.find(b)]
            if ia != ib:
                cur.append((abs(v[ia] - v[ib]) / R, R, meta))
        return {r: v[idx[r]] for r in roots}, cur


def resistance(netobj, a, b):
    v, cur = netobj.solve({a: None}, {b: 1.0})
    return -v[netobj.find(b)], cur


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geometry", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--led-site", action="append", default=[], metavar="REF=INDEX")
    args = parser.parse_args()
    selected_sites = {}
    for setting in args.led_site:
        ref, index = setting.split("=", 1)
        if ref in selected_sites:
            raise ValueError(f"Duplicate population selection: {ref}")
        selected_sites[ref] = int(index)
    board = json.loads(args.geometry.read_text())
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    res = {"constants": {"rho20_ohm_mm": RHO20, "outer_um": 35, "inner_um": 15.2, "via_plating_um_assumed": 20,
                         "via_resistance_mohm": round(RHO20 * BOARD_T / (math.pi * (VIA_DRILL + VIA_PLATING) * VIA_PLATING) * 1e3, 3)}}
    # self-check: a 100 mm x 0.5 mm outer track must be 98.3 mOhm
    chk = {"fps": [], "vias": [], "zones": [], "tracks": [{"x1": 0, "y1": 0, "x2": 100, "y2": 0, "w": 0.5, "layer": "F.Cu", "net": "T"}]}
    t = Net(chk, "T")
    r, _ = resistance(t, 0, 1)
    res["self_check"] = {"computed_ohm": round(r, 6), "hand_ohm": round(RHO20 * 100 / (0.5 * 0.035), 6)}
    assert abs(r - RHO20 * 100 / (0.5 * 0.035)) < 1e-9

    fps = {f["ref"]: f for f in board["fps"]}
    for ref, site in selected_sites.items():
        if ref not in fps or not ref.startswith("LED"):
            raise ValueError(f"Unknown LED reference: {ref}")
        led_supply_pad(fps[ref], site=site)
    res["provenance"] = {"geometry": str(args.geometry), "geometry_sha256": hashlib.sha256(args.geometry.read_bytes()).hexdigest(),
                         "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "selected_led_sites": selected_sites}
    res["limitations"] = ["Supply-path DC approximation; not PWM, inrush, thermal, or fabrication qualification",
                          "Ground-return impedance omitted; pads and individual zone islands equipotential",
                          "Via barrel model lumps inner-layer connections at the top node; internal span resistance approximated",
                          "Run every mutually exclusive LED population separately; default site is nearest footprint origin"]
    res["led_population"] = {f["ref"]: {k: led_supply_pad(f, site=selected_sites.get(f["ref"], 0))[k] for k in ("num", "x", "y")}
                             for f in board["fps"] if f["ref"].startswith("LED")}
    paths = {}
    heavy = []

    def path(name, net, a, b, amps, temp=20.0):
        n = Net(board, net, temp)
        r, cur = resistance(n, n.pad(*a), n.pad(*b))
        vias_used = sum(1 for i, R, m in cur if m["kind"] == "via" and i > 0.3)
        paths[name] = {"net": net, "from": ".".join(a[:2]), "to": ".".join(b[:2]), "resistance_mohm": round(r * 1e3, 2), "amps": amps,
                       "drop_mv": round(r * amps * 1e3, 2), "loss_mw": round(r * amps * amps * 1e3, 2), "temp_c": temp, "vias_carrying_over_30pct": vias_used}
        for i, R, m in cur:
            if m["kind"] == "track":
                lim = ipc2221_limit(m["w"], T_OUTER if m["layer"] in ("F.Cu", "B.Cu") else T_INNER, external=m["layer"] in ("F.Cu", "B.Cu"))
                if i * amps / lim > 0.5:
                    heavy.append({"path": name, "layer": m["layer"], "width_mm": m["w"], "amps": round(float(i * amps), 3), "ipc2221_10C_limit_a": round(lim, 3), "x": round(m["x"], 1), "y": round(m["y"], 1)})
        return r

    for temp in (20.0, 60.0):
        tag = f"@{int(temp)}C"
        path("VBUS J1 -> F1 " + tag, "VBUS", ("J1", "A4", "B.Cu"), ("F1", "1"), 0.5, temp)
        path("VBUS_FUSED F1 -> U8 " + tag, "VBUS_FUSED", ("F1", "2"), ("U8", "5"), 0.5, temp)
        path("VBUS_PROTECTED_RAW U8 -> U18 " + tag, "VBUS_PROTECTED_RAW", ("U8", "6"), ("U18", "3"), 0.5, temp)
        path("+4V_REG L2 -> U2 " + tag, "+4V_REG", ("L2", "2"), ("U2", "1"), 0.15, temp)
        path("+4V_REG L2 -> U7 " + tag, "+4V_REG", ("L2", "2"), ("U7", "1"), 0.234, temp)
        path("+3V3 U2 -> U1 pin 49 (VREG_VIN) " + tag, "+3V3", ("U2", "5"), ("U1", "49"), 0.15, temp)
        path("+3V3 U2 -> U3 " + tag, "+3V3", ("U2", "5"), ("U3", "8"), 0.05, temp)
    res["paths"] = paths
    res["tracks_over_half_ipc2221"] = heavy

    # LED rail
    led_cases = {}
    for temp in (20.0, 60.0):
        n = Net(board, "+4V_LED", temp)
        src = n.pad("U7", "6")
        leds = []
        for f in board["fps"]:
            if f["ref"].startswith("LED"):
                # the land site at the footprint origin
                p = led_supply_pad(f, site=selected_sites.get(f["ref"], 0))
                layer = "F.Cu" if "F.Cu" in p["layers"] else "B.Cu"
                leds.append((f["ref"], n.pad_at(f["ref"], p["num"], layer, p["x"], p["y"]), p["x"], p["y"]))
        ux, uy = fps["U7"]["x"], fps["U7"]["y"]
        far = sorted(leds, key=lambda l: -math.hypot(l[2] - ux, l[3] - uy))[:16]
        cases = {
            "firmware cap: 38 mA static + 25 mA drive, even": distribute_current([l[1] for l in leds], 0.063),
            "limiter maximum 234 mA, even": distribute_current([l[1] for l in leds], 0.234),
            "38 mA static even + 196 mA in the 16 LEDs furthest from U7": None,
        }
        reverse_count = sum(f["ref"].startswith("LED") and f["value"] == "SK6812MINI-E-012" for f in board["fps"])
        if reverse_count:
            del cases["firmware cap: 38 mA static + 25 mA drive, even"]
            cases["DC screen: typical idle plus 58 mA PWM average; NOT peak qualification"] = distribute_current([l[1] for l in leds], (.6*reverse_count+.5*(len(leds)-reverse_count)+58)/1000)
            cases["DC screen: assumed 1 mA/reverse LED idle plus 58 mA average; NOT guaranteed"] = distribute_current([l[1] for l in leds], (reverse_count+.5*(len(leds)-reverse_count)+58)/1000)
        worst = defaultdict(float)
        for l in leds:
            worst[l[1]] += 0.038 / len(leds)
        for l in far:
            worst[l[1]] += 0.196 / 16
        cases["38 mA static even + 196 mA in the 16 LEDs furthest from U7"] = dict(worst)
        if reverse_count:
            cases["DC stress allocation: 38 mA even + 196 mA in 16 remote LEDs; not an idle-current model"] = cases.pop("38 mA static even + 196 mA in the 16 LEDs furthest from U7")
        for name, sinks in cases.items():
            merged = defaultdict(float)
            for k, a in sinks.items():
                merged[k] += a
            v, cur = n.solve({src: None}, merged)
            drops = {ref: -v[node] * 1e3 for ref, node, x, y in leds}
            wref = max(drops, key=drops.get)
            led_cases[f"{name} @{int(temp)}C"] = {"max_drop_mv": round(drops[wref], 2), "at": wref, "median_drop_mv": round(sorted(drops.values())[len(drops) // 2], 2),
                                                  "max_track_current_a": round(max(i for i, R, m in cur if m["kind"] == "track"), 3)}
            if temp == 20.0 and name.startswith("limiter"):
                res["led_drop_map_mv"] = {ref: [round(x, 2), round(y, 2), round(drops[ref], 2)] for ref, node, x, y in leds}
    res["led_rail"] = led_cases
    (out / "results.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, v in paths.items():
        print(f"{k:48} {v['resistance_mohm']:8.2f} mOhm  {v['drop_mv']:7.2f} mV @ {v['amps']} A  vias>{30}%: {v['vias_carrying_over_30pct']}")
    for k, v in led_cases.items():
        print(f"LED rail | {k:70} max drop {v['max_drop_mv']:7.2f} mV at {v['at']}  (median {v['median_drop_mv']})  max track current {v['max_track_current_a']} A")
    print("tracks over 50% of the IPC-2221 10 C limit:", len(heavy))
    for h in heavy[:10]:
        print("  ", h)


if __name__ == "__main__":
    main()
