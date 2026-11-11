#!/usr/bin/env python3
"""Maru60 lumped thermal network and 2D board-spreading simulation.

This is a simulation-only screening tool.  It does not qualify the thermal
design.  Every material, convection, via-fill and junction-to-ambient value is
an assumption unless it is explicitly read from the board or a datasheet
extract.  The output is written under:

    pcb/experiments/resume-20261109-relocated-expansion-zero-opens/qa/thermal-sim/

Run with the repository venv:

    .venv/bin/python pcb/tools/simulate_thermal.py
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import os
import re
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths and matplotlib cache
# ---------------------------------------------------------------------------
TOOL = Path(__file__).resolve()
REPO = TOOL.parents[2]
EXP = REPO / "pcb/experiments/resume-20261109-relocated-expansion-zero-opens"
BOARD = EXP / "pcb/maru60.kicad_pcb"
POWER_REVIEW = EXP / "qa/power-review/power-review.json"
FIT_JSON = EXP / "qa/mechanical-fit/fit.json"
OUT = EXP / "qa/thermal-sim"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / ".mplconfig").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(OUT / ".mplconfig"))

import numpy as np  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy.sparse import coo_matrix, diags, lil_matrix  # noqa: E402
from scipy.sparse.csgraph import connected_components  # noqa: E402
from scipy.sparse.linalg import factorized, spsolve  # noqa: E402
from shapely.geometry import LineString, Point, Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fnum(x, nd=3):
    """JSON-friendly float."""
    if x is None:
        return None
    return float(round(float(x), nd))


def table(rows, headers):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# KiCad board parser (s-expression, no pcbnew dependency)
# ---------------------------------------------------------------------------
_TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')


def parse_sexpr(text: str):
    stack = [[]]
    for m in _TOKEN.finditer(text):
        tok = m.group(0)
        if tok == "(":
            stack.append([])
        elif tok == ")":
            node = stack.pop()
            stack[-1].append(node)
        else:
            if tok.startswith('"'):
                tok = tok[1:-1]
            stack[-1].append(tok)
    return stack[0][0]


def children(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def child(node, name):
    for c in node:
        if isinstance(c, list) and c and c[0] == name:
            return c
    return None


def xy_points(node):
    pts = []
    for pts_node in children(node, "pts"):
        for xy in children(pts_node, "xy"):
            pts.append((float(xy[1]), float(xy[2])))
    return pts


class Board:
    def __init__(self, path: Path):
        self.path = path
        self.text = path.read_text()
        self.root = parse_sexpr(self.text)
        self.netmap = {}
        for n in children(self.root, "net"):
            if len(n) >= 3:
                self.netmap[n[1]] = n[2]
        self._parse_footprints()
        self._parse_tracks()
        self._parse_vias()
        self._parse_zones()
        self._parse_outline()

    def _parse_footprints(self):
        self.footprints = []
        for fp in children(self.root, "footprint"):
            ref = None
            for p in children(fp, "property"):
                if len(p) > 2 and p[1] == "Reference":
                    ref = p[2]
            at = child(fp, "at")
            if not at:
                continue
            x, y = float(at[1]), float(at[2])
            rot = float(at[3]) if len(at) > 3 else 0.0
            layer = child(fp, "layer")
            pads = []
            for pad in children(fp, "pad"):
                pat = child(pad, "at")
                psz = child(pad, "size")
                pnet = child(pad, "net")
                plays = child(pad, "layers")
                if not pat or not psz:
                    continue
                px, py = float(pat[1]), float(pat[2])
                a = math.radians(rot)
                ca, sa = math.cos(a), math.sin(a)
                pads.append(
                    dict(
                        num=pad[1],
                        x=x + px * ca - py * sa,
                        y=y + px * sa + py * ca,
                        w=float(psz[1]),
                        h=float(psz[2]),
                        net=self.netmap.get(pnet[1], "?") if pnet else None,
                        layers=plays[1:] if plays else [],
                    )
                )
            self.footprints.append(
                dict(
                    ref=ref,
                    x=x,
                    y=y,
                    rot=rot,
                    layer=layer[1] if layer else None,
                    pads=pads,
                )
            )
        self.by_ref = {f["ref"]: f for f in self.footprints if f["ref"]}

    def _parse_tracks(self):
        self.tracks = []
        for t in children(self.root, "segment"):
            lay = child(t, "layer")
            st = child(t, "start")
            en = child(t, "end")
            w = child(t, "width")
            net = child(t, "net")
            if not (lay and st and en and w):
                continue
            self.tracks.append(
                dict(
                    layer=lay[1],
                    net=self.netmap.get(net[1], "?") if net else "?",
                    a=(float(st[1]), float(st[2])),
                    b=(float(en[1]), float(en[2])),
                    w=float(w[1]),
                )
            )

    def _parse_vias(self):
        self.vias = []
        for v in children(self.root, "via"):
            at = child(v, "at")
            sz = child(v, "size")
            net = child(v, "net")
            if not at:
                continue
            self.vias.append(
                dict(
                    x=float(at[1]),
                    y=float(at[2]),
                    d=float(sz[1]) if sz else 0.6,
                    net=self.netmap.get(net[1], "?") if net else "?",
                )
            )

    def _parse_zones(self):
        self.zone_polys = []
        for z in children(self.root, "zone"):
            net = child(z, "net_name")
            net_name = net[1] if net else "?"
            layer = child(z, "layer")
            default_layer = layer[1] if layer else "?"
            for fp in children(z, "filled_polygon"):
                lay = child(fp, "layer")
                lay_name = lay[1] if lay else default_layer
                pts = xy_points(fp)
                if len(pts) < 3:
                    continue
                try:
                    g = Polygon(pts)
                    if not g.is_valid:
                        g = g.buffer(0)
                    if g.area > 0:
                        self.zone_polys.append((lay_name, net_name, g))
                except Exception:
                    pass

    def _parse_outline(self):
        xs, ys = [], []
        for g in children(self.root, "gr_line"):
            lay = child(g, "layer")
            if not lay or lay[1] != "Edge.Cuts":
                continue
            st, en = child(g, "start"), child(g, "end")
            if st and en:
                xs += [float(st[1]), float(en[1])]
                ys += [float(st[2]), float(en[2])]
        self.bbox = (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 285, 94.6)
        self.width = self.bbox[2] - self.bbox[0]
        self.height = self.bbox[3] - self.bbox[1]
        self.area_mm2 = self.width * self.height

    # -- copper geometry -------------------------------------------------
    def copper_union(self, layer: str):
        geoms = [g for lay, _net, g in self.zone_polys if lay == layer]
        for t in self.tracks:
            if t["layer"] == layer:
                geoms.append(LineString([t["a"], t["b"]]).buffer(t["w"] / 2.0, cap_style=2))
        for f in self.footprints:
            for p in f["pads"]:
                if layer in p["layers"] or "*.Cu" in p["layers"]:
                    geoms.append(Point(p["x"], p["y"]).buffer(max(p["w"], p["h"]) / 2.0, resolution=8))
        return unary_union(geoms) if geoms else Polygon()

    def copper_area_near(self, x, y, radius_mm, layers=("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")):
        circ = Point(x, y).buffer(radius_mm)
        out = {}
        for lay in layers:
            out[lay] = self.copper[lay].intersection(circ).area
        out["total"] = sum(out.values())
        return out

    def vias_near(self, x, y, radius_mm):
        return [v for v in self.vias if math.dist((v["x"], v["y"]), (x, y)) <= radius_mm]

    def nearest_via(self, x, y, net=None):
        cand = [v for v in self.vias if net is None or v["net"] == net]
        if not cand:
            return None
        v = min(cand, key=lambda v: math.dist((v["x"], v["y"]), (x, y)))
        return dict(v, dist=math.dist((v["x"], v["y"]), (x, y)))


# ---------------------------------------------------------------------------
# +4V_LED rail resistive network
# ---------------------------------------------------------------------------
def rail_network(board: Board, net_name="+4V_LED", led_current_a=15e-3, thickness=1.6e-3):
    """Solve the +4V_LED track/via/pad network and return loss and drop.

    Nodes are track endpoints, via centres and pad centres.  Tracks are
    resistors (1 oz outer copper, 35 um).  Vias are barrel resistors.  Pads
    are connected to the nearest same-layer node within 1 mm.  A 0.10 mm
    tolerance also joins track endpoints that overlap within a trace width.
    """
    segs = [t for t in board.tracks if t["net"] == net_name]
    vias = [v for v in board.vias if v["net"] == net_name]
    pads = []
    for f in board.footprints:
        for p in f["pads"]:
            if p["net"] == net_name:
                pads.append(dict(ref=f["ref"], num=p["num"], x=p["x"], y=p["y"],
                                 w=p["w"], h=p["h"], layers=p["layers"]))

    node_list, node_index = [], {}

    def add_node(lay, x, y):
        k = (lay, round(x, 4), round(y, 4))
        if k not in node_index:
            node_index[k] = len(node_list)
            node_list.append(k)
        return node_index[k]

    for t in segs:
        add_node(t["layer"], *t["a"])
        add_node(t["layer"], *t["b"])
    for v in vias:
        for lay in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"):
            add_node(lay, v["x"], v["y"])
    for p in pads:
        for lay in p["layers"]:
            if lay in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"):
                add_node(lay, p["x"], p["y"])

    edges = []

    def add_edge(ia, ib, R):
        if ia != ib and R > 0:
            edges.append((ia, ib, R))

    for t in segs:
        ia = node_index[(t["layer"], round(t["a"][0], 4), round(t["a"][1], 4))]
        ib = node_index[(t["layer"], round(t["b"][0], 4), round(t["b"][1], 4))]
        L = math.dist(t["a"], t["b"])
        add_edge(ia, ib, 1.72e-8 * L / (t["w"] * 35e-6))

    for v in vias:
        ks = [node_index[(lay, round(v["x"], 4), round(v["y"], 4))]
              for lay in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
              if (lay, round(v["x"], 4), round(v["y"], 4)) in node_index]
        R = 1.72e-8 * thickness / (math.pi * (v["d"] / 2.0) ** 2)
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                add_edge(ks[i], ks[j], R)

    for p in pads:
        for lay in p["layers"]:
            if lay not in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"):
                continue
            ip = node_index[(lay, round(p["x"], 4), round(p["y"], 4))]
            best, bd = None, 1e9
            for k, idx in node_index.items():
                if k[0] != lay or idx == ip:
                    continue
                d = math.dist((k[1], k[2]), (p["x"], p["y"]))
                if d < bd:
                    bd, best = d, idx
            if best is not None and bd <= 1.0:
                add_edge(ip, best, 0.01)

    # T-junctions / overlapping endpoints: connect a node to a segment it lies on.
    seg_by_layer = defaultdict(list)
    for t in segs:
        seg_by_layer[t["layer"]].append(t)
    for k, idx in node_index.items():
        lay, x, y = k
        for t in seg_by_layer[lay]:
            ax, ay = t["a"]
            bx, by = t["b"]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            if L2 == 0:
                continue
            u = ((x - ax) * dx + (y - ay) * dy) / L2
            if u <= 0.001 or u >= 0.999:
                continue
            px, py = ax + u * dx, ay + u * dy
            if math.hypot(x - px, y - py) < 0.10:
                ia = node_index[(lay, round(ax, 4), round(ay, 4))]
                ib = node_index[(lay, round(bx, 4), round(by, 4))]
                L = math.sqrt(L2)
                add_edge(idx, ia, 1.72e-8 * (u * L) / (t["w"] * 35e-6))
                add_edge(idx, ib, 1.72e-8 * ((1 - u) * L) / (t["w"] * 35e-6))

    N = len(node_list)
    rows, cols, vals = [], [], []
    for ia, ib, R in edges:
        g = 1.0 / R
        rows += [ia, ib, ia, ib]
        cols += [ia, ib, ib, ia]
        vals += [g, g, -g, -g]
    G = coo_matrix((vals, (rows, cols)), shape=(N, N)).tocsr()

    src = next((p for p in pads if p["ref"] == "U7" and p["num"] == "6"), None)
    if src is None:
        return dict(ok=False, reason="U7 pad 6 not found on +4V_LED")
    src_node = None
    for lay in src["layers"]:
        key = (lay, round(src["x"], 4), round(src["y"], 4))
        if key in node_index:
            src_node = node_index[key]
            break
    led_nodes = []
    for p in pads:
        if p["ref"] and p["ref"].startswith("LED"):
            for lay in p["layers"]:
                key = (lay, round(p["x"], 4), round(p["y"], 4))
                if key in node_index:
                    led_nodes.append(node_index[key])
                    break

    ncomp, lab = connected_components(G, directed=False)
    comp = lab[src_node]
    idx = np.where(lab == comp)[0]
    mapn = {int(n): i for i, n in enumerate(idx)}
    Gc = G[idx][:, idx]
    I = np.zeros(len(idx))
    n_led = 0
    for n in led_nodes:
        if lab[n] == comp:
            I[mapn[n]] += led_current_a
            n_led += 1
    I[mapn[src_node]] -= led_current_a * n_led
    free = np.ones(len(idx), dtype=bool)
    free[mapn[src_node]] = False
    V = np.zeros(len(idx))
    V[free] = spsolve(Gc[free][:, free], I[free])

    loss = 0.0
    for ia, ib, R in edges:
        if lab[ia] == comp:
            dv = V[mapn[ia]] - V[mapn[ib]]
            loss += dv * dv / R
    drops = [V[mapn[n]] - V[mapn[src_node]] for n in led_nodes if lab[n] == comp]
    return dict(
        ok=True,
        net=net_name,
        segments=len(segs),
        vias=len(vias),
        pads=len(pads),
        nodes=N,
        edges=len(edges),
        components=int(ncomp),
        leds_connected=n_led,
        leds_total=len(led_nodes),
        current_a=led_current_a * n_led,
        loss_w=loss,
        max_drop_v=max(drops) if drops else None,
        min_drop_v=min(drops) if drops else None,
    )


# ---------------------------------------------------------------------------
# Component-level thermal calculations
# ---------------------------------------------------------------------------
TA_LIST = [25.0, 40.0, 60.0, 85.0]
TJ_LIMIT = 125.0


def tj_table(power_w, theta_ja_values, ta_list=TA_LIST):
    rows = []
    for ta in ta_list:
        row = {"ta_c": ta}
        for th in theta_ja_values:
            row[f"tj_at_{th:g}_c_per_w"] = ta + th * power_w
        row["required_theta_ja_c_per_w"] = (TJ_LIMIT - ta) / power_w
        rows.append(row)
    return rows


def u2_calc(board: Board):
    p_given = 0.2484
    p_4v = (4.0 - 3.3) * 0.300
    p_5v = (5.0 - 3.3) * 0.300
    theta_values = [80.0, 100.0, 120.0, 140.0]
    f = board.by_ref["U2"]
    areas = {r: board.copper_area_near(f["x"], f["y"], r) for r in (1, 2, 3, 5, 8, 12)}
    vias_15 = board.vias_near(f["x"], f["y"], 1.5)
    vias_3 = board.vias_near(f["x"], f["y"], 3.0)
    nearest_gnd = board.nearest_via(f["x"], f["y"], net="GND")
    ep = next((p for p in f["pads"] if p["num"] == "9"), None)
    ep_vias = []
    if ep:
        ep_vias = [v for v in board.vias
                   if abs(v["x"] - ep["x"]) <= ep["w"] / 2 and abs(v["y"] - ep["y"]) <= ep["h"] / 2]
    return dict(
        ref="U2",
        part="MAX38902AATA+T",
        package="TDFN-8 2x2 mm with exposed pad (EP 0.8 x 1.38 mm)",
        power_w=dict(given=p_given, at_4v_in=p_4v, at_5v_in=p_5v),
        power_basis="0.2484 W at 300 mA is the task input; it is equivalent to 0.828 V dropout (4.128 V in, 3.3 V out). 4.0 V in gives 0.210 W; 5.0 V in gives 0.510 W.",
        theta_ja_c_per_w=dict(nominal=120.0, range=[80.0, 140.0],
                              basis="UNKNOWN. 80 C/W assumes a soldered EP with thermal vias and 4-layer spreading; 120 C/W is the as-built screening value because no via is inside the EP. Not a datasheet value."),
        tj_vs_ta=tj_table(p_given, theta_values),
        tj_vs_ta_4v=tj_table(p_4v, theta_values),
        tj_vs_ta_5v=tj_table(p_5v, theta_values),
        required_theta_ja={f"{ta:g}": (TJ_LIMIT - ta) / p_given for ta in TA_LIST},
        required_theta_ja_5v={f"{ta:g}": (TJ_LIMIT - ta) / p_5v for ta in TA_LIST},
        copper_area_mm2={str(k): {kk: fnum(vv, 2) for kk, vv in v.items()} for k, v in areas.items()},
        vias_within_1p5mm=len(vias_15),
        vias_within_3mm=len(vias_3),
        vias_in_ep=len(ep_vias),
        nearest_gnd_via=nearest_gnd,
        ep=dict(x=ep["x"], y=ep["y"], w=ep["w"], h=ep["h"]) if ep else None,
    )


def u18_calc(board: Board):
    # Datasheet-anchored efficiency for TPS62932, Vout=5 V, fsw=500 kHz,
    # L=10 uH, Vin=6 V (Figure 8-21).  Our Vout=4 V, L=4.7 uH, so the
    # efficiency is derated slightly and a band is carried.
    eff = {0.1: dict(nom=0.87, low=0.84, high=0.90),
           0.3: dict(nom=0.91, low=0.88, high=0.93)}
    vout = 4.0
    vin = 5.0
    fsw = 500e3
    L = 4.7e-6
    dcr = 0.0275  # Coilcraft XAL4030-472MEC, assumed max
    rds_hs = 0.076
    rds_ls = 0.032
    duty = vout / vin
    rows = []
    for iout in (0.1, 0.3):
        pout = vout * iout
        p_total = pout * (1.0 / eff[iout]["nom"] - 1.0)
        p_total_low = pout * (1.0 / eff[iout]["high"] - 1.0)
        p_total_high = pout * (1.0 / eff[iout]["low"] - 1.0)
        dIL = vout * (1.0 - duty) / (L * fsw)
        irms2 = iout * iout + dIL * dIL / 12.0
        p_cond = irms2 * (duty * rds_hs + (1.0 - duty) * rds_ls)
        p_dcr = iout * iout * dcr
        p_sw_etc = p_total - p_cond - p_dcr
        rows.append(dict(
            iout_a=iout,
            pout_w=pout,
            efficiency=eff[iout],
            p_total_w=p_total,
            p_total_range_w=[p_total_low, p_total_high],
            ripple_a=dIL,
            p_conduction_w=p_cond,
            p_inductor_dcr_w=p_dcr,
            p_switching_quiescent_other_w=p_sw_etc,
            theta_ja_c_per_w=dict(evm=60.2, jedec=112.2, screening=70.0),
            tj_at_ta={f"{ta:g}": ta + 70.0 * p_total for ta in TA_LIST},
            tj_at_ta_jedec={f"{ta:g}": ta + 112.2 * p_total for ta in TA_LIST},
            required_theta_ja={f"{ta:g}": (TJ_LIMIT - ta) / p_total for ta in TA_LIST},
        ))
    f = board.by_ref["U18"]
    areas = {r: board.copper_area_near(f["x"], f["y"], r) for r in (2, 3, 5, 8)}
    nearest_gnd = board.nearest_via(f["x"], f["y"], net="GND")
    return dict(
        ref="U18",
        part="TPS62932DRLR",
        package="SOT-583-8",
        vin_v=vin,
        vout_v=vout,
        fsw_hz=fsw,
        inductor="L2 XAL4030-472MEC 4.7 uH, DCR assumed 27.5 mOhm max",
        rds_on=dict(high_side_25c=rds_hs, low_side_25c=rds_ls,
                    note="datasheet typical at TJ=25 C; Rds rises with temperature and is not iterated here"),
        efficiency_basis="TPS62932 datasheet Figure 8-21 (Vout=5 V, fsw=500 kHz, L=10 uH, Vin=6 V), derated for 4 V output and 4.7 uH. Efficiency is an assumption, not a measurement.",
        losses=rows,
        copper_area_mm2={str(k): {kk: fnum(vv, 2) for kk, vv in v.items()} for k, v in areas.items()},
        nearest_gnd_via=nearest_gnd,
    )


def u7_calc(board: Board, currents=None):
    if currents is None:
        currents = [0.173657469, 0.20151272, 0.233901173]
    rds_cold = 0.095  # DBV max at 25 C
    rds_hot = 0.135   # DBV max over -40..125 C
    theta = 182.6     # DBV SOT-23-6 JEDEC
    rows = []
    for i in currents:
        p_cold = i * i * rds_cold
        p_hot = i * i * rds_hot
        rows.append(dict(
            current_a=i,
            p_cold_w=p_cold,
            p_hot_w=p_hot,
            tj_cold_at_ta={f"{ta:g}": ta + theta * p_cold for ta in TA_LIST},
            tj_hot_at_ta={f"{ta:g}": ta + theta * p_hot for ta in TA_LIST},
            required_theta_ja_hot={f"{ta:g}": (TJ_LIMIT - ta) / p_hot for ta in TA_LIST},
        ))
    p_full = 1.14 ** 2 * rds_hot
    f = board.by_ref["U7"]
    areas = {r: board.copper_area_near(f["x"], f["y"], r) for r in (2, 3, 5, 8)}
    nearest_gnd = board.nearest_via(f["x"], f["y"], net="GND")
    return dict(
        ref="U7",
        part="TPS2553DBVR-1",
        package="SOT-23-6 (DBV)",
        rds_on=dict(cold_max_25c=rds_cold, hot_max_125c=rds_hot,
                    note="datasheet DBV values; hot value used for worst case"),
        theta_ja_c_per_w=theta,
        currents=rows,
        full_white=dict(current_a=1.14, p_hot_w=p_full,
                        tj_at_85c=85.0 + theta * p_full,
                        note="Full white is not reachable: the TPS2553-1 current limit is 173.7-233.9 mA and the part latches off. This row is a what-if, not an operating point."),
        copper_area_mm2={str(k): {kk: fnum(vv, 2) for kk, vv in v.items()} for k, v in areas.items()},
        nearest_gnd_via=nearest_gnd,
    )


def led_calc(board: Board, rail_full, rail_cap, n_led=None, per_ch_full=5.0e-3, per_ch_cap=0.761656e-3):
    leds = [f for f in board.footprints if f["ref"] and f["ref"].startswith("LED")]
    n = n_led if n_led is not None else len(leds)
    i_led_full = 3 * per_ch_full
    i_led_cap = 3 * per_ch_cap
    p_led_full = 4.0 * i_led_full
    p_led_cap = 4.0 * i_led_cap
    total_full = n * p_led_full
    total_cap = n * p_led_cap
    # local copper around each LED
    local = []
    for f in leds:
        a = board.copper_area_near(f["x"], f["y"], 2.5)
        local.append(a["total"])
    return dict(
        count=n,
        per_key=sum(1 for f in leds if f["layer"] == "F.Cu"),
        underglow=sum(1 for f in leds if f["layer"] == "B.Cu"),
        channels_per_led=3,
        per_channel_current=dict(full_white_a=per_ch_full, limiter_cap_a=per_ch_cap),
        per_led_current=dict(full_white_a=i_led_full, limiter_cap_a=i_led_cap),
        per_led_power=dict(full_white_w=p_led_full, limiter_cap_w=p_led_cap,
                           basis="4.0 V rail x 3 channels; all electrical power treated as heat (conservative, optical output ignored)"),
        total_power=dict(full_white_w=total_full, limiter_cap_w=total_cap),
        rail=dict(full_white=rail_full, limiter_cap=rail_cap),
        local_copper_2p5mm_mm2=dict(mean=fnum(np.mean(local), 2), min=fnum(np.min(local), 2),
                                    max=fnum(np.max(local), 2)),
        theta_ja_c_per_w=dict(nominal=45.0, range=[30.0, 60.0],
                              basis="UNKNOWN. 1.5 x 1.5 mm LED on 1.6 mm FR4 with local copper; 45 C/W is a screening assumption."),
        tj_at_ta={f"{ta:g}": ta + 45.0 * p_led_full for ta in TA_LIST},
        tj_at_ta_cap={f"{ta:g}": ta + 45.0 * p_led_cap for ta in TA_LIST},
    )


# ---------------------------------------------------------------------------
# 2D board + lumped case model
# ---------------------------------------------------------------------------
class BoardThermal2D:
    def __init__(self, board: Board, dx_mm=2.5, k_eff=20.0, h_bc=5.0,
                 h_ca=8.0, a_case=0.054, c_case=200.0, rho_cp=1.8e6,
                 thickness=1.6e-3):
        self.board = board
        self.dx = dx_mm * 1e-3
        self.dy = self.dx
        self.nx = int(round(board.width * 1e-3 / self.dx))
        self.ny = int(round(board.height * 1e-3 / self.dy))
        self.n = self.nx * self.ny
        self.k = k_eff
        self.t = thickness
        self.h_bc = h_bc
        self.h_ca = h_ca
        self.a_case = a_case
        self.c_case = c_case
        self.c_board = rho_cp * (board.width * 1e-3) * (board.height * 1e-3) * self.t
        self.a_cell = self.dx * self.dy
        self.gx = self.k * self.t * self.dy / self.dx
        self.gy = self.k * self.t * self.dx / self.dy
        self.gbc = self.h_bc * self.a_cell
        self.r_bc = 1.0 / (self.h_bc * board.width * 1e-3 * board.height * 1e-3)
        self.r_ca = 1.0 / (self.h_ca * a_case)
        self._build_matrix()

    def cell(self, x_mm, y_mm):
        i = min(max(int((x_mm - self.board.bbox[0]) * 1e-3 / self.dx), 0), self.nx - 1)
        j = min(max(int((y_mm - self.board.bbox[1]) * 1e-3 / self.dy), 0), self.ny - 1)
        return j * self.nx + i

    def _build_matrix(self):
        n = self.n
        M = lil_matrix((n + 1, n + 1))
        for j in range(self.ny):
            for i in range(self.nx):
                idx = j * self.nx + i
                diag = 0.0
                if i > 0:
                    M[idx, idx - 1] -= self.gx
                    diag += self.gx
                if i < self.nx - 1:
                    M[idx, idx + 1] -= self.gx
                    diag += self.gx
                if j > 0:
                    M[idx, idx - self.nx] -= self.gy
                    diag += self.gy
                if j < self.ny - 1:
                    M[idx, idx + self.nx] -= self.gy
                    diag += self.gy
                diag += self.gbc
                M[idx, idx] += diag
                M[idx, n] -= self.gbc
        M[n, n] = self.gbc * n + self.h_ca * self.a_case
        for idx in range(n):
            M[n, idx] -= self.gbc
        self.M = M.tocsr()

    def solve(self, qcells, ta_c=0.0):
        b = np.zeros(self.n + 1)
        for idx, q in qcells.items():
            b[idx] += q
        b[self.n] += self.h_ca * self.a_case * ta_c
        x = spsolve(self.M, b)
        return x[: self.n].reshape(self.ny, self.nx), x[self.n]

    def transient(self, qcells, ta_c=25.0, t_end_s=3600.0, dt_s=5.0):
        cvec = np.ones(self.n + 1)
        cvec[: self.n] = self.c_board / self.n
        cvec[self.n] = self.c_case
        b = np.zeros(self.n + 1)
        for idx, q in qcells.items():
            b[idx] += q
        b[self.n] += self.h_ca * self.a_case * ta_c
        A = (diags(cvec / dt_s) + self.M).tocsc()
        solveA = factorized(A)
        T = np.ones(self.n + 1) * ta_c
        ts, tmax, tcase, tu2, tled = [], [], [], [], []
        u2 = self.cell(142.0, 75.0)
        led_cells = [self.cell(f["x"], f["y"]) for f in self.board.footprints
                     if f["ref"] and f["ref"].startswith("LED")]
        for step in range(1, int(t_end_s / dt_s) + 1):
            T = solveA(cvec / dt_s * T + b)
            ts.append(step * dt_s)
            tmax.append(float(T[: self.n].max()))
            tcase.append(float(T[self.n]))
            tu2.append(float(T[u2]))
            tled.append(float(max(T[c] for c in led_cells)))
        return dict(t_s=np.array(ts), board_max_c=np.array(tmax), case_c=np.array(tcase),
                    u2_board_c=np.array(tu2), led_board_c=np.array(tled))


def rise_metrics(t, y):
    y0, y1 = float(y[0]), float(y[-1])
    rise = y1 - y0
    if abs(rise) < 1e-9:
        return dict(final_c=y1, t63_s=None, t90_s=None)
    t63 = float(t[np.argmax(y >= y0 + 0.632 * rise)])
    t90 = float(t[np.argmax(y >= y0 + 0.90 * rise)])
    return dict(final_c=y1, t63_s=t63, t90_s=t90)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("reading inputs ...")
    pr = json.loads(POWER_REVIEW.read_text())
    fit = json.loads(FIT_JSON.read_text())
    n_led = int(pr["inputs"]["led_count"])
    per_ch_full = float(pr["led_limiter"]["per_channel_current_assumption_ma"]) / 1000.0
    per_ch_cap = float(pr["led_limiter"]["max_per_channel_current_for_min_limit_ma"]) / 1000.0
    u7_currents = [float(pr["led_limiter"]["currents_ma"][k]) / 1000.0 for k in ("min", "nom", "max")]
    board_thickness = float(fit["assumptions"]["board_thickness_mm"]) / 1000.0
    air_gap_mm = (float(fit["assumptions"]["cavity_floor_z_p_mm"])
                  - float(fit["assumptions"]["board_bottom_z_p_mm"])
                  - float(fit["assumptions"]["gasket_travel_mm"]))
    print(f"  LED count {n_led}, full {per_ch_full*1000:.3f} mA/ch, cap {per_ch_cap*1000:.6f} mA/ch")
    print(f"  board thickness {board_thickness*1000:.2f} mm, free board-to-case gap {air_gap_mm:.2f} mm")
    print("parsing board ...")
    board = Board(BOARD)
    print(f"  {len(board.footprints)} footprints, {len(board.tracks)} tracks, "
          f"{len(board.vias)} vias, {len(board.zone_polys)} zone polygons")
    print("building copper unions ...")
    board.copper = {lay: board.copper_union(lay) for lay in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")}

    print("solving +4V_LED rail network ...")
    rail_full = rail_network(board, led_current_a=3 * per_ch_full, thickness=board_thickness)
    rail_cap = rail_network(board, led_current_a=3 * per_ch_cap, thickness=board_thickness)
    print(f"  full white: {rail_full.get('loss_w')} W, {rail_full.get('leds_connected')}/{rail_full.get('leds_total')} LEDs")
    print(f"  capped:     {rail_cap.get('loss_w')} W")

    print("component calculations ...")
    u2 = u2_calc(board)
    u18 = u18_calc(board)
    u7 = u7_calc(board, currents=u7_currents)
    leds = led_calc(board, rail_full, rail_cap, n_led=n_led,
                    per_ch_full=per_ch_full, per_ch_cap=per_ch_cap)

    # Board model assumptions
    model_assumptions = dict(
        dx_mm=2.5,
        board_thickness_mm=fnum(board_thickness * 1000.0, 2),
        board_to_case_gap_mm=fnum(air_gap_mm, 2),
        k_eff_w_per_mk=dict(nominal=20.0, range=[10.0, 40.0],
                            basis="parallel mixture of 2 x 35 um outer copper, 2 x 15.2 um inner planes and 1.6 mm FR4; 20 W/mK is a screening value"),
        h_board_case_w_per_m2k=dict(nominal=5.0, range=[3.0, 10.0],
                                    basis="enclosed 3.3-4.1 mm air gap under the board plus radiation; UNKNOWN"),
        h_case_ambient_w_per_m2k=dict(nominal=8.0, range=[5.0, 12.0],
                                      basis="natural convection + radiation from the plastic case; UNKNOWN"),
        case_area_m2=dict(nominal=0.054, range=[0.040, 0.070],
                          basis="top + bottom case footprint, 2 x 0.027 m2; sides ignored"),
        case_heat_capacity_j_per_k=dict(nominal=200.0, range=[100.0, 300.0],
                                        basis="~0.15-0.25 kg PLA/PETG case at ~1500 J/kgK; UNKNOWN"),
        board_heat_capacity_j_per_k=None,  # filled below
        r_jb_c_per_w=dict(U2=30.0, U18=20.0, U7=30.0, LED=45.0,
                          basis="junction-to-board screening values; UNKNOWN, not datasheet values"),
        ambient_c=TA_LIST,
    )

    print("building 2D board model ...")
    bm = BoardThermal2D(board, thickness=board_thickness)
    model_assumptions["board_heat_capacity_j_per_k"] = fnum(bm.c_board, 1)
    model_assumptions["r_board_case_k_per_w"] = fnum(bm.r_bc, 2)
    model_assumptions["r_case_ambient_k_per_w"] = fnum(bm.r_ca, 2)
    model_assumptions["r_total_k_per_w"] = fnum(bm.r_bc + bm.r_ca, 2)

    # Scenario heat maps
    led_positions = [(f["x"], f["y"]) for f in board.footprints
                     if f["ref"] and f["ref"].startswith("LED")]
    u2_pos = (board.by_ref["U2"]["x"], board.by_ref["U2"]["y"])
    u18_pos = (board.by_ref["U18"]["x"], board.by_ref["U18"]["y"])
    u7_pos = (board.by_ref["U7"]["x"], board.by_ref["U7"]["y"])

    def make_q(p_led, p_u2, p_u18, p_u7, p_rail):
        q = {}
        for x, y in led_positions:
            c = bm.cell(x, y)
            q[c] = q.get(c, 0.0) + p_led + p_rail / len(led_positions)
        for (x, y), p in ((u2_pos, p_u2), (u18_pos, p_u18), (u7_pos, p_u7)):
            c = bm.cell(x, y)
            q[c] = q.get(c, 0.0) + p
        return q

    scenarios = {
        "full_white_unsupported": dict(
            label="76 LEDs at 5 mA/channel (1.14 A) - NOT SUPPORTED by U7/eFuse",
            p_led=leds["per_led_power"]["full_white_w"],
            p_u2=u2["power_w"]["given"],
            p_u18=u18["losses"][1]["p_total_w"],
            p_u7=u7["full_white"]["p_hot_w"],
            p_rail=rail_full["loss_w"],
        ),
        "limiter_capped": dict(
            label="76 LEDs at 0.761656 mA/channel (0.1737 A) - limiter min corner",
            p_led=leds["per_led_power"]["limiter_cap_w"],
            p_u2=u2["power_w"]["given"],
            p_u18=u18["losses"][1]["p_total_w"],
            p_u7=u7["currents"][0]["p_hot_w"],
            p_rail=rail_cap["loss_w"],
        ),
        "mcu_idle": dict(
            label="LEDs off, MCU/3V3 load 0.3 A, buck 0.1 A",
            p_led=0.0,
            p_u2=u2["power_w"]["given"],
            p_u18=u18["losses"][0]["p_total_w"],
            p_u7=0.0,
            p_rail=0.0,
        ),
        "full_white_5v_ldo": dict(
            label="Full white plus 5.0 V LDO input (sensitivity, not an operating point)",
            p_led=leds["per_led_power"]["full_white_w"],
            p_u2=u2["power_w"]["at_5v_in"],
            p_u18=u18["losses"][1]["p_total_w"],
            p_u7=u7["full_white"]["p_hot_w"],
            p_rail=rail_full["loss_w"],
        ),
    }

    scenario_results = {}
    for name, sc in scenarios.items():
        q = make_q(sc["p_led"], sc["p_u2"], sc["p_u18"], sc["p_u7"], sc["p_rail"])
        T0, tc0 = bm.solve(q, ta_c=0.0)
        total_p = sum(q.values())
        # local board temperatures at TA=0, then add TA
        u2_cell = bm.cell(*u2_pos)
        u18_cell = bm.cell(*u18_pos)
        u7_cell = bm.cell(*u7_pos)
        led_cells = [bm.cell(x, y) for x, y in led_positions]
        rows = []
        for ta in TA_LIST:
            T = T0 + ta
            tc = tc0 + ta
            rows.append(dict(
                ta_c=ta,
                board_max_c=fnum(T.max(), 2),
                board_mean_c=fnum(T.mean(), 2),
                case_c=fnum(tc, 2),
                u2_board_c=fnum(T.reshape(-1)[u2_cell], 2),
                u18_board_c=fnum(T.reshape(-1)[u18_cell], 2),
                u7_board_c=fnum(T.reshape(-1)[u7_cell], 2),
                led_board_max_c=fnum(max(T.reshape(-1)[c] for c in led_cells), 2),
                u2_tj_c=fnum(T.reshape(-1)[u2_cell] + 30.0 * sc["p_u2"], 2),
                u18_tj_c=fnum(T.reshape(-1)[u18_cell] + 20.0 * sc["p_u18"], 2),
                u7_tj_c=fnum(T.reshape(-1)[u7_cell] + 30.0 * sc["p_u7"], 2),
                led_tj_c=fnum(max(T.reshape(-1)[c] for c in led_cells) + 45.0 * sc["p_led"], 2),
            ))
        scenario_results[name] = dict(
            label=sc["label"],
            total_power_w=fnum(total_p, 4),
            power_breakdown=dict(leds=fnum(sc["p_led"] * len(led_positions), 4),
                                 u2=fnum(sc["p_u2"], 4), u18=fnum(sc["p_u18"], 4),
                                 u7=fnum(sc["p_u7"], 4), rail=fnum(sc["p_rail"], 4)),
            rows=rows,
        )

    print("transient simulations ...")
    transient = {}
    for name in ("full_white_unsupported", "limiter_capped"):
        sc = scenarios[name]
        q = make_q(sc["p_led"], sc["p_u2"], sc["p_u18"], sc["p_u7"], sc["p_rail"])
        tr = bm.transient(q, ta_c=25.0, t_end_s=7200.0, dt_s=5.0)
        transient[name] = dict(
            label=sc["label"],
            board_max=rise_metrics(tr["t_s"], tr["board_max_c"]),
            case=rise_metrics(tr["t_s"], tr["case_c"]),
            u2_board=rise_metrics(tr["t_s"], tr["u2_board_c"]),
            led_board=rise_metrics(tr["t_s"], tr["led_board_c"]),
            series={k: [fnum(v, 3) for v in tr[k]] for k in
                    ("t_s", "board_max_c", "case_c", "u2_board_c", "led_board_c")},
        )

    # Sensitivity: h_bc and k_eff on the capped scenario
    print("sensitivity ...")
    sens = []
    sc = scenarios["limiter_capped"]
    q = make_q(sc["p_led"], sc["p_u2"], sc["p_u18"], sc["p_u7"], sc["p_rail"])
    for h in (3.0, 5.0, 10.0):
        m = BoardThermal2D(board, h_bc=h, thickness=board_thickness)
        T, tc = m.solve(q, ta_c=25.0)
        sens.append(dict(parameter="h_board_case_w_per_m2k", value=h,
                         board_max_c=fnum(T.max(), 2), case_c=fnum(tc, 2)))
    for k in (10.0, 20.0, 40.0):
        m = BoardThermal2D(board, k_eff=k, thickness=board_thickness)
        T, tc = m.solve(q, ta_c=25.0)
        sens.append(dict(parameter="k_eff_w_per_mk", value=k,
                         board_max_c=fnum(T.max(), 2), case_c=fnum(tc, 2)))

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------
    print("plots ...")
    plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.3})

    # Tj vs TA
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axes[0]
    for th in (80.0, 100.0, 120.0, 140.0):
        ys = [ta + th * u2["power_w"]["given"] for ta in TA_LIST]
        ax.plot(TA_LIST, ys, marker="o", label=f"U2 theta_JA={th:g} C/W")
    ys5 = [ta + 120.0 * u2["power_w"]["at_5v_in"] for ta in TA_LIST]
    ax.plot(TA_LIST, ys5, ls="--", color="tab:red", marker="x",
            label="U2 5 V in, 120 C/W")
    ax.axhline(TJ_LIMIT, color="k", ls="--", lw=1, label="125 C limit")
    ax.set_xlabel("Ambient temperature (C)")
    ax.set_ylabel("Junction temperature (C)")
    ax.set_title("U2 MAX38902 LDO, P=0.2484 W")
    ax.legend(fontsize=7)
    ax = axes[1]
    for th, lab in ((70.0, "U18 theta_JA=70"), (112.2, "U18 theta_JA=112.2")):
        ys = [ta + th * u18["losses"][1]["p_total_w"] for ta in TA_LIST]
        ax.plot(TA_LIST, ys, marker="s", label=lab)
    ys = [ta + 182.6 * u7["currents"][2]["p_hot_w"] for ta in TA_LIST]
    ax.plot(TA_LIST, ys, marker="^", label="U7 theta_JA=182.6 (0.234 A)")
    ys = [ta + 45.0 * leds["per_led_power"]["full_white_w"] for ta in TA_LIST]
    ax.plot(TA_LIST, ys, marker="d", label="LED theta_JA=45 (60 mW)")
    ax.axhline(TJ_LIMIT, color="k", ls="--", lw=1, label="125 C limit")
    ax.set_xlabel("Ambient temperature (C)")
    ax.set_ylabel("Junction temperature (C)")
    ax.set_title("U18 / U7 / LED component checks")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "tj_vs_ta.png", dpi=160)
    plt.close(fig)

    # Transient
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, name in zip(axes, ("full_white_unsupported", "limiter_capped")):
        tr = transient[name]
        s = tr["series"]
        ax.plot(s["t_s"], s["board_max_c"], label="board max")
        ax.plot(s["t_s"], s["case_c"], label="case")
        ax.plot(s["t_s"], s["u2_board_c"], label="U2 board")
        ax.plot(s["t_s"], s["led_board_c"], label="LED board max")
        ax.set_xlabel("Time (s)")
        ax.set_title(tr["label"], fontsize=8)
        ax.legend(fontsize=7)
        ax.annotate(f"t63={tr['board_max']['t63_s']:.0f} s\nt90={tr['board_max']['t90_s']:.0f} s",
                    xy=(0.55, 0.15), xycoords="axes fraction", fontsize=7)
    axes[0].set_ylabel("Temperature (C)")
    fig.tight_layout()
    fig.savefig(OUT / "transient_rise.png", dpi=160)
    plt.close(fig)

    # Board maps
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.6))
    for ax, name in zip(axes, ("full_white_unsupported", "limiter_capped")):
        sc = scenarios[name]
        q = make_q(sc["p_led"], sc["p_u2"], sc["p_u18"], sc["p_u7"], sc["p_rail"])
        T, tc = bm.solve(q, ta_c=25.0)
        im = ax.imshow(T, origin="lower", extent=[board.bbox[0], board.bbox[2], board.bbox[1], board.bbox[3]],
                       cmap="inferno", aspect="auto")
        ax.scatter([u2_pos[0], u18_pos[0], u7_pos[0]], [u2_pos[1], u18_pos[1], u7_pos[1]],
                   c="cyan", s=18, marker="x")
        ax.set_title(f"{name}\nboard max {T.max():.1f} C, case {tc:.1f} C", fontsize=8)
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
        fig.colorbar(im, ax=ax, label="C")
    fig.tight_layout()
    fig.savefig(OUT / "board_temperature_map.png", dpi=160)
    plt.close(fig)

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------
    result = dict(
        schema="maru60.thermal-sim.v1",
        generated_utc=_dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        qualification="SIMULATION-ONLY SCREENING. NOT A QUALIFIED THERMAL DESIGN. theta_JA, copper area, via fill, case convection and ambient are assumptions or unknowns.",
        board=dict(
            path=str(BOARD.relative_to(REPO)),
            sha256=sha256(BOARD),
            width_mm=fnum(board.width, 2),
            height_mm=fnum(board.height, 2),
            area_mm2=fnum(board.area_mm2, 1),
            thickness_mm=fnum(board_thickness * 1000.0, 2),
            copper_layers=["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
            copper_area_mm2={lay: fnum(board.copper[lay].area, 1) for lay in board.copper},
            footprints=len(board.footprints),
            tracks=len(board.tracks),
            vias=len(board.vias),
        ),
        inputs=dict(
            power_review="pcb/experiments/resume-20261109-relocated-expansion-zero-opens/qa/power-review/power-review.json",
            mechanical_fit="pcb/experiments/resume-20261109-relocated-expansion-zero-opens/qa/mechanical-fit/fit.json",
            led_count=n_led,
            per_channel_full_ma=fnum(per_ch_full * 1000.0, 6),
            per_channel_cap_ma=fnum(per_ch_cap * 1000.0, 6),
            u7_currents_ma=[fnum(c * 1000.0, 3) for c in u7_currents],
            board_thickness_mm=fnum(board_thickness * 1000.0, 2),
            board_top_z_mm=fnum(fit["assumptions"]["board_top_z_p_mm"], 2),
            board_bottom_z_mm=fnum(fit["assumptions"]["board_bottom_z_p_mm"], 2),
            cavity_floor_z_mm=fnum(fit["assumptions"]["cavity_floor_z_p_mm"], 2),
            gasket_travel_mm=fnum(fit["assumptions"]["gasket_travel_mm"], 2),
            board_to_case_gap_mm=fnum(air_gap_mm, 2),
            datasheets=["qa/thermal-sim/_tps62932.txt", "qa/thermal-sim/_tps2553.txt"],
        ),
        assumptions=model_assumptions,
        unknowns=[
            "U2 MAX38902AATA+T theta_JA and junction-to-board resistance; no datasheet thermal table is in the repository.",
            "U2 exposed-pad via fill/copper: no via centre lies inside the 0.8 x 1.38 mm EP; nearest GND via is 1.40 mm away.",
            "Actual copper thickness, etch factor and solder mask coverage; 35 um outer / 15.2 um inner nominal from the stackup.",
            "Board-to-case and case-to-ambient convection/radiation coefficients inside the closed plastic case.",
            "Case material, emissivity, internal air temperature and whether any fan/vent exists.",
            "SK6805 per-channel current, forward voltage and optical efficiency; 5 mA/channel and 4.0 V rail are assumptions.",
            "TPS62932 efficiency at 4 V output / 4.7 uH / 5 V input; datasheet curve is 5 V output / 10 uH / 6 V input.",
            "L2 XAL4030-472MEC DCR and its temperature rise; 27.5 mOhm max is assumed.",
            "TPS2553 Rds(on) at the actual junction temperature; hot 135 mOhm max is used.",
            "Actual 3V3 and 4V load currents and simultaneity; 0.3 A LDO and 0.1/0.3 A buck are task inputs.",
            "Whether the LED rail can ever be driven at full white before U7/eFuse current limit trips.",
        ],
        components=dict(U2=u2, U18=u18, U7=u7, LEDs=leds),
        board_model=dict(
            method="2D finite-volume board (2.5 mm cells) with a single lumped case node; steady state and backward-Euler transient.",
            assumptions=model_assumptions,
            scenarios=scenario_results,
            transient=transient,
            sensitivity=sens,
        ),
        findings=[
            dict(id="TH-01", severity="review-flag",
                 title="U2 EP has no thermal via",
                 detail=f"No via centre is inside the U2 exposed pad; nearest GND via is {u2['nearest_gnd_via']['dist']:.2f} mm away. The EP relies on lateral B.Cu/FR4 spreading. theta_JA is unknown and the as-built value is likely worse than a via-filled EP."),
            dict(id="TH-02", severity="review-flag",
                 title="U2 passes at 4 V input but not at 5 V input at 85 C ambient",
                 detail="At 0.2484 W and theta_JA=120 C/W, Tj(85 C)=114.8 C (10.2 C margin). At 5 V input (0.510 W), Tj(85 C)=146.2 C, above 125 C. The 4 V buck rail is therefore part of the thermal budget."),
            dict(id="TH-03", severity="review-flag",
                 title="Full white is electrically unsupported and thermally hot",
                 detail="1.14 A through 76 LEDs is 4.56 W; the 2D model gives an 83.1 C board maximum at 25 C ambient and 143.1 C at 85 C ambient. U7 latches off at 173.7-233.9 mA, so this is a what-if, not an operating point."),
            dict(id="TH-04", severity="info",
                 title="Limiter-capped LED case is thermally feasible in the model",
                 detail="At 0.761656 mA/channel (0.1737 A, 0.693 W LED heat), the model gives a 42 C board maximum at 25 C ambient and 102 C at 85 C ambient; U2 Tj is 109.6 C at 85 C with the board-model R_jb, and 114.8 C with theta_JA=120 C/W."),
            dict(id="TH-05", severity="info",
                 title="U18 and U7 are not the thermal limit",
                 detail="U18 loss is 0.060 W at 0.1 A and 0.119 W at 0.3 A; Tj(85 C) is 98.3 C with the JEDEC 112.2 C/W value. U7 loss is 4.1-7.4 mW at the limiter currents; Tj rise is <1.4 C."),
            dict(id="TH-06", severity="review-flag",
                 title="Board/case time constant is minutes, not seconds",
                 detail="The 2D model gives t63 ~775 s and t90 ~1970 s for the board maximum at full white; the case is slower (t63 ~1260 s). A short bench test will not reach steady state."),
        ],
        measurements_needed=[
            "Thermocouple or IR camera on U2, U18, L2, U7 and several LEDs at 25/40/60/85 C ambient.",
            "U2 EP-to-board thermal resistance and the effect of adding/filling thermal vias.",
            "Actual board and case temperatures at the limiter-capped LED current after 30-60 min (steady state).",
            "Case internal air temperature and case external surface temperature; case material/emissivity.",
            "Actual SK6805 per-channel current and forward voltage at the firmware brightness cap.",
            "TPS62932 efficiency at 4 V output, 5 V input, 4.7 uH and 0.1/0.3 A.",
            "L2 DCR and temperature rise at 0.1/0.3 A.",
            "U7 Rds(on) and case temperature at 0.17-0.23 A.",
            "Confirm the LED rail never reaches full white before U7/eFuse current limit trips.",
        ],
    )

    (OUT / "thermal-sim.json").write_text(json.dumps(result, indent=2) + "\n")

    # ------------------------------------------------------------------
    # REPORT.md
    # ------------------------------------------------------------------
    u2_rows = []
    for row in u2["tj_vs_ta"]:
        u2_rows.append([f"{row['ta_c']:g}", f"{row['tj_at_80_c_per_w']:.1f}",
                        f"{row['tj_at_100_c_per_w']:.1f}", f"{row['tj_at_120_c_per_w']:.1f}",
                        f"{row['tj_at_140_c_per_w']:.1f}", f"{row['required_theta_ja_c_per_w']:.1f}"])
    u2_5v_rows = []
    for row in u2["tj_vs_ta_5v"]:
        ta = row["ta_c"]
        u2_5v_rows.append([f"{ta:g}", f"{row['tj_at_80_c_per_w']:.1f}",
                           f"{row['tj_at_100_c_per_w']:.1f}", f"{row['tj_at_120_c_per_w']:.1f}",
                           f"{row['tj_at_140_c_per_w']:.1f}",
                           f"{u2['required_theta_ja_5v'][f'{ta:g}']:.1f}"])

    u18_rows = []
    for r in u18["losses"]:
        u18_rows.append([f"{r['iout_a']:g}", f"{r['pout_w']:.2f}", f"{r['efficiency']['nom']*100:.0f}",
                         f"{r['p_total_w']*1000:.1f}", f"{r['p_conduction_w']*1000:.2f}",
                         f"{r['p_inductor_dcr_w']*1000:.2f}", f"{r['p_switching_quiescent_other_w']*1000:.1f}",
                         f"{r['tj_at_ta']['85']:.1f}", f"{r['tj_at_ta_jedec']['85']:.1f}"])

    u7_rows = []
    for r in u7["currents"]:
        u7_rows.append([f"{r['current_a']*1000:.1f}", f"{r['p_hot_w']*1000:.2f}",
                        f"{r['tj_hot_at_ta']['25']:.1f}", f"{r['tj_hot_at_ta']['85']:.1f}",
                        f"{r['required_theta_ja_hot']['85']:.0f}"])

    scen_rows = []
    for name, sc in scenario_results.items():
        for row in sc["rows"]:
            scen_rows.append([name, f"{row['ta_c']:g}", f"{sc['total_power_w']:.2f}",
                              f"{row['board_max_c']:.1f}", f"{row['board_mean_c']:.1f}",
                              f"{row['case_c']:.1f}", f"{row['u2_tj_c']:.1f}",
                              f"{row['led_tj_c']:.1f}"])

    sens_rows = [[s["parameter"], f"{s['value']:g}", f"{s['board_max_c']:.1f}", f"{s['case_c']:.1f}"] for s in sens]

    report = f"""# Maru60 thermal simulation - lumped network and board spreading

