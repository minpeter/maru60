"""12 MHz crystal (Y1 ABM8-272-T3, C106/C107 15 pF, R108 1 k in XOUT).

What the documents give
  Abracon ABM8-272-T3 (drawing 456603 rev B) and RP2350 datasheet Table 629:
      CL 10 pF, ESR <= 50 ohm, C0 <= 3.0 pF, +-30 ppm, drive level 10 uW typ / 200 uW max
  RP2350 datasheet Table 1686 (oscillator pin characteristics): frequency range and
      the square-wave input thresholds only. It gives NO amplifier transconductance,
      NO pin capacitance and NO negative-resistance figure, so:
        pin capacitance XIN/XOUT : ASSUMED 2 pF (1-4 pF bracket)
        motional capacitance C1  : ASSUMED 4 fF (2-6 fF bracket; not on the Abracon sheet)
        amplifier gm             : swept; the value needed is reported, the value
                                   present in the chip is UNVERIFIED
  Hardware design with RP2350, chapter 4: the reference assumes 3 pF of parasitics and
      arrives at 7.5 + 3 = 10.5 pF.

Computed here
  1. Load capacitance from the routed copper (geometry.json) and the frequency offset.
  2. ngspice AC: resistance seen by the crystal's motional arm as a function of gm
     (negative = the circuit sustains oscillation), with R108 and all capacitances.
  3. ngspice AC: upper bound of the drive level, with XOUT swinging rail to rail as
     a square wave (fundamental 2.1 V peak) and the loop at its oscillation phase.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spice  # noqa: E402

F0 = 12e6
W = 2 * math.pi * F0
CL_SPEC, ESR_MAX, C0_MAX, DRIVE_MAX_UW, DRIVE_TYP_UW = 10.0, 50.0, 3.0, 200.0, 10.0
C_FIT = 15.0


def load_cap(geo, c_pin, c0_stray=0.05):
    ca = C_FIT + geo["XIN"]["cap"]["C_copper_pF"] + c_pin
    cb = C_FIT + geo["XTAL_OUT"]["cap"]["C_copper_pF"]
    # XOUT pin and its 3 mm of track sit behind the 1 k resistor: at 12 MHz they add in series with it
    cx = geo["XOUT"]["cap"]["C_copper_pF"] + c_pin
    # series R-C branch: effective parallel capacitance = Cx / (1 + (w R Cx)^2)
    cb_eff = cb + cx / (1 + (W * 1000.0 * cx * 1e-12) ** 2)
    return {"C_XIN_node_pF": round(ca, 2), "C_XTAL_OUT_node_pF": round(cb, 2), "C_behind_R108_pF": round(cx, 2),
            "CL_amplifier_driving_pF": round(ca * cb / (ca + cb) + c0_stray, 2),
            "CL_xout_branch_counted_pF": round(ca * cb_eff / (ca + cb_eff) + c0_stray, 2)}


def pull_ppm(cl, c1_fF, c0):
    return 0.5 * c1_fF * 1e-3 * (1 / (c0 + cl) - 1 / (c0 + CL_SPEC)) * 1e6


def neg_resistance(geo, c_pin, c0, gms, ro=20e3):
    d = spice.Deck("crystal: resistance seen by the motional arm vs amplifier gm (AC, 12 MHz)")
    ca = C_FIT + geo["XIN"]["cap"]["C_copper_pF"] + c_pin
    cb = C_FIT + geo["XTAL_OUT"]["cap"]["C_copper_pF"]
    cx = geo["XOUT"]["cap"]["C_copper_pF"] + c_pin
    for i, gm in enumerate(gms):
        d.add(f"I{i} xb{i} xin{i} AC 1", f"Ca{i} xin{i} 0 {ca}p", f"Cb{i} xb{i} 0 {cb}p", f"C0{i} xin{i} xb{i} {c0}p",
              f"R108_{i} xb{i} xo{i} 1k", f"Cx{i} xo{i} 0 {cx}p", f"G{i} xo{i} 0 xin{i} 0 {gm}", f"Ro{i} xo{i} 0 {ro}",
              f"Rf{i} xin{i} xo{i} 1meg")
    d.add(".ac lin 1 12meg 12meg")
    lets = "\n".join(f"let zr{i} = real(v(xin{i})-v(xb{i}))\nlet zi{i} = imag(v(xin{i})-v(xb{i}))" for i in range(len(gms)))
    r = d.run("xtal_negative_resistance", [f"zr{i}" for i in range(len(gms))] + [f"zi{i}" for i in range(len(gms))], control_extra=lets)
    return [{"gm_mS": gm * 1e3, "R_ohm": float(r[f"zr{i}"][0]), "X_ohm": float(r[f"zi{i}"][0])} for i, gm in enumerate(gms)]


def drive_bound(geo, c_pin, c0, esr, c1_fF=4.0):
    """XOUT as a 2.1 V-peak source (fundamental of a 3.3 V square wave); crystal current at the loop's 180 degree point."""
    ca = C_FIT + geo["XIN"]["cap"]["C_copper_pF"] + c_pin
    cb = C_FIT + geo["XTAL_OUT"]["cap"]["C_copper_pF"]
    lm = 1 / (W ** 2 * c1_fF * 1e-15)
    d = spice.Deck(f"crystal: drive-level upper bound, ESR {esr} ohm, rail-to-rail square wave at XOUT")
    d.add("Vx xo 0 AC 2.1008", "R108 xo xb 1k", f"Cb xb 0 {cb}p", f"Ca xin 0 {ca}p", f"C0 xin xb {c0}p",
          f"Lm xb m1 {lm:.9g}", f"Cm m1 m2 {c1_fF}f", f"Rm m2 m3 {esr}", "Vi m3 xin 0",
          ".ac lin 40001 12.000meg 12.020meg")
    lets = "let xr = real(v(xin))\nlet xi = imag(v(xin))\nlet ir = real(i(vi))\nlet ii = imag(i(vi))"
    r = d.run(f"xtal_drive_bound_esr{int(esr)}", ["xr", "xi", "ir", "ii"], control_extra=lets)
    f = r[list(r)[0]]
    xr, xi, ir, ii = r["xr"], r["xi"], r["ir"], r["ii"]
    # oscillation phase: V(XIN) exactly opposite to V(XOUT) -> imag = 0 with real < 0; take the crossing with the largest current
    idx = np.where((np.sign(xi[:-1]) != np.sign(xi[1:])) & (xr[:-1] < 0))[0]
    if len(idx) == 0:
        return {"error": "no 180 degree point"}
    k = max(idx, key=lambda j: ir[j] ** 2 + ii[j] ** 2)
    i_pk = math.hypot(ir[k], ii[k])
    v_xin = math.hypot(xr[k], xi[k])
    p = 0.5 * i_pk ** 2 * esr
    # XIN cannot swing beyond the rails for long (pad clamps): cap the amplitude at 1.65 V peak
    scale = min(1.0, 1.65 / v_xin)
    return {"ESR_ohm": esr, "f_osc_offset_ppm_from_series": round((f[k] - F0) / F0 * 1e6, 1),
            "I_crystal_mA_peak_unclamped": round(i_pk * 1e3, 3), "V_XIN_peak_unclamped": round(v_xin, 3),
            "drive_uW_unclamped": round(p * 1e6, 1),
            "drive_uW_with_XIN_limited_to_rails": round(p * scale ** 2 * 1e6, 1)}


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    geo = spice.geometry()["nets"]
    out = {"spec": {"CL_pF": CL_SPEC, "ESR_max_ohm": ESR_MAX, "C0_max_pF": C0_MAX, "drive_typ_uW": DRIVE_TYP_UW, "drive_max_uW": DRIVE_MAX_UW,
                    "tolerance_ppm": 30, "stability_ppm": 30, "usb_fs_data_rate_tolerance_ppm": 2500},
           "copper": {k: {"length_mm": geo[k]["net_total"]["length_mm"], **geo[k]["cap"]} for k in ("XIN", "XTAL_OUT", "XOUT")},
           "neighbours": {k: geo[k]["neighbours"] for k in ("XIN", "XTAL_OUT", "XOUT")},
           "load_capacitance": {}, "frequency_offset_ppm": {}}
    for c_pin in (1.0, 2.0, 4.0):
        lc = load_cap(geo, c_pin)
        out["load_capacitance"][f"pin_{c_pin:.0f}pF"] = lc
        for c1 in (2.0, 4.0, 6.0):
            out["frequency_offset_ppm"][f"pin_{c_pin:.0f}pF_C1_{c1:.0f}fF"] = [
                round(pull_ppm(lc["CL_xout_branch_counted_pF"], c1, 2.0), 1), round(pull_ppm(lc["CL_amplifier_driving_pF"], c1, 2.0), 1)]
    offs = [v for pair in out["frequency_offset_ppm"].values() for v in pair]
    out["frequency_offset_ppm_range"] = [min(offs), max(offs)]
    out["reference_design_CL_pF_as_stated_by_raspberry_pi"] = 10.5

    gms = [g * 1e-3 for g in (0.1, 0.2, 0.3, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24, 32)]
    nr = {}
    for label, (c_pin, c0) in {"nominal (pin 2 pF, C0 2 pF)": (2.0, 2.0), "worst (pin 4 pF, C0 3 pF)": (4.0, 3.0)}.items():
        rows = neg_resistance(geo, c_pin, c0, gms)
        need1 = next((x["gm_mS"] for x in rows if x["R_ohm"] < -ESR_MAX), None)
        need5 = next((x["gm_mS"] for x in rows if x["R_ohm"] < -5 * ESR_MAX), None)
        best = min(rows, key=lambda x: x["R_ohm"])
        nr[label] = {"rows": [{k: round(v, 3) for k, v in x.items()} for x in rows],
                     "gm_mS_for_minus_ESRmax": need1, "gm_mS_for_minus_5x_ESRmax": need5,
                     "most_negative_R_ohm": round(best["R_ohm"], 1), "at_gm_mS": best["gm_mS"],
                     "safety_factor_at_best_gm": round(-best["R_ohm"] / ESR_MAX, 1)}
    out["negative_resistance"] = nr
    out["drive_level_bound"] = {f"ESR_{int(e)}": drive_bound(geo, 2.0, 2.0, e) for e in (50.0, 30.0, 15.0)}
    print(json.dumps({k: v for k, v in out.items() if k != "neighbours"}, indent=1)[:6000])
    (spice.OUT / "xtal.json").write_text(json.dumps(out, indent=1))

    fig, ax = plt.subplots(figsize=(6.8, 3.6), facecolor="#fcfcfb")
    for (label, v), col in zip(nr.items(), spice.SERIES):
        ax.plot([x["gm_mS"] for x in v["rows"]], [x["R_ohm"] for x in v["rows"]], color=col, linewidth=1.8, marker="o", markersize=4, label=label)
    ax.axhline(-ESR_MAX, color=spice.INK2, linewidth=0.8, linestyle="--")
    ax.axhline(-5 * ESR_MAX, color=spice.INK2, linewidth=0.8, linestyle=":")
    ax.text(31, -ESR_MAX + 12, "−ESR max (50 Ω): oscillation limit", fontsize=7.5, color=spice.INK2, ha="right")
    ax.text(31, -5 * ESR_MAX + 12, "−5 × ESR max: usual design target", fontsize=7.5, color=spice.INK2, ha="right")
    ax.set_xscale("log")
    spice.style(ax, "Resistance seen by the crystal vs amplifier transconductance (12 MHz, R108 = 1 kΩ)\nRP2350 does not publish its gm: the chip's own value is unverified",
                "assumed amplifier gm, mS", "resistance, Ω (negative sustains oscillation)")
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(spice.QA / "xtal-negative-resistance.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
