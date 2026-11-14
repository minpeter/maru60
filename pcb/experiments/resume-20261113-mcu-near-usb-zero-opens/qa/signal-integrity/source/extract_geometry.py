"""Pull every number the signal-integrity checks need out of the routed board.

Input : build/si/board.json (pcb/tools/dump_board_geometry.py, run by run_all.py)
Output: build/si/out/geometry.json and build/si/out/lines.json

Capacitance model per net (all COMPUTED from geometry, nothing measured):
    C = sum(track length * C'(width))            C' from the 2-D field solve
      + sum(pad area over plane * eps/h) + pad perimeter * fringe
      + vias * C_VIA + component pins (datasheet values, added by the callers)
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fieldsolve as fs  # noqa: E402
from geom import Board, PLANE_FOR, ROOT  # noqa: E402

OUT = ROOT / "build" / "si" / "out"
EPS0_PF_MM = 8.8541878128e-3  # pF/mm

# Via through both planes: C = 1.41 * er * T * D1 / (D2 - D1) (Johnson & Graham), inches -> pF.
# T 1.6 mm, pad 0.5 mm, antipad 0.5 + 2 * 0.2 mm clearance.  L = 5.08 h (ln(4h/d) + 1) nH, h in inches.
VIA_C_PF = 1.41 * 4.4 * (1.6 / 25.4) * (0.5 / 25.4) / ((0.9 - 0.5) / 25.4)
VIA_L_NH = 5.08 * (1.6 / 25.4) * (math.log(4 * 1.6 / 0.25) + 1)

WIDTHS = [0.15, 0.2, 0.25, 0.3, 0.35, 0.5, 0.8]


def line_table():
    tab = {f"{w:.2f}": fs.single(w) for w in WIDTHS}
    wide = fs.single(2.0)
    fringe = (wide["C_pF_per_mm"] - EPS0_PF_MM * fs.ER_PREPREG * 2.0 / fs.H) / 2  # pF per mm of pad edge
    return {"single": tab, "pad_fringe_pF_per_mm_edge": fringe,
            "plate_pF_per_mm2": EPS0_PF_MM * fs.ER_PREPREG / fs.H,
            "via_C_pF": VIA_C_PF, "via_L_nH": VIA_L_NH,
            "stack": {"h_mm": fs.H, "t_mm": fs.T, "er_prepreg": fs.ER_PREPREG, "er_mask": fs.ER_MASK, "mask_mm": fs.MASK},
            "selftest": fs.selftest()}


class Caps:
    def __init__(self, board, lines):
        self.b, self.l = board, lines
        self.ws = sorted(float(k) for k in lines["single"])

    def per_mm(self, w, key="C_pF_per_mm"):
        ws = self.ws
        if w <= ws[0]:
            return self.l["single"][f"{ws[0]:.2f}"][key]
        if w >= ws[-1]:
            return self.l["single"][f"{ws[-1]:.2f}"][key]
        for a, c in zip(ws, ws[1:]):
            if a <= w <= c:
                u = (w - a) / (c - a)
                return (1 - u) * self.l["single"][f"{a:.2f}"][key] + u * self.l["single"][f"{c:.2f}"][key]

    def net(self, name):
        b = self.b
        c_track = sum(math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"]) * self.per_mm(t["w"]) for t in b.by_net[name])
        c_pad, pad_area = 0.0, 0.0
        for p in b.pads_by_net[name]:
            if not p["poly"] or len(p["poly"][0]) < 3:
                continue
            poly = Polygon(p["poly"][0])
            layers = [l for l in ("F.Cu", "B.Cu") if l in p["layers"] or p["drill"][0] > 0]
            for layer in layers:
                plane = b.plane.get(PLANE_FOR[layer])
                over = poly.intersection(plane).area if plane is not None else 0.0
                c_pad += over * self.l["plate_pF_per_mm2"] + poly.length * (over / max(poly.area, 1e-9)) * self.l["pad_fringe_pF_per_mm_edge"]
                pad_area += poly.area
        n_via = len(b.vias_by_net[name])
        return {"C_track_pF": round(c_track, 2), "C_pads_pF": round(c_pad, 2), "C_vias_pF": round(n_via * VIA_C_PF, 2),
                "C_copper_pF": round(c_track + c_pad + n_via * VIA_C_PF, 2), "pad_area_mm2": round(pad_area, 2)}


def clusters(samples, board, net):
    """Group no-plane samples; say what the opening is (own via antipad, a drilled hole, or a real gap)."""
    if not samples:
        return []
    groups, cur = [], [samples[0]]
    for s in samples[1:]:
        if s[2] == cur[-1][2] and math.hypot(s[0] - cur[-1][0], s[1] - cur[-1][1]) < 0.35:
            cur.append(s)
        else:
            groups.append(cur); cur = [s]
    groups.append(cur)
    out = []
    holes = [(p["x"], p["y"], max(p["drill"]), p["ref"]) for ps in board.pads_by_net.values() for p in ps if p["drill"][0] > 0]
    for g in groups:
        cx, cy = sum(s[0] for s in g) / len(g), sum(s[1] for s in g) / len(g)
        length = math.hypot(g[-1][0] - g[0][0], g[-1][1] - g[0][1]) + 0.1
        why = "plane opening"
        dv = min((math.hypot(v["x"] - cx, v["y"] - cy) for v in board.vias_by_net[net]), default=9)
        if dv < 0.8:
            why = "own via antipad"
        else:
            dvo = min((math.hypot(v["x"] - cx, v["y"] - cy) for v in board.vias if v["net"] != "GND"), default=9)
            dh = min(((math.hypot(h[0] - cx, h[1] - cy) - h[2] / 2, h[3]) for h in holes), default=(9, ""))
            if dh[0] < 0.8:
                why = f"clearance of drilled hole {dh[1]}"
            elif dvo < 0.9:
                why = "antipad of a neighbouring via"
        out.append({"x": round(cx, 2), "y": round(cy, 2), "layer": g[0][2], "length_mm": round(length, 2), "cause": why})
    return out


def describe(board, caps, net, src, dst, pick=None, with_segments=False):
    r = board.route(net, src, dst, pick)
    if r is None:
        return {"net": net, "error": "no copper path"}
    seg = r.pop("segments")
    gaps = clusters(board.plane_gaps(seg), board, net)
    nb = board.neighbours(net)
    r.update({
        "net": net, "from": ".".join(src), "to": ".".join(dst),
        "net_total": board.net_stats(net),
        "cap": caps.net(net),
        "plane_openings": gaps,
        "plane_openings_not_own_via_mm": round(sum(g["length_mm"] for g in gaps if g["cause"] != "own via antipad"), 2),
        "neighbours": {k: v for k, v in list(nb.items())[:6] if k != "GND"},
        "near_buck": board.pads_near(seg, {"BUCK_SW", "BUCK_BST"}, reach=5.0),
        "near_buck_tracks": {k: v for k, v in nb.items() if k in ("BUCK_SW", "BUCK_BST", "VREG_LX")},
        "delay_ps": round(sum(math.hypot(b[0] - a[0], b[1] - a[1]) * caps.per_mm(w, "delay_ps_per_mm") for a, b, l, w in seg), 1),
    })
    if with_segments:
        r["segments"] = seg
    return r


def led_chains(board):
    """Each hop as (net at the receiver, source pad, DIN pad, series part at the source or None)."""
    din, dout, series = {}, {}, {}
    for f in board.raw["fps"]:
        if f["ref"].startswith("LED"):
            for p in f["pads"]:
                if p["num"] == "1":
                    din[p["net"]] = f["ref"]
                if p["num"] == "3":
                    dout[f["ref"]] = p["net"]
        elif f["ref"].startswith("R") and len(f["pads"]) == 2:
            a, b = f["pads"]
            for x, y in ((a, b), (b, a)):
                series.setdefault(x["net"], []).append((f["ref"], x["num"], y["num"], y["net"], f["value"]))
    chains = {}
    for name, start, drv in (("key", "KEY_RGB_5V", ("R110", "2")), ("underglow", "UNDERGLOW_5V", ("R111", "2"))):
        hops, n, src = [], start, drv
        while True:
            pre = None
            if n not in din:
                # a DOUT that reaches the next DIN through a series resistor (R115 on UG_LED_6)
                for ref, p_in, p_out, n2, value in series.get(n, []):
                    if n2 in din:
                        pre = {"ref": ref, "ohm": float(value.split()[0]), "net": n, "from": src, "to": (ref, p_in)}
                        src, n = (ref, p_out), n2
                        break
            if n not in din:
                break
            hops.append((n, src, (din[n], "1"), pre))
            src = (din[n], "3")
            n = dout[din[n]]
        chains[name] = hops
    return chains


def usb_pair(board, caps):
    """Walk the D+ route and measure the distance to D- copper at every 0.1 mm."""
    out = {}
    routes = {}
    for net, a, bpad in (("USB_DP_CONN", ("J1", "A6"), ("R102", "1")), ("USB_DM_CONN", ("J1", "A7"), ("R103", "1")),
                         ("USB_DP", ("R102", "2"), ("U1", "52")), ("USB_DM", ("R103", "2"), ("U1", "51"))):
        d = describe(board, caps, net, a, bpad, with_segments=True)
        routes[net] = d.pop("segments")
        out[net] = d
    for net, ref in (("USB_DP_CONN", "U10"), ("USB_DM_CONN", "U10")):
        num = "1" if net == "USB_DP_CONN" else "2"
        r = board.route(net, ("J1", "A6" if num == "1" else "A7"), (ref, num))
        out[net]["J1_to_U10_mm"] = r["length_mm"] if r else None
    dm = [(LineString([a, b]), layer, w) for a, b, layer, w in routes["USB_DM_CONN"]]
    samples, s = [], 0.0
    for a, b, layer, w in routes["USB_DP_CONN"]:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(round(L / 0.1)))
        for i in range(n):
            x = a[0] + (b[0] - a[0]) * (i + 0.5) / n
            y = a[1] + (b[1] - a[1]) * (i + 0.5) / n
            pt = Point(x, y)
            best = min(((g.distance(pt) - w / 2 - w2 / 2) for g, l2, w2 in dm if l2 == layer), default=None)
            samples.append((s + (i + 0.5) * L / n, x, y, layer, w, best))
        s += L
    # histogram of gap and list of uncoupled stretches (gap > 0.5 mm or other layer)
    hist = defaultdict(float)
    for _, _, _, layer, w, g in samples:
        key = "other layer" if g is None else ("<=0.16" if g <= 0.16 else "<=0.21" if g <= 0.21 else "<=0.26" if g <= 0.26 else "<=0.5" if g <= 0.5 else ">0.5")
        hist[f"{layer} w{w:.2f} gap {key}"] += 0.1
    stretches, cur = [], None
    for sm in samples:
        apart = sm[5] is None or sm[5] > 0.5
        if apart:
            if cur is None:
                cur = [sm, sm, sm[5] or 0.0]
            cur[1] = sm
            cur[2] = max(cur[2], sm[5] or 99.0)
        elif cur is not None:
            stretches.append(cur); cur = None
    if cur is not None:
        stretches.append(cur)
    out["pair"] = {
        "gap_histogram_mm": {k: round(v, 1) for k, v in sorted(hist.items())},
        "separated_stretches": [{"from_J1_mm": round(a[0], 1), "to_J1_mm": round(b[0], 1), "length_mm": round(b[0] - a[0] + 0.1, 1),
                                 "at": [round(a[1], 2), round(a[2], 2)], "layer": a[3],
                                 "max_gap_mm": None if g >= 99 else round(g, 2)} for a, b, g in stretches],
        "vias_DP": [[round(v["x"], 2), round(v["y"], 2)] for v in board.vias_by_net["USB_DP_CONN"]],
        "vias_DM": [[round(v["x"], 2), round(v["y"], 2)] for v in board.vias_by_net["USB_DM_CONN"]],
        "skew_mm": round(out["USB_DP_CONN"]["length_mm"] + out["USB_DP"]["length_mm"] - out["USB_DM_CONN"]["length_mm"] - out["USB_DM"]["length_mm"], 3),
        "skew_ps": round(out["USB_DP_CONN"]["delay_ps"] + out["USB_DP"]["delay_ps"] - out["USB_DM_CONN"]["delay_ps"] - out["USB_DM"]["delay_ps"], 1),
    }
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lines = line_table()
    (OUT / "lines.json").write_text(json.dumps(lines, indent=1))
    board = Board()
    caps = Caps(board, lines)
    g = {"source": "build/si/board.json", "led": {}, "nets": {}}

    # ---- LED chains ----
    for name, hops in led_chains(board).items():
        rows = []
        for net, src, dst, pre in hops:
            row = describe(board, caps, net, src, dst)
            if pre:
                row["series_at_source"] = {"ref": pre["ref"], "ohm": pre["ohm"],
                                           "source_side": describe(board, caps, pre["net"], pre["from"], pre["to"])}
            rows.append(row)
        g["led"][name] = rows
    # the two-site footprints: evaluate each fitted combination explicitly
    def site(ref, layer=None, near=None):
        def pick(p):
            if p["ref"] != ref:
                return True
            if layer is not None and layer not in p["layers"]:
                return False
            if near is not None and math.hypot(p["x"] - near[0], p["y"] - near[1]) > 1.5:
                return False
            return True
        return pick
    L30_WIN, L30_ALT, L75_TOP = (16.49, 42.22), (19.99, 38.22), (11.33, 52.38)
    variants = {}
    for label, p30, p75 in (
        ("default: LED30 window site, LED75 on B.Cu", site("LED30", near=L30_WIN), site("LED75", layer="B.Cu")),
        ("stepped Caps: LED30 alt site, LED75 on B.Cu", site("LED30", near=L30_ALT), site("LED75", layer="B.Cu")),
        ("LED75 on its F.Cu window pads, LED30 window site", site("LED30", near=L30_WIN), site("LED75", layer="F.Cu")),
        ("LED75 on its F.Cu window pads, LED30 alt site", site("LED30", near=L30_ALT), site("LED75", layer="F.Cu")),
    ):
        both = lambda p, a=p30, b=p75: a(p) and b(p)
        variants[label] = [
            describe(board, caps, "KEY_RGB_CHAIN_29", ("LED16", "3"), ("LED30", "1"), both),
            describe(board, caps, "KEY_RGB_CHAIN_30", ("LED30", "3"), ("LED75", "1"), both),
            describe(board, caps, "KEY_RGB_CHAIN_31", ("LED75", "3"), ("LED31", "1"), both),
        ]
    g["led"]["caps_variants"] = variants
    g["led"]["buffers"] = {
        "KEY_RGB": describe(board, caps, "KEY_RGB", ("U1", "32"), ("U5", "2")),
        "KEY_RGB_5V_BUF": describe(board, caps, "KEY_RGB_5V_BUF", ("U5", "4"), ("R110", "1")),
        "UNDERGLOW": describe(board, caps, "UNDERGLOW", ("U1", "33"), ("U6", "2")),
        "UNDERGLOW_5V_BUF": describe(board, caps, "UNDERGLOW_5V_BUF", ("U6", "4"), ("R111", "1")),
    }

    # ---- USB ----
    g["usb"] = usb_pair(board, caps)

    # ---- crystal, QSPI, SWD, RUN/BOOT ----
    simple = {
        "XIN": (("Y1", "1"), ("U1", "21")), "XTAL_OUT": (("Y1", "3"), ("R108", "1")), "XOUT": (("R108", "2"), ("U1", "22")),
        "QSPI_SCLK": (("U1", "56"), ("U3", "6")), "QSPI_SD0": (("U1", "57"), ("U3", "5")), "QSPI_SD1": (("U1", "59"), ("U3", "2")),
        "QSPI_SD2": (("U1", "58"), ("U3", "3")), "QSPI_SD3": (("U1", "55"), ("U3", "7")), "QSPI_SS": (("U1", "60"), ("U3", "1")),
        "BOOT_BUTTON": (("R106", "2"), ("SW100", "1")),
        "SWCLK": (("J2", "3"), ("U1", "24")), "SWDIO": (("J2", "1"), ("U1", "25")),
        "RUN": (("SW101", "1"), ("U1", "26")), "RESET_GND": (("SW101", "2"), ("R107", "1")),
        "LED_ENABLE": (("U1", "34"), ("U7", "3")), "LED_FAULT_N": (("U7", "4"), ("U1", "35")),
        "GPIO_ISOLATE": (("U12", "2"), ("U11", "19")),
    }
    for i, (gp, pin, a, bpin, jp) in enumerate((("3", "5", "2", "18", "2"), ("10", "14", "3", "17", "3"), ("24", "36", "4", "16", "5"),
                                               ("25", "37", "5", "15", "6"), ("26", "40", "6", "14", "8"), ("27", "41", "7", "13", "9"))):
        simple[f"MCU_GPIO{gp}"] = (("U1", pin), (f"R13{i}", "1"))
        simple[f"GPIO{gp}_ISO"] = ((f"R13{i}", "2"), ("U11", a))
        simple[f"EXT_GPIO{gp}"] = (("U11", bpin), ("J3", jp))
    for net, (a, b) in simple.items():
        g["nets"][net] = describe(board, caps, net, a, b)

    # ---- matrix ----
    rows = {f"ROW{i}": ("U1", n) for i, n in enumerate(("2", "3", "4", "43", "7"))}
    cols = {f"COL{i}": ("U1", n) for i, n in enumerate(("8", "9", "10", "12", "13", "42", "15", "16", "17", "18", "19", "27", "28", "29", "31"))}
    m = {}
    for net, mcu in {**rows, **cols}.items():
        st = board.net_stats(net)
        adj = board.graph(net)
        src = board.pad_nodes(adj, *mcu)[0]
        far = 0.0
        for n in adj:
            if n[0] == "pad" and n != src:
                p = board.shortest(adj, src, n)
                if p:
                    far = max(far, sum(e[2] for e in p))
        nb = board.neighbours(net)
        m[net] = {"length_mm": st["length_mm"], "by_layer_width": st["by_layer_width"], "vias": st["vias"],
                  "pads": len(st["pads"]), "farthest_pad_mm": round(far, 1), "cap": caps.net(net),
                  "neighbours": {k: v for k, v in list(nb.items())[:5] if k != "GND"},
                  "plane_openings_mm": round(sum(c["length_mm"] for c in clusters(board.plane_gaps(
                      [((t["x1"], t["y1"]), (t["x2"], t["y2"]), t["layer"], t["w"]) for t in board.by_net[net]]), board, net)
                      if c["cause"] != "own via antipad"), 1)}
    # switch-to-diode nets
    keys = [n for n in board.by_net if n.startswith("KEY_") and n[4:].isdigit()]
    kc = [caps.net(n)["C_copper_pF"] for n in keys]
    m["KEY_nets"] = {"count": len(keys), "C_copper_pF_min": min(kc), "C_copper_pF_max": max(kc), "C_copper_pF_mean": round(sum(kc) / len(kc), 2)}
    g["matrix"] = m

    # ---- buck proximity for every net of interest ----
    sw_tracks = [LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2) for t in board.by_net["BUCK_SW"]]
    sw_pads = [Polygon(p["poly"][0]) for p in board.pads_by_net["BUCK_SW"] if p["poly"]]
    from shapely.ops import unary_union
    sw = unary_union(sw_tracks + sw_pads)
    g["buck_switch_node"] = {"area_mm2": round(sw.area, 2), "bbox": [round(v, 2) for v in sw.bounds],
                             "layers": sorted({t["layer"] for t in board.by_net["BUCK_SW"]} | {l for p in board.pads_by_net["BUCK_SW"] for l in p["layers"] if l.endswith(".Cu")})}
    prox = {}
    for net, ts in board.by_net.items():
        if net in ("GND", "BUCK_SW", "BUCK_BST", "+4V_REG", "VBUS_PROTECTED_RAW", "") or not ts:
            continue
        d = min(LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).distance(sw) - t["w"] / 2 for t in ts)
        if d < 6.0:
            same = min((LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).distance(sw) - t["w"] / 2 for t in ts if t["layer"] == "B.Cu"), default=None)
            prox[net] = {"min_distance_mm_any_layer": round(d, 2), "min_distance_mm_B.Cu": None if same is None else round(same, 2)}
    g["buck_switch_node"]["nets_within_6mm"] = dict(sorted(prox.items(), key=lambda kv: kv[1]["min_distance_mm_any_layer"]))

    (OUT / "geometry.json").write_text(json.dumps(g, indent=1))
    print("wrote", OUT / "geometry.json")


if __name__ == "__main__":
    main()
