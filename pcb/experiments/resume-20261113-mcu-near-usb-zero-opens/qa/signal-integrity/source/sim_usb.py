"""USB 2.0 full speed (12 Mbit/s) on the routed D+/D- pair (ngspice transient).

Limits checked, all read from the USB 2.0 specification (usb_20.pdf, 27 April 2000,
in usb_20_20240604.zip from usb.org):
  Table 7-7  VCRS 1.3-2.0 V, VOH 2.8-3.6 V, VOL 0-0.3 V, VDI >= 0.2 V, VCM 0.8-2.5 V
  Table 7-9  TFR, TFF 4-20 ns (Figure 7-8/7-9, CL = 50 pF), TFRFM 90-111.11 %,
             ZDRV 28-44 ohm, TDJ1 +-3.5 ns, TDJ2 +-4 ns, TJR1 +-18.5 ns, TJR2 +-9 ns
  7.1.16     1 ns from the upstream connector to the transceiver of a device,
             26 ns cable, 30 ns total one way

Models
  board pair  : coupled LC ladder (<= 3 mm sections) with the odd/even parameters
                from the 2-D field solve for the routed width/gap; the 0.15 mm
                break-outs are uncoupled ladders; 4 vias per line; U10 0.7 pF
                (TPD2EUSB30 CIO-GND typ), connector pads from geometry
  device PHY  : RP2350. The datasheet gives VOH >= 2.8 V, VOL <= 0.3 V, the pull-up
                values and "external 27 ohm series resistors"; it gives no output
                resistance or edge rate. ASSUMED: 3.3 V swing, 9 ohm source
                (36 ohm with the 27 ohm part), ramp 4 / 8 / 16 ns
  cable       : 1 m, two 45 ohm lines (90 ohm differential), 5.2 ns/m (the maximum
                the spec allows: 26 ns / 5 m), as a 50-section LC ladder
  host        : 3.3 V, 36 ohm per line, 15 kohm pull-downs, 20 pF (ASSUMED; the
                spec allows up to 150 pF on a downstream port)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fieldsolve as fs  # noqa: E402
import spice  # noqa: E402
from geom import Board  # noqa: E402

UI = 1e9 / 12e6  # ns
SPEC = {"VCRS": (1.3, 2.0), "TFR_ns": (4, 20), "TFF_ns": (4, 20), "TFRFM_pct": (90, 111.11), "ZDRV_ohm": (28, 44),
        "TDJ1_ns": 3.5, "TDJ2_ns": 4.0, "TJR1_ns": 18.5, "TJR2_ns": 9.0, "VDI_V": 0.2, "VCM_V": (0.8, 2.5),
        "device_trace_delay_ns": 1.0}
# NRZI line states (1 = J: D+ high for full speed). SYNC-like alternation, then runs up to 7 bit times.
STATES = [1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0,
          0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1]


def pwl(states, hi, edge_ns, invert=False, rise_ns=None, fall_ns=None):
    rise_ns = rise_ns or edge_ns
    fall_ns = fall_ns or edge_ns
    pts = []
    cur = states[0] ^ invert
    pts.append((0.0, hi if cur else 0.0))
    for i, s in enumerate(states[1:], start=1):
        s ^= invert
        if s != cur:
            t = i * UI
            e = rise_ns if s else fall_ns
            # edges are centred on the bit boundary so that rise and fall cross at mid swing
            pts += [(t - e / 2, hi if cur else 0.0), (t + e / 2, hi if s else 0.0)]
            cur = s
    return " ".join(f"{a:.4f}n {b:.4g}" for a, b in pts)


def board_pair(d, board, table, dp_conn, dm_conn, dp_r, dm_r, pair_par):
    """Connector-side nodes (dp_conn, dm_conn) to the 27R pads (dp_r, dm_r), from the routed element lists."""
    rdp = board.route("USB_DP_CONN", ("J1", "A6"), ("R102", "1"))
    rdm = board.route("USB_DM_CONN", ("J1", "A7"), ("R103", "1"))

    def groups(route):
        """Split the element list into [break-out, coupled, break-out, coupled, ...] by width."""
        g, cur = [], None
        for e in route["elements"]:
            kind = "c" if (e[0] == "track" and e[2] >= 0.24) else "u"
            if cur is None or cur[0] != kind:
                cur = [kind, []]
                g.append(cur)
            cur[1].append(e)
        return g

    gp, gm = groups(rdp), groups(rdm)
    assert [x[0] for x in gp] == [x[0] for x in gm], "D+ and D- do not have the same break-out/coupled sequence"
    np_, nm = dp_conn, dm_conn
    info = []
    for i, (a, b) in enumerate(zip(gp, gm)):
        last = i == len(gp) - 1
        ep = dp_r if last else d.uid("dp")
        em = dm_r if last else d.uid("dm")
        if a[0] == "c":
            lp = sum(e[3] for e in a[1])
            lm = sum(e[3] for e in b[1])
            common = min(lp, lm)
            xp, xm = d.uid("dpx"), d.uid("dmx")
            d.coupled_ladder(np_, xp, nm, xm, common, pair_par, max_section_mm=3.0, tag=f"p{i}")
            d.ladder(xp, ep, lp - common, 0.25, table)   # length difference, uncoupled
            d.ladder(xm, em, lm - common, 0.25, table)
            info.append({"coupled_mm": round(common, 2), "extra_dp_mm": round(lp - common, 2), "extra_dm_mm": round(lm - common, 2)})
        else:
            for node, end, els in ((np_, ep, a[1]), (nm, em, b[1])):
                cur = node
                for j, e in enumerate(els):
                    nxt = end if j == len(els) - 1 else d.uid("u")
                    if e[0] == "via":
                        d.via(cur, nxt, table)
                    else:
                        d.ladder(cur, nxt, e[3], e[2], table)
                    cur = nxt
            info.append({"breakout_dp_mm": round(sum(e[3] for e in a[1] if e[0] == "track"), 2),
                         "breakout_dm_mm": round(sum(e[3] for e in b[1] if e[0] == "track"), 2),
                         "vias_dp": sum(1 for e in a[1] if e[0] == "via"), "vias_dm": sum(1 for e in b[1] if e[0] == "via")})
        np_, nm = ep, em
    # U10 and the second connector contacts hang on short stubs at the connector end
    d.add(f"Cu10p {dp_conn} 0 0.7p", f"Cu10m {dm_conn} 0 0.7p")
    for node, route in ((dp_conn, rdp), (dm_conn, rdm)):
        for s in route["stubs"]:
            if s["length_mm"] > 0.3:
                end = d.uid("st")
                d.ladder(node, end, s["length_mm"], 0.15, table, tag="st")
                d.add(f"Cst{d.uid('')} {end} 0 0.3p")
    return info


def phy_pair(d, board, table, max_section_mm=2.0):
    """RP2350 pins to the 27R pads, including the actual routed vias."""
    routes = (
        ("pinp", "rp_a", board.route("USB_DP", ("U1", "52"), ("R102", "2"))),
        ("pinm", "rm_a", board.route("USB_DM", ("U1", "51"), ("R103", "2"))),
    )
    for source, end, route in routes:
        if route is None:
            raise ValueError(f"No routed PHY path from {source} to {end}")
        cur = source
        for i, e in enumerate(route["elements"]):
            nxt = end if i == len(route["elements"]) - 1 else d.uid("phy")
            if e[0] == "via":
                d.via(cur, nxt, table)
            else:
                d.ladder(cur, nxt, e[3], e[2], table, max_section_mm=max_section_mm)
            cur = nxt
        if not route["elements"]:
            d.ladder(cur, end, 0, 0.15, table)


def build(board, table, pair_par, direction, edge_ns, cable=True, test_load=False, rise_ns=None, fall_ns=None, host_c=20.0):
    d = spice.Deck(f"USB full speed, {direction}, source ramp {edge_ns} ns, cable {'1 m' if cable else 'none'}")
    dev_tx = direction == "device_tx"
    # device PHY side
    if dev_tx:
        d.add(f"Vdp sp 0 PWL({pwl(STATES, 3.3, edge_ns, False, rise_ns, fall_ns)})",
              f"Vdm sm 0 PWL({pwl(STATES, 3.3, edge_ns, True, rise_ns, fall_ns)})",
              "Rphyp sp pinp 9", "Rphym sm pinm 9")
    else:
        d.add("Rrxp pinp 0 10meg", "Rrxm pinm 0 10meg")
    d.add("Cpinp pinp 0 5p", "Cpinm pinm 0 5p", "Vpu vpu 0 3.3", "Rpu vpu pinp 1.5k")
    phy_pair(d, board, table)
    d.add("R102 rp_a rp_b 27", "R103 rm_a rm_b 27")
    info = board_pair(d, board, table, "conp", "conm", "rp_b", "rm_b", pair_par)
    d.add("Cconp conp 0 0.6p", "Cconm conm 0 0.6p")
    if test_load:
        d.add("Clp conp 0 50p", "Clm conm 0 50p", "Rlp conp 0 15k", "Rlm conm 0 15k")
        hp, hm = "conp", "conm"
    else:
        if cable:
            # 1 m of cable as 50 sections of 20 mm (104 ps each): L' = Z0*td, C' = td/Z0, 0.23 ohm/m (28 AWG)
            for line, a, b in (("p", "conp", "hp"), ("m", "conm", "hm")):
                prev = a
                for k in range(50):
                    mid, nxt = d.uid("cb"), (b if k == 49 else d.uid("cb"))
                    d.add(f"Rcb{line}{k} {prev} {mid} 4.6m", f"Lcb{line}{k} {mid} {nxt} {45 * 5.2e-9 / 50 * 1e9:.5g}n",
                          f"Ccb{line}{k} {nxt} 0 {5.2e-9 / 45 / 50 * 1e12:.5g}p")
                    prev = nxt
        else:
            d.add("Rcp conp hp 1m", "Rcm conm hm 1m")
        hp, hm = "hp", "hm"
        d.add(f"Chp hp 0 {host_c}p", f"Chm hm 0 {host_c}p", "Rhp hp 0 15k", "Rhm hm 0 15k")
        if not dev_tx:
            d.add(f"Vhp shp 0 PWL({pwl(STATES, 3.3, edge_ns, False, rise_ns, fall_ns)})",
                  f"Vhm shm 0 PWL({pwl(STATES, 3.3, edge_ns, True, rise_ns, fall_ns)})",
                  "Rhdp shp hp 36", "Rhdm shm hm 36")
    d.add(".options method=gear reltol=2e-3")
    return d, hp, hm, info


def sim_delay(board, table, pair_par):
    """One differential edge launched at the J1 pads from a matched source; time to the RP2350 pins.

    The pins are terminated (no pin capacitance, no pull-up) so that the number is the
    propagation delay of the board alone: connector pads, U10, vias, tracks, 27 ohm parts.
    """
    d = spice.Deck("USB: propagation delay from the J1 pads to the RP2350 pins (one differential edge, matched ends)")
    d.add("Vp sp 0 PWL(0 0 2n 0 3n 3.3)", "Vm sm 0 PWL(0 3.3 2n 3.3 3n 0)", "Rsp sp conp 45", "Rsm sm conm 45",
          "Rtp pinp 0 20", "Rtm pinm 0 20")   # 27 + 20 = 47 ohm: close to the odd-mode impedance
    phy_pair(d, board, table, max_section_mm=1.0)
    d.add("R102 rp_a rp_b 27", "R103 rm_a rm_b 27")
    board_pair(d, board, table, "conp", "conm", "rp_b", "rm_b", pair_par)
    d.add("Cconp conp 0 0.6p", "Cconm conm 0 0.6p", ".options method=gear reltol=1e-3")
    r = d.run("usb_delay", ["v(conp)", "v(conm)", "v(pinp)", "v(pinm)", "v(rp_b)", "v(rm_b)"], tran="0.01n 8n 0 0.02n")
    t = r["time"] * 1e9
    def zero(a, b):
        s = a - b
        i = np.where((s[:-1] < 0) & (s[1:] >= 0))[0][0]
        return t[i] + (t[i + 1] - t[i]) * (-s[i]) / (s[i + 1] - s[i])
    t_con, t_pin, t_res = zero(r["v(conp)"], r["v(conm)"]), zero(r["v(pinp)"], r["v(pinm)"]), zero(r["v(rp_b)"], r["v(rm_b)"])
    # single-ended arrival of each line at mid swing of its own final level, for the skew
    def half(v):
        lvl = 0.5 * (v[0] + v[-1])
        rising = v[-1] > v[0]
        return spice.crossings(t, v, lvl, rising)[0]
    return {"J1_to_RP2350_pins_ns": round(float(t_pin - t_con), 4), "J1_to_27R_ns": round(float(t_res - t_con), 4),
            "skew_DP_minus_DM_ps": round(float(half(r["v(pinp)"]) - half(r["v(pinm)"])) * 1e3, 2),
            "limit_ns": SPEC["device_trace_delay_ns"]}


def analyse(t, vp, vm, skip_bits=4):
    t = t * 1e9
    diff = vp - vm
    sel = t > skip_bits * UI
    t, vp, vm, diff = t[sel], vp[sel], vm[sel], diff[sel]
    # differential zero crossings
    zc, vcrs = [], []
    s = diff
    idx = np.where(np.signbit(s[:-1]) != np.signbit(s[1:]))[0]
    for i in idx:
        u = -s[i] / (s[i + 1] - s[i])
        zc.append(t[i] + u * (t[i + 1] - t[i]))
        vcrs.append(vp[i] + u * (vp[i + 1] - vp[i]))
    zc = np.array(zc)
    # jitter against the best-fit bit clock
    n = np.round((zc - zc[0]) / UI)
    off = zc - (zc[0] + n * UI)
    off -= off.mean()
    consec = np.diff(zc) - np.diff(n) * UI           # to next transition
    paired = (zc[2:] - zc[:-2]) - (n[2:] - n[:-2]) * UI
    # eye: fold on the fitted clock, centre = half a bit after a crossing
    t0 = zc[0] - (zc - (zc[0] + n * UI)).mean()
    ph = ((t - t0) % UI)
    centre = np.abs(ph - UI / 2) < 1.0
    eye_h = float(np.abs(diff[centre]).min())
    closed = ph[np.abs(diff) < SPEC["VDI_V"]]
    left = closed[closed < UI / 2].max() if (closed < UI / 2).any() else 0.0
    right = closed[closed > UI / 2].min() if (closed > UI / 2).any() else UI
    # single-ended edges 10-90 % of the settled swing
    def edges(v):
        lo, hi = 0.0, 3.3  # nominal swing; percentiles would follow the overshoot
        a, b = lo + 0.1 * (hi - lo), lo + 0.9 * (hi - lo)
        rise, fall = [], []
        for x in spice.crossings(t, v, a, True):
            y = [c for c in spice.crossings(t, v, b, True) if c > x]
            if y and y[0] - x < UI:
                rise.append(y[0] - x)
        for x in spice.crossings(t, v, b, False):
            y = [c for c in spice.crossings(t, v, a, False) if c > x]
            if y and y[0] - x < UI:
                fall.append(y[0] - x)
        return float(np.mean(rise)), float(np.mean(fall)), float(lo), float(hi)
    rp, fp, lop, hip = edges(vp)
    rm, fm, lom, him = edges(vm)
    tfr, tff = (rp + rm) / 2, (fp + fm) / 2
    return {
        "VCRS_min_V": round(float(min(vcrs)), 3), "VCRS_max_V": round(float(max(vcrs)), 3),
        "TFR_ns": round(tfr, 2), "TFF_ns": round(tff, 2), "TFRFM_pct": round(100 * tfr / tff, 1),
        "DP_rise_fall_ns": [round(rp, 2), round(fp, 2)], "DM_rise_fall_ns": [round(rm, 2), round(fm, 2)],
        "levels_V": {"DP": [round(lop, 3), round(hip, 3)], "DM": [round(lom, 3), round(him, 3)]},
        "jitter_pkpk_ns": round(float(off.max() - off.min()), 3),
        "jitter_next_transition_ns": [round(float(consec.min()), 3), round(float(consec.max()), 3)],
        "jitter_paired_ns": [round(float(paired.min()), 3), round(float(paired.max()), 3)],
        "eye_height_at_centre_V": round(eye_h, 3), "eye_width_above_VDI_ns": round(float(right - left), 2),
        "eye_width_UI": round(float(right - left) / UI, 3),
        "overshoot_V": round(float(max(vp.max(), vm.max()) - 3.3), 3), "undershoot_V": round(float(-min(vp.min(), vm.min())), 3),
        "_fold": (t0,),
    }


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    spice.QA.mkdir(parents=True, exist_ok=True)
    table = spice.lines()
    geo = spice.geometry()
    board = Board()
    out = {"spec": SPEC, "impedance": {}, "cases": {}}
    # impedance of every routed cross-section
    for w, g in ((0.25, 0.20), (0.25, 0.16), (0.25, 0.25), (0.15, 0.20), (0.15, 0.50)):
        p = fs.pair(w, g)
        out["impedance"][f"w{w:.2f}_gap{g:.2f}"] = {k: round(v, 4) for k, v in p.items()}
    out["impedance"]["single_0.15"] = table["single"]["0.15"]
    out["impedance"]["single_0.25"] = table["single"]["0.25"]
    pair_par = fs.pair(0.25, 0.20)
    pair_par["w_mm"] = 0.25
    # routed delay: coupled part at the odd-mode velocity, break-outs at the single-line velocity
    u = geo["usb"]
    delay = {}
    for net, short in (("USB_DP_CONN", "USB_DP"), ("USB_DM_CONN", "USB_DM")):
        wide = sum(v for k, v in u[net]["by_layer_width"].items() if float(k.split(":")[1]) >= 0.24)
        narrow = u[net]["length_mm"] - wide + u[short]["length_mm"]
        ps = wide * pair_par["delay_odd_ps_per_mm"] + narrow * table["single"]["0.15"]["delay_ps_per_mm"]
        via_ps = (u[net]["vias"] + u[short]["vias"]) * (table["via_L_nH"] * 1e-9 * table["via_C_pF"] * 1e-12) ** 0.5 * 1e12
        delay[net] = {"coupled_mm": round(wide, 2), "breakout_mm": round(narrow, 2), "vias": u[net]["vias"],
                      "phy_vias": u[short]["vias"],
                      "delay_ps_odd_mode": round(ps + via_ps, 1),
                      "delay_ps_single_ended_upper": round(u[net]["delay_ps"] + u[short]["delay_ps"] + via_ps, 1)}
    out["delay"] = delay
    out["delay"]["skew_ps"] = round(delay["USB_DP_CONN"]["delay_ps_odd_mode"] - delay["USB_DM_CONN"]["delay_ps_odd_mode"], 2)

    out["delay"]["simulated"] = sim_delay(board, table, pair_par)
    print("delay", out["delay"])

    waves = {}
    runs = {
        "device TX, test load 50 pF at J1 (Figure 7-9), ramp 4 ns": ("device_tx", 4, dict(cable=False, test_load=True)),
        "device TX, test load 50 pF at J1 (Figure 7-9), ramp 8 ns": ("device_tx", 8, dict(cable=False, test_load=True)),
        "device TX, test load 50 pF at J1 (Figure 7-9), ramp 16 ns": ("device_tx", 16, dict(cable=False, test_load=True)),
        "device TX, 1 m cable, eye at host, ramp 4 ns": ("device_tx", 4, dict(cable=True)),
        "device TX, 1 m cable, eye at host, ramp 8 ns": ("device_tx", 8, dict(cable=True)),
        "device TX, 1 m cable, eye at host 150 pF, ramp 8 ns": ("device_tx", 8, dict(cable=True, host_c=150.0)),
        "host TX, 1 m cable, eye at RP2350 pins, ramp 4 ns": ("host_tx", 4, dict(cable=True)),
        "host TX, 1 m cable, eye at RP2350 pins, ramp 8 ns": ("host_tx", 8, dict(cable=True)),
        "host TX, 1 m cable, eye at RP2350 pins, ramp 16 ns": ("host_tx", 16, dict(cable=True)),
    }
    for i, (label, (direction, edge, kw)) in enumerate(runs.items()):
        d, hp, hm, info = build(board, table, pair_par, direction, edge, **kw)
        obs = (hp, hm) if direction == "device_tx" else ("pinp", "pinm")
        r = d.run(f"usb_{i:02d}_{direction}_{edge}ns", [f"v({obs[0]})", f"v({obs[1]})", "v(conp)", "v(conm)"],
                  tran=f"0.1n {len(STATES) * UI:.1f}n 0 0.2n")
        a = analyse(r["time"], r[f"v({obs[0]})"], r[f"v({obs[1]})"])
        fold = a.pop("_fold")
        out["cases"][label] = a
        out["pair_model_sections"] = info
        waves[label] = (r["time"] * 1e9, r[f"v({obs[0]})"], r[f"v({obs[1]})"], fold[0])
        print(label, a)
    (spice.OUT / "usb.json").write_text(json.dumps(out, indent=1))

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.9), facecolor="#fcfcfb")
    for ax, label, title in zip(axes, ("device TX, 1 m cable, eye at host, ramp 8 ns", "host TX, 1 m cable, eye at RP2350 pins, ramp 8 ns",
                                       "device TX, test load 50 pF at J1 (Figure 7-9), ramp 8 ns"),
                                ("Differential eye at the host, device transmitting\n(1 m cable, 8 ns source ramp)",
                                 "Differential eye at the RP2350 pins, host transmitting\n(1 m cable, 8 ns source ramp)",
                                 "D+ and D- at J1 into the 50 pF test load\n(crossover window 1.3–2.0 V)")):
        t, vp, vm, t0 = waves[label]
        if "test load" in label:
            ph = (t - t0 + UI / 2) % (2 * UI)
            order = np.argsort(ph)
            brk = np.where(np.diff(((t - t0 + UI / 2) // (2 * UI))) != 0)[0] + 1
            for seg in np.split(np.arange(len(t)), brk):
                if t[seg[0]] < 4 * UI:
                    continue
                ax.plot(ph[seg], vp[seg], color=spice.SERIES[0], linewidth=0.9, alpha=0.7)
                ax.plot(ph[seg], vm[seg], color=spice.SERIES[1], linewidth=0.9, alpha=0.7)
            ax.axhspan(1.3, 2.0, color="#e6e5e0", alpha=0.7, linewidth=0)
            ax.plot([], [], color=spice.SERIES[0], label="D+")
            ax.plot([], [], color=spice.SERIES[1], label="D−")
            ax.legend(fontsize=8, frameon=False, loc="center right")
            spice.style(ax, title, "time, ns (two bit times)", "V")
        else:
            ph = (t - t0 + UI / 2) % (2 * UI)
            brk = np.where(np.diff(((t - t0 + UI / 2) // (2 * UI))) != 0)[0] + 1
            for seg in np.split(np.arange(len(t)), brk):
                if t[seg[0]] < 4 * UI:
                    continue
                ax.plot(ph[seg], (vp - vm)[seg], color=spice.SERIES[0], linewidth=0.9, alpha=0.7)
            ax.axhspan(-0.2, 0.2, color="#e6e5e0", alpha=0.9, linewidth=0)
            ax.text(UI, 0.0, "receiver sensitivity ±0.2 V", fontsize=7.5, color=spice.INK2, ha="center", va="center")
            spice.style(ax, title, "time, ns (two bit times)", "D+ − D−, V")
    fig.tight_layout()
    fig.savefig(spice.QA / "usb-fs-eye.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