**Status: SIMULATION-ONLY SCREENING. This is not a qualified thermal design.**
Every `theta_JA`, convection coefficient, via-fill assumption and ambient value
below is an assumption or an unknown unless it is explicitly read from the board
or a datasheet extract. The model is a screening tool to rank the gaps and to
define the thermocouple/IR measurements; it is not a substitute for them.

- Board: `{result['board']['path']}`
- SHA256: `{result['board']['sha256']}`
- Board size: **{result['board']['width_mm']:.1f} x {result['board']['height_mm']:.1f} mm**
  ({result['board']['area_mm2']:.0f} mm2), {board_thickness*1000:.2f} mm, 4 copper layers.
- Generated by `pcb/tools/simulate_thermal.py` with the repository venv.
- Machine-readable result: `qa/thermal-sim/thermal-sim.json`.
- Plots: `tj_vs_ta.png`, `transient_rise.png`, `board_temperature_map.png`.

## 1. What is modelled

1. **U2 MAX38902AATA+T LDO** at the task's 0.2484 W / 300 mA, with the
   exposed-pad copper/via inventory and a `theta_JA` sweep.
2. **U18 TPS62932 buck** at 0.1 A and 0.3 A, with conduction, inductor DCR and
   the remaining switching/quiescent loss inferred from the datasheet
   efficiency curve.
