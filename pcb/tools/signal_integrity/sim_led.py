"""Addressable-LED data: per-hop waveform at the receiving DIN (ngspice transient).

Every SK6805 regenerates the data, so each LED-to-LED hop is simulated as its
own link, from the routed geometry (path pieces, vias, stubs in routed order).

Models
  line      : lossy LC ladder, <= 2 mm sections, L' and C' from the 2-D field
              solve (lines.json), DC copper resistance
  via       : 1.36 nH + 0.49 pF (formula, see extract_geometry.py)
  stub      : ladder branch at its routed position, open end + 0.15 pF pad
  receiver  : SK6805 DIN = capacitor CIN. The OPSCO sheet gives no input
              capacitance: ASSUMED 5 pF, stress case 15 pF
  driver    : SK6805 DOUT. The OPSCO SK6805-EC15-001 Rev A/1 sheet gives no
              output resistance or edge rate: ASSUMED and swept
                 fast   20 ohm,  2 ns edge
                 nom   100 ohm, 10 ns edge
                 weak  500 ohm, 30 ns edge
                 weak+ 1 kohm, 30 ns edge, CIN 15 pF  (the sheet itself suggests
                        up to ~500 ohm of extra series resistance per hop)
  first hop : RP2350 GPIO (3.3 V, 40 ohm, 1.5 ns: ASSUMED typical; the datasheet
              only bounds VOL/VOH) -> track -> SN74LV1T125 at 4.0 V (behavioural:
              threshold, delay, output resistance; values from the TI sheet where
              it has them) -> 330 ohm -> track -> LED DIN
Thresholds: VIH 0.78 VDD, VIL 0.35 VDD at VDD 4.0 V (OPSCO section 9).
Timing limits: T0H 0.20-0.40 us, T1H >= 0.70 us, T0L >= 0.70 us, T1L >= 0.20 us
(OPSCO section 10); firmware sends 300/900/900/300 ns (keyboards/maru60/rp2350/config.h).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fieldsolve as fs  # noqa: E402
import spice  # noqa: E402
from geom import Board  # noqa: E402

VDD = 4.0
VIH, VIL = 0.78 * VDD, 0.35 * VDD
T0H, T0L, T1H, T1L = 300e-9, 900e-9, 900e-9, 300e-9
LIMITS = {"T0H_min": 200e-9, "T0H_max": 400e-9, "T1H_min": 700e-9, "T0L_min": 700e-9, "T1L_min": 200e-9}
DRIVERS = {
    "fast": {"r": 20.0, "edge": 2e-9, "cin": 5e-12},
    "nom": {"r": 100.0, "edge": 10e-9, "cin": 5e-12},
    "weak": {"r": 500.0, "edge": 30e-9, "cin": 5e-12},
    "weak+": {"r": 1000.0, "edge": 30e-9, "cin": 15e-12},
}
BITS = "0101"  # one 0 and one 1 after a settled start, then repeated


def pwl(bits, v, edge, t0=100e-9):
    pts, t = [(0.0, 0.0)], t0
    for b in bits:
        hi, lo = (T0H, T0L) if b == "0" else (T1H, T1L)
        pts += [(t, 0.0), (t + edge, v), (t + hi, v), (t + hi + edge, 0.0)]
        t += hi + lo
    return " ".join(f"{a * 1e9:.4f}n {b:.4g}" for a, b in pts), t


def add_route(deck, route, a, b, table, stub_w=0.2):
    """Path pieces, vias and stubs between nodes a and b in routed order."""
    stubs = sorted((s for s in route["stubs"] if s["length_mm"] > 0.3), key=lambda s: s["from_src_mm"])
    node, pos, si = a, 0.0, 0

    def stub(at_node, s):
        end = deck.uid("stubend")
        deck.ladder(at_node, end, s["length_mm"], stub_w, table, tag="s")
        for _ in range(s["vias"]):
            deck.add(f"Cs{deck.uid('')} {end} 0 {table['via_C_pF']:.4g}p")
        deck.add(f"Cs{deck.uid('')} {end} 0 0.15p")

    els = route["elements"]
    for i, e in enumerate(els):
        last = i == len(els) - 1
        if e[0] == "via":
            nxt = b if last else deck.uid("v")
            deck.via(node, nxt, table)
            node = nxt
            continue
        _, layer, w, length = e
        end_pos = pos + length
        while si < len(stubs) and stubs[si]["from_src_mm"] <= end_pos + 1e-6:
            cut = max(stubs[si]["from_src_mm"] - pos, 0.0)
            if cut > 1e-3:
                mid = deck.uid("p")
                deck.ladder(node, mid, cut, w, table)
                node, pos, length = mid, pos + cut, length - cut
            stub(node, stubs[si])
            si += 1
        nxt = b if last else deck.uid("p")
        deck.ladder(node, nxt, max(length, 0.0), w, table)
        node, pos = nxt, end_pos
    if node != b:
        deck.add(f"R{deck.uid('j')} {node} {b} 1m")
    while si < len(stubs):
        stub(b, stubs[si]); si += 1


def measure(t, v, t_bits, edge):
    """Widths of the '0' and '1' pulses of the second bit pair (settled), edges, levels."""
    period = T0H + T0L
    t0 = t_bits + 2 * period            # third bit: '0'; fourth: '1'
    res = {}
    for name, start, hi in (("0", t0, T0H), ("1", t0 + period, T1H)):
        win = (t >= start - 50e-9) & (t <= start + period - 60e-9)
        tw, vw = t[win], v[win]
        r_ih = spice.crossings(tw, vw, VIH, True)
        r_il = spice.crossings(tw, vw, VIL, True)
        f_ih = spice.crossings(tw, vw, VIH, False)
        f_il = spice.crossings(tw, vw, VIL, False)
        ok = r_ih and r_il and f_ih and f_il
        if not ok:
            res[name] = {"error": "threshold not crossed"}
            continue
        # receiver may switch as late as VIH on the way up and as early as VIH on the way down (shortest),
        # or as early as VIL on the way up and as late as VIL on the way down (longest)
        w_min = f_ih[-1] - r_ih[0]
        w_max = f_il[-1] - r_il[0]
        # ring-back: after the first peak the level must stay above VIH; after the first trough below VIL
        top = (tw >= r_ih[0]) & (tw <= f_ih[-1])
        t_peak = tw[top][np.argmax(vw[top])]
        high_min = float(vw[(tw >= t_peak) & (tw <= start + hi - 1e-9)].min()) if start + hi - 1e-9 > t_peak else float(vw[top].max())
        bot = tw >= f_il[-1]
        t_trough = tw[bot][np.argmin(vw[bot])]
        low_max = float(vw[tw >= t_trough].max())
        res[name] = {
            "sent_ns": hi * 1e9, "width_min_ns": round(w_min * 1e9, 2), "width_max_ns": round(w_max * 1e9, 2),
            "extra_threshold_crossings": (len(r_ih) - 1) + (len(f_ih) - 1) + (len(r_il) - 1) + (len(f_il) - 1),
            "delay_rise_ns": round((r_ih[0] - start) * 1e9, 2), "delay_fall_ns": round((f_il[-1] - start - hi) * 1e9, 2),
            "high_min_after_peak_V": round(high_min, 3), "low_max_after_trough_V": round(low_max, 3),
        }
    win = (t >= t0 - 50e-9)
    def first_edge(rising, after):
        a = [x for x in spice.crossings(t, v, (0.1 if rising else 0.9) * VDD, rising) if x >= after]
        b = [x for x in spice.crossings(t, v, (0.9 if rising else 0.1) * VDD, rising) if a and x >= a[0]]
        return round((b[0] - a[0]) * 1e9, 2) if b else None
    res["rise_10_90_ns"] = first_edge(True, t0 - 50e-9)
    res["fall_90_10_ns"] = first_edge(False, t0 + T0H - 5e-9)
    res["overshoot_V"] = round(float(v[win].max() - VDD), 3)
    res["undershoot_V"] = round(float(-v[win].min()), 3)
    if "error" not in res["0"] and "error" not in res["1"]:
        z, o = res["0"], res["1"]
        res["noise_margin_high_V"] = round(min(z["high_min_after_peak_V"], o["high_min_after_peak_V"]) - VIH, 3)
        res["noise_margin_low_V"] = round(VIL - max(z["low_max_after_trough_V"], o["low_max_after_trough_V"]), 3)
        res["budget_ns"] = {
            "T0H_above_min": round(z["width_min_ns"] - LIMITS["T0H_min"] * 1e9, 1),
            "T0H_below_max": round(LIMITS["T0H_max"] * 1e9 - z["width_max_ns"], 1),
            "T1H_above_min": round(o["width_min_ns"] - LIMITS["T1H_min"] * 1e9, 1),
            "T0L_above_min": round((T0H + T0L) * 1e9 - z["width_max_ns"] - LIMITS["T0L_min"] * 1e9, 1),
            "T1L_above_min": round((T1H + T1L) * 1e9 - o["width_max_ns"] - LIMITS["T1L_min"] * 1e9, 1),
        }
        res["pulse_width_error_ns"] = [round(min(z["width_min_ns"] - 300, o["width_min_ns"] - 900), 2),
                                       round(max(z["width_max_ns"] - 300, o["width_max_ns"] - 900), 2)]
    return res


def sim_hop(name, route, table, drv):
    d = spice.Deck(f"{name}: SK6805 DOUT (assumed {drv['r']:.0f} ohm, {drv['edge'] * 1e9:.0f} ns) -> routed hop -> DIN {drv['cin'] * 1e12:.0f} pF")
    wave, tend = pwl(BITS, VDD, drv["edge"])
    d.add(f"Vsrc src 0 PWL({wave})", f"Rdrv src dout {drv['r']}", "Cdout dout 0 2p")
    add_route(d, route, "dout", "din", table)
    d.add(f"Cin din 0 {drv['cin'] * 1e12:.3g}p")
    r = d.run(name, ["v(dout)", "v(din)"], tran=f"0.1n {tend * 1e9 + 100:.0f}n 0 0.2n")
    m = measure(r["time"], r["v(din)"], 100e-9, drv["edge"])
    return m, r


def sim_first_hop(name, board, table, mcu_net, mcu_pads, buf_net, buf_pads, led_net, led_pads, case):
    d = spice.Deck(f"{name}: RP2350 GPIO -> SN74LV1T125 at 4.0 V -> 330R -> first LED ({case['label']})")
    wave, tend = pwl(BITS, 3.3, 1.5e-9)
    d.add(f"Vsrc src 0 PWL({wave})", f"Rgpio src gpio {case['r_gpio']}", "Cgpio gpio 0 3p")
    add_route(d, board.route(mcu_net, *mcu_pads), "gpio", "bufin", table)
    d.add(f"Cbufin bufin 0 {case['c_buf_in']}p")
    # behavioural buffer: threshold -> delay -> edge shaping -> output resistance
    d.add(f"Bthr thr 0 V={VDD}/(1+exp(-(v(bufin)-{case['vth']})/0.03))",
          "Rthr thr dly_in 50", f"Tdly dly_in 0 dly_out 0 Z0=50 TD={case['tpd']}n", "Rdly dly_out 0 50",
          "Eshp shp 0 dly_out 0 2", f"Rshp shp shpc 1k", f"Cshp shpc 0 {case['t_out'] / 2.2:.4g}p",
          "Ebuf bufi 0 shpc 0 1", f"Rbuf bufi bufout {case['r_buf']}", "Cbufout bufout 0 2.5p")
    add_route(d, board.route(buf_net, *buf_pads), "bufout", "rin", table)
    d.add("R110 rin rout 330", "Crpad rout 0 0.1p")
    add_route(d, board.route(led_net, *led_pads), "rout", "din", table)
    d.add(f"Cin din 0 {case['cin']}p")
    r = d.run(name, ["v(gpio)", "v(bufin)", "v(bufout)", "v(din)"], tran=f"0.1n {tend * 1e9 + 100:.0f}n 0 0.2n")
    m = measure(r["time"], r["v(din)"], 100e-9, 1.5e-9)
    # buffer input margin against the TI limits interpolated to 4.0 V
    m["buffer_input_high_V"] = round(float(r["v(bufin)"][(r["time"] > 250e-9) & (r["time"] < 380e-9)].min()), 3)
    return m, r


def sim_crosstalk(name, table, victim_len, coupled_len, gap, w_v, w_a, drv_r, level):
    """Aggressor (3.3 V matrix line, 1 ns edges) beside a quiet LED hop held at `level` by DOUT."""
    cp = fs.coupled(w_v, w_a, gap)
    d = spice.Deck(f"{name}: matrix line beside a quiet LED data hop, {coupled_len:.0f} mm at {gap} mm gap")
    d.add(f"Vq q 0 {level}", f"Rq q v0 {drv_r}",
          "Vagg a 0 PWL(0 0 20n 0 21n 3.3 120n 3.3 121n 0)", "Ragg a a0 40")
    pre = (victim_len - coupled_len) / 2
    d.ladder("v0", "v1", pre, w_v, table)
    d.coupled_ladder("v1", "v2", "a0", "a1", coupled_len, cp, max_section_mm=1.0)
    d.ladder("v2", "din", pre, w_v, table)
    d.add("Cin din 0 5p", "Cagg a1 0 30p")
    d.add(".options method=gear reltol=1e-3")
    r = d.run(name, ["v(din)", "v(a1)", "v(v1)"], tran="0.05n 220n 0 0.1n")
    v = r["v(din)"] - level
    return {"coupled": cp, "peak_pos_V": round(float(v.max()), 4), "peak_neg_V": round(float(v.min()), 4)}, r


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    spice.QA.mkdir(parents=True, exist_ok=True)
    table = spice.lines()
    geo = spice.geometry()
    board = Board()
    out = {"thresholds": {"VDD": VDD, "VIH": VIH, "VIL": VIL}, "limits_ns": {k: v * 1e9 for k, v in LIMITS.items()},
           "driver_cases_assumed": DRIVERS, "hops": {}, "first_hop": {}, "crosstalk": {}}

    def site(ref, layer=None, near=None):
        def pick(p):
            if p["ref"] != ref:
                return True
            if layer is not None and layer not in p["layers"]:
                return False
            return near is None or math.hypot(p["x"] - near[0], p["y"] - near[1]) <= 1.5
        return pick

    win, alt = (16.49, 42.22), (19.99, 38.22)
    both = lambda a, b: (lambda p: a(p) and b(p))
    hops = {
        "UG_LED_6 (longest: 276 mm, 8 vias)": ("UG_LED_6", ("LED68", "3"), ("LED69", "1"), None),
        "UNDERGLOW hop UG_LED_9 (105 mm)": ("UG_LED_9", ("LED71", "3"), ("LED72", "1"), None),
        "KEY_RGB_CHAIN_60 (longest key hop: 81 mm, 4 vias)": ("KEY_RGB_CHAIN_60", ("LED58", "3"), ("LED59", "1"), None),
        "KEY_RGB_CHAIN_52 (64 mm, 8 vias)": ("KEY_RGB_CHAIN_52", ("LED48", "3"), ("LED47", "1"), None),
        "KEY_RGB_CHAIN_29 default (stub to LED30 alt site)": ("KEY_RGB_CHAIN_29", ("LED16", "3"), ("LED30", "1"), both(site("LED30", near=win), site("LED75", layer="B.Cu"))),
        "KEY_RGB_CHAIN_29 stepped (LED30 on alt site)": ("KEY_RGB_CHAIN_29", ("LED16", "3"), ("LED30", "1"), both(site("LED30", near=alt), site("LED75", layer="B.Cu"))),
        "KEY_RGB_CHAIN_30 default (LED30 window, LED75 bottom)": ("KEY_RGB_CHAIN_30", ("LED30", "3"), ("LED75", "1"), both(site("LED30", near=win), site("LED75", layer="B.Cu"))),
        "KEY_RGB_CHAIN_30 stepped (LED30 alt, LED75 bottom)": ("KEY_RGB_CHAIN_30", ("LED30", "3"), ("LED75", "1"), both(site("LED30", near=alt), site("LED75", layer="B.Cu"))),
        "KEY_RGB_CHAIN_30 LED75 on top pads (stub with via)": ("KEY_RGB_CHAIN_30", ("LED30", "3"), ("LED75", "1"), both(site("LED30", near=alt), site("LED75", layer="F.Cu"))),
        "KEY_RGB_CHAIN_31 default (LED75 bottom)": ("KEY_RGB_CHAIN_31", ("LED75", "3"), ("LED31", "1"), site("LED75", layer="B.Cu")),
        "KEY_RGB_CHAIN_31 LED75 on top pads (stub with via)": ("KEY_RGB_CHAIN_31", ("LED75", "3"), ("LED31", "1"), site("LED75", layer="F.Cu")),
        "KEY_RGB_CHAIN_3 (typical 18.8 mm hop)": ("KEY_RGB_CHAIN_3", ("LED3", "3"), ("LED4", "1"), None),
    }
    waves = {}
    for i, (label, (net, a, b, pick)) in enumerate(hops.items()):
        route = board.route(net, a, b, pick)
        entry = {"net": net, "length_mm": route["length_mm"], "vias": route["vias"],
                 "stubs_mm": [s["length_mm"] for s in route["stubs"] if s["length_mm"] > 0.3], "cases": {}}
        for dn, drv in DRIVERS.items():
            m, r = sim_hop(f"led_hop{i:02d}_{dn.replace('+', 'p')}", route, table, drv)
            entry["cases"][dn] = m
            waves[(label, dn)] = r
        out["hops"][label] = entry
        print(label, {k: (v.get("pulse_width_error_ns"), v.get("overshoot_V"), v.get("rise_10_90_ns"), v.get("noise_margin_high_V"), v.get("noise_margin_low_V")) for k, v in entry["cases"].items()})

    # ---- how strong/fast may DOUT be on the long underglow hops before ring-back eats the margin ----
    sweep = {}
    for label, (net, a, b) in {"UG_LED_6 276 mm": ("UG_LED_6", ("LED68", "3"), ("LED69", "1")),
                               "UG_LED_9 105 mm": ("UG_LED_9", ("LED71", "3"), ("LED72", "1")),
                               "KEY_RGB_CHAIN_60 81 mm": ("KEY_RGB_CHAIN_60", ("LED58", "3"), ("LED59", "1"))}.items():
        route = board.route(net, a, b)
        rows = []
        for rr in (10.0, 20.0, 35.0, 50.0, 75.0, 100.0):
            for ee in (1e-9, 2e-9, 4e-9, 6e-9, 10e-9):
                m, _ = sim_hop("led_sweep", route, table, {"r": rr, "edge": ee, "cin": 5e-12})
                rows.append({"r_ohm": rr, "edge_ns": ee * 1e9, "NM_high_V": m.get("noise_margin_high_V"), "NM_low_V": m.get("noise_margin_low_V"),
                             "overshoot_V": m["overshoot_V"], "undershoot_V": m["undershoot_V"]})
        sweep[label] = rows
    out["dout_strength_sweep"] = sweep

    # ---- first hops ----
    cases = {
        "typical": {"label": "typical", "r_gpio": 40, "c_buf_in": 2, "vth": 1.3, "tpd": 3.5, "t_out": 1.5, "r_buf": 25, "cin": 5},
        "slow corner": {"label": "slow corner", "r_gpio": 125, "c_buf_in": 10, "vth": 1.75, "tpd": 6.5, "t_out": 3.0, "r_buf": 100, "cin": 15},
        "low threshold": {"label": "low threshold", "r_gpio": 40, "c_buf_in": 2, "vth": 0.8, "tpd": 2.5, "t_out": 1.0, "r_buf": 15, "cin": 5},
    }
    for chain, args in (("key", ("KEY_RGB", (("U1", "32"), ("U5", "2")), "KEY_RGB_5V_BUF", (("U5", "4"), ("R110", "1")), "KEY_RGB_5V", (("R110", "2"), ("LED1", "1")))),
                        ("underglow", ("UNDERGLOW", (("U1", "33"), ("U6", "2")), "UNDERGLOW_5V_BUF", (("U6", "4"), ("R111", "1")), "UNDERGLOW_5V", (("R111", "2"), ("LED63", "1"))))):
        out["first_hop"][chain] = {}
        for cn, case in cases.items():
            m, r = sim_first_hop(f"led_first_{chain}_{cn.replace(' ', '_')}", board, table, *args, case)
            out["first_hop"][chain][cn] = m
            waves[("first " + chain, cn)] = r
        print("first hop", chain, {k: (v.get("pulse_width_error_ns"), v.get("rise_10_90_ns"), v.get("overshoot_V")) for k, v in out["first_hop"][chain].items()})

    # ---- crosstalk ----
    xt = {}
    for label, args in {
        "UG_LED_6 beside COL10: 49 mm at 0.25 mm (routed)": (276.0, 49.0, 0.25, 0.2, 0.2),
        "UG_LED_3 beside COL13: 32 mm at 0.20 mm (routed)": (60.2, 31.8, 0.20, 0.2, 0.2),
        "bound: 80 mm at 0.15 mm (minimum clearance, longer than any routed pair)": (276.0, 80.0, 0.15, 0.2, 0.2),
    }.items():
        xt[label] = {}
        for state, level, rdrv in (("victim low, weak driver 500R", 0.0, 500.0), ("victim high, weak driver 500R", VDD, 500.0),
                                   ("victim low, driver 1k", 0.0, 1000.0)):
            m, r = sim_crosstalk(f"led_xtalk_{len(xt)}_{state.split(',')[0].replace(' ', '_')}_{int(rdrv)}", table, *args, rdrv, level)
            xt[label][state] = {k: v for k, v in m.items() if k != "coupled"} | {"kC": round(m["coupled"]["kC"], 4), "kL": round(m["coupled"]["kL"], 4)}
            waves[("xt " + label, state)] = r
    out["crosstalk"]["matrix_to_led"] = xt
    out["crosstalk"]["noise_margin_V"] = {"low": VIL, "high": VDD - VIH}
    # buck switch node: capacitive coupling over the plane, from the field solve
    buck = {}
    for net, dist, clen in (("UG_LED_10", geo["buck_switch_node"]["nets_within_6mm"]["UG_LED_10"]["min_distance_mm_B.Cu"], 6.0),
                            ("RUN", geo["buck_switch_node"]["nets_within_6mm"]["RUN"]["min_distance_mm_B.Cu"], 6.0)):
        cp = fs.coupled(0.2 if net != "RUN" else 0.15, 2.4, dist)
        cm = cp["Cm_pF_per_mm"] * clen
        cv = 6.0 if net != "RUN" else geo["nets"]["RUN"]["cap"]["C_copper_pF"]
        buck[net] = {"distance_mm": dist, "coupled_length_assumed_mm": clen, "Cm_fF": round(cm * 1e3, 3),
                     "victim_C_pF": cv, "step_if_victim_floating_mV": round(5.0 * cm / (cm + cv) * 1e3, 3)}
    out["crosstalk"]["buck_switch_node"] = buck
    print(json.dumps(out["crosstalk"], indent=1))

    (spice.OUT / "led.json").write_text(json.dumps(out, indent=1))

    # ---- plots ----
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.6), facecolor="#fcfcfb")
    panels = ["UG_LED_6 (longest: 276 mm, 8 vias)", "KEY_RGB_CHAIN_60 (longest key hop: 81 mm, 4 vias)",
              "KEY_RGB_CHAIN_30 default (LED30 window, LED75 bottom)", "KEY_RGB_CHAIN_30 LED75 on top pads (stub with via)"]
    t0 = 100e-9 + 2 * (T0H + T0L)
    for ax, label in zip(axes.ravel(), panels):
        for (dn, col) in zip(DRIVERS, spice.SERIES):
            r = waves[(label, dn)]
            ax.plot((r["time"] - t0) * 1e9, r["v(din)"], color=col, linewidth=1.6,
                    label=f"{dn}: {DRIVERS[dn]['r']:.0f} Ω, {DRIVERS[dn]['edge'] * 1e9:.0f} ns")
        ax.axhline(VIH, color=spice.INK2, linewidth=0.8, linestyle="--")
        ax.axhline(VIL, color=spice.INK2, linewidth=0.8, linestyle="--")
        ax.text(1150, VIH + 0.08, "VIH 3.12 V", fontsize=7.5, color=spice.INK2, ha="right")
        ax.text(1150, VIL + 0.08, "VIL 1.40 V", fontsize=7.5, color=spice.INK2, ha="right")
        ax.set_xlim(-60, 1540)
        spice.style(ax, label, "time from the start of a '0' bit, ns", "V at DIN")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=8, frameon=False, loc="upper right", ncol=4, bbox_to_anchor=(0.995, 0.955), title="assumed SK6805 DOUT (not in the datasheet)", title_fontsize=8)
    fig.suptitle("SK6805 data hops, simulated at the receiving DIN ('0' then '1', 300/900 ns sent). No hardware measurement.",
                 fontsize=10, color="#0b0b0b", x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(spice.QA / "led-hops.png", dpi=140)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), facecolor="#fcfcfb")
    for ax, chain in zip(axes, ("key", "underglow")):
        r = waves[("first " + chain, "typical")]
        for vec, lab, col in (("v(gpio)", "RP2350 GPIO (3.3 V)", spice.SERIES[0]), ("v(bufout)", "LV1T125 output", spice.SERIES[1]),
                              ("v(din)", "first LED DIN, typical", spice.SERIES[2])):
            ax.plot((r["time"] - t0) * 1e9, r[vec], color=col, linewidth=1.6, label=lab)
        r2 = waves[("first " + chain, "slow corner")]
        ax.plot((r2["time"] - t0) * 1e9, r2["v(din)"], color=spice.SERIES[3], linewidth=1.6, label="first LED DIN, slow corner")
        ax.axhline(VIH, color=spice.INK2, linewidth=0.8, linestyle="--")
        ax.axhline(VIL, color=spice.INK2, linewidth=0.8, linestyle="--")
        ax.set_xlim(-20, 420)
        spice.style(ax, f"First hop, {chain} chain: '0' bit (300 ns) through U{'5' if chain == 'key' else '6'} and 330 Ω", "time, ns", "V")
    axes[0].legend(fontsize=7.5, frameon=False, loc="center right")
    fig.tight_layout()
    fig.savefig(spice.QA / "led-first-hop.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 3.6), facecolor="#fcfcfb")
    for (label, col) in zip(xt, spice.SERIES):
        r = waves[("xt " + label, "victim low, weak driver 500R")]
        ax.plot(r["time"] * 1e9, r["v(din)"] * 1e3, color=col, linewidth=1.6, label=label)
    spice.style(ax, "Noise coupled into a quiet LED data hop by a 3.3 V, 1 ns matrix edge (victim low, 500 Ω driver)", "time, ns", "mV at DIN")
    ax.legend(fontsize=7.5, frameon=False, loc="upper right")
    ax.text(0.01, 0.04, "noise margin: 1400 mV (low), 880 mV (high)", transform=ax.transAxes, fontsize=8, color=spice.INK2)
    fig.tight_layout()
    fig.savefig(spice.QA / "led-crosstalk.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
