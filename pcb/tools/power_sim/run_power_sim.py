#!/usr/bin/env python3
"""Run the Maru60 power-tree ngspice decks and collect the numbers.

usage (repository root):
    docker build -t maru60-ngspice:local pcb/tools/power_sim
    .venv/bin/python pcb/tools/power_sim/run_power_sim.py OUT_DIR

Each case copies the decks into build/psim/<case>/, overrides the parameters of
that case (params.inc values and the deck's own .param lines), runs ngspice in
the container without network and reads the written vectors.  The models in
models.lib are behavioural; every parameter there is tagged with its source.
Nothing here is a measurement.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
IMAGE = "maru60-ngspice:local"


def run(case: str, deck: str, params: dict | None = None, deck_params: dict | None = None, drop: tuple = ()):
    d = ROOT / "build/psim" / case
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    for f in list(HERE.glob("*.inc")) + [HERE / "models.lib"]:
        shutil.copy(f, d / f.name)
    text = (HERE / f"{deck}.cir").read_text()
    for k, v in (deck_params or {}).items():
        text, n = re.subn(rf"(?m)^\.param {k}=\S+", f".param {k}={v}", text)
        if n != 1:
            raise SystemExit(f"{deck}: .param {k} not found")
    for vec in drop:                      # vectors ngspice does not keep without extra options
        text = text.replace(" " + vec, "")
    (d / f"{deck}.cir").write_text(text)
    if params:
        p = (d / "params.inc").read_text()
        for k, v in params.items():
            p, n = re.subn(rf"(?m)^\.param {k}=\S+", f".param {k}={v}", p)
            if n != 1:
                raise SystemExit(f"params.inc: {k} not found")
        (d / "params.inc").write_text(p)
    r = subprocess.run(["docker", "run", "--rm", "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "-v", f"{d}:/work", IMAGE, "-b", f"{deck}.cir"],
                       capture_output=True, text=True, timeout=1800)
    (d / "log.txt").write_text(r.stdout + r.stderr)
    out = d / "out.txt"
    if not out.exists():
        raise SystemExit(f"{case}: no output, see {d}/log.txt")
    names = [n.lower() for n in out.open().readline().split()]
    data = np.loadtxt(out, skiprows=1)
    return {n: data[:, i] for i, n in enumerate(names)}


def at(v, t, t0):
    return float(np.interp(t0, t, v))


def window(v, t, a, b):
    m = (t >= a) & (t <= b)
    return v[m]


def first_above(v, t, level):
    i = np.argmax(v >= level)
    return float(t[i]) if v[i] >= level else None


def main():
    outdir = Path(sys.argv[1])
    outdir.mkdir(parents=True, exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    R = {}

    # (a) plug-in
    fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for vs in (5.0, 5.5):
        w = run(f"plugin_{vs}", "plugin", {"vsrc": vs})
        t = w["time"]
        v33, v4 = w["v(v33)"], w["v(v4)"]
        t2 = first_above(v33, t, 2.0)
        after = v33[t >= t2] if t2 else v33
        dip = float(np.max(np.maximum.accumulate(after) - after)) if t2 else None
        R[f"plugin_{vs}V"] = {
            "inrush_peak_a": round(float(np.max(np.abs(w["i(vsrc)"]))), 4),
            "t_vprot_4v_ms": round((first_above(w["v(vprot)"], t, 4.0) - 1e-3) * 1e3, 2),
            "t_4v_rail_3p9_ms": round((first_above(v4, t, 3.9) - 1e-3) * 1e3, 2),
            "t_3v3_3p135_ms": round((first_above(v33, t, 3.135) - 1e-3) * 1e3, 2),
            "v4_max": round(float(v4.max()), 4), "v33_max": round(float(v33.max()), 4),
            "v33_largest_dip_after_2v_mv": round(dip * 1e3, 2),
            "v33_slew_at_1v8_v_per_ms": round(float(np.gradient(v33, t)[np.argmax(v33 >= 1.8)] / 1e3), 3),
        }
        ax[0].plot(t * 1e3, w["v(vprot)"], label=f"VBUS_PROTECTED_RAW {vs} V")
        ax[0].plot(t * 1e3, v4, label=f"+4V_REG {vs} V")
        ax[0].plot(t * 1e3, v33, label=f"+3V3 {vs} V")
        ax[1].plot(t * 1e3, np.abs(w["i(vsrc)"]) * 1e3, label=f"input current {vs} V")
    ax[0].set_ylabel("V"); ax[1].set_ylabel("mA"); ax[1].set_xlabel("ms"); ax[0].legend(fontsize=7); ax[1].legend(fontsize=7); ax[0].grid(True); ax[1].grid(True)
    ax[0].set_title("Plug-in (behavioural models, averaged buck)")
    fig.savefig(outdir / "plugin.png", dpi=110, bbox_inches="tight"); plt.close(fig)

    # (3) steady input current
    for name, dp, p in (("idle 20 mA on 3V3, LEDs off", {"ledon": 0}, {"i33a": 0.020}),
                        ("typing 60 mA on 3V3, LEDs off", {"ledon": 0}, {"i33a": 0.060}),
                        ("60 mA on 3V3, LEDs at the firmware cap (38 mA static + 25 mA)", {"ledon": 1}, {"i33a": 0.060, "iled": 0.025}),
                        ("120 mA on 3V3, LED rail at the 234 mA limiter maximum", {"ledon": 1}, {"i33a": 0.120, "iled": 0.196})):
        w = run("steady", "steady", p, dp, drop=("i(Rtr1)",))
        t = w["time"]
        R.setdefault("steady_input_current_ma", {})[name] = round(float(np.mean(np.abs(window(w["i(vsrc)"], t, 14e-3, 16e-3)))) * 1e3, 1)

    # (b) load steps
    fig, ax = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    for deck in ("loadstep_avg", "loadstep_sw"):
        w = run(deck, deck)
        t = w["time"]
        r = {}
        for label, a, b, pre in (("3v3_step_20_to_120mA", 6e-3, 8e-3, 5.9e-3), ("led_rail_enable", 10e-3, 16e-3, 9.9e-3), ("led_step_0_to_150mA", 16e-3, 19e-3, 15.9e-3)):
            for vec, key in (("v(v33)", "3v3"), ("v(v4)", "4v_reg"), ("v(vprot)", "vprot"), ("v(vled)", "4v_led")):
                if key == "4v_led" and label != "led_step_0_to_150mA":
                    continue
                r[f"{label}:{key}_droop_mv"] = round((at(w[vec], t, pre) - float(window(w[vec], t, a, b).min())) * 1e3, 1)
        r["led_enable_inrush_peak_ma"] = round(float(np.max(np.abs(window(w["i(vsrc)"], t, 10e-3, 12e-3)))) * 1e3, 1)
        R[deck] = r
        for i, vec in enumerate(("v(v33)", "v(v4)", "v(vled)")):
            ax[i].plot(t * 1e3, w[vec], label=f"{vec} {deck}", lw=0.8)
            ax[i].legend(fontsize=7); ax[i].grid(True)
    ax[2].set_xlabel("ms"); ax[0].set_title("Load steps: 3V3 20->120 mA at 6 ms, LED enable at 10 ms, LED 0->150 mA at 16 ms")
    fig.savefig(outdir / "loadstep.png", dpi=110, bbox_inches="tight"); plt.close(fig)

    # (e) loop gain
    fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for name, dp, p in (("0.1 A, nominal capacitors, kea 1", {"rload": 40}, {}),
                        ("0.3 A, nominal capacitors, kea 1", {"rload": 13.3}, {}),
                        ("0.3 A, capacitors at -20 % / -10 %, kea 1", {"rload": 13.3}, {"cloc": "13.9u", "c100": "14.2u"}),
                        ("0.3 A, nominal capacitors, kea 0.68", {"rload": 13.3}, {"kea": 0.68}),
                        ("0.02 A, nominal capacitors, kea 1", {"rload": 200}, {}),
                        ("0.3 A, capacitors at -20 % / -10 %, kea 1.3", {"rload": 13.3}, {"cloc": "13.9u", "c100": "14.2u", "kea": 1.3}),
                        ("0.3 A, nominal capacitors, kea 1, C143 not fitted", {"rload": 13.3}, {"cff": "1f"}),
                        ("0.3 A, capacitors at -20 % / -10 %, kea 1, C143 not fitted", {"rload": 13.3}, {"cloc": "13.9u", "c100": "14.2u", "cff": "1f"}),
                        ("0.3 A, nominal capacitors, kea 0.68, C143 not fitted", {"rload": 13.3}, {"kea": 0.68, "cff": "1f"}),
                        ("0.3 A, nominal capacitors, kea 1, C143 47 pF", {"rload": 13.3}, {"cff": "47p"}),
                        ("0.3 A, capacitors at -20 % / -10 %, kea 1.3, C143 47 pF", {"rload": 13.3}, {"cloc": "13.9u", "c100": "14.2u", "kea": 1.3, "cff": "47p"})):
        w = run("loop", "loop_ac", p, dp)
        f = w["frequency"]
        T = w["tr"] + 1j * w["ti"]
        mag = 20 * np.log10(np.abs(T))
        ph = np.degrees(np.unwrap(np.angle(T)))
        i = int(np.argmax(mag < 0))
        fc = float(np.interp(0, [mag[i], mag[i - 1]], [f[i], f[i - 1]])) if i > 0 else None
        pm = float(np.interp(fc, f, ph)) + 180 if fc else None
        while pm is not None and pm > 180:
            pm -= 360
        j = np.where(np.diff(np.sign(ph + 180)) != 0)[0]
        gm = float(-np.interp(f[j[0]], f, mag)) if len(j) else None
        R.setdefault("buck_loop", {})[name] = {"crossover_khz": round(fc / 1e3, 1) if fc else None, "phase_margin_deg": round(pm, 1) if pm is not None else None,
                                               "gain_margin_db": round(gm, 1) if gm is not None else None}
        ax[0].semilogx(f, mag, label=name); ax[1].semilogx(f, ph)
    ax[0].set_ylabel("|T| dB"); ax[1].set_ylabel("phase deg"); ax[1].set_xlabel("Hz"); ax[0].legend(fontsize=7); ax[0].grid(True, which="both"); ax[1].grid(True, which="both")
    ax[0].set_title("Buck loop gain (averaged model after TI SLUAAG4)")
    fig.savefig(outdir / "loop.png", dpi=110, bbox_inches="tight"); plt.close(fig)

    # (d) brown-out
    w = run("brownout", "brownout")
    t = w["time"]
    en = w["v(xu8.en)"] > 0.5
    R["brownout"] = {
        "at_4p2v_source: 3v3_min": round(float(window(w["v(v33)"], t, 27e-3, 44e-3).min()), 3), "at_4p2v_source: 4v_reg_min": round(float(window(w["v(v4)"], t, 27e-3, 44e-3).min()), 3),
        "at_3p9v_source: 3v3_min": round(float(window(w["v(v33)"], t, 52e-3, 69e-3).min()), 3), "at_3p9v_source: 4v_reg_min": round(float(window(w["v(v4)"], t, 52e-3, 69e-3).min()), 3),
        "at_3p3v_source: 3v3_min": round(float(window(w["v(v33)"], t, 92e-3, 109e-3).min()), 3),
        "efuse_enable_transitions": int(np.sum(np.diff(en.astype(int)) != 0)),
        "3v3_after_recovery": round(at(w["v(v33)"], t, 158e-3), 3),
    }
    fig, ax = plt.subplots(figsize=(9, 4))
    for vec in ("v(vbus)", "v(vprot)", "v(v4)", "v(v33)", "v(vled)"):
        ax.plot(t * 1e3, w[vec], label=vec, lw=0.9)
    ax.plot(t * 1e3, w["v(xu8.en)"], label="eFuse enabled", lw=0.6)
    ax.set_xlabel("ms"); ax.set_ylabel("V"); ax.legend(fontsize=7); ax.grid(True); ax.set_title("Brown-out: source 5.0 -> 4.2 -> 3.9 -> 3.3 -> 5.0 V, 120 mA on 3V3, LEDs 150 mA")
    fig.savefig(outdir / "brownout.png", dpi=110, bbox_inches="tight"); plt.close(fig)

    # (c) faults
    for name, dp in (("short applied to the running LED rail", {"ten": "6m", "tsh": "14m"}), ("LED rail enabled into a short", {"ten": "6m", "tsh": 0})):
        w = run("fault_led", "fault_led", None, dp)
        t = w["time"]
        t0 = 14e-3 if "running" in name else 6e-3
        R.setdefault("fault_led_rail", {})[name] = {
            "short_current_peak_a": round(float(np.max(np.abs(window(w["i(lsh)"], t, t0, 24e-3)))), 3),
            "short_current_settled_a": round(float(np.mean(np.abs(window(w["i(lsh)"], t, 22e-3, 24e-3)))), 3),
            "4v_reg_min": round(float(window(w["v(v4)"], t, t0, 24e-3).min()), 3), "3v3_min": round(float(window(w["v(v33)"], t, t0, 24e-3).min()), 3),
            "input_current_peak_a": round(float(np.max(np.abs(window(w["i(vsrc)"], t, t0, 24e-3)))), 3),
        }
    w = run("fault_3v3", "fault_3v3", drop=("i(S33)",))
    t = w["time"]
    R["fault_3v3_short"] = {"4v_reg_min": round(float(window(w["v(v4)"], t, 8e-3, 14e-3).min()), 3), "input_current_peak_a": round(float(np.max(np.abs(window(w["i(vsrc)"], t, 8e-3, 14e-3)))), 3),
                            "input_current_during_short_a": round(float(np.mean(np.abs(window(w["i(vsrc)"], t, 12e-3, 14e-3)))), 3),
                            "3v3_after_release": round(at(w["v(v33)"], t, 21e-3), 3)}
    # C125 and C144 lose capacitance with bias: at 20 V both are taken at about half [ASSUMED]
    for name, dp, p in (("5 V source", {"va": 5, "vb": 5}, {}), ("6 V source", {"va": 6, "vb": 6}, {}),
                        ("20 V source", {"va": 20, "vb": 20}, {"c125": "0.5u", "csn": "2.4u"}),
                        ("5 V source, R187/C144 not fitted", {"va": 5, "vb": 5}, {"rsn": "1meg"}),
                        ("6 V source, R187/C144 not fitted", {"va": 6, "vb": 6}, {"rsn": "1meg"}),
                        ("20 V source, R187/C144 not fitted", {"va": 20, "vb": 20}, {"c125": "0.5u", "rsn": "1meg"})):
        w = run("ovp", "overvoltage", p, dp)
        R.setdefault("wrong_source", {})[name] = {"vbus_max": round(float(w["v(vbus)"].max()), 2), "efuse_input_max": round(float(w["v(vfused)"].max()), 2),
                                                  "inrush_peak_a": round(float(np.max(np.abs(w["i(vsrc)"]))), 2),
                                                  "vprot_max": round(float(w["v(vprot)"].max()), 3), "4v_reg_max": round(float(w["v(v4)"].max()), 3),
                                                  "3v3_max": round(float(w["v(v33)"].max()), 3), "efuse_ever_enabled": bool((w["v(xu8.en)"] > 0.5).any())}
    try:
        w = run("ovp", "overvoltage", {}, {"va": 5, "vb": 6, "tb": "60m", "tc": "70m"})
        t = w["time"]
        R["wrong_source"]["6 V surge for 10 ms while running"] = {"vprot_max": round(float(w["v(vprot)"].max()), 3), "4v_reg_max": round(float(w["v(v4)"].max()), 3),
                                                                 "3v3_min_during_and_after": round(float(window(w["v(v33)"], t, 60e-3, 130e-3).min()), 3),
                                                                 "3v3_at_end": round(at(w["v(v33)"], t, 129e-3), 3)}
    except SystemExit as e:
        R["wrong_source"]["6 V surge for 10 ms while running"] = {"error": str(e)}
    (outdir / "results.json").write_text(json.dumps(R, indent=1) + "\n")
    print(json.dumps(R, indent=1))


if __name__ == "__main__":
    main()