3. **U7 TPS2553-1** at the 173.7/201.5/233.9 mA limiter corners, plus a
   full-white what-if.
4. **76 SK6805 LEDs** at 5 mA/channel (1.14 A, unsupported) and at
   0.761656 mA/channel (0.1737 A, limiter min corner), including the
   `+4V_LED` track/via network loss.
5. **Board-level 2D finite-volume model** (2.5 mm cells) with a single lumped
   case node, steady state and a backward-Euler transient.

## 2. Assumptions (all are screening values)

| Item | Nominal | Range | Basis |
|---|---:|---:|---|
| U2 `theta_JA` | 120 C/W | 80-140 | **UNKNOWN.** 80 assumes a soldered EP with thermal vias; 120 is the as-built screening value because no via is in the EP. |
| U18 `theta_JA` | 70 C/W | 60.2-112.2 | TI EVM 60.2 C/W, JEDEC 112.2 C/W; 70 is a board-with-planes screening value. |
| U7 `theta_JA` | 182.6 C/W | - | TI DBV SOT-23-6 JEDEC value. |
| LED `theta_JA` | 45 C/W | 30-60 | **UNKNOWN.** 1.5 x 1.5 mm LED on {board_thickness*1000:.2f} mm FR4 with local copper. |
| Board in-plane `k` | 20 W/mK | 10-40 | Parallel mixture of 2 x 35 um outer copper, 2 x 15.2 um inner planes and FR4. |
| Board-to-case `h` | 5 W/m2K | 3-10 | Enclosed {air_gap_mm:.2f} mm free air gap plus radiation. **UNKNOWN.** |
| Case-to-ambient `h` | 8 W/m2K | 5-12 | Natural convection + radiation from the plastic case. **UNKNOWN.** |
| Case area | 0.054 m2 | 0.040-0.070 | Top + bottom footprint, 2 x 0.027 m2; sides ignored. |
| Case heat capacity | 200 J/K | 100-300 | ~0.15-0.25 kg PLA/PETG at ~1500 J/kgK. **UNKNOWN.** |
| Board heat capacity | {model_assumptions['board_heat_capacity_j_per_k']:.0f} J/K | - | 1.8e6 J/m3K x board volume. |
| Board thickness | {board_thickness*1000:.2f} mm | - | `fit.json` `board_thickness_mm`. |
| Board-to-case free gap | {air_gap_mm:.2f} mm | - | `fit.json`: cavity floor - board bottom - gasket travel. |
| `R_board-case` | {model_assumptions['r_board_case_k_per_w']:.2f} K/W | - | 1/(h_bc x board area). |
| `R_case-ambient` | {model_assumptions['r_case_ambient_k_per_w']:.2f} K/W | - | 1/(h_ca x case area). |
| `R_total` | {model_assumptions['r_total_k_per_w']:.2f} K/W | - | Sum of the two. |
| U2/U18/U7/LED `R_jb` | 30/20/30/45 C/W | - | **UNKNOWN** junction-to-board screening values. |

