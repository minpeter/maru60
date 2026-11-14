"""Key matrix (5 x 15, COL2ROW, 1N4148W cathode to row): settling and leakage.

QMK timing (build/pcb-qmk-20261109/qmk_firmware, quantum/matrix.c, matrix_common.c,
platforms/chibios/_wait.h): the row is driven low, matrix_output_select_delay()
waits GPIO_INPUT_PIN_DELAY CPU cycles (120 = 0.8 us at 150 MHz in this keyboard's config.h;
QMK's default is CPU_CLOCK/1e6/4 = 37 cycles = 0.25 us, the "default" figures below),
the 15 columns are read, the row is released to an input with pull-up, and
matrix_output_unselect_delay() waits MATRIX_IO_DELAY = 30 us before the next row.

ngspice transient
  row       : RP2350 GPIO pulling low through RON, internal pull-up RPU when released
              RON: 4 mA drive, VOL <= 0.5 V at 4 mA  -> <= 125 ohm (datasheet Table 1683);
                   40 ohm ASSUMED typical
              RPU: 32-86 kohm at 3.3 V (Table 1683)
  nets      : LC ladders with the routed copper capacitance (geometry.json) of the
              row with the most copper and of the columns of the closed keys: the
              column that is watched is the one with the most copper, the other
              closed keys take the next largest columns, each with its own
              capacitance and length; + 5 pF per MCU pin (ASSUMED, not in the
              datasheet), + the junction capacitance of the row's other diodes
  diode     : 1N4148 SPICE model, CJO 0.9 pF (Diodes Inc. Figure 4: 0.75 pF typ at 0 V)
  thresholds: VIL 0.8 V, VIH 2.0 V (RP2350 Table 1683)
Leakage is a hand calculation from the Diodes Inc. 1N4148W reverse-current curve.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spice  # noqa: E402

VIL, VIH, VDD = 0.8, 2.0, 3.3
SELECT_DELAY_NS = 120 / 150e6 * 1e9            # keyboards/maru60/rp2350/config.h: GPIO_INPUT_PIN_DELAY 120
DEFAULT_SELECT_DELAY_NS = 37 / 150e6 * 1e9     # QMK default, what the firmware used before
UNSELECT_DELAY_US = 30.0
PIN_C = 5.0


def build(row, cols, n_keys, ron, rpu, temp=27, key_c=8.8):
    """cols: column nets, largest capacitance first; key k closes onto cols[k], key 0 is the one watched."""
    d = spice.Deck(f"matrix: {n_keys} key(s) of the same row closed, RON {ron} ohm, RPU {rpu / 1e3:.0f} k, {temp} C")
    d.add(f".options temp={temp} method=gear", "Vdd vdd 0 3.3",
          ".model D4148 D(IS=2.52n RS=0.568 N=1.752 CJO=0.9p M=0.4 VJ=0.7 TT=4n BV=100 IBV=1u)",
          ".model SWROW SW(RON=1 ROFF=1G VT=0.5 VH=0.01)",
          # select: 0 -> selected at 100 ns, released at 2 us
          "Vsel sel 0 PWL(0 0 100n 0 101.5n 1 2000n 1 2001.5n 0)",
          f"Srow rowpin rdrv sel 0 SWROW", f"Rron rdrv 0 {ron - 1}", f"Rpur vdd rowpin {rpu}", f"Cpinr rowpin 0 {PIN_C}p")
    # row copper: MCU pin to the farthest diode
    p = spice.line_params(0.2)
    nsec = 12
    c_row = row["cap"]["C_copper_pF"] + 14 * 0.7     # other diodes: CJ in series with their KEY net
    length = row["farthest_pad_mm"]
    prev = "rowpin"
    for i in range(nsec):
        nxt = "rowfar" if i == nsec - 1 else f"rw{i + 1}"
        d.add(f"Rr{i} {prev} {nxt}x {p['R_ohm_per_mm'] * length / nsec:.5g}", f"Lr{i} {nxt}x {nxt} {p['L_nH_per_mm'] * length / nsec:.5g}n",
              f"Cr{i} {nxt} 0 {c_row / nsec:.5g}p")
        prev = nxt
    for k in range(n_keys):
        tap = "rowfar" if k == 0 else f"rw{1 + (k * 3) % (nsec - 1)}"   # other pressed keys spread along the row
        cpin = f"colpin{k}"
        d.add(f"D{k} key{k} {tap} D4148", f"Ckey{k} key{k} 0 {key_c}p", f"Rsw{k} key{k} colfar{k} 0.2",
              f"Rpuc{k} vdd {cpin} {rpu}", f"Cpinc{k} {cpin} 0 {PIN_C}p")
        c_col = cols[k]["cap"]["C_copper_pF"]
        lc = cols[k]["farthest_pad_mm"]
        prev = f"colfar{k}"
        for i in range(nsec):
            nxt = cpin if i == nsec - 1 else f"c{k}_{i}"
            d.add(f"Rc{k}_{i} {prev} {nxt}x {p['R_ohm_per_mm'] * lc / nsec:.5g}", f"Lc{k}_{i} {nxt}x {nxt} {p['L_nH_per_mm'] * lc / nsec:.5g}n",
                  f"Cc{k}_{i} {nxt} 0 {c_col / nsec:.5g}p")
            prev = nxt
    return d


def run_case(name, row, cols, n_keys, ron, rpu, temp=27):
    d = build(row, cols, n_keys, ron, rpu, temp)
    r = d.run(name, ["v(rowpin)", "v(rowfar)", "v(colpin0)", "v(sel)"], tran="0.2n 40u 0 20n")
    t, vc, vr = r["time"], r["v(colpin0)"], r["v(rowpin)"]
    # last time the column falls through VIL while the row is selected (ringing can cross it more than once)
    fall = [x for x in spice.crossings(t, vc, VIL, False) if 100e-9 < x < 2000e-9][-1:]
    rise = [x for x in spice.crossings(t, vc, VIH, True) if x > 2000e-9]
    low = float(vc[(t > 1.8e-6) & (t < 2.0e-6)].mean())
    return {
        "keys_closed_in_row": n_keys, "RON_ohm": ron, "RPU_ohm": rpu, "temp_C": temp,
        "column_capacitance_total_pF": round(sum(c["cap"]["C_copper_pF"] + PIN_C for c in cols[:n_keys]), 1),
        "t_col_below_VIL_ns": round(float(fall[0] - 100e-9) * 1e9, 1) if fall else None,
        "select_delay_ns": round(SELECT_DELAY_NS, 1),
        "select_margin_x": round(float(SELECT_DELAY_NS / ((fall[0] - 100e-9) * 1e9)), 1) if fall else None,
        "default_select_delay_ns": round(DEFAULT_SELECT_DELAY_NS, 1),
        "default_select_margin_x": round(float(DEFAULT_SELECT_DELAY_NS / ((fall[0] - 100e-9) * 1e9)), 1) if fall else None,
        "col_low_level_V": round(low, 3), "low_level_margin_to_VIL_V": round(VIL - low, 3),
        "t_col_above_VIH_after_release_us": round(float(rise[0] - 2000e-9) * 1e6, 2) if rise else None,
        "unselect_delay_us": UNSELECT_DELAY_US,
        "unselect_margin_x": round(float(UNSELECT_DELAY_US / ((rise[0] - 2000e-9) * 1e6)), 1) if rise else None,
    }, r


def leakage():
    """Sneak path: column read high while n reverse-biased diodes of an unselected row leak to a selected row."""
    # Diodes Inc. BAV16W/1N4148W Figure 3, read at VR about 3 V: 10 nA at 25 C, 80 nA at 75 C (typical curves)
    typ60 = 10e-9 * (80 / 10) ** ((60 - 25) / 50)
    # Guaranteed: 25 nA max at 20 V, 25 C (table); same temperature slope applied
    max60 = 25e-9 * (80 / 10) ** ((60 - 25) / 50)
    rpu_max, iin = 86e3, 1e-6
    out = {"IR_typ_60C_nA": round(typ60 * 1e9, 1), "IR_max_60C_nA_scaled_from_25nA_at_20V": round(max60 * 1e9, 1)}
    for n in (1, 14, 61):
        i = n * max60 + iin
        out[f"column_droop_V_{n}_leaking_diodes_plus_1uA_pin"] = round(i * rpu_max, 3)
    out["allowed_droop_V"] = round(VDD - VIH, 2)
    out["leakage_budget_uA_at_RPU_86k"] = round((VDD - VIH) / rpu_max * 1e6, 2)
    out["margin_x_worst_61_diodes"] = round((VDD - VIH) / ((61 * max60 + iin) * rpu_max), 1)
    return out


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    geo = spice.geometry()["matrix"]
    rows = {k: v for k, v in geo.items() if k.startswith("ROW")}
    cols = {k: v for k, v in geo.items() if k.startswith("COL")}
    wr = max(rows, key=lambda k: rows[k]["cap"]["C_copper_pF"])
    order = sorted(cols, key=lambda k: -cols[k]["cap"]["C_copper_pF"])
    wc = order[0]
    by_size = [cols[k] for k in order]
    n_row = rows[wr]["pads"] - 1          # pads on the row net: one MCU pin, the rest are diodes
    out = {"worst_row": wr, "worst_col": wc,
           "net_capacitance_pF": {k: v["cap"]["C_copper_pF"] for k, v in {**rows, **cols}.items()},
           "net_length_mm": {k: v["length_mm"] for k, v in {**rows, **cols}.items()},
           "pin_capacitance_assumed_pF": PIN_C,
           "keys_on_worst_row": n_row, "wait_cpuclock_max_cycles": 135, "cases": {}}
    waves = {}
    for label, (n, ron, rpu, temp) in {
        "typical: 1 key, RON 40, RPU 50k": (1, 40, 50e3, 27),
        "limit: 1 key, RON 125, RPU 86k": (1, 125, 86e3, 27),
        "limit: 6 keys in the row, RON 125, RPU 86k": (6, 125, 86e3, 27),
        "limit: all 15 keys of the row, RON 125, RPU 86k": (n_row, 125, 86e3, 27),
        "typical RON 40: all 15 keys of the row, RPU 86k": (n_row, 40, 86e3, 27),
        "RON 80: all 15 keys of the row, RPU 86k": (n_row, 80, 86e3, 27),
        "limit, hot 60 C: all 15 keys of the row, RON 125, RPU 86k": (n_row, 125, 86e3, 60),
        "limit, cold 0 C: all 15 keys of the row, RON 125, RPU 86k": (n_row, 125, 86e3, 0),
        "cold 0 C: 1 key, RON 125, RPU 32k (highest low level)": (1, 125, 32e3, 0),
    }.items():
        m, r = run_case("matrix_" + label.split(":")[0].replace(" ", "_").replace(",", "") + f"_{n}k_{ron}", rows[wr], by_size, n, ron, rpu, temp)
        out["cases"][label] = m
        waves[label] = r
        print(label, m)
    out["leakage_60C"] = leakage()
    print(out["leakage_60C"])
    (spice.OUT / "matrix.json").write_text(json.dumps(out, indent=1))

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.7), facecolor="#fcfcfb")
    picks = ["typical: 1 key, RON 40, RPU 50k", "limit: 6 keys in the row, RON 125, RPU 86k", "limit: all 15 keys of the row, RON 125, RPU 86k"]
    for lab, col in zip(picks, spice.SERIES):
        r = waves[lab]
        axes[0].plot((r["time"] - 100e-9) * 1e9, r["v(colpin0)"], color=col, linewidth=1.6, label=lab)
        axes[1].plot((r["time"] - 2e-6) * 1e6, r["v(colpin0)"], color=col, linewidth=1.6, label=lab)
    axes[0].axhline(VIL, color=spice.INK2, linewidth=0.8, linestyle="--")
    axes[0].axvline(DEFAULT_SELECT_DELAY_NS, color=spice.INK2, linewidth=0.8, linestyle=":")
    axes[0].text(DEFAULT_SELECT_DELAY_NS - 5, 3.0, "QMK default read\n(0.25 µs)", fontsize=7.5, color=spice.INK2, ha="right")
    axes[0].axvline(SELECT_DELAY_NS, color=spice.INK2, linewidth=0.8, linestyle=":")
    axes[0].text(SELECT_DELAY_NS - 5, 3.0, "this firmware reads\n(0.8 µs)", fontsize=7.5, color=spice.INK2, ha="right")
    axes[0].text(395, VIL + 0.07, "VIL 0.8 V", fontsize=7.5, color=spice.INK2, ha="right")
    axes[0].set_xlim(-20, 400)
    spice.style(axes[0], f"Column {wc} at the MCU pin after {wr} is driven low", "time after row select, ns", "V")
    axes[1].axhline(VIH, color=spice.INK2, linewidth=0.8, linestyle="--")
    axes[1].axvline(UNSELECT_DELAY_US, color=spice.INK2, linewidth=0.8, linestyle=":")
    axes[1].text(UNSELECT_DELAY_US - 0.5, 0.4, "next row selected\n(30 µs)", fontsize=7.5, color=spice.INK2, ha="right")
    axes[1].text(37, VIH + 0.07, "VIH 2.0 V", fontsize=7.5, color=spice.INK2, ha="right")
    axes[1].set_xlim(-1, 38)
    spice.style(axes[1], "Column recovery after the row is released to its pull-up", "time after row release, µs", "V")
    axes[1].legend(fontsize=7.5, frameon=False, loc="center right")
    fig.tight_layout()
    fig.savefig(spice.QA / "matrix-settling.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
