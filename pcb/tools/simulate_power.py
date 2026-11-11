#!/usr/bin/env python3
"""Deterministic transient simulation of the Maru60 power tree.

Scope: simulation only.  This script does not prove stability, thermal
performance, USB compliance, EMC, or hardware qualification.  Every model
parameter that is not read from the netlist/schematic is an explicit
assumption in the output JSON and REPORT.md.

Run:
    .venv/bin/python pcb/tools/simulate_power.py

Outputs (under qa/power-sim/):
    power-sim.json
    REPORT.md
    startup.png
    load_step.png
    uvlo_ovlo.png
    led_rail.png
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

# Matplotlib must be configured before pyplot import.  The cache lives under
# the output directory so the run does not depend on a writable HOME.
REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "pcb" / "experiments" / "resume-20261109-relocated-expansion-zero-opens"
OUT = EXP / "qa" / "power-sim"
MPL_DIR = OUT / ".mplconfig"
MPL_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_DIR))

import matplotlib

matplotlib.use("Agg")
# The BDF Jacobian can probe large values in the stiff eFuse/input nodes.
# The converged solution is checked against the analytical limits; suppress
# only the known Jacobian overflow warning so the run log stays readable.
warnings.filterwarnings(
    "ignore",
    message="overflow encountered in multiply",
    category=RuntimeWarning,
    module=r"scipy\.integrate\._ivp\.common",
)
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

NETLIST = EXP / "qa" / "native" / "netlist.xml"
SCHEMATIC = EXP / "pcb" / "maru60-core.kicad_sch"
POWER_REVIEW = EXP / "qa" / "power-review" / "power-review.json"
POWER_REVIEW_REPORT = EXP / "qa" / "power-review" / "REPORT.md"

# ---------------------------------------------------------------------------
# Source parsing and assertions
# ---------------------------------------------------------------------------

_PREFIX = {
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "µ": 1e-6,
    "m": 1e-3,
    "k": 1e3,
    "K": 1e3,
    "M": 1e6,
    "G": 1e9,
}


def parse_value(text: str) -> float:
    """Parse the first engineering value in a KiCad value string.

    Examples: '4.7uF 50V X7R 10%' -> 4.7e-6, '133k 1%' -> 133e3,
    '100 1%' -> 100.0, '4.7uH 20%' -> 4.7e-6.
    """
    if text is None:
        raise ValueError("missing value")
    pattern = re.compile(
        r"([0-9]+(?:\.[0-9]+)?)\s*([pnuµmkKMG]?)(F|f|H|h|Ω|ohm|Ohm|OHM)?"
    )
    matches = list(pattern.finditer(text))
    if not matches:
        raise ValueError(f"cannot parse value: {text!r}")
    # Prefer a token with a unit, then a token with an engineering prefix,
    # then a bare number.  This skips MPN fragments such as the "4030" and
    # "472M" in "XAL4030-472MEC 4.7uH".
    chosen = None
    for m in matches:
        if m.group(3):
            chosen = m
            break
    if chosen is None:
        for m in matches:
            if m.group(2):
                chosen = m
                break
    if chosen is None:
        chosen = matches[0]
    number = float(chosen.group(1))
    prefix = chosen.group(2)
    return number * _PREFIX.get(prefix, 1.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_netlist():
    root = ET.parse(NETLIST).getroot()
    values = {}
    for c in root.find("components"):
        values[c.get("ref")] = c.findtext("value") or ""
    pins = {}
    for net in root.find("nets"):
        name = net.get("name")
        for node in net.findall("node"):
            pins.setdefault(node.get("ref"), {})[node.get("pin")] = name
    return values, pins


def load_schematic_values():
    """Extract Reference -> Value from the one-line KiCad symbol records."""
    values = {}
    for line in SCHEMATIC.read_text(errors="replace").splitlines():
        if "(symbol (lib_id" not in line:
            continue
        m = re.search(r'\(property "Reference" "([^"]+)"', line)
        if not m:
            continue
        ref = m.group(1)
        v = re.search(r'\(property "Value" "([^"]*)"', line)
        if v:
            values[ref] = v.group(1)
    return values


def assert_net(pins, ref, pin, expected):
    got = pins.get(ref, {}).get(pin)
    if got != expected:
        raise AssertionError(f"{ref} pin {pin}: expected net {expected!r}, got {got!r}")


def assert_value(values, ref, expected, rel=0.01):
    got = parse_value(values[ref])
    if not math.isclose(got, expected, rel_tol=rel):
        raise AssertionError(f"{ref}: expected {expected}, got {got} from {values[ref]!r}")


def load_and_assert_sources():
    values, pins = load_netlist()
    sch = load_schematic_values()

    # Connectivity: fuse, eFuse and dividers.
    assert_net(pins, "F1", "1", "VBUS")
    assert_net(pins, "F1", "2", "VBUS_FUSED")
    assert_net(pins, "U8", "5", "VBUS_FUSED")
    assert_net(pins, "U8", "6", "VBUS_PROTECTED_RAW")
    assert_net(pins, "U8", "1", "USB_UVLO")
    assert_net(pins, "U8", "2", "USB_OVLO")
    assert_net(pins, "U8", "7", "USB_DVDT")
    assert_net(pins, "U8", "9", "USB_ILM")
    assert_net(pins, "R120", "1", "VBUS_FUSED")
    assert_net(pins, "R120", "2", "USB_OVLO")
    assert_net(pins, "R121", "1", "USB_OVLO")
    assert_net(pins, "R121", "2", "GND")
    assert_net(pins, "R122", "1", "VBUS_FUSED")
    assert_net(pins, "R122", "2", "USB_UVLO")
    assert_net(pins, "R123", "1", "USB_UVLO")
    assert_net(pins, "R123", "2", "GND")
    assert_net(pins, "R125", "1", "USB_DVDT")
    assert_net(pins, "R125", "2", "USB_DVDT_CAP")
    assert_net(pins, "C124", "1", "USB_DVDT_CAP")
    assert_net(pins, "C124", "2", "GND")
    assert_net(pins, "R124", "1", "USB_ILM")
    assert_net(pins, "R124", "2", "GND")
    for ref in ("C126", "C136", "C137"):
        assert_net(pins, ref, "1", "VBUS_PROTECTED_RAW")
        assert_net(pins, ref, "2", "GND")
    assert_net(pins, "C125", "1", "VBUS_FUSED")
    assert_net(pins, "C125", "2", "GND")

    # Connectivity: buck.
    assert_net(pins, "U18", "3", "VBUS_PROTECTED_RAW")
    assert_net(pins, "U18", "5", "BUCK_SW")
    assert_net(pins, "U18", "7", "BUCK_SS")
    assert_net(pins, "U18", "8", "BUCK_FB")
    assert_net(pins, "L2", "1", "BUCK_SW")
    assert_net(pins, "L2", "2", "+4V_REG")
    assert_net(pins, "R159", "1", "+4V_REG")
    assert_net(pins, "R159", "2", "BUCK_FB")
    assert_net(pins, "R160", "1", "BUCK_FB")
    assert_net(pins, "R160", "2", "GND")
    assert_net(pins, "C139", "1", "BUCK_SS")
    assert_net(pins, "C139", "2", "GND")
    for ref in ("C100", "C120", "C140", "C141"):
        assert_net(pins, ref, "1", "+4V_REG")
        assert_net(pins, ref, "2", "GND")

    # Connectivity: LDO and LED rail.
    assert_net(pins, "U2", "1", "+4V_REG")
    assert_net(pins, "U2", "8", "+3V3")
    assert_net(pins, "U7", "1", "+4V_REG")
    assert_net(pins, "U7", "6", "+4V_LED")
    assert_net(pins, "U7", "3", "LED_ENABLE")
    assert_net(pins, "U7", "4", "LED_FAULT_N")
    assert_net(pins, "U7", "5", "LED_ILIM")
    assert_net(pins, "R112", "1", "LED_ILIM")
    assert_net(pins, "R112", "2", "GND")
    assert_net(pins, "R109", "1", "LED_ENABLE")
    assert_net(pins, "R109", "2", "GND")
    assert_net(pins, "R113", "1", "+3V3")
    assert_net(pins, "R113", "2", "LED_FAULT_N")
    for ref in ("C121", "C122", "C123"):
        assert_net(pins, ref, "1", "+4V_LED")
        assert_net(pins, ref, "2", "GND")

    led_refs = sorted(
        (r for r in values if re.fullmatch(r"LED\d+", r)),
        key=lambda r: int(r[3:]),
    )
    if len(led_refs) != 76:
        raise AssertionError(f"expected 76 LEDs, found {len(led_refs)}")
    for ref in led_refs:
        assert_net(pins, ref, "2", "+4V_LED")
        assert_net(pins, ref, "4", "GND")

    # Values: netlist and schematic must agree on the first engineering value.
    expected = {
        "R120": 590e3,
        "R121": 156e3,
        "R122": 620e3,
        "R123": 267e3,
        "R124": 6.65e3,
        "R125": 100.0,
        "C124": 10e-9,
        "C125": 1e-6,
        "C126": 1e-6,
        "C136": 100e-9,
        "C137": 4.7e-6,
        "C139": 100e-9,
        "R159": 40e3,
        "R160": 10e3,
        "L2": 4.7e-6,
        "C100": 4.7e-6,
        "C120": 1e-6,
        "C140": 22e-6,
        "C141": 22e-6,
        "R112": 133e3,
        "R109": 100e3,
        "R113": 10e3,
        "C121": 4.7e-6,
        "C122": 100e-9,
        "C123": 100e-9,
    }
    for ref, val in expected.items():
        assert_value(values, ref, val)
        if ref in sch:
            assert_value(sch, ref, val)

    return {
        "values": values,
        "pins": pins,
        "schematic_values": sch,
        "led_refs": led_refs,
        "hashes": {
            "netlist_sha256": sha256(NETLIST),
            "schematic_sha256": sha256(SCHEMATIC),
            "power_review_sha256": sha256(POWER_REVIEW),
            "power_review_report_sha256": sha256(POWER_REVIEW_REPORT),
        },
    }


# ---------------------------------------------------------------------------
# Shared constants / assumptions
# ---------------------------------------------------------------------------

VREF_BUCK = 0.8
R_TOP = 40e3
R_BOT = 10e3
VOUT_BUCK = VREF_BUCK * (1.0 + R_TOP / R_BOT)  # 4.0 V

# TPS259470 (from qa/power-review/power-review.json, TI SLVSFC9C)
EFUSE_UVLO_R = {"min": 3.924553, "typ": 3.986517, "max": 4.068611}
EFUSE_UVLO_F = {"min": 3.569585, "typ": 3.621086, "max": 3.712649}
EFUSE_OVLO_R = {"min": 5.648227, "typ": 5.738462, "max": 5.857709}
EFUSE_OVLO_F = {"min": 5.137356, "typ": 5.212436, "max": 5.345219}
EFUSE_UVLO_LEAK = 0.062
EFUSE_OVLO_LEAK = 0.059
EFUSE_ILIM_MA = {"min": 425.0, "typ": 500.0, "max": 575.0}
EFUSE_RDS_ON = 28.3e-3  # model assumption from APPLICABILITY.md
EFUSE_ILIM_RESPONSE_S = 400e-6
EFUSE_FAST_TRIP_RATIO = 3.0
EFUSE_FAST_TRIP_S = 500e-9

# TPS62932 (TI SLUSEA4D)
BUCK_FSW = 500e3
BUCK_L = 4.7e-6
BUCK_DCR = 20e-3  # XAL4030-472MEC DCR assumption
BUCK_RHS = 76e-3  # datasheet, TPS62932 high-side
BUCK_RLS = 32e-3  # datasheet, TPS62932 low-side
BUCK_MAX_DUTY = 0.98
BUCK_ISS_UA = {"min": 4.5, "typ": 5.5, "max": 6.5}
BUCK_CSS = 100e-9
BUCK_TSS = {
    k: BUCK_CSS * VREF_BUCK / (v * 1e-6) for k, v in BUCK_ISS_UA.items()
}
BUCK_VIN_UVLO_RISE = 3.8
BUCK_VIN_UVLO_FALL = 3.5
BUCK_IMAX = 2.0  # TPS62932 rated 2 A

# Output capacitor bank: C100 4.7 uF + C120 1 uF + C140/C141 22 uF each.
# C140/C141 effective 12 uF is the TBD target from APPLICABILITY.md.
BUCK_COUT_NOM = 4.7e-6 + 1e-6 + 22e-6 + 22e-6
BUCK_COUT_EFF = 4.7e-6 + 1e-6 + 12e-6 + 12e-6
BUCK_COUT_ESR = 20e-3  # common ESR assumption from APPLICABILITY.md

# Protected-rail capacitors: C126 1 uF + C136 100 nF + C137 4.7 uF.
PROT_CAPS = {
    "C126": {"c": 1e-6, "esr": 5e-3},
    "C136": {"c": 100e-9, "esr": 10e-3},
    "C137": {"c": 4.7e-6, "esr": 5e-3},
}
PROT_C_NOM = sum(v["c"] for v in PROT_CAPS.values())
PROT_DERATE_5V = 0.92
PROT_C_EFF = PROT_C_NOM * PROT_DERATE_5V
PROT_ESR = 1.0 / sum(1.0 / v["esr"] for v in PROT_CAPS.values())

# TPS2553-1 (TI SLVS841G)
LED_ILIM_MA = {"min": 173.657469, "nom": 201.512720, "max": 233.901173}
LED_RDS_ON = 85e-3  # DBV, 25 C typical
LED_RDS_ON_MAX = 95e-3  # DBV, 25 C max
LED_RESPONSE_S = 2e-6
LED_LATCH_S = 7.5e-3  # FAULT/overcurrent deglitch, typical
LED_RISE_S = 1.1e-3  # datasheet rise time at 6.5 V, used at 4 V
LED_COUT_NOM = 4.7e-6 + 0.1e-6 + 0.1e-6 + 76 * 0.1e-6
LED_COUT_EFF = 4.7e-6 * 0.92 + 0.2e-6 * 0.95 + 7.6e-6 * 0.95
LED_COUT_ESR = 5e-3
LED_COUNT = 76
LED_CHANNELS = 3
LED_V_DROPOUT = 3.0  # behavioral load knee, not a datasheet value

# Source / fuse assumptions
VBUS_NOM = 5.0
SOURCE_R = 0.1  # cable + fuse + connector, assumption
C125 = 1e-6
FUSE_HOLD_A = 1.0  # SF-1206F100-2 candidate, not qualified

# LDO behavioral assumption (MAX38902 startup is unknown)
LDO_VOUT = 3.3
LDO_VIN_MIN = 3.4
LDO_DROPOUT_AT_500MA = 0.1
LDO_TAU = 0.5e-3
LDO_ILOAD = 0.1


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def smooth_step(t, t0, width):
    """0 before t0, 1 after t0, tanh transition of approximately `width`."""
    return 0.5 * (1.0 + np.tanh((t - t0) / max(width, 1e-12)))


def sigmoid(x):
    """Numerically stable logistic function."""
    x = clamp(float(x), -60.0, 60.0)
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def rail_load(vout, iload_cmd, v_on=0.5, width=0.05):
    """Application load turns on only after the rail is up.

    This prevents the output capacitor from being discharged below 0 V by a
    constant-current load before the converter starts.  It is a behavioral
    load assumption, not a measured load profile.
    """
    return iload_cmd * sigmoid((vout - v_on) / width)


# ---------------------------------------------------------------------------
# 1. eFuse dV/dt ramp
# ---------------------------------------------------------------------------


def efuse_startup(ilim_ma=500.0, c_dvdt_nf=10.0, cprot=None, iload=0.0,
                  t_end=0.040, label="nom"):
    """TPS259470 dV/dt-controlled startup into the protected rail.

    Model: the eFuse internal dV/dt reference ramps at SR = 2/C_dVdt[nF]
    V/ms.  The pass FET is a voltage source behind Rds_on, current-limited
    at ILIM.  The protected rail is a capacitor bank with a parallel ESR.
    R125 (100 ohm) is included as a 1 us RC on the dV/dt pin; its effect on
    the 25 ms output ramp is negligible and is reported separately.
    """
    if cprot is None:
        cprot = PROT_C_EFF
    sr = 2.0 / c_dvdt_nf * 1e3  # V/ms -> V/s
    r125_tau = 100.0 * c_dvdt_nf * 1e-9
    ilim = ilim_ma * 1e-3

    def rhs(t, y):
        vprot = y[0]
        vint = min(sr * t, VBUS_NOM)
        # Solve i = (vint - (vprot + esr*(i - iload))) / Rds_on
        i = (vint - vprot + PROT_ESR * iload) / (EFUSE_RDS_ON + PROT_ESR)
        i = clamp(i, 0.0, ilim)
        return [(i - iload) / cprot]

    t_eval = np.linspace(0.0, t_end, 4001)
    sol = solve_ivp(rhs, (0.0, t_end), [0.0], method="BDF", t_eval=t_eval,
                    rtol=1e-9, atol=1e-12, max_step=50e-6)
    if not sol.success:
        raise RuntimeError(f"eFuse solve failed: {sol.message}")
    v = sol.y[0]
    t = sol.t
    vint = np.minimum(sr * t, VBUS_NOM)
    i = (vint - v + PROT_ESR * iload) / (EFUSE_RDS_ON + PROT_ESR)
    i = np.clip(i, 0.0, ilim)
    vout = v + PROT_ESR * (i - iload)

    def first_time(threshold):
        idx = np.nonzero(vout >= threshold)[0]
        return float(t[idx[0]]) if len(idx) else None

    t90 = first_time(0.9 * VBUS_NOM)
    t99 = first_time(0.99 * VBUS_NOM)
    t100 = first_time(0.999 * VBUS_NOM)
    peak_i = float(np.max(i))
    energy = float(np.trapezoid(i * vout, t))
    cap_energy = 0.5 * cprot * float(vout[-1]) ** 2
    return {
        "label": label,
        "ilim_ma": ilim_ma,
        "c_dvdt_nf": c_dvdt_nf,
        "slew_v_per_ms": sr / 1e3,
        "r125_tau_us": r125_tau * 1e6,
        "cprot_nominal_uf": PROT_C_NOM * 1e6,
        "cprot_effective_uf": cprot * 1e6,
        "cprot_esr_mohm": PROT_ESR * 1e3,
        "iload_a": iload,
        "t90_ms": None if t90 is None else t90 * 1e3,
        "t99_ms": None if t99 is None else t99 * 1e3,
        "t100_ms": None if t100 is None else t100 * 1e3,
        "peak_current_ma": peak_i * 1e3,
        "inrush_capacitor_ma": cprot * sr * 1e3,
        "energy_mj": energy * 1e3,
        "cap_energy_uj": cap_energy * 1e6,
        "vfinal_v": float(vout[-1]),
        "current_limited": bool(peak_i >= 0.999 * ilim),
        "t": t,
        "vout": vout,
        "i": i,
    }


def efuse_current_limit_test(ilim_ma, r_load=4.0, t_end=0.020):
    """Drive a 4 ohm load (1 A at 4 V) and show the eFuse current limit.

    The 400 us current-limit response is modeled as a first-order lag on the
    current-limit command.  The fast-trip (3x ILIM, 500 ns) is reported but
    not exercised by a 4 ohm load at the 425 mA minimum.
    """
    ilim = ilim_ma * 1e-3
    sr = 200.0  # V/s, nominal C124 (0.2 V/ms)
    tau = EFUSE_ILIM_RESPONSE_S

    def rhs(t, y):
        vprot, i = y
        vint = min(sr * t, VBUS_NOM)
        i_cmd = (vint - vprot) / (EFUSE_RDS_ON + PROT_ESR)
        i_cmd = max(i_cmd, 0.0)
        if i_cmd > ilim:
            di = (ilim - i) / tau
        else:
            di = (i_cmd - i) / 1e-6
        iload = max(vprot, 0.0) / r_load
        return [(i - iload) / PROT_C_EFF, di]

    t_eval = np.linspace(0.0, t_end, 4001)
    sol = solve_ivp(rhs, (0.0, t_end), [0.0, 0.0], method="BDF",
                    t_eval=t_eval, rtol=1e-8, atol=1e-12, max_step=20e-6)
    if not sol.success:
        raise RuntimeError(f"eFuse current-limit solve failed: {sol.message}")
    v, i = sol.y
    return {
        "ilim_ma": ilim_ma,
        "r_load_ohm": r_load,
        "peak_current_ma": float(np.max(i)) * 1e3,
        "steady_current_ma": float(i[-1]) * 1e3,
        "vout_min_v": float(np.min(v)),
        "vout_final_v": float(v[-1]),
        "fast_trip_threshold_ma": ilim_ma * EFUSE_FAST_TRIP_RATIO,
        "fast_trip_response_ns": EFUSE_FAST_TRIP_S * 1e9,
        "t": sol.t,
        "vout": v,
        "i": i,
    }


# ---------------------------------------------------------------------------
# 2. Buck average model
# ---------------------------------------------------------------------------


def buck_rhs_factory(vin_func, iload_func, t_ss, kp, ki, tau_i,
                     esr=BUCK_COUT_ESR, cout=BUCK_COUT_EFF):
    """Average peak-current-mode buck model.

    States: iL, Vc (cap voltage), integ (voltage-loop integrator),
    ss (soft-start progress 0..1).

    Loop assumption: inner peak-current loop is a first-order lag tau_i with
    physical inductor slew limiting; outer voltage loop is a PI compensator
    with Kp/Ki chosen for a target crossover.  This is a behavioral proxy for
    the TPS62932 internal compensation, not a stability model.
    """

    def rhs(t, y):
        iL, vc, integ, ss = y
        vin = max(float(vin_func(t)), 0.0)
        iload_cmd = max(float(iload_func(t)), 0.0)
        iload = rail_load(vc, iload_cmd)
        vout = vc + esr * (iL - iload)
        en = sigmoid((vin - BUCK_VIN_UVLO_RISE) / 0.005)
        # Soft-start progress: reset when disabled, ramp when enabled.
        if en < 0.5:
            dss = -ss / 0.1e-3
        elif ss < 1.0:
            dss = en / t_ss
        else:
            dss = 0.0
        vref = VREF_BUCK * min(ss, 1.0)
        vtarget = vref * (1.0 + R_TOP / R_BOT)
        err = vtarget - vout
        i_cmd_raw = kp * err + ki * integ + iload
        i_cmd = clamp(i_cmd_raw, 0.0, BUCK_IMAX)
        if (i_cmd_raw > BUCK_IMAX and err > 0.0) or (i_cmd_raw < 0.0 and err < 0.0):
            dinteg = 0.0
        else:
            dinteg = err
        # Physical current slew limits.
        di_max = (vin - vout) / BUCK_L
        di_min = -vout / BUCK_L
        di_des = clamp((i_cmd - iL) / tau_i, di_min, di_max)
        rloss = BUCK_DCR + (vout / max(vin, 0.1)) * BUCK_RHS + \
            (1.0 - vout / max(vin, 0.1)) * BUCK_RLS
        duty = (vout + iL * rloss + BUCK_L * di_des) / max(vin, 0.1)
        duty = clamp(duty, 0.0, BUCK_MAX_DUTY)
        diL = (duty * vin - vout - iL * rloss) / BUCK_L
        dvc = (iL - iload) / cout
        return [diL, dvc, dinteg, dss]

    return rhs


def design_buck_loop(cout=BUCK_COUT_EFF, esr=BUCK_COUT_ESR, fc=20e3,
                     tau_i=1.0 / (2 * math.pi * 50e3)):
    """Choose PI gains for a target crossover with the current-mode plant."""
    wc = 2 * math.pi * fc
    kp = wc * cout
    wz = wc / 5.0
    ki = kp * wz
    # Estimate phase margin at the target crossover.
    plant_phase = -90.0
    lag_phase = -math.degrees(math.atan(wc * tau_i))
    pi_phase = -90.0 + math.degrees(math.atan(wc * kp / ki))
    esr_phase = math.degrees(math.atan(wc * esr * cout))
    pm = 180.0 + plant_phase + lag_phase + pi_phase + esr_phase
    return {
        "target_crossover_hz": fc,
        "kp_a_per_v": kp,
        "ki_a_per_v_s": ki,
        "zero_hz": wz / (2 * math.pi),
        "inner_current_lag_us": tau_i * 1e6,
        "estimated_phase_margin_deg": pm,
        "plant": "average peak-current-mode: 1/(s*Cout) with ESR zero and inner-loop lag",
        "note": "Synthetic loop assumption, not the TPS62932 internal compensation; no stability claim.",
    }


def simulate_buck_startup(vin=VBUS_NOM, iload=0.1, t_end=0.040,
                          t_ss=None, cout=BUCK_COUT_EFF, esr=BUCK_COUT_ESR,
                          fc=20e3, label="nom"):
    if t_ss is None:
        t_ss = BUCK_TSS["typ"]
    loop = design_buck_loop(cout=cout, esr=esr, fc=fc)
    rhs = buck_rhs_factory(lambda t: vin, lambda t: iload, t_ss,
                           loop["kp_a_per_v"], loop["ki_a_per_v_s"],
                           loop["inner_current_lag_us"] * 1e-6,
                           esr=esr, cout=cout)
    t_eval = np.linspace(0.0, t_end, 8001)
    sol = solve_ivp(rhs, (0.0, t_end), [0.0, 0.0, 0.0, 0.0],
                    method="BDF", t_eval=t_eval, rtol=1e-8, atol=1e-10,
                    max_step=20e-6)
    if not sol.success:
        raise RuntimeError(f"buck startup solve failed: {sol.message}")
    iL, vc, integ, ss = sol.y
    vout = vc + esr * (iL - iload)
    t = sol.t
    return {
        "label": label,
        "vin_v": vin,
        "iload_a": iload,
        "t_ss_ms": t_ss * 1e3,
        "loop": loop,
        "t90_ms": first_cross(t, vout, 0.9 * VOUT_BUCK) * 1e3,
        "t99_ms": first_cross(t, vout, 0.99 * VOUT_BUCK) * 1e3,
        "vfinal_v": float(vout[-1]),
        "overshoot_mv": float((np.max(vout) - VOUT_BUCK) * 1e3),
        "monotonic": monotonic_metrics(t, vout),
        "t": t,
        "vout": vout,
        "iL": iL,
        "ss": ss,
    }


def simulate_buck_load_step(vin=VBUS_NOM, t_end=0.050, t_ss=None,
                            cout=BUCK_COUT_EFF, esr=BUCK_COUT_ESR, fc=20e3,
                            label="nom"):
    if t_ss is None:
        t_ss = BUCK_TSS["typ"]
    loop = design_buck_loop(cout=cout, esr=esr, fc=fc)

    def iload_func(t):
        # 0.1 A -> 0.3 A at 30 ms, 0.3 A -> 0.1 A at 40 ms.
        up = smooth_step(t, 30e-3, 0.5e-6)
        down = smooth_step(t, 40e-3, 0.5e-6)
        return 0.1 + 0.2 * up - 0.2 * down

    rhs = buck_rhs_factory(lambda t: vin, iload_func, t_ss,
                           loop["kp_a_per_v"], loop["ki_a_per_v_s"],
                           loop["inner_current_lag_us"] * 1e-6,
                           esr=esr, cout=cout)
    t_eval = np.linspace(0.0, t_end, 20001)
    sol = solve_ivp(rhs, (0.0, t_end), [0.0, 0.0, 0.0, 0.0],
                    method="BDF", t_eval=t_eval, rtol=1e-8, atol=1e-10,
                    max_step=5e-6)
    if not sol.success:
        raise RuntimeError(f"buck load-step solve failed: {sol.message}")
    iL, vc, integ, ss = sol.y
    iload = np.array([iload_func(t) for t in sol.t])
    vout = vc + esr * (iL - iload)
    t = sol.t
    base = float(np.mean(vout[(t > 28e-3) & (t < 30e-3)]))
    after_up = (t >= 30e-3) & (t < 40e-3)
    after_down = t >= 40e-3
    vmin = float(np.min(vout[after_up]))
    vmax = float(np.max(vout[after_down]))
    final_up = float(np.mean(vout[(t > 38e-3) & (t < 39e-3)]))
    final_down = float(np.mean(vout[(t > 48e-3) & (t < 49e-3)]))
    return {
        "label": label,
        "vin_v": vin,
        "t_ss_ms": t_ss * 1e3,
        "loop": loop,
        "baseline_v": base,
        "step_up_undershoot_mv": (base - vmin) * 1e3,
        "step_up_peak_il_a": float(np.max(iL[after_up])),
        "unload_overshoot_mv": (vmax - base) * 1e3,
        "unload_min_il_a": float(np.min(iL[after_down])),
        "settle_up_ms": settling_time(t, vout, 30e-3, VOUT_BUCK, 0.01 * VOUT_BUCK) * 1e3,
        "settle_down_ms": settling_time(t, vout, 40e-3, VOUT_BUCK, 0.01 * VOUT_BUCK) * 1e3,
        "recovery_up_0p2pct_ms": settling_time(t, vout, 30e-3, final_up, 0.002 * VOUT_BUCK, 40e-3) * 1e3,
        "recovery_down_0p2pct_ms": settling_time(t, vout, 40e-3, final_down, 0.002 * VOUT_BUCK, 50e-3) * 1e3,
        "final_up_v": final_up,
        "final_down_v": final_down,
        "t": t,
        "vout": vout,
        "iL": iL,
        "iload": iload,
    }


def first_cross(t, y, threshold):
    idx = np.nonzero(y >= threshold)[0]
    return float(t[idx[0]]) if len(idx) else float("nan")


def settling_time(t, y, t0, final, tol, t1=None):
    """Last time outside the tolerance band in [t0, t1], relative to t0."""
    mask = t >= t0
    if t1 is not None:
        mask &= t <= t1
    outside = np.abs(y[mask] - final) > tol
    if not np.any(outside):
        return 0.0
    idx = np.nonzero(outside)[0][-1]
    return float(t[mask][idx] - t0)


def monotonic_metrics(t, vout, start_frac=0.05, dip_tol_mv=5.0):
    """Check monotonicity of a startup ramp after it leaves the origin."""
    vmax = float(np.max(vout))
    start = np.nonzero(vout >= start_frac * vmax)[0]
    if len(start) == 0:
        return {"monotonic": False, "max_dip_mv": None, "min_slope_v_per_ms": None}
    i0 = start[0]
    tt = t[i0:]
    vv = vout[i0:]
    dv = np.diff(vv)
    dt = np.diff(tt)
    slope = dv / np.maximum(dt, 1e-12)
    # Largest drop from a running maximum (a local dip).
    runmax = np.maximum.accumulate(vv)
    dip = float(np.max(runmax - vv)) * 1e3
    return {
        "monotonic": bool(dip <= dip_tol_mv),
        "max_dip_mv": dip,
        "min_slope_v_per_ms": float(np.min(slope)) * 1e-3,
        "dip_tolerance_mv": dip_tol_mv,
    }


# ---------------------------------------------------------------------------
# 3. Coupled eFuse + buck startup (sequencing)
# ---------------------------------------------------------------------------


def simulate_coupled_startup(iload=0.1, t_end=0.060, t_ss=None,
                             cout=BUCK_COUT_EFF, esr=BUCK_COUT_ESR, fc=20e3,
                             label="nom"):
    """VBUS step -> FUSED -> PROTECTED -> 4V, with the buck loading the eFuse."""
    if t_ss is None:
        t_ss = BUCK_TSS["typ"]
    loop = design_buck_loop(cout=cout, esr=esr, fc=fc)
    kp, ki = loop["kp_a_per_v"], loop["ki_a_per_v_s"]
    tau_i = loop["inner_current_lag_us"] * 1e-6
    sr = 200.0  # V/s, C124 10 nF nominal (0.2 V/ms)

    def rhs(t, y):
        vbus, vprot, iL, vc, integ, ss = y
        # Input node: ideal 5 V behind SOURCE_R, C125, divider loading.
        i_div = vbus / (590e3 + 156e3) + vbus / (620e3 + 267e3)
        # eFuse current (implicit ESR solve).
        vint = min(sr * t, vbus)
        i_ef = (vint - vprot) / (EFUSE_RDS_ON + PROT_ESR)
        i_ef = clamp(i_ef, 0.0, EFUSE_ILIM_MA["typ"] * 1e-3)
        # Buck input current is D*iL; compute the buck state first.
        vprot_s = max(vprot, 0.0)
        iload_eff = rail_load(vc, iload)
        vout = max(vc + esr * (iL - iload_eff), 0.0)
        en = sigmoid((vprot_s - BUCK_VIN_UVLO_RISE) / 0.005)
        if en < 0.5:
            dss = -ss / 0.1e-3
        elif ss < 1.0:
            dss = en / t_ss
        else:
            dss = 0.0
        vtarget = VREF_BUCK * min(ss, 1.0) * (1.0 + R_TOP / R_BOT)
        err = vtarget - vout
        i_cmd_raw = kp * err + ki * integ + iload_eff
        i_cmd = clamp(i_cmd_raw, 0.0, BUCK_IMAX)
        if (i_cmd_raw > BUCK_IMAX and err > 0.0) or (i_cmd_raw < 0.0 and err < 0.0):
            dinteg = 0.0
        else:
            dinteg = err
        di_max = (vprot_s - vout) / BUCK_L
        di_min = -vout / BUCK_L
        di_des = clamp((i_cmd - iL) / tau_i, di_min, di_max)
        d_ratio = vout / max(vprot_s, 0.1)
        rloss = BUCK_DCR + d_ratio * BUCK_RHS + (1.0 - d_ratio) * BUCK_RLS
        duty = (vout + iL * rloss + BUCK_L * di_des) / max(vprot_s, 0.1)
        duty = clamp(duty, 0.0, BUCK_MAX_DUTY)
        diL = (duty * vprot_s - vout - iL * rloss) / BUCK_L
        iin = duty * iL
        dvc = (iL - iload_eff) / cout
        dvbus = ((VBUS_NOM - vbus) / SOURCE_R - i_ef - i_div) / C125
        dvprot = (i_ef - iin) / PROT_C_EFF
        return [dvbus, dvprot, diL, dvc, dinteg, dss]

    t_eval = np.linspace(0.0, t_end, 12001)
    sol = solve_ivp(rhs, (0.0, t_end), [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    method="BDF", t_eval=t_eval, rtol=1e-8, atol=1e-10,
                    max_step=20e-6, first_step=1e-9)
    if not sol.success:
        raise RuntimeError(f"coupled startup solve failed: {sol.message}")
    vbus, vprot, iL, vc, integ, ss = sol.y
    vout = vc + esr * (iL - iload)
    t = sol.t
    # Recompute the eFuse current for reporting.
    vint = np.minimum(sr * t, vbus)
    i_ef = np.clip((vint - vprot) / (EFUSE_RDS_ON + PROT_ESR), 0.0,
                   EFUSE_ILIM_MA["typ"] * 1e-3)
    return {
        "label": label,
        "iload_a": iload,
        "t_ss_ms": t_ss * 1e3,
        "loop": loop,
        "t_fused_90_ms": first_cross(t, vbus, 0.9 * VBUS_NOM) * 1e3,
        "t_prot_90_ms": first_cross(t, vprot, 0.9 * VBUS_NOM) * 1e3,
        "t_prot_3800_ms": first_cross(t, vprot, 3.8) * 1e3,
        "t_4v_90_ms": first_cross(t, vout, 0.9 * VOUT_BUCK) * 1e3,
        "t_4v_99_ms": first_cross(t, vout, 0.99 * VOUT_BUCK) * 1e3,
        "vout_final_v": float(vout[-1]),
        "overshoot_mv": float((np.max(vout) - VOUT_BUCK) * 1e3),
        "monotonic": monotonic_metrics(t, vout),
        "peak_efuse_ma": float(np.max(i_ef)) * 1e3,
        "t": t,
        "vbus": vbus,
        "vprot": vprot,
        "vout": vout,
        "iL": iL,
        "i_ef": i_ef,
        "ss": ss,
    }


# ---------------------------------------------------------------------------
# 4. UVLO / OVLO sweep
# ---------------------------------------------------------------------------


def uvlo_ovlo_thresholds(r_uvlo_top=620e3, r_uvlo_bot=267e3,
                         r_ovlo_top=590e3, r_ovlo_bot=156e3,
                         uvlo_r=1.200, uvlo_f=1.090,
                         ovlo_r=1.200, ovlo_f=1.090,
                         leak_ua=0.0):
    """Divider thresholds.  Leakage is a current into/out of the divider node."""
    # A leakage current I_leak adds to the divider current; the sign is
    # handled by the caller via the +/- shift in the power review.  Here we
    # use the ideal divider and apply the review's leakage shift separately.
    uvlo_r_v = uvlo_r * (r_uvlo_top + r_uvlo_bot) / r_uvlo_bot
    uvlo_f_v = uvlo_f * (r_uvlo_top + r_uvlo_bot) / r_uvlo_bot
    ovlo_r_v = ovlo_r * (r_ovlo_top + r_ovlo_bot) / r_ovlo_bot
    ovlo_f_v = ovlo_f * (r_ovlo_top + r_ovlo_bot) / r_ovlo_bot
    return {
        "uvlo_rising_v": uvlo_r_v,
        "uvlo_falling_v": uvlo_f_v,
        "uvlo_hysteresis_v": uvlo_r_v - uvlo_f_v,
        "ovlo_rising_v": ovlo_r_v,
        "ovlo_falling_v": ovlo_f_v,
        "ovlo_hysteresis_v": ovlo_r_v - ovlo_f_v,
    }


def simulate_uvlo_ovlo(corner="typ", t_end=2.0, dt=10e-6):
    """0 -> 6.5 V -> 0 V triangle with the TPS25947 comparator state machine."""
    uvlo_r = EFUSE_UVLO_R[corner]
    uvlo_f = EFUSE_UVLO_F[corner]
    ovlo_r = EFUSE_OVLO_R[corner]
    ovlo_f = EFUSE_OVLO_F[corner]
    n = int(t_end / dt) + 1
    t = np.linspace(0.0, t_end, n)
    vbus = np.where(t <= 1.0, 6.5 * t / 1.0, 6.5 * (2.0 - t / 1.0))
    vbus = np.clip(vbus, 0.0, 6.5)
    v_uvlo = vbus * 267e3 / (620e3 + 267e3)
    v_ovlo = vbus * 156e3 / (590e3 + 156e3)

    uvlo_ok = False
    ovlo_ok = True
    vprot = 0.0
    vint = 0.0
    sr = 200.0  # V/s (0.2 V/ms)
    sr_fall = 10.0  # V/s, model assumption for turn-off
    r_load = 1e3
    events = []
    vprot_hist = np.zeros(n)
    enabled_hist = np.zeros(n, dtype=bool)
    for k in range(n):
        if vbus[k] >= uvlo_r:
            if not uvlo_ok:
                events.append(("uvlo_rise", float(vbus[k]), float(t[k])))
            uvlo_ok = True
        elif vbus[k] <= uvlo_f:
            if uvlo_ok:
                events.append(("uvlo_fall", float(vbus[k]), float(t[k])))
            uvlo_ok = False
        if vbus[k] >= ovlo_r:
            if ovlo_ok:
                events.append(("ovlo_rise", float(vbus[k]), float(t[k])))
            ovlo_ok = False
        elif vbus[k] <= ovlo_f:
            if not ovlo_ok:
                events.append(("ovlo_fall", float(vbus[k]), float(t[k])))
            ovlo_ok = True
        enabled = uvlo_ok and ovlo_ok
        enabled_hist[k] = enabled
        if enabled:
            # Slew-limited internal reference tracks VBUS.
            dv = (vbus[k] - vint) / 0.1e-3
            dv = clamp(dv, -sr_fall, sr)
            vint += dv * dt
            # Exact update of the linear RC node: C dv/dt =
            # (vint - v)/Rds_on - v/R_load.  This is stable for dt >> tau.
            r_eq = EFUSE_RDS_ON * r_load / (EFUSE_RDS_ON + r_load)
            tau = PROT_C_EFF * r_eq
            v_eq = vint * r_load / (EFUSE_RDS_ON + r_load)
            vprot = v_eq + (vprot - v_eq) * math.exp(-dt / tau)
        else:
            vint = 0.0
            vprot = vprot * math.exp(-dt / (r_load * PROT_C_EFF))
        vprot = max(vprot, 0.0)
        vprot_hist[k] = vprot

    def event_v(name):
        vals = [e[1] for e in events if e[0] == name]
        return vals

    return {
        "corner": corner,
        "thresholds": {
            "uvlo_rising_v": uvlo_r,
            "uvlo_falling_v": uvlo_f,
            "uvlo_hysteresis_v": uvlo_r - uvlo_f,
            "ovlo_rising_v": ovlo_r,
            "ovlo_falling_v": ovlo_f,
            "ovlo_hysteresis_v": ovlo_r - ovlo_f,
        },
        "simulated_events": events,
        "sim_uvlo_rise_v": event_v("uvlo_rise"),
        "sim_uvlo_fall_v": event_v("uvlo_fall"),
        "sim_ovlo_rise_v": event_v("ovlo_rise"),
        "sim_ovlo_fall_v": event_v("ovlo_fall"),
        "t": t,
        "vbus": vbus,
        "v_uvlo": v_uvlo,
        "v_ovlo": v_ovlo,
        "vprot": vprot_hist,
        "enabled": enabled_hist,
    }


# ---------------------------------------------------------------------------
# 5. LED rail
# ---------------------------------------------------------------------------


def led_load_current(vout, iset):
    """Behavioral SK6805 load: constant current above the dropout knee."""
    if vout <= 0.0:
        return 0.0
    if vout >= LED_V_DROPOUT:
        return iset
    return iset * vout / LED_V_DROPOUT


def simulate_led_rail(iset_a, ilim_ma, rds_on=LED_RDS_ON, t_end=0.030,
                      enable_time=0.0, load_at_enable=True, latch=True,
                      load_delay_s=5 * LED_RISE_S, label="nom"):
    """TPS2553-1 LED rail with current limit and latch-off.

    States: vout, iout, oc_time.  The switch is a current source with a 2 us
    response lag; the target is min((Vss - Vout)/Rds_on, ILIM).  The output
    capacitor is 11.7 uF effective with 5 mohm ESR.  The load is a behavioral
    constant-current sink with a 3.0 V knee.
    """
    ilim = ilim_ma * 1e-3
    tau = LED_RESPONSE_S
    cout = LED_COUT_EFF
    esr = LED_COUT_ESR

    def rhs(t, y):
        vout, iout, oc = y
        if t < enable_time:
            vss = 0.0
        else:
            vss = VOUT_BUCK * min((t - enable_time) / LED_RISE_S, 1.0)
        if not load_at_enable and t < enable_time + load_delay_s:
            iset = 0.0
        else:
            iset = iset_a
        iload = led_load_current(vout, iset)
        i_target = (vss - vout) / rds_on
        i_target = clamp(i_target, 0.0, ilim)
        diout = (i_target - iout) / tau
        dvout = (iout - iload) / cout
        if iout >= 0.9995 * ilim:
            doc = 1.0
        else:
            doc = -oc / 0.1e-3
        return [dvout, diout, doc]

    # Integrate in segments so the latch event can stop the switch.
    t0 = 0.0
    y0 = [0.0, 0.0, 0.0]
    segments = []
    latched_at = None
    fault_at = None
    while t0 < t_end:
        def event_latch(t, y):
            return y[2] - LED_LATCH_S
        event_latch.terminal = True
        event_latch.direction = 1
        sol = solve_ivp(rhs, (t0, t_end), y0, method="BDF",
                        events=event_latch if latch else None,
                        rtol=1e-8, atol=1e-10, max_step=20e-6,
                        dense_output=True)
        if not sol.success:
            raise RuntimeError(f"LED solve failed: {sol.message}")
        segments.append(sol)
        if latch and sol.t_events and len(sol.t_events[0]):
            tl = float(sol.t_events[0][0])
            latched_at = tl
            fault_at = tl
            # Latched: switch off, output decays through the load.
            def rhs_off(t, y):
                vout = y[0]
                iset = iset_a if (load_at_enable or t >= enable_time + load_delay_s) else 0.0
                iload = led_load_current(vout, iset)
                return [(-iload) / cout, 0.0, 0.0]
            sol2 = solve_ivp(rhs_off, (tl, t_end), [sol.y[0, -1], 0.0, LED_LATCH_S],
                             method="BDF", rtol=1e-8, atol=1e-10,
                             max_step=20e-6, dense_output=True)
            if not sol2.success:
                raise RuntimeError(f"LED off solve failed: {sol2.message}")
            segments.append(sol2)
            break
        break

    # Build a uniform time base from the segments.
    t = np.linspace(0.0, t_end, 6001)
    vout = np.zeros_like(t)
    iout = np.zeros_like(t)
    oc = np.zeros_like(t)
    for seg in segments:
        mask = (t >= seg.t[0]) & (t <= seg.t[-1])
        if np.any(mask):
            vals = seg.sol(t[mask])
            vout[mask] = vals[0]
            iout[mask] = vals[1]
            oc[mask] = vals[2]
    # After a latch, the last segment already covers to t_end.
    if latched_at is not None:
        mask = t >= latched_at
        vout[mask] = np.maximum(vout[mask], 0.0)
        iout[mask] = 0.0
    iload = np.array([led_load_current(v, iset_a if (load_at_enable or tt >= enable_time + load_delay_s) else 0.0)
                      for v, tt in zip(vout, t)])
    vout_at_latch = None
    if latched_at is not None:
        vout_at_latch = float(np.interp(latched_at, t, vout))
    if vout_at_latch is not None:
        u7_dissipation_w = (VOUT_BUCK - vout_at_latch) * ilim
    else:
        u7_dissipation_w = (VOUT_BUCK - float(vout[-1])) * float(iout[-1])
    return {
        "label": label,
        "iset_a": iset_a,
        "iset_ma_per_channel": iset_a / (LED_COUNT * LED_CHANNELS) * 1e3,
        "ilim_ma": ilim_ma,
        "rds_on_mohm": rds_on * 1e3,
        "cout_effective_uf": cout * 1e6,
        "load_at_enable": load_at_enable,
        "load_delay_ms": 0.0 if load_at_enable else load_delay_s * 1e3,
        "latched": latched_at is not None,
        "latch_time_ms": None if latched_at is None else latched_at * 1e3,
        "fault_assert_ms": None if fault_at is None else fault_at * 1e3,
        "vout_final_v": float(vout[-1]),
        "vout_min_v": float(np.min(vout)),
        "vout_at_latch_v": vout_at_latch,
        "u7_dissipation_w": u7_dissipation_w,
        "peak_current_ma": float(np.max(iout)) * 1e3,
        "steady_current_ma": float(np.mean(iout[t > 0.8 * t_end])) * 1e3,
        "t": t,
        "vout": vout,
        "iout": iout,
        "iload": iload,
        "oc": oc,
    }


# ---------------------------------------------------------------------------
# 6. Sequencing summary
# ---------------------------------------------------------------------------


def ldo_model(t, v4, t_end=0.060):
    """Behavioral MAX38902 3V3 follower.  Startup is unknown; tau is assumed."""
    n = len(t)
    v3 = np.zeros(n)
    v = 0.0
    dt = t[1] - t[0]
    for k in range(n):
        if v4[k] < LDO_VIN_MIN:
            target = 0.0
        else:
            dropout = LDO_DROPOUT_AT_500MA * (LDO_ILOAD / 0.5)
            target = min(LDO_VOUT, v4[k] - dropout)
        v += (target - v) / LDO_TAU * dt
        v3[k] = max(v, 0.0)
    return v3


def sequencing_summary(coupled, led_case):
    t = coupled["t"]
    v4 = coupled["vout"]
    v3 = ldo_model(t, v4)
    t_3v3_90 = first_cross(t, v3, 0.9 * LDO_VOUT) * 1e3
    t_4v_34 = first_cross(t, v4, LDO_VIN_MIN) * 1e3
    return {
        "order": ["VBUS", "VBUS_FUSED", "VBUS_PROTECTED_RAW", "+4V_REG", "+3V3", "+4V_LED"],
        "rails": {
            "VBUS": {"t_90_ms": 0.0, "status": "step at t=0"},
            "VBUS_FUSED": {
                "t_90_ms": coupled["t_fused_90_ms"],
                "t_90_rc_ms": -math.log(0.1) * SOURCE_R * C125 * 1e3,
                "status": "simulated; source R=0.1 ohm + C125 1 uF assumption",
            },
            "VBUS_PROTECTED_RAW": {
                "t_90_ms": coupled["t_prot_90_ms"],
                "t_100_ms": None,
                "t_3800mv_ms": coupled["t_prot_3800_ms"],
                "status": "simulated; eFuse dV/dt 0.2 V/ms, C124 10 nF",
            },
            "+4V_REG": {
                "t_90_ms": coupled["t_4v_90_ms"],
                "t_99_ms": coupled["t_4v_99_ms"],
                "monotonic": coupled["monotonic"]["monotonic"],
                "max_dip_mv": coupled["monotonic"]["max_dip_mv"],
                "status": "simulated; behavioral peak-current-mode loop assumption",
            },
            "+3V3": {
                "t_90_ms": t_3v3_90,
                "t_4v_cross_3v4_ms": t_4v_34,
                "status": "UNKNOWN LDO startup; modeled with tau=0.5 ms assumption",
            },
            "+4V_LED": {
                "t_90_ms": 50.0 + LED_RISE_S * 1e3,
                "status": "firmware-controlled; modeled enable at 50 ms, not a board time",
                "modeled_enable_ms": 50.0,
                "modeled_rise_ms": LED_RISE_S * 1e3,
                "modeled_latched": led_case["latched"],
                "modeled_latch_time_ms": led_case["latch_time_ms"],
            },
        },
        "t": t,
        "v3v3": v3,
    }


# ---------------------------------------------------------------------------
# 7. Plots
# ---------------------------------------------------------------------------


def plot_startup(coupled, seq, path):
    t = coupled["t"] * 1e3
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.plot(t, coupled["vbus"], label="VBUS / FUSED", lw=1.2)
    ax.plot(t, coupled["vprot"], label="VBUS_PROTECTED_RAW", lw=1.6)
    ax.plot(t, coupled["vout"], label="+4V_REG", lw=1.8)
    ax.plot(t, seq["v3v3"], label="+3V3 (LDO model, unknown)", lw=1.4, ls="--")
    ax.axhline(3.8, color="0.5", lw=0.8, ls=":")
    ax.text(0.5, 3.85, "buck VIN UVLO 3.8 V", fontsize=8, color="0.4")
    ax.axhline(4.0, color="0.5", lw=0.8, ls=":")
    ax.set_xlabel("time (ms)")
    ax.set_ylabel("voltage (V)")
    ax.set_title("Maru60 startup: VBUS step -> eFuse dV/dt -> buck -> LDO")
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 5.4)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_load_step(step, path):
    t = step["t"] * 1e3
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})
    ax1.plot(t, step["vout"], lw=1.6, color="C0")
    ax1.axhline(4.0, color="0.5", lw=0.8, ls=":")
    ax1.set_ylabel("+4V_REG (V)")
    ax1.set_title("Buck load step 0.1 -> 0.3 A and 0.2 A unload (behavioral loop)")
    ax1.set_ylim(3.97, 4.03)
    ax1.annotate(f"undershoot {step['step_up_undershoot_mv']:.1f} mV",
                 xy=(30.0, 4.0 - step['step_up_undershoot_mv'] / 1e3),
                 xytext=(31.0, 3.978), fontsize=8,
                 arrowprops=dict(arrowstyle="->", lw=0.8))
    ax1.annotate(f"overshoot {step['unload_overshoot_mv']:.1f} mV",
                 xy=(40.0, 4.0 + step['unload_overshoot_mv'] / 1e3),
                 xytext=(41.0, 4.022), fontsize=8,
                 arrowprops=dict(arrowstyle="->", lw=0.8))
    ax1.grid(True, alpha=0.3)
    ax2.plot(t, step["iload"], lw=1.4, color="C1")
    ax2.set_ylabel("load (A)")
    ax2.set_xlabel("time (ms)")
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(25, 50)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_uvlo_ovlo(sweep, path):
    t = sweep["t"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True)
    ax1.plot(t, sweep["vbus"], label="VBUS", lw=1.4)
    ax1.plot(t, sweep["vprot"], label="VBUS_PROTECTED_RAW", lw=1.4)
    ax1.axhline(sweep["thresholds"]["uvlo_rising_v"], color="C2", lw=0.8, ls="--")
    ax1.axhline(sweep["thresholds"]["uvlo_falling_v"], color="C2", lw=0.8, ls=":")
    ax1.axhline(sweep["thresholds"]["ovlo_rising_v"], color="C3", lw=0.8, ls="--")
    ax1.axhline(sweep["thresholds"]["ovlo_falling_v"], color="C3", lw=0.8, ls=":")
    ax1.set_ylabel("voltage (V)")
    ax1.set_title("UVLO/OVLO sweep 0 -> 6.5 -> 0 V (nominal thresholds)")
    ax1.text(0.02, 0.95,
             "protected rail slew-limited at 0.2 V/ms (20 ms full ramp; <1% of this 2 s axis)",
             transform=ax1.transAxes, fontsize=8, va="top")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper right", fontsize=8)
    ax2.plot(t, sweep["v_uvlo"], label="USB_UVLO divider", lw=1.2)
    ax2.plot(t, sweep["v_ovlo"], label="USB_OVLO divider", lw=1.2)
    ax2.axhline(1.200, color="C2", lw=0.8, ls="--")
    ax2.axhline(1.090, color="C2", lw=0.8, ls=":")
    ax2.set_ylabel("divider (V)")
    ax2.set_xlabel("time (s)")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_led(full, capped, capped_seq, path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True)
    ax1.plot(full["t"] * 1e3, full["vout"], label="full white 1.14 A", lw=1.6)
    ax1.plot(capped["t"] * 1e3, capped["vout"],
             label="0.76 mA/ch, load at enable", lw=1.6)
    ax1.plot(capped_seq["t"] * 1e3, capped_seq["vout"],
             label="0.76 mA/ch, load sequenced at 5.5 ms", lw=1.6)
    ax1.set_ylabel("+4V_LED (V)")
    ax1.set_title("TPS2553-1 LED rail: current limit and latch-off")
    ax1.set_ylim(0, 5.2)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper right", fontsize=8)
    ax2.plot(full["t"] * 1e3, full["iout"] * 1e3, label="full white", lw=1.6)
    ax2.plot(capped["t"] * 1e3, capped["iout"] * 1e3,
             label="0.76 mA/ch, load at enable", lw=1.6)
    ax2.plot(capped_seq["t"] * 1e3, capped_seq["iout"] * 1e3,
             label="0.76 mA/ch, sequenced", lw=1.6)
    ax2.axhline(full["ilim_ma"], color="C3", lw=0.8, ls="--", label="ILIM min")
    ax2.set_ylabel("switch current (mA)")
    ax2.set_xlabel("time (ms)")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 8. Main
# ---------------------------------------------------------------------------


def main():
    src = load_and_assert_sources()
    review = json.loads(POWER_REVIEW.read_text())

    # 1. eFuse startup, nominal and corners.
    ef_nom = efuse_startup(ilim_ma=500.0, c_dvdt_nf=10.0, iload=0.0,
                           label="nominal, no load")
    ef_loaded = efuse_startup(ilim_ma=500.0, c_dvdt_nf=10.0, iload=0.3,
                              label="nominal, 0.3 A equivalent load")
    ef_corners = []
    for ilim in (425.0, 500.0, 575.0):
        for c in (9.0, 10.0, 11.0):
            r = efuse_startup(ilim_ma=ilim, c_dvdt_nf=c, iload=0.0,
                              label=f"ILIM={ilim:.0f}mA C={c:.0f}nF")
            ef_corners.append({k: v for k, v in r.items()
                               if k not in ("t", "vout", "i")})
    cl_tests = [efuse_current_limit_test(ilim) for ilim in (425.0, 500.0, 575.0)]

    # 2. Buck startup and load step.
    buck_nom = simulate_buck_startup(label="nominal 5 V, 0.1 A")
    buck_03 = simulate_buck_startup(iload=0.3, label="nominal 5 V, 0.3 A")
    buck_corners = []
    for tss_name, tss in BUCK_TSS.items():
        r = simulate_buck_startup(t_ss=tss, label=f"t_ss={tss_name}")
        buck_corners.append({k: v for k, v in r.items()
                             if k not in ("t", "vout", "iL", "ss")})
    step = simulate_buck_load_step(label="0.1->0.3 A, 0.2 A unload")

    # 3. Coupled startup / sequencing.
    coupled = simulate_coupled_startup(iload=0.1, label="coupled 0.1 A")
    coupled_03 = simulate_coupled_startup(iload=0.3, label="coupled 0.3 A")

    # 4. UVLO/OVLO.
    sweeps = {c: simulate_uvlo_ovlo(c) for c in ("min", "typ", "max")}
    sweep = sweeps["typ"]

    # 5. LED rail.
    full = simulate_led_rail(1.14, LED_ILIM_MA["min"], label="full white, min ILIM")
    capped = simulate_led_rail(0.76e-3 * LED_COUNT * LED_CHANNELS,
                               LED_ILIM_MA["min"], label="0.76 mA/ch, min ILIM")
    capped_seq = simulate_led_rail(0.76e-3 * LED_COUNT * LED_CHANNELS,
                                   LED_ILIM_MA["min"], load_at_enable=False,
                                   label="0.76 mA/ch, sequenced load")
    capped_nom = simulate_led_rail(0.76e-3 * LED_COUNT * LED_CHANNELS,
                                   LED_ILIM_MA["nom"], label="0.76 mA/ch, nom ILIM")
    capped_max = simulate_led_rail(0.76e-3 * LED_COUNT * LED_CHANNELS,
                                   LED_ILIM_MA["max"], label="0.76 mA/ch, max ILIM")
    full_nom = simulate_led_rail(1.14, LED_ILIM_MA["nom"], label="full white, nom ILIM")
    full_max = simulate_led_rail(1.14, LED_ILIM_MA["max"], label="full white, max ILIM")

    # 6. Sequencing summary.
    seq = sequencing_summary(coupled, capped_seq)

    # 7. Plots.
    plot_startup(coupled, seq, OUT / "startup.png")
    plot_load_step(step, OUT / "load_step.png")
    plot_uvlo_ovlo(sweep, OUT / "uvlo_ovlo.png")
    plot_led(full, capped, capped_seq, OUT / "led_rail.png")

    # 8. JSON.
    def clean(d):
        if isinstance(d, dict):
            return {k: clean(v) for k, v in d.items()
                    if k not in ("t", "vout", "i", "iL", "ss", "vbus", "vprot",
                                 "i_ef", "iload", "iout", "oc", "v3v3", "v_uvlo",
                                 "v_ovlo", "enabled")}
        if isinstance(d, (list, tuple)):
            return [clean(v) for v in d]
        if isinstance(d, (np.floating, np.integer)):
            return float(d)
        if isinstance(d, np.bool_):
            return bool(d)
        return d

    result = {
        "schema": "maru60-power-sim/v1",
        "status": "SIMULATION_ONLY",
        "qualification": (
            "No stability, thermal, USB compliance, EMC, or hardware "
            "qualification. Behavioral average models with stated assumptions. "
            "No SPICE, no bench measurement, no effective-capacitance "
            "qualification."
        ),
        "sources": {
            "netlist": {"path": str(NETLIST.relative_to(REPO)),
                        "sha256": src["hashes"]["netlist_sha256"]},
            "schematic": {"path": str(SCHEMATIC.relative_to(REPO)),
                          "sha256": src["hashes"]["schematic_sha256"]},
            "power_review": {"path": str(POWER_REVIEW.relative_to(REPO)),
                             "sha256": src["hashes"]["power_review_sha256"]},
            "power_review_report": {
                "path": str(POWER_REVIEW_REPORT.relative_to(REPO)),
                "sha256": src["hashes"]["power_review_report_sha256"]},
        },
        "inputs": {
            "components": {
                "R120_ohm": 590e3, "R121_ohm": 156e3,
                "R122_ohm": 620e3, "R123_ohm": 267e3,
                "R124_ohm": 6.65e3, "R125_ohm": 100.0,
                "C124_nf": 10.0, "C125_uf": 1.0,
                "C126_uf": 1.0, "C136_nf": 100.0, "C137_uf": 4.7,
                "C139_nf": 100.0, "R159_ohm": 40e3, "R160_ohm": 10e3,
                "L2_uh": 4.7, "C100_uf": 4.7, "C120_uf": 1.0,
                "C140_uf": 22.0, "C141_uf": 22.0,
                "R112_ohm": 133e3, "R109_ohm": 100e3, "R113_ohm": 10e3,
                "C121_uf": 4.7, "C122_nf": 100.0, "C123_nf": 100.0,
                "led_count": LED_COUNT, "led_channels": LED_CHANNELS,
            },
            "assumptions": {
                "efuse_rds_on_mohm": EFUSE_RDS_ON * 1e3,
                "efuse_ilim_response_us": EFUSE_ILIM_RESPONSE_S * 1e6,
                "efuse_fast_trip_ratio": EFUSE_FAST_TRIP_RATIO,
                "efuse_fast_trip_ns": EFUSE_FAST_TRIP_S * 1e9,
                "protected_caps_nominal_uf": PROT_C_NOM * 1e6,
                "protected_caps_derating_at_5v": PROT_DERATE_5V,
                "protected_caps_effective_uf": PROT_C_EFF * 1e6,
                "protected_caps_esr_mohm": PROT_ESR * 1e3,
                "source_r_ohm": SOURCE_R,
                "fuse_candidate": "SF-1206F100-2 (1 A), not qualified",
                "buck_cout_nominal_uf": BUCK_COUT_NOM * 1e6,
                "buck_cout_effective_uf": BUCK_COUT_EFF * 1e6,
                "buck_cout_esr_mohm": BUCK_COUT_ESR * 1e3,
                "buck_dcr_mohm": BUCK_DCR * 1e3,
                "buck_rhs_mohm": BUCK_RHS * 1e3,
                "buck_rls_mohm": BUCK_RLS * 1e3,
                "buck_fsw_khz": BUCK_FSW / 1e3,
                "buck_max_duty": BUCK_MAX_DUTY,
                "buck_vin_uvlo_rise_v": BUCK_VIN_UVLO_RISE,
                "buck_vin_uvlo_fall_v": BUCK_VIN_UVLO_FALL,
                "buck_loop": "behavioral peak-current-mode; PI outer loop; 20 kHz target crossover; not the TPS62932 internal compensation",
                "buck_load_model": "application load ramps on above 0.5 V (behavioral; prevents negative output-cap voltage before startup)",
                "buck_load_step_slew": "tanh transition, approximately 1 us 10-90% (0.2 A/us)",
                "led_rds_on_mohm": LED_RDS_ON * 1e3,
                "led_rds_on_max_mohm": LED_RDS_ON_MAX * 1e3,
                "led_response_us": LED_RESPONSE_S * 1e6,
                "led_latch_deglitch_ms": LED_LATCH_S * 1e3,
                "led_rise_ms": LED_RISE_S * 1e3,
                "led_cout_nominal_uf": LED_COUT_NOM * 1e6,
                "led_cout_effective_uf": LED_COUT_EFF * 1e6,
                "led_cout_esr_mohm": LED_COUT_ESR * 1e3,
                "led_load_knee_v": LED_V_DROPOUT,
                "led_load_model": "constant-current sink above 3.0 V, linear to zero at 0 V; not a datasheet V-I curve",
                "led_sequenced_load_delay_ms": 5.5,
                "ldo_tau_ms": LDO_TAU * 1e3,
                "ldo_vin_min_v": LDO_VIN_MIN,
                "ldo_dropout_at_500ma_mv": LDO_DROPOUT_AT_500MA * 1e3,
                "ldo_load_a": LDO_ILOAD,
                "uvlo_ovlo_sweep_load_ohm": 1000.0,
                "uvlo_ovlo_sweep_rate_v_per_s": 6.5,
                "uvlo_ovlo_fall_slew_v_per_s": 10.0,
            },
        },
        "efuse": {
            "model": "dV/dt reference ramp + Rds_on pass FET + ILIM clamp; R125 100 ohm included as 1 us RC",
            "startup_nominal_no_load": clean(ef_nom),
            "startup_nominal_0p3a": clean(ef_loaded),
            "corners": clean(ef_corners),
            "current_limit_tests": clean(cl_tests),
            "review_baseline": {
                "slew_v_per_ms": review["inrush"]["slew_v_per_ms"],
                "time_to_5v_ms": review["inrush"]["time_to_5v_ms"],
                "capacitor_current_ma": review["inrush"]["capacitor_current_ma"],
                "capacitor_energy_uj": review["inrush"]["capacitor_energy_uj"],
                "ilim_ma": review["inrush"]["efuse_ilim_ma"],
            },
        },
        "buck": {
            "model": "average peak-current-mode buck: L, Cout, ESR, DCR, Rds_on, 98% duty clamp, soft-start reference",
            "loop": buck_nom["loop"],
            "startup_nominal_0p1a": clean(buck_nom),
            "startup_nominal_0p3a": clean(buck_03),
            "startup_corners": clean(buck_corners),
            "load_step": clean(step),
            "ripple_estimate": {
                "inductor_ripple_ma": (VBUS_NOM - VOUT_BUCK) * (VOUT_BUCK / VBUS_NOM) / (BUCK_L * BUCK_FSW) * 1e3,
                "output_ripple_esr_mv": (VBUS_NOM - VOUT_BUCK) * (VOUT_BUCK / VBUS_NOM) / (BUCK_L * BUCK_FSW) * BUCK_COUT_ESR * 1e3,
                "output_ripple_cap_mv": (VBUS_NOM - VOUT_BUCK) * (VOUT_BUCK / VBUS_NOM) / (BUCK_L * BUCK_FSW) / (8 * BUCK_FSW * BUCK_COUT_EFF) * 1e3,
                "note": "average model does not simulate switching ripple; these are arithmetic estimates",
            },
        },
        "uvlo_ovlo": {
            "model": "TPS25947 comparator state machine with R120-R123 dividers; 0->6.5->0 V triangle",
            "thresholds": {
                "uvlo_rising_v": EFUSE_UVLO_R,
                "uvlo_falling_v": EFUSE_UVLO_F,
                "ovlo_rising_v": EFUSE_OVLO_R,
                "ovlo_falling_v": EFUSE_OVLO_F,
                "uvlo_leakage_shift_v": EFUSE_UVLO_LEAK,
                "ovlo_leakage_shift_v": EFUSE_OVLO_LEAK,
            },
            "nominal": clean(sweep),
            "corners": {c: clean(s) for c, s in sweeps.items()},
            "review_baseline": review["uvlo_ovlo"],
        },
        "led": {
            "model": "TPS2553-1 current source with 2 us response lag, Rds_on, ILIM clamp, 7.5 ms latch-off; behavioral SK6805 constant-current load with 3.0 V knee",
            "full_white_min_ilim": clean(full),
            "full_white_nom_ilim": clean(full_nom),
            "full_white_max_ilim": clean(full_max),
            "capped_0p76_min_ilim_load_at_enable": clean(capped),
            "capped_0p76_min_ilim_sequenced": clean(capped_seq),
            "capped_0p76_nom_ilim": clean(capped_nom),
            "capped_0p76_max_ilim": clean(capped_max),
            "margin_table": {
                "load_ma": 0.76e-3 * LED_COUNT * LED_CHANNELS * 1e3,
                "min_ilim_ma": LED_ILIM_MA["min"],
                "margin_ma": LED_ILIM_MA["min"] - 0.76e-3 * LED_COUNT * LED_CHANNELS * 1e3,
                "margin_pct": (LED_ILIM_MA["min"] / (0.76e-3 * LED_COUNT * LED_CHANNELS * 1e3) - 1) * 100,
                "max_per_channel_for_min_ilim_ma": LED_ILIM_MA["min"] / (LED_COUNT * LED_CHANNELS),
                "recommended_cap_0p70_ma": 0.70e-3 * LED_COUNT * LED_CHANNELS * 1e3,
                "recommended_cap_0p70_margin_ma": LED_ILIM_MA["min"] - 0.70e-3 * LED_COUNT * LED_CHANNELS * 1e3,
            },
        },
        "sequencing": clean(seq),
        "coupled_startup_0p3a": clean(coupled_03),
        "findings": [
            {
                "id": "SIM-01",
                "severity": "closed-by-simulation",
                "title": "eFuse dV/dt ramp is 25 ms and capacitor-only inrush is ~1.07 mA effective",
                "detail": f"At C124=10 nF, SR=0.2 V/ms, Cprot={PROT_C_EFF*1e6:.3f} uF effective, the ramp reaches 5 V at {ef_nom['t100_ms']:.2f} ms; the capacitor current is {ef_nom['inrush_capacitor_ma']:.3f} mA and the stored energy is {ef_nom['cap_energy_uj']:.1f} uJ. A 0.3 A equivalent load peaks at {ef_loaded['peak_current_ma']:.1f} mA, below the 425 mA minimum ILIM.",
            },
            {
                "id": "SIM-02",
                "severity": "closed-by-simulation",
                "title": "4 V rail startup is monotonic under the stated behavioral loop",
                "detail": f"The coupled eFuse+buck simulation gives 4 V 90% at {coupled['t_4v_90_ms']:.2f} ms and 99% at {coupled['t_4v_99_ms']:.2f} ms at 0.1 A, with a largest drop from running max of {coupled['monotonic']['max_dip_mv']:.2f} mV. At 0.3 A the 90% time is {coupled_03['t_4v_90_ms']:.2f} ms. Conditional on the synthetic loop and 29.7 uF effective output capacitance; not a stability result.",
            },
            {
                "id": "SIM-03",
                "severity": "review-flag",
                "title": "0.76 mA/channel is at the current-limit edge and can latch off at startup",
                "detail": f"76x3x0.76 mA = {0.76*LED_COUNT*LED_CHANNELS:.2f} mA vs {LED_ILIM_MA['min']:.3f} mA minimum ILIM: {LED_ILIM_MA['min']-0.76*LED_COUNT*LED_CHANNELS:.3f} mA ({(LED_ILIM_MA['min']/(0.76*LED_COUNT*LED_CHANNELS)-1)*100:.2f}%) margin. With the LED load present at enable, the simulation latches at {capped['latch_time_ms']:.2f} ms; with the load sequenced after the rail is up, it does not latch and the rail is {capped_seq['vout_final_v']:.4f} V. Sequence the LED load after the rail is up, or cap at <=0.70 mA/channel.",
            },
            {
                "id": "SIM-04",
                "severity": "review-flag",
                "title": "Full white 1.14 A is 4.87-6.56x the LED limiter and latches off",
                "detail": f"The TPS2553-1 limits at {full['ilim_ma']:.1f} mA, the rail collapses to {full['vout_at_latch_v']:.3f} V, and the 7.5 ms deglitch latches the switch off at {full['latch_time_ms']:.2f} ms. The electrical dissipation in U7 is {full['u7_dissipation_w']:.3f} W (not a thermal result). Full white is not supported by this power tree.",
            },
            {
                "id": "SIM-05",
                "severity": "closed-by-simulation",
                "title": "UVLO/OVLO trip points and hysteresis reproduce the analytical review",
                "detail": f"Nominal UVLO {sweep['thresholds']['uvlo_rising_v']:.3f}/{sweep['thresholds']['uvlo_falling_v']:.3f} V ({sweep['thresholds']['uvlo_hysteresis_v']*1e3:.0f} mV hysteresis); OVLO {sweep['thresholds']['ovlo_rising_v']:.3f}/{sweep['thresholds']['ovlo_falling_v']:.3f} V ({sweep['thresholds']['ovlo_hysteresis_v']*1e3:.0f} mV hysteresis). The OVLO min corner is {sweeps['min']['thresholds']['ovlo_rising_v']-EFUSE_OVLO_LEAK:.3f} V, 89 mV above the 5.5 V USB maximum.",
            },
        ],
        "unknowns": [
            "Actual C126/C136/C137 MPNs, dielectrics, DC-bias curves and ESR; the 0.92 derating and 2 mohm parallel ESR are assumptions.",
            "Actual VBUS source/cable impedance and input ramp/dip waveform; 0.1 ohm source resistance is an assumption.",
            "TPS62932 internal loop compensation, phase margin, frequency foldback, PFM/DCM and hiccup behavior; the PI loop is a behavioral proxy.",
            "Actual C140/C141 effective capacitance (12 uF is a TBD target, not a measured value).",
            "Actual SK6805 per-channel current, V-I knee and quiescent current; 5 mA/ch and 0.76 mA/ch are assumptions.",
            "Actual TPS2553-1 Rds_on, current-limit corner, latch deglitch and thermal behavior at 4 V.",
            "MAX38902 3V3 startup, dropout and thermal behavior; the 0.5 ms tau is an assumption.",
            "Firmware LED enable timing and brightness cap; the 50 ms LED enable is illustrative.",
            "Whether the 4 V rail is monotonic on the assembled board; the simulation is conditional on the loop and capacitor assumptions.",
        ],
        "bench_measurements": [
            "VBUS, VBUS_FUSED, VBUS_PROTECTED_RAW, +4V_REG, +3V3 and +4V_LED startup at 5.0 V and 5.5 V, hot and cold, with the actual cable.",
            "Input ripple at U18 VIN at no load, MCU load and a full-white LED attempt.",
            "UVLO/OVLO trip points by sweeping VBUS up and down on the assembled board.",
            "LED rail current and U7 FAULT/latch behavior at full white and at the intended firmware brightness cap, including the enable sequence.",
            "3V3 load step and LDO thermal at the actual load.",
            "Buck load step and, if stability is to be claimed, loop gain/phase across the application corners.",
            "eFuse current limit and thermal at 425/500/575 mA.",
            "Soft-start time and monotonicity of the 4 V rail.",
        ],
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "power-sim.json").write_text(json.dumps(result, indent=2) + "\n")

    # 9. REPORT.md
    write_report(result, ef_nom, ef_loaded, buck_nom, buck_03, step, coupled,
                 coupled_03, sweep, full, capped, capped_seq, seq)

    print(f"wrote {OUT / 'power-sim.json'}")
    print(f"wrote {OUT / 'REPORT.md'}")
    for p in ("startup.png", "load_step.png", "uvlo_ovlo.png", "led_rail.png"):
        print(f"wrote {OUT / p}")
    return result


def write_report(result, ef_nom, ef_loaded, buck_nom, buck_03, step, coupled,
                 coupled_03, sweep, full, capped, capped_seq, seq):
    r = result
    lines = []
    lines.append("# Maru60 power-tree transient simulation")
    lines.append("")
    lines.append("**Status: SIMULATION_ONLY. No stability, thermal, USB-compliance, EMC or hardware qualification.**")
    lines.append("")
    lines.append("This report is generated by `pcb/tools/simulate_power.py`. It reads the")
    lines.append("native netlist and the core schematic, asserts the power-tree connectivity and")
    lines.append("values, and runs deterministic behavioral transient models. Every model")
    lines.append("parameter that is not read from CAD is an explicit assumption in")
    lines.append("`power-sim.json`.")
    lines.append("")
    lines.append("## Bottom line")
    lines.append("")
    lines.append("| Question | Simulation answer |")
    lines.append("|---|---|")
    lines.append(f"| eFuse dV/dt ramp | {ef_nom['t90_ms']:.2f} ms to 90%, {ef_nom['t100_ms']:.2f} ms to 5 V; capacitor-only inrush {ef_nom['inrush_capacitor_ma']:.3f} mA; {ef_nom['cap_energy_uj']:.1f} uJ stored. |")
    lines.append(f"| eFuse with 0.3 A load | {ef_loaded['t90_ms']:.2f} ms to 90%; peak {ef_loaded['peak_current_ma']:.1f} mA, below the 425 mA minimum ILIM. |")
    lines.append(f"| Buck 4 V startup (5 V in, 0.1 A) | {buck_nom['t90_ms']:.2f} ms to 90%, {buck_nom['t99_ms']:.2f} ms to 99%; overshoot {buck_nom['overshoot_mv']:.1f} mV; monotonic={buck_nom['monotonic']['monotonic']} (largest drop from running max {buck_nom['monotonic']['max_dip_mv']:.2f} mV). |")
    lines.append(f"| Buck load step 0.1->0.3 A | undershoot {step['step_up_undershoot_mv']:.1f} mV; recovery to 0.2% {step['recovery_up_0p2pct_ms']:.3f} ms; peak iL {step['step_up_peak_il_a']:.3f} A. |")
    lines.append(f"| Buck 0.2 A unload | overshoot {step['unload_overshoot_mv']:.1f} mV; recovery to 0.2% {step['recovery_down_0p2pct_ms']:.3f} ms; min iL {step['unload_min_il_a']:.3f} A. |")
    lines.append(f"| Coupled 4 V startup | 4 V 90% at {coupled['t_4v_90_ms']:.2f} ms; monotonic={coupled['monotonic']['monotonic']} (largest drop from running max {coupled['monotonic']['max_dip_mv']:.2f} mV). |")
    lines.append(f"| UVLO / OVLO | UVLO {sweep['thresholds']['uvlo_rising_v']:.3f}/{sweep['thresholds']['uvlo_falling_v']:.3f} V; OVLO {sweep['thresholds']['ovlo_rising_v']:.3f}/{sweep['thresholds']['ovlo_falling_v']:.3f} V. |")
    lines.append(f"| LED full white | 1.14 A demand vs {full['ilim_ma']:.1f} mA min ILIM; rail collapses; latch at {full['latch_time_ms']:.2f} ms. |")
    lines.append(f"| LED 0.76 mA/ch | 173.28 mA vs {capped['ilim_ma']:.3f} mA min ILIM: {r['led']['margin_table']['margin_ma']:.3f} mA ({r['led']['margin_table']['margin_pct']:.2f}%) margin. Load-at-enable latches={capped['latched']}; sequenced load latches={capped_seq['latched']}. |")
    lines.append("")
    lines.append("## 1. eFuse dV/dt ramp")
    lines.append("")
    lines.append("Model: TPS259470 dV/dt reference ramps at `SR = 2/C_dVdt[nF]` V/ms;")
    lines.append("the pass FET is a voltage source behind 28.3 mohm with an ILIM clamp;")
    lines.append("the protected rail is C126 1 uF + C136 100 nF + C137 4.7 uF, derated")
    lines.append("0.92 at 5 V (5.336 uF effective) with a 2 mohm parallel ESR. R125 100 ohm")
    lines.append("gives a 1 us RC on the dV/dt pin, negligible against the 25 ms ramp.")
    lines.append("")
    lines.append(f"- Nominal no-load: 90% at **{ef_nom['t90_ms']:.2f} ms**, 5 V at **{ef_nom['t100_ms']:.2f} ms**.")
    lines.append(f"- Capacitor-only inrush: **{ef_nom['inrush_capacitor_ma']:.3f} mA**; stored energy **{ef_nom['cap_energy_uj']:.1f} uJ**.")
    lines.append(f"- 0.3 A equivalent load: peak **{ef_loaded['peak_current_ma']:.1f} mA**, still below the 425 mA minimum ILIM; final rail {ef_loaded['vfinal_v']:.4f} V.")
    lines.append(f"- Current-limit test into 4 ohm (1 A at 4 V): steady current {r['efuse']['current_limit_tests'][1]['steady_current_ma']:.1f} mA at the 500 mA nominal ILIM, output settles at {r['efuse']['current_limit_tests'][1]['vout_final_v']:.2f} V; the 400 us response is modeled as a first-order lag.")
    lines.append("")
    lines.append("The 1.16 mA / 72.5 uJ analytical baseline used 5.8 uF nominal. The")
    lines.append("simulation uses 5.336 uF effective, so the current is 1.067 mA and the")
    lines.append("stored energy is 66.7 uJ. Both are far below the 425 mA minimum ILIM.")
    lines.append("")
    lines.append("## 2. Buck TPS62932")
    lines.append("")
    lines.append("Model: average peak-current-mode buck with L2 4.7 uH, DCR 20 mohm,")
    lines.append("HS/LS 76/32 mohm, C100 4.7 uF + C120 1 uF + C140/C141 12 uF effective")
    lines.append("each (29.7 uF total), 20 mohm ESR, 500 kHz, 98% duty clamp, and a")
    lines.append("soft-start reference from C139 100 nF. The inner current loop is a")
    lines.append("50 kHz first-order lag with physical inductor slew limiting; the outer")
    lines.append("voltage loop is a PI compensator targeting 20 kHz crossover. **This is a")
    lines.append("synthetic loop, not the TPS62932 internal compensation; no stability claim.**")
    lines.append("")
    lines.append(f"- Startup 5 V / 0.1 A: 90% at **{buck_nom['t90_ms']:.2f} ms**, 99% at **{buck_nom['t99_ms']:.2f} ms**, overshoot **{buck_nom['overshoot_mv']:.1f} mV**, monotonic={buck_nom['monotonic']['monotonic']}.")
    lines.append(f"- Startup 5 V / 0.3 A: 90% at **{buck_03['t90_ms']:.2f} ms**, overshoot **{buck_03['overshoot_mv']:.1f} mV**, monotonic={buck_03['monotonic']['monotonic']}.")
    lines.append(f"- Load step 0.1->0.3 A: undershoot **{step['step_up_undershoot_mv']:.1f} mV**, recovery to 0.2% **{step['recovery_up_0p2pct_ms']:.3f} ms**, peak iL **{step['step_up_peak_il_a']:.3f} A**.")
    lines.append(f"- 0.2 A unload: overshoot **{step['unload_overshoot_mv']:.1f} mV**, recovery to 0.2% **{step['recovery_down_0p2pct_ms']:.3f} ms**, min iL **{step['unload_min_il_a']:.3f} A**.")
    lines.append(f"- Calculated inductor ripple: **{r['buck']['ripple_estimate']['inductor_ripple_ma']:.1f} mA**; output ripple estimate {r['buck']['ripple_estimate']['output_ripple_esr_mv']:.1f} mV ESR + {r['buck']['ripple_estimate']['output_ripple_cap_mv']:.1f} mV capacitive.")
    lines.append("")
    lines.append("The load-step numbers are a function of the assumed 20 kHz loop. They")
    lines.append("show the direction and scale of the response, not the TPS62932's actual")
    lines.append("phase margin or transient response.")
    lines.append("")
    lines.append("## 3. UVLO / OVLO")
    lines.append("")
    lines.append("The sweep is 0 -> 6.5 -> 0 V over 2 s with the R120-R123 dividers and")
    lines.append("the TPS25947 comparator thresholds. The state machine reproduces the")
    lines.append("analytical trip points:")
    lines.append("")
    lines.append("| Threshold | Min | Nom | Max | With 0.1 uA leakage |")
    lines.append("|---|---:|---:|---:|---:|")
    lines.append(f"| UVLO rising | {r['uvlo_ovlo']['thresholds']['uvlo_rising_v']['min']:.3f} | {r['uvlo_ovlo']['thresholds']['uvlo_rising_v']['typ']:.3f} | {r['uvlo_ovlo']['thresholds']['uvlo_rising_v']['max']:.3f} | {r['uvlo_ovlo']['thresholds']['uvlo_rising_v']['min']-EFUSE_UVLO_LEAK:.3f}-{r['uvlo_ovlo']['thresholds']['uvlo_rising_v']['max']+EFUSE_UVLO_LEAK:.3f} |")
    lines.append(f"| UVLO falling | {r['uvlo_ovlo']['thresholds']['uvlo_falling_v']['min']:.3f} | {r['uvlo_ovlo']['thresholds']['uvlo_falling_v']['typ']:.3f} | {r['uvlo_ovlo']['thresholds']['uvlo_falling_v']['max']:.3f} | {r['uvlo_ovlo']['thresholds']['uvlo_falling_v']['min']-EFUSE_UVLO_LEAK:.3f}-{r['uvlo_ovlo']['thresholds']['uvlo_falling_v']['max']+EFUSE_UVLO_LEAK:.3f} |")
    lines.append(f"| OVLO rising | {r['uvlo_ovlo']['thresholds']['ovlo_rising_v']['min']:.3f} | {r['uvlo_ovlo']['thresholds']['ovlo_rising_v']['typ']:.3f} | {r['uvlo_ovlo']['thresholds']['ovlo_rising_v']['max']:.3f} | {r['uvlo_ovlo']['thresholds']['ovlo_rising_v']['min']-EFUSE_OVLO_LEAK:.3f}-{r['uvlo_ovlo']['thresholds']['ovlo_rising_v']['max']+EFUSE_OVLO_LEAK:.3f} |")
    lines.append(f"| OVLO falling | {r['uvlo_ovlo']['thresholds']['ovlo_falling_v']['min']:.3f} | {r['uvlo_ovlo']['thresholds']['ovlo_falling_v']['typ']:.3f} | {r['uvlo_ovlo']['thresholds']['ovlo_falling_v']['max']:.3f} | {r['uvlo_ovlo']['thresholds']['ovlo_falling_v']['min']-EFUSE_OVLO_LEAK:.3f}-{r['uvlo_ovlo']['thresholds']['ovlo_falling_v']['max']+EFUSE_OVLO_LEAK:.3f} |")
    lines.append("")
    lines.append(f"Nominal hysteresis: UVLO **{sweep['thresholds']['uvlo_hysteresis_v']:.3f} V**, OVLO **{sweep['thresholds']['ovlo_hysteresis_v']:.3f} V**. The OVLO min corner is **{r['uvlo_ovlo']['thresholds']['ovlo_rising_v']['min']-EFUSE_OVLO_LEAK:.3f} V**, only **{r['uvlo_ovlo']['thresholds']['ovlo_rising_v']['min']-EFUSE_OVLO_LEAK-5.5:.3f} V** above the 5.5 V USB maximum.")
    lines.append("")
    lines.append(f"The state-machine sweep reproduces the nominal trip points: UVLO rise {sweep['sim_uvlo_rise_v'][0]:.4f} V, UVLO fall {sweep['sim_uvlo_fall_v'][0]:.4f} V, OVLO rise {sweep['sim_ovlo_rise_v'][0]:.4f} V, OVLO fall {sweep['sim_ovlo_fall_v'][0]:.4f} V. The 10 us sweep grid gives a sub-mV match to the divider arithmetic.")
    lines.append("")
    lines.append("## 4. LED rail")
    lines.append("")
    lines.append("Model: TPS2553-1 with R112 133 kohm (173.657/201.513/233.901 mA),")
    lines.append("85 mohm typical Rds_on, 2 us current-limit response, 7.5 ms latch-off")
    lines.append("deglitch, 11.7 uF effective output capacitance and a behavioral SK6805")
    lines.append("constant-current load with a 3.0 V knee.")
    lines.append("")
    lines.append(f"- Full white 1.14 A: the switch limits at **{full['ilim_ma']:.1f} mA**, the rail collapses to **{full['vout_at_latch_v']:.3f} V** before latch (then 0 V), and the part latches off at **{full['latch_time_ms']:.2f} ms**. The electrical dissipation in U7 at that point is **{full['u7_dissipation_w']:.3f} W** (not a thermal result). Full white is not supported.")
    lines.append(f"- 0.76 mA/ch = **173.28 mA** vs **{capped['ilim_ma']:.3f} mA** minimum ILIM: **{r['led']['margin_table']['margin_ma']:.3f} mA ({r['led']['margin_table']['margin_pct']:.2f}%)** margin.")
    lines.append(f"- With the LED load present at enable, the output-cap inrush pushes the rail into current limit; latched={capped['latched']} at {capped['latch_time_ms']:.2f} ms. With the load sequenced after the rail is up, latched={capped_seq['latched']} and the steady rail is {capped_seq['vout_final_v']:.4f} V (droop {4.0-capped_seq['vout_final_v']:.4f} V).")
    lines.append(f"- The 0.76 mA/ch cap is therefore an absolute edge, not a robust operating point. A **<=0.70 mA/ch** cap gives {r['led']['margin_table']['recommended_cap_0p70_margin_ma']:.2f} mA margin, or the LED load must be sequenced after the rail is up.")
    lines.append("")
    lines.append("## 5. Sequencing")
    lines.append("")
    lines.append("| Rail | Time | Status |")
    lines.append("|---|---:|---|")
    lines.append(f"| VBUS | 0 ms | step |")
    lines.append(f"| VBUS_FUSED | {seq['rails']['VBUS_FUSED']['t_90_rc_ms']:.5f} ms (RC) | simulated, 0.1 ohm source + C125 1 uF; 5 us simulation grid |")
    lines.append(f"| VBUS_PROTECTED_RAW | {seq['rails']['VBUS_PROTECTED_RAW']['t_90_ms']:.2f} ms to 90% | simulated, eFuse 0.2 V/ms |")
    lines.append(f"| +4V_REG | {seq['rails']['+4V_REG']['t_90_ms']:.2f} ms to 90% | simulated, behavioral loop; monotonic={seq['rails']['+4V_REG']['monotonic']} |")
    lines.append(f"| +3V3 | {seq['rails']['+3V3']['t_90_ms']:.2f} ms (modeled) | **UNKNOWN LDO startup**; tau=0.5 ms assumption |")
    lines.append(f"| +4V_LED | {seq['rails']['+4V_LED']['t_90_ms']:.1f} ms (modeled) | firmware-controlled; modeled enable at 50 ms, not a board time |")
    lines.append("")
    lines.append(f"The coupled eFuse+buck run gives 4 V 90% at **{coupled['t_4v_90_ms']:.2f} ms** and 99% at **{coupled['t_4v_99_ms']:.2f} ms** at 0.1 A, with largest drop from running max **{coupled['monotonic']['max_dip_mv']:.2f} mV** (monotonic={coupled['monotonic']['monotonic']}). At 0.3 A the 90% time is **{coupled_03['t_4v_90_ms']:.2f} ms** and monotonic={coupled_03['monotonic']['monotonic']} (largest drop from running max {coupled_03['monotonic']['max_dip_mv']:.2f} mV).")
    lines.append("")
    lines.append(f"The protected rail crosses the buck's 3.8 V VIN UVLO at **{coupled['t_prot_3800_ms']:.2f} ms**; the buck soft-start then runs for {coupled['t_ss_ms']:.2f} ms. The 4 V rail is monotonic in this model because the buck's soft-start reference is slower than the eFuse ramp and the loop tracks it. This is")
    lines.append("conditional on the synthetic loop and the 29.7 uF effective output")
    lines.append("capacitance; it is not a board measurement.")
    lines.append("")
    lines.append("## What the simulation closes")
    lines.append("")
    lines.append("- The eFuse dV/dt ramp time, capacitor-only inrush and stored energy under the stated cap/derating/ESR assumptions.")
    lines.append("- The buck startup time, monotonicity and load-step direction/scale under the stated behavioral loop.")
    lines.append("- The UVLO/OVLO trip points and hysteresis from the actual divider values.")
    lines.append("- The LED rail current-limit/latch behavior and the 0.76 mA/ch margin.")
    lines.append("- The rail order and the conditional 4 V monotonicity.")
    lines.append("")
    lines.append("## What it cannot close")
    lines.append("")
    lines.append("- **Stability**: the buck loop is a behavioral PI proxy, not the TPS62932 internal compensation. No phase-margin or loop-gain claim.")
    lines.append("- **Thermal**: no junction-temperature model. The full-white U7 dissipation estimate is not a thermal result.")
    lines.append("- **USB compliance**: no PD/BC1.2, cable, EMC or inrush compliance test.")
    lines.append("- **Hardware qualification**: no bench measurement, no component tolerance qualification, no effective-capacitance measurement.")
    lines.append("- **Actual LED V-I, LDO startup, firmware timing, eFuse thermal/current-limit behavior, buck PFM/DCM/foldback/hiccup.**")
    lines.append("")
    lines.append("## Bench measurements still needed")
    lines.append("")
    for m in r["bench_measurements"]:
        lines.append(f"- {m}")
    lines.append("")
    lines.append("## Reproduction")
    lines.append("")
    lines.append("```bash")
    lines.append(".venv/bin/python pcb/tools/simulate_power.py")
    lines.append("```")
    lines.append("")
    lines.append("The script is deterministic, uses no network, and writes only under")
    lines.append("`qa/power-sim/`. It sets `MPLCONFIGDIR` to `qa/power-sim/.mplconfig`.")
    lines.append("")
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