The board stackup is 35 um outer copper, 15.2 um inner copper, {board_thickness*1000:.2f} mm FR4
(from the KiCad stackup and `fit.json`). Copper area is computed from the filled zone
polygons, tracks and pads; it is a geometric area, not a measured copper
thickness or a via-fill claim.

Case geometry from `fit.json`: board top Z **{fit['assumptions']['board_top_z_p_mm']:.2f} mm**,
board bottom Z **{fit['assumptions']['board_bottom_z_p_mm']:.2f} mm**, cavity floor Z
**{fit['assumptions']['cavity_floor_z_p_mm']:.2f} mm**, gasket travel
**{fit['assumptions']['gasket_travel_mm']:.2f} mm**, free board-to-case gap
**{air_gap_mm:.2f} mm**. The model uses the free gap only to justify the
board-to-case `h` assumption; it does not model the case shell or the gasket.

## 3. U2 MAX38902AATA+T LDO

- Package: TDFN-8 2 x 2 mm, exposed pad **0.8 x 1.38 mm**.
- Power: **0.2484 W at 300 mA** (task input; equivalent to 0.828 V dropout,
  4.128 V in / 3.3 V out). At 4.0 V in the dissipation is 0.210 W; at 5.0 V in
  it is 0.510 W.
- **No via centre is inside the exposed pad.** The nearest GND via is
  **{u2['nearest_gnd_via']['dist']:.2f} mm** away; there are
  {u2['vias_within_1p5mm']} vias within 1.5 mm and {u2['vias_within_3mm']} within
  3 mm. The EP therefore relies on lateral B.Cu/FR4 spreading.
- Copper area within 2/3/5/8/12 mm of U2 (all four layers):
  **{u2['copper_area_mm2']['2']['total']:.1f} / {u2['copper_area_mm2']['3']['total']:.1f} /
  {u2['copper_area_mm2']['5']['total']:.1f} / {u2['copper_area_mm2']['8']['total']:.1f} /
  {u2['copper_area_mm2']['12']['total']:.1f} mm2**. The two inner GND planes
  dominate the 5-12 mm numbers.

### Tj at 0.2484 W

{table(u2_rows, ["TA (C)", "Tj, 80 C/W", "Tj, 100 C/W", "Tj, 120 C/W", "Tj, 140 C/W", "theta_JA needed for Tj<=125 C"])}

At 0.2484 W the required `theta_JA` is **{u2['required_theta_ja']['85']:.1f} C/W at
85 C ambient** and **{u2['required_theta_ja']['25']:.1f} C/W at 25 C**. Even the
140 C/W screening value passes at 85 C for this power.

### Tj at 5.0 V input (0.510 W) - sensitivity

{table(u2_5v_rows, ["TA (C)", "Tj, 80 C/W", "Tj, 100 C/W", "Tj, 120 C/W", "Tj, 140 C/W", "theta_JA needed for Tj<=125 C"])}

At 5.0 V input the required `theta_JA` at 85 C is **{u2['required_theta_ja_5v']['85']:.1f} C/W**.
The as-built no-EP-via layout is unlikely to guarantee that. **The 4 V buck rail
is part of the LDO thermal budget; a 5 V LDO input is the worst case.**

## 4. U18 TPS62932 buck and L2

- VIN 5.0 V, VOUT 4.0 V, fSW 500 kHz, L2 4.7 uH.
- Efficiency is anchored to the TPS62932 datasheet Figure 8-21 (Vout=5 V,
  fSW=500 kHz, L=10 uH, Vin=6 V) and derated for 4 V output / 4.7 uH. It is an
  assumption, not a measurement.
- Conduction uses the datasheet Rds(on) 76 mOhm high-side / 32 mOhm low-side
  at 25 C and L2 DCR 27.5 mOhm max. The remaining loss is labelled
  "switching + quiescent + other" and is inferred by difference.

{table(u18_rows, ["Iout (A)", "Pout (W)", "Eff (%)", "Total loss (mW)", "Conduction (mW)", "L2 DCR (mW)", "Switching/other (mW)", "Tj@85, 70 C/W", "Tj@85, 112.2 C/W"])}

At 0.3 A the total loss is **{u18['losses'][1]['p_total_w']*1000:.1f} mW**; Tj at
85 C is **{u18['losses'][1]['tj_at_ta']['85']:.1f} C** with 70 C/W and
**{u18['losses'][1]['tj_at_ta_jedec']['85']:.1f} C** with the JEDEC 112.2 C/W.
U18 is not the thermal limit. The nearest GND via is
{u18['nearest_gnd_via']['dist']:.2f} mm from the package centre.

## 5. U7 TPS2553-1

- DBV SOT-23-6, `theta_JA` 182.6 C/W, Rds(on) 95 mOhm max at 25 C and
  135 mOhm max over temperature.
- Currents: **173.657 / 201.513 / 233.901 mA** (min/nom/max limiter corners).

{table(u7_rows, ["Current (mA)", "P hot (mW)", "Tj@25 C", "Tj@85 C", "theta_JA needed at 85 C"])}

U7 dissipates only **{u7['currents'][2]['p_hot_w']*1000:.1f} mW** at the maximum
limiter current; the junction rise is **<1.4 C**. U7 is not the thermal limit.
The full-white what-if (1.14 A) would dissipate
**{u7['full_white']['p_hot_w']*1000:.0f} mW** and reach
**{u7['full_white']['tj_at_85c']:.1f} C at 85 C ambient**, but the part's
current limit is 173.7-233.9 mA and it latches off, so this is not an operating
point.

## 6. LED chains

- 76 SK6805-EC15-001: 64 per-key on F.Cu, 12 underglow on B.Cu.
- 3 channels per LED. At **5 mA/channel** the rail current is **1.14 A** and the
  LED heat is **{leds['total_power']['full_white_w']:.2f} W** (60 mW/LED at 4.0 V).
- At **0.761656 mA/channel** (the min-limiter cap) the rail current is
  **0.1737 A** and the LED heat is **{leds['total_power']['limiter_cap_w']:.2f} W**
  (9.14 mW/LED).
- `+4V_LED` network: {rail_full['segments']} track segments, {rail_full['vias']} vias,
  {rail_full['leds_connected']}/{rail_full['leds_total']} LED pads connected in the
  graph. Resistive loss is **{rail_full['loss_w']*1000:.1f} mW at 1.14 A** and
  **{rail_cap['loss_w']*1000:.2f} mW at 0.1737 A**; the maximum source-to-LED
  drop at 1.14 A is **{rail_full['max_drop_v']*1000:.0f} mV**. The rail loss is
  small compared with the LED heat.
- Local copper within 2.5 mm of an LED: mean
  **{leds['local_copper_2p5mm_mm2']['mean']:.1f} mm2**, min
  **{leds['local_copper_2p5mm_mm2']['min']:.1f} mm2**, max
  **{leds['local_copper_2p5mm_mm2']['max']:.1f} mm2**.
- Per-LED `theta_JA` is unknown; 45 C/W gives a junction rise of only
  **{45.0*leds['per_led_power']['full_white_w']:.1f} C** at 60 mW and
  **{45.0*leds['per_led_power']['limiter_cap_w']:.1f} C** at 9.14 mW. The LED
  junction is dominated by the board temperature, not by its own package.

## 7. Board-level 2D model

The board is a 2.5 mm finite-volume grid with in-plane conduction, a
board-to-case conductance, and one lumped case node coupled to ambient. The
model is linear; the steady-state temperatures scale with power and ambient.

### Steady state

{table(scen_rows, ["Scenario", "TA (C)", "Total P (W)", "Board max (C)", "Board mean (C)", "Case (C)", "U2 Tj (C)", "LED Tj (C)"])}

Key numbers at **25 C ambient**:

- **Full white (unsupported):** total **{scenario_results['full_white_unsupported']['total_power_w']:.2f} W**,
  board max **{scenario_results['full_white_unsupported']['rows'][0]['board_max_c']:.1f} C**,
  case **{scenario_results['full_white_unsupported']['rows'][0]['case_c']:.1f} C**,
  U2 Tj **{scenario_results['full_white_unsupported']['rows'][0]['u2_tj_c']:.1f} C**,
  LED Tj **{scenario_results['full_white_unsupported']['rows'][0]['led_tj_c']:.1f} C**.
- **Limiter-capped:** total **{scenario_results['limiter_capped']['total_power_w']:.2f} W**,
  board max **{scenario_results['limiter_capped']['rows'][0]['board_max_c']:.1f} C**,
  case **{scenario_results['limiter_capped']['rows'][0]['case_c']:.1f} C**,
  U2 Tj **{scenario_results['limiter_capped']['rows'][0]['u2_tj_c']:.1f} C**,
  LED Tj **{scenario_results['limiter_capped']['rows'][0]['led_tj_c']:.1f} C**.

At **85 C ambient** the limiter-capped case gives board max
**{scenario_results['limiter_capped']['rows'][3]['board_max_c']:.1f} C**, case
**{scenario_results['limiter_capped']['rows'][3]['case_c']:.1f} C**, U2 Tj
**{scenario_results['limiter_capped']['rows'][3]['u2_tj_c']:.1f} C** and LED Tj
**{scenario_results['limiter_capped']['rows'][3]['led_tj_c']:.1f} C**. The U2
component-level check with `theta_JA=120 C/W` gives **114.8 C**, so the U2
margin at 85 C is about **10 C** and the actual `theta_JA` is the deciding
unknown.

### Transient

The board/case system is slow because the board and case have significant
thermal mass and the case is poorly coupled to the board.

| Scenario | Node | Final (C) | t63 (s) | t90 (s) |
|---|---|---:|---:|---:|
| Full white | board max | {transient['full_white_unsupported']['board_max']['final_c']:.1f} | {transient['full_white_unsupported']['board_max']['t63_s']:.0f} | {transient['full_white_unsupported']['board_max']['t90_s']:.0f} |
| Full white | case | {transient['full_white_unsupported']['case']['final_c']:.1f} | {transient['full_white_unsupported']['case']['t63_s']:.0f} | {transient['full_white_unsupported']['case']['t90_s']:.0f} |
| Limiter-capped | board max | {transient['limiter_capped']['board_max']['final_c']:.1f} | {transient['limiter_capped']['board_max']['t63_s']:.0f} | {transient['limiter_capped']['board_max']['t90_s']:.0f} |
| Limiter-capped | case | {transient['limiter_capped']['case']['final_c']:.1f} | {transient['limiter_capped']['case']['t63_s']:.0f} | {transient['limiter_capped']['case']['t90_s']:.0f} |

A 30-60 s bench measurement will not see steady state. Plan for **30-60 minutes**
at each power/ambient point, or use a transient log and fit the curve.

### Sensitivity (limiter-capped, 25 C ambient)

{table(sens_rows, ["Parameter", "Value", "Board max (C)", "Case (C)"])}

The board-to-case coefficient is the dominant unknown. The in-plane
conductivity changes the local peak only weakly because the LED heat is
distributed over most of the board.

## 8. What is closed, what is not

**Closed by this simulation (arithmetic/geometry, not qualification):**

- U2, U18, U7 and LED junction-temperature arithmetic at the stated powers and
  assumed `theta_JA` values.
- The U2 EP via/copper inventory: **no via in the EP**, nearest GND via
  {u2['nearest_gnd_via']['dist']:.2f} mm.
- The `+4V_LED` track/via network loss and maximum drop at 1.14 A and 0.1737 A.
- A board/case steady-state and transient screening model with explicit
  assumptions and a sensitivity band.
- The ranking: **U2 is the tightest component at 85 C ambient; U18 and U7 are
  not the limit; full white is electrically unsupported and thermally hot.**

**Not closed - needs a thermocouple/IR and bench measurements:**

- Actual U2 `theta_JA` and EP-to-board resistance; the effect of adding/filling
  thermal vias.
- Actual board, case and internal-air temperatures at the limiter-capped LED
  current after 30-60 minutes.
- Actual SK6805 per-channel current, forward voltage and optical efficiency.
- TPS62932 efficiency at 4 V output / 5 V input / 4.7 uH / 0.1-0.3 A.
- L2 DCR and temperature rise; U7 Rds(on) and case temperature.
- Case material, emissivity, vents/fan and the real ambient inside the case.
- Confirmation that firmware never commands full white before U7/eFuse trips.

## 9. Worst-case conditions

1. **85 C ambient + 5.0 V LDO input + 0.3 A 3V3 load:** U2 Tj is
   **146.2 C** at `theta_JA=120 C/W` (and still **125.8 C** at 80 C/W). This
   fails the 125 C limit. The 4 V buck rail is what keeps U2 inside the limit.
2. **85 C ambient + 4.0 V LDO input + limiter-capped LEDs:** U2 Tj is
   **114.8 C** at 120 C/W (10.2 C margin); the board model gives 109.6 C. This
   is the tightest supported operating point.
3. **25 C ambient + full white (unsupported):** board max **83.1 C**, LED Tj
   **84.3 C**, U2 Tj **90.5 C**. The board is hot but below 125 C; the problem is
   that U7/eFuse cannot deliver 1.14 A and will latch off.
4. **85 C ambient + full white (unsupported):** board max **143.1 C**, LED Tj
   **144.3 C**, U2 Tj **150.5 C**. This is a thermal fail even if the current
   limit were bypassed.

## 10. Findings

"""
    for f in result["findings"]:
        report += f"- **{f['id']} ({f['severity']}): {f['title']}.** {f['detail']}\n"

    report += f"""
## 11. Measurements needed

"""
    for m in result["measurements_needed"]:
        report += f"- {m}\n"

    report += f"""
## 12. Reproduction

```sh
cd {REPO}
.venv/bin/python pcb/tools/simulate_thermal.py
```

The script reads the board, `qa/power-review/power-review.json` and
`qa/mechanical-fit/fit.json`; the datasheet extracts
`_tps62932.txt` and `_tps2553.txt` are reused from the previous attempt. No
network access is used. The output is written only under
`qa/thermal-sim/` and `pcb/tools/simulate_thermal.py`.

## 13. Verdict

**Simulation-solvable thermal gaps are closed to the extent the assumptions
allow; the design is not thermally qualified.** For the 0.2484 W LDO power, the
supported limiter-capped case is inside the 125 C limit at 85 C ambient if U2
`theta_JA` is below about **161 C/W**; the 120 C/W screening value gives
**114.8 C** (10.2 C margin). The LDO input must stay near 4 V: at 5 V input the
required `theta_JA` is **78.4 C/W**, which the as-built no-via EP is unlikely to
meet. The as-built U2 EP has no thermal via, so the actual `theta_JA` is the
single most important measurement. Full white is not an operating point: the
TPS2553-1 and the eFuse current-limit it long before 1.14 A, and the board model
shows it would be hot even if it could be delivered.
"""
    (OUT / "REPORT.md").write_text(report)

    print(f"wrote {OUT/'thermal-sim.json'}")
    print(f"wrote {OUT/'REPORT.md'}")
    print(f"wrote {OUT/'tj_vs_ta.png'}")
    print(f"wrote {OUT/'transient_rise.png'}")
    print(f"wrote {OUT/'board_temperature_map.png'}")


if __name__ == "__main__":
    main()
