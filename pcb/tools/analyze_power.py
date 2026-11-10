#!/usr/bin/env python3
"""Maru60 power-review arithmetic.

This script is an *analysis* tool.  It reads the exported KiCad netlist for the
selected development prototype, verifies the power-tree connectivity and the
component values used below, and computes the numbers recorded in
``qa/power-review/power-review.json``.

It does not run SPICE, does not qualify capacitor effective values, does not
prove loop stability, and does not replace bench measurement.  Every number is
conditional on the assumptions printed in the JSON and in REPORT.md.

Run with the repository virtual environment, for example:

    .venv/bin/python pcb/tools/analyze_power.py

The default output is
``pcb/experiments/resume-20261109-relocated-expansion-zero-opens/qa/power-review/power-review.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = REPO_ROOT / "pcb/experiments/resume-20261109-relocated-expansion-zero-opens"
DEFAULT_NETLIST = EXPERIMENT / "qa/native/netlist.xml"
DEFAULT_BOARD = EXPERIMENT / "pcb/maru60.kicad_pcb"
DEFAULT_OUT = EXPERIMENT / "qa/power-review/power-review.json"

# ---------------------------------------------------------------------------
# Datasheet facts used by the arithmetic.  These are transcribed constants,
# not a substitute for the cited documents.
# ---------------------------------------------------------------------------

TPS25947 = {
    "part": "TPS259470LRPW",
    "source": "https://www.ti.com/lit/ds/symlink/tps25947.pdf",
    "revision": "SLVSFC9C (revised May 2026)",
    "uvlo_rising_v": {"min": 1.183, "typ": 1.200, "max": 1.223},
    "uvlo_falling_v": {"min": 1.076, "typ": 1.090, "max": 1.116},
    "ovlo_rising_v": {"min": 1.183, "typ": 1.200, "max": 1.223},
    "ovlo_falling_v": {"min": 1.076, "typ": 1.090, "max": 1.116},
    "pin_leakage_ua": 0.1,
    "ilim_table_ma": {
        "6.65k": {"min": 425, "typ": 500, "max": 575},
        "3.32k": {"min": 850, "typ": 1007, "max": 1150},
        "1.65k": {"min": 1800, "typ": 2028, "max": 2200},
        "750": {"min": 3960, "typ": 4452, "max": 4840},
        "549": {"min": 5400, "typ": 6068, "max": 6600},
    },
    "current_limit_response_us": 400,
    "fast_trip_ratio": 3.0,
    "fast_trip_response_ns": 500,
    "dvdt_equation": "SR[V/ms] = 2 / C_dVdt[nF]",
    "dvdt_series_resistor_recommendation": "100 ohm in series with C_dVdt for C_dVdt > 10 nF",
}

TPS2553 = {
    "part": "TPS2553DBVR-1",
    "source": "https://www.ti.com/lit/ds/symlink/tps2553.pdf",
    "revision": "SLVS841G (revised October 2026)",
    "equations_ma": {
        "max": "22980 / R_ILIM[kohm]^0.94",
        "nom": "23950 / R_ILIM[kohm]^0.977",
        "min": "25230 / R_ILIM[kohm]^1.016",
    },
    "r_ilim_range_kohm": {"min": 15, "max": 232},
    "response_us": 2,
    "latch_off": True,
}

TPS62932 = {
    "part": "TPS62932DRLR",
    "source": "https://www.ti.com/lit/ds/symlink/tps62932.pdf",
    "revision": "SLUSEA4D (revised August 2022)",
    "vin_recommended_min_v": 3.8,
    "vin_abs_max_v": 30.0,
    "vref_v": 0.8,
    "iss_ua": {"min": 4.5, "typ": 5.5, "max": 6.5},
    "ss_equation": "t_SS[s] = C_SS[F] * VREF[V] / ISS[A]",
    "ss_min_cap_nf": 6.8,
    "input_cap_typical_uf": 10.0,
    "input_cap_additional_uf": 0.1,
    "max_duty_98pct": 0.98,
    "min_off_time_ns": 140,
    "frequency_foldback": True,
}

MAX38902 = {
    "part": "MAX38902AATA+T",
    "source": "https://www.analog.com/media/en/technical-documentation/data-sheets/MAX38902A-MAX38902D.pdf",
    "vin_range_v": {"min": 1.7, "max": 5.5},
    "vout_v": 3.3,
    "iout_ma": 500,
    "dropout_typ_mv_at_500ma": 100,  # assumption; not verified in this repo
}

SK6805 = {
    "part": "SK6805-EC15-001",
    "channels_per_led": 3,
    "per_channel_current_ma_assumption": 5.0,
    "note": (
        "No SK6805 datasheet is present in this repository. 5 mA/channel is an "
        "explicit assumption used for the full-white estimate; the sensitivity "
        "table covers 0.5, 1, 2, 5 and 12 mA/channel. Replace the assumption with "
        "the exact LED datasheet before treating the full-white number as a "
        "specification."
    ),
}

# Generic Class-II (X7R/X5R) DC-bias derating curve used for the existing
# 50 V-rated input capacitors.  This is a screening assumption, not a
# manufacturer guarantee for the unnamed parts.
DERATING_CURVE = [
    {"v": 0.0, "c_over_c0": 1.00},
    {"v": 5.0, "c_over_c0": 0.92},
    {"v": 10.0, "c_over_c0": 0.85},
    {"v": 16.0, "c_over_c0": 0.75},
    {"v": 25.0, "c_over_c0": 0.60},
    {"v": 50.0, "c_over_c0": 0.35},
]

# Existing design-screen values from qa/portable/power/calculations.json.
BUCK_4V_NO_FOLDBACK_IDEAL_V = 400.0 / 93.0  # 4.301075...
BUCK_4V_98PCT_IDEAL_V = 200.0 / 49.0  # 4.081632...
LDO_3V3_MIN_INPUT_ASSUMED_V = 3.4  # 3.3 V + 100 mV assumed dropout
USB_5V_MAX_V = 5.5
USB_DESCRIPTOR_MA = 500.0


# ---------------------------------------------------------------------------
# Netlist parsing
# ---------------------------------------------------------------------------


def parse_netlist(path: Path) -> tuple[dict, dict, dict]:
    """Return (components, nets, net_of) from a KiCad XML netlist."""
    root = ET.parse(path).getroot()
    components: dict[str, dict] = {}
    for comp in root.iter("comp"):
        ref = comp.get("ref")
        if not ref:
            continue
        components[ref] = {
            "value": (comp.findtext("value") or "").strip(),
            "footprint": (comp.findtext("footprint") or "").strip(),
        }

    nets: dict[str, list[tuple[str, str]]] = {}
    net_of: dict[tuple[str, str], str] = {}
    for net in root.iter("net"):
        name = net.get("name")
        if not name:
            continue
        nodes = []
        for node in net.iter("node"):
            ref = node.get("ref")
            pin = node.get("pin")
            if ref and pin:
                nodes.append((ref, pin))
                net_of[(ref, pin)] = name
        nets[name] = nodes
    return components, nets, net_of


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"NETLIST ASSERTION FAILED: {message}")


def parse_capacitance_f(value: str) -> float:
    """Parse the first capacitance in a KiCad value string into farads."""
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(p|n|u|µ|m)?F", value, re.IGNORECASE)
    if not m:
        raise ValueError(f"cannot parse capacitance from {value!r}")
    number = float(m.group(1))
    prefix = (m.group(2) or "").lower()
    scale = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3, "": 1.0}[prefix]
    return number * scale


def parse_resistance_ohm(value: str) -> float:
    """Parse the first resistance in a KiCad value string into ohms."""
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(k|K|M|m)?(?:ohm|Ω)?", value)
    if not m:
        raise ValueError(f"cannot parse resistance from {value!r}")
    number = float(m.group(1))
    prefix = m.group(2) or ""
    scale = {"k": 1e3, "K": 1e3, "M": 1e6, "m": 1e-3, "": 1.0}[prefix]
    return number * scale


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def round_floats(obj, ndigits: int = 6):
    """Recursively round floats for readable, deterministic JSON output."""
    if isinstance(obj, float):
        return round(obj, ndigits)
    if isinstance(obj, dict):
        return {k: round_floats(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, list):
        return [round_floats(v, ndigits) for v in obj]
    return obj


# ---------------------------------------------------------------------------
# Arithmetic helpers
# ---------------------------------------------------------------------------


def derating_at(voltage: float, curve: list[dict]) -> float:
    """Piecewise-linear interpolation of the stated derating curve."""
    if voltage <= curve[0]["v"]:
        return curve[0]["c_over_c0"]
    for a, b in zip(curve, curve[1:]):
        if voltage <= b["v"]:
            frac = (voltage - a["v"]) / (b["v"] - a["v"])
            return a["c_over_c0"] + frac * (b["c_over_c0"] - a["c_over_c0"])
    return curve[-1]["c_over_c0"]


def divider_threshold(vref: float, r_top: float, r_bottom: float) -> float:
    return vref * (r_top + r_bottom) / r_bottom


def divider_corners(
    vref: dict, r_top: float, r_bottom: float, tol: float, leakage_ua: float
) -> dict:
    """Min/typ/max divider threshold with resistor tolerance and pin leakage.

    The leakage term is a sensitivity, not a datasheet-guaranteed signed
    interval.  It is applied symmetrically to the resistor/reference corners.
    """
    r_par = r_top * r_bottom / (r_top + r_bottom)
    leakage_shift = leakage_ua * 1e-6 * r_par * (r_top + r_bottom) / r_bottom
    out = {}
    for label, vref_key, top_factor, bottom_factor in [
        ("min", "min", 1.0 - tol, 1.0 + tol),
        ("typ", "typ", 1.0, 1.0),
        ("max", "max", 1.0 + tol, 1.0 - tol),
    ]:
        v = divider_threshold(vref[vref_key], r_top * top_factor, r_bottom * bottom_factor)
        out[label] = {
            "v": v,
            "with_leakage_min_v": v - leakage_shift,
            "with_leakage_max_v": v + leakage_shift,
        }
    out["leakage_shift_v"] = leakage_shift
    out["r_parallel_ohm"] = r_par
    return out


def tps2553_currents_ma(r_kohm: float, tol: float) -> dict:
    """TPS2553 min/nom/max current limit including R_ILIM tolerance.

    The datasheet equations already include process/temperature variation.
    The external resistor tolerance is applied by using the worst resistor
    value for each current corner: Rmax for Imin, Rnom for Inom, Rmin for Imax.
    """
    r_min = r_kohm * (1.0 - tol)
    r_max = r_kohm * (1.0 + tol)
    return {
        "min_ma": 25230.0 / (r_max ** 1.016),
        "nom_ma": 23950.0 / (r_kohm ** 0.977),
        "max_ma": 22980.0 / (r_min ** 0.94),
        "r_min_kohm": r_min,
        "r_nom_kohm": r_kohm,
        "r_max_kohm": r_max,
    }


def soft_start_corners(c_ss_f: float, c_tol: float, iss_ua: dict, vref: float) -> dict:
    """Eight non-nominal corners: C in {min,nom,max} x ISS in {min,nom,max}."""
    c_values = {
        "min": c_ss_f * (1.0 - c_tol),
        "nom": c_ss_f,
        "max": c_ss_f * (1.0 + c_tol),
    }
    corners = []
    for c_label, c in c_values.items():
        for i_label, i_ua in iss_ua.items():
            if c_label == "nom" and i_label == "typ":
                continue
            t_s = c * vref / (i_ua * 1e-6)
            corners.append(
                {
                    "c_label": c_label,
                    "c_nf": c * 1e9,
                    "iss_label": i_label,
                    "iss_ua": i_ua,
                    "t_ms": t_s * 1e3,
                }
            )
    times = [c["t_ms"] for c in corners]
    return {
        "corners": corners,
        "min_ms": min(times),
        "max_ms": max(times),
        "nominal_ms": c_ss_f * vref / (iss_ua["typ"] * 1e-6) * 1e3,
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------


def analyze(netlist_path: Path, board_path: Path) -> dict:
    components, nets, net_of = parse_netlist(netlist_path)

    # --- Verify the power-tree connectivity and values ---------------------
    expected_values = {
        "C126": "1uF",
        "C136": "100nF",
        "C137": "4.7uF",
        "C139": "100nF",
        "C124": "10nF",
        "R120": "590k",
        "R121": "156k",
        "R122": "620k",
        "R123": "267k",
        "R112": "133k",
        "R124": "6.65k",
        "U18": "TPS62932",
        "U8": "TPS259470",
        "U7": "TPS2553",
        "U2": "MAX38902",
    }
    for ref, token in expected_values.items():
        require(ref in components, f"missing component {ref}")
        require(
            token.lower() in components[ref]["value"].lower(),
            f"{ref} value {components[ref]['value']!r} does not contain {token!r}",
        )

    expected_nets = {
        "VBUS_PROTECTED_RAW": {
            ("C126", "1"),
            ("C136", "1"),
            ("C137", "1"),
            ("U18", "3"),
            ("U8", "6"),
        },
        "BUCK_SS": {("C139", "1"), ("U18", "7")},
        "USB_UVLO": {("R122", "2"), ("R123", "1"), ("U8", "1")},
        "USB_OVLO": {("R120", "2"), ("R121", "1"), ("U8", "2")},
        "LED_ILIM": {("R112", "1"), ("U7", "5")},
        "USB_ILM": {("R124", "1"), ("U8", "9")},
        "USB_DVDT": {("R125", "1"), ("U8", "7")},
        "+4V_REG": {("U2", "1"), ("U2", "3"), ("U7", "1"), ("L2", "2")},
    }
    for net, required in expected_nets.items():
        require(net in nets, f"missing net {net}")
        present = set(nets[net])
        require(required <= present, f"net {net} missing {sorted(required - present)}")

    require("+4V_LED" in nets, "missing +4V_LED net")
    led_refs = sorted(
        {ref for ref, pin in nets["+4V_LED"] if ref.startswith("LED") and pin == "2"}
    )
    require(len(led_refs) == 76, f"expected 76 LEDs on +4V_LED, found {len(led_refs)}")
    require(("U7", "6") in nets["+4V_LED"], "U7 VOUT is not on +4V_LED")

    # --- Component values --------------------------------------------------
    c126 = parse_capacitance_f(components["C126"]["value"])
    c136 = parse_capacitance_f(components["C136"]["value"])
    c137 = parse_capacitance_f(components["C137"]["value"])
    c139 = parse_capacitance_f(components["C139"]["value"])
    c124 = parse_capacitance_f(components["C124"]["value"])
    r120 = parse_resistance_ohm(components["R120"]["value"])
    r121 = parse_resistance_ohm(components["R121"]["value"])
    r122 = parse_resistance_ohm(components["R122"]["value"])
    r123 = parse_resistance_ohm(components["R123"]["value"])
    r112 = parse_resistance_ohm(components["R112"]["value"])
    r124 = parse_resistance_ohm(components["R124"]["value"])

    c_input_nom = c126 + c136 + c137
    c_input_eff = c_input_nom * derating_at(5.0, DERATING_CURVE)

    # --- Input capacitance -------------------------------------------------
    ti_typical = TPS62932["input_cap_typical_uf"] * 1e-6
    required_effective = ti_typical - c_input_eff
    add_derating = derating_at(5.0, DERATING_CURVE)
    required_nominal = required_effective / add_derating
    standard_options = []
    for nominal_uf in [4.7, 5.6, 6.8, 10.0]:
        eff = nominal_uf * 1e-6 * add_derating
        standard_options.append(
            {
                "nominal_uf": nominal_uf,
                "assumed_derating_at_5v": add_derating,
                "effective_uf": eff * 1e6,
                "total_effective_uf": (c_input_eff + eff) * 1e6,
                "meets_10uf_effective": (c_input_eff + eff) >= ti_typical,
            }
        )

    input_capacitance = {
        "nominal_uf": c_input_nom * 1e6,
        "nominal_breakdown_uf": {
            "C126": c126 * 1e6,
            "C136": c136 * 1e6,
            "C137": c137 * 1e6,
        },
        "ti_typical_uf": ti_typical * 1e6,
        "ti_additional_uf": TPS62932["input_cap_additional_uf"],
        "derating_curve": DERATING_CURVE,
        "derating_at_5v": add_derating,
        "effective_uf_at_5v": c_input_eff * 1e6,
        "nominal_ratio_to_ti_typical": c_input_nom / ti_typical,
        "effective_ratio_to_ti_typical": c_input_eff / ti_typical,
        "additional_cap": {
            "required_effective_uf": required_effective * 1e6,
            "required_nominal_uf_at_assumed_derating": required_nominal * 1e6,
            "nearest_standard_uf": 5.6,
            "standard_options": standard_options,
        },
        "verdict": (
            "BELOW_TI_TYPICAL_GUIDANCE_NOT_PROVEN_INSTABILITY. 5.8 uF nominal "
            "is 58% of TI's 10 uF typical recommendation; the assumed 0.92 "
            "derating gives 5.336 uF effective (53.4%). This is a review flag, "
            "not a measured failure and not a stability result."
        ),
    }

    # --- Inrush ------------------------------------------------------------
    sr_v_per_ms = 2.0 / (c124 * 1e9)  # TPS25947 Eq. 4, C in nF
    sr_v_per_s = sr_v_per_ms * 1e3
    inrush_a = c_input_nom * sr_v_per_s
    energy_j = 0.5 * c_input_nom * 5.0**2
    time_to_5v_ms = 5.0 / sr_v_per_ms
    c_with_add = c_input_nom + 5.6e-6
    inrush_with_add_a = c_with_add * sr_v_per_s
    energy_with_add_j = 0.5 * c_with_add * 5.0**2
    efuse_ilim = TPS25947["ilim_table_ma"]["6.65k"]

    inrush = {
        "c_dvdt_nf": c124 * 1e9,
        "slew_v_per_ms": sr_v_per_ms,
        "slew_v_per_s": sr_v_per_s,
        "time_to_5v_ms": time_to_5v_ms,
        "load_capacitance_uf": c_input_nom * 1e6,
        "capacitor_current_ma": inrush_a * 1e3,
        "capacitor_energy_uj": energy_j * 1e6,
        "efuse_ilim_ma": efuse_ilim,
        "usb_descriptor_ma": USB_DESCRIPTOR_MA,
        "ratio_to_efuse_min": inrush_a / (efuse_ilim["min"] * 1e-3),
        "ratio_to_usb_descriptor": inrush_a / (USB_DESCRIPTOR_MA * 1e-3),
        "efuse_response": (
            "The dV/dt-controlled capacitor current is far below the 425 mA "
            "minimum ILIM, so the eFuse does not current-limit the capacitor "
            "alone. The 400 us current-limit response and 500 ns fast-trip are "
            "not expected to act on this ramp. Active buck/LED load current is "
            "additional and is not included."
        ),
        "with_added_5p6uf": {
            "load_capacitance_uf": c_with_add * 1e6,
            "capacitor_current_ma": inrush_with_add_a * 1e3,
            "capacitor_energy_uj": energy_with_add_j * 1e6,
        },
        "verdict": (
            "Capacitor-only inrush is ~1.16 mA at 5.8 uF and 0.2 V/ms, ~0.23% "
            "of the 500 mA USB descriptor and ~0.27% of the 425 mA eFuse "
            "minimum. Inrush is not the limiting compliance issue; steady-state "
            "LED load is."
        ),
    }

    # --- UVLO / OVLO -------------------------------------------------------
    uvlo = divider_corners(
        TPS25947["uvlo_rising_v"], r122, r123, 0.001, TPS25947["pin_leakage_ua"]
    )
    uvlo_fall = divider_corners(
        TPS25947["uvlo_falling_v"], r122, r123, 0.001, TPS25947["pin_leakage_ua"]
    )
    ovlo = divider_corners(
        TPS25947["ovlo_rising_v"], r120, r121, 0.001, TPS25947["pin_leakage_ua"]
    )
    ovlo_fall = divider_corners(
        TPS25947["ovlo_falling_v"], r120, r121, 0.001, TPS25947["pin_leakage_ua"]
    )

    def margin_table(corners: dict, reference_v: float) -> dict:
        return {
            "reference_v": reference_v,
            "min_margin_v": corners["min"]["v"] - reference_v,
            "typ_margin_v": corners["typ"]["v"] - reference_v,
            "max_margin_v": corners["max"]["v"] - reference_v,
            "min_margin_with_leakage_v": corners["min"]["with_leakage_min_v"] - reference_v,
            "max_margin_with_leakage_v": corners["max"]["with_leakage_max_v"] - reference_v,
        }

    uvlo_ovlo = {
        "resistors": {
            "R120_ohm": r120,
            "R121_ohm": r121,
            "R122_ohm": r122,
            "R123_ohm": r123,
            "tolerance": 0.001,
        },
        "uvlo_rising": uvlo,
        "uvlo_falling": uvlo_fall,
        "ovlo_rising": ovlo,
        "ovlo_falling": ovlo_fall,
        "margins": {
            "uvlo_rising_vs_buck_4v_no_foldback_ideal": margin_table(
                uvlo, BUCK_4V_NO_FOLDBACK_IDEAL_V
            ),
            "uvlo_rising_vs_buck_4v_98pct_ideal": margin_table(
                uvlo, BUCK_4V_98PCT_IDEAL_V
            ),
            "uvlo_rising_vs_buck_recommended_min_3v8": margin_table(
                uvlo, TPS62932["vin_recommended_min_v"]
            ),
            "uvlo_falling_vs_ldo_3v3_min_input_assumed": margin_table(
                uvlo_fall, LDO_3V3_MIN_INPUT_ASSUMED_V
            ),
            "ovlo_rising_vs_usb_5v5_max": margin_table(ovlo, USB_5V_MAX_V),
        },
        "verdict": (
            "UVLO rising is ~3.99 V nominal (3.86-4.13 V with resistor, "
            "reference and leakage sensitivity). That is above the buck's "
            "3.8 V recommended minimum but below the 4.30 V no-foldback ideal "
            "and at/below the 4.08 V 98%-duty ideal at the nominal/min corners. "
            "The 4 V rail may rely on frequency foldback at UVLO release. OVLO "
            "rising is ~5.74 V nominal; the min corner with leakage is ~5.59 V, "
            "only ~89 mV above the 5.5 V USB maximum. Both are review flags, not "
            "measured failures."
        ),
    }

    # --- Soft start --------------------------------------------------------
    ss = soft_start_corners(c139, 0.10, TPS62932["iss_ua"], TPS62932["vref_v"])
    # Existing conservative screen from qa/portable/power/calculations.json:
    # ISS 4.41/5.5/6.63 uA (slightly wider than the datasheet 4.5/6.5 uA).
    ss_existing = soft_start_corners(
        c139, 0.10, {"min": 4.41, "typ": 5.5, "max": 6.63}, TPS62932["vref_v"]
    )
    soft_start = {
        "c_ss_nf": c139 * 1e9,
        "c_tolerance": 0.10,
        "vref_v": TPS62932["vref_v"],
        "iss_ua": TPS62932["iss_ua"],
        "equation": TPS62932["ss_equation"],
        "nominal_ms": ss["nominal_ms"],
        "corners": ss["corners"],
        "min_ms": ss["min_ms"],
        "max_ms": ss["max_ms"],
        "existing_conservative_screen": {
            "iss_ua": {"min": 4.41, "typ": 5.5, "max": 6.63},
            "min_ms": ss_existing["min_ms"],
            "max_ms": ss_existing["max_ms"],
            "note": (
                "The existing calculations.json used 4.41/6.63 uA, slightly "
                "wider than the datasheet 4.5/6.5 uA. Both are analysis "
                "screens, not measured startup times."
            ),
        },
        "verdict": (
            "Nominal SS reference ramp is 14.545 ms; the datasheet-limit 8 "
            "corners span 11.077-19.556 ms. The existing conservative screen "
            "spans 10.855-19.947 ms. This is the SS reference ramp, not the "
            "observed board startup, and it excludes capacitor derating, the "
            "eFuse ramp and load dynamics."
        ),
    }

    # --- LED limiter -------------------------------------------------------
    led_currents = tps2553_currents_ma(r112 / 1e3, 0.01)
    led_count = len(led_refs)
    channels = SK6805["channels_per_led"]
    per_channel_ma = SK6805["per_channel_current_ma_assumption"]
    full_white_a = led_count * channels * per_channel_ma * 1e-3
    sensitivity = []
    for ich_ma in [0.5, 1.0, 2.0, 5.0, 12.0]:
        total_a = led_count * channels * ich_ma * 1e-3
        sensitivity.append(
            {
                "per_channel_ma": ich_ma,
                "per_led_ma": ich_ma * channels,
                "total_a": total_a,
                "ratio_to_min_limit": total_a / (led_currents["min_ma"] * 1e-3),
                "ratio_to_nom_limit": total_a / (led_currents["nom_ma"] * 1e-3),
                "ratio_to_max_limit": total_a / (led_currents["max_ma"] * 1e-3),
            }
        )
    max_per_channel_for_min = led_currents["min_ma"] / (led_count * channels)
    max_per_channel_for_max = led_currents["max_ma"] / (led_count * channels)

    led_limiter = {
        "r_ilim_kohm": r112 / 1e3,
        "r_ilim_tolerance": 0.01,
        "equations_ma": TPS2553["equations_ma"],
        "currents_ma": {
            "min": led_currents["min_ma"],
            "nom": led_currents["nom_ma"],
            "max": led_currents["max_ma"],
        },
        "r_corners_kohm": {
            "min": led_currents["r_min_kohm"],
            "nom": led_currents["r_nom_kohm"],
            "max": led_currents["r_max_kohm"],
        },
        "led_count": led_count,
        "channels_per_led": channels,
        "per_channel_current_assumption_ma": per_channel_ma,
        "full_white_current_a": full_white_a,
        "full_white_ratio_to_limits": {
            "min": full_white_a / (led_currents["min_ma"] * 1e-3),
            "nom": full_white_a / (led_currents["nom_ma"] * 1e-3),
            "max": full_white_a / (led_currents["max_ma"] * 1e-3),
        },
        "max_per_channel_current_for_min_limit_ma": max_per_channel_for_min,
        "max_per_channel_current_for_max_limit_ma": max_per_channel_for_max,
        "sensitivity": sensitivity,
        "latch_off": TPS2553["latch_off"],
        "verdict": (
            "R112 = 133 kohm 1% sets 173.657/201.513/233.901 mA (min/nom/max) "
            "using the TPS2553 datasheet equations and the resistor tolerance. "
            "At the stated 5 mA/channel assumption, 76 SK6805 LEDs at full "
            "white draw 1.14 A, 4.87-6.56x the limiter. The TPS2553-1 is a "
            "latch-off part, so a full-white attempt is expected to latch the "
            "LED rail off, not merely dim it. The eFuse 500 mA nominal is also "
            "below 1.14 A. Full-white capability is not supported by this "
            "power tree."
        ),
    }

    # --- Sequencing --------------------------------------------------------
    sequencing = {
        "order": [
            "VBUS (USB-C J1)",
            "F1 polyfuse -> VBUS_FUSED",
            "U8 TPS259470 eFuse -> VBUS_PROTECTED_RAW",
            "U18 TPS62932 buck -> +4V_REG",
            "U2 MAX38902 LDO -> +3V3",
            "U7 TPS2553-1 switch -> +4V_LED (enabled by GPIO22 through R109)",
        ],
        "timing": {
            "efuse_slew_v_per_ms": sr_v_per_ms,
            "efuse_time_to_5v_ms": time_to_5v_ms,
            "efuse_uvlo_release_nominal_ms": uvlo["typ"]["v"] / sr_v_per_ms,
            "buck_ss_nominal_ms": ss["nominal_ms"],
            "buck_4v_ready_after_efuse_release_nominal_ms": ss["nominal_ms"],
            "buck_4v_ready_after_vbus_nominal_ms": (
                uvlo["typ"]["v"] / sr_v_per_ms + ss["nominal_ms"]
            ),
            "ldo_3v3_startup_ms": "unknown; MAX38902 BYP/soft-start not measured here",
            "led_rail_enable": "firmware-controlled after boot; R109 100k pulls EN low at reset",
        },
        "verdict": (
            "The netlist order is VBUS -> FUSED -> PROTECTED -> 4V -> 3V3 -> "
            "LED rail. The eFuse 25 ms ramp and the buck 14.5 ms SS overlap: the "
            "buck starts at the eFuse UVLO release (~20 ms) while the input is "
            "still ramping. The 4 V rail may not be monotonic. The LED rail is "
            "last and is held off by R109 until firmware drives GPIO22. Measure "
            "the actual rail order and monotonicity."
        ),
    }

    # --- Findings / unknowns / bench --------------------------------------
    findings = [
        {
            "id": "PWR-01",
            "severity": "review-flag",
            "title": "Input capacitance is below TI's 10 uF typical guidance",
            "detail": (
                "5.8 uF nominal (1 uF + 100 nF + 4.7 uF) and 5.336 uF effective "
                "at 5 V under the stated 0.92 derating. This is 58%/53% of the "
                "10 uF typical recommendation. It is not a proven instability."
            ),
        },
        {
            "id": "PWR-02",
            "severity": "review-flag",
            "title": "UVLO release is below the 4 V buck's no-foldback input",
            "detail": (
                "UVLO rising ~3.99 V nominal vs 4.30 V no-foldback ideal and "
                "4.08 V 98%-duty ideal. The 4 V rail may rely on frequency "
                "foldback at startup."
            ),
        },
        {
            "id": "PWR-03",
            "severity": "review-flag",
            "title": "OVLO min corner is close to the 5.5 V USB maximum",
            "detail": (
                "OVLO rising ~5.74 V nominal; ~5.59 V at the min corner with "
                "0.1% resistors, reference tolerance and 0.1 uA leakage. That "
                "is ~89 mV above 5.5 V."
            ),
        },
        {
            "id": "PWR-04",
            "severity": "review-flag",
            "title": "LED rail limiter cannot support 76 LEDs at full white",
            "detail": (
                "173.657/201.513/233.901 mA vs 1.14 A at 5 mA/channel. The "
                "TPS2553-1 latches off on overcurrent. The eFuse 500 mA nominal "
                "is also below 1.14 A."
            ),
        },
        {
            "id": "PWR-05",
            "severity": "review-flag",
            "title": "eFuse ILIM min is below the 500 mA USB descriptor",
            "detail": (
                "R124 = 6.65 kohm gives 425/500/575 mA. The 425 mA minimum is "
                "15% below the 500 mA descriptor, so the board cannot guarantee "
                "500 mA. The LED rail plus MCU/load must stay below 425 mA."
            ),
        },
        {
            "id": "PWR-06",
            "severity": "review-flag",
            "title": "eFuse ramp and buck soft-start overlap",
            "detail": (
                "The eFuse 0.2 V/ms ramp takes 25 ms to 5 V; the buck SS is "
                "14.5 ms and starts at the ~20 ms UVLO release. The 4 V rail "
                "may not be monotonic."
            ),
        },
    ]

    unknowns = [
        "Exact C126/C136/C137 MPNs, dielectrics and DC-bias curves; the 0.92 derating is an assumption.",
        "Actual VBUS source/cable impedance and input ramp/dip waveform.",
        "Actual SK6805 per-channel current; 5 mA is an assumption, not a datasheet fact in this repo.",
        "Actual MCU, flash, logic and LED load currents and their simultaneity.",
        "TPS62932 loop stability, phase margin, load-step response and frequency-foldback behavior on this board.",
        "TPS259470 thermal/current-limit behavior and actual trip point on this board.",
        "MAX38902 dropout, startup and thermal behavior at the actual 3V3 load.",
        "Firmware LED brightness cap, fault handling and latch-off recovery.",
        "Whether the 4 V rail is monotonic through the eFuse/buck overlap.",
    ]

    bench_measurements = [
        "VBUS, VBUS_FUSED, VBUS_PROTECTED_RAW, +4V_REG, +3V3 and +4V_LED startup at 5.0 V and 5.5 V, hot and cold, with the actual cable.",
        "Input ripple at U18 VIN at no load, MCU load and LED full-white attempt.",
        "UVLO/OVLO trip points by sweeping VBUS up and down on the assembled board.",
        "LED rail current and U7 FAULT/latch behavior at full white and at the intended firmware brightness cap.",
        "3V3 load step and LDO thermal at the actual load.",
        "Buck load step and, if stability is to be claimed, loop gain/phase across the application corners.",
        "eFuse current limit and thermal at 425/500/575 mA.",
        "Soft-start time and monotonicity of the 4 V rail.",
    ]

    recommendation = {
        "primary": "ADD_CAP",
        "detail": (
            "Add a 5.6 uF/50 V X7R (or 6.8 uF) on VBUS_PROTECTED_RAW to reach "
            ">=10 uF effective at 5 V under the stated 0.92 derating. This is a "
            "margin improvement, not a stability proof. If board space is "
            "tight, measure the existing 5.8 uF first; the analysis does not "
            "show that 5.8 uF fails."
        ),
        "led": (
            "Do not claim full-white LED capability. Either enforce a firmware "
            "brightness cap of <=0.76 mA/channel at the min limiter corner, or "
            "change the LED rail current limit and the USB power source. The "
            "current R112 = 133 kohm cannot pass 1.14 A."
        ),
        "uvlo": (
            "If the 4 V rail must be regulated at startup, raise the UVLO "
            "rising threshold above ~4.3 V (e.g. 4.5 V) by changing R122/R123, "
            "and re-check the OVLO margin."
        ),
        "measure_first": (
            "Measure the actual startup, input ripple, UVLO/OVLO trip points and "
            "LED rail current before changing the board. The analysis identifies "
            "margins; it does not prove a failure."
        ),
    }

    result = {
        "schema": "maru60-power-review/v1",
        "analysis_date_utc": "2026-11-10",
        "status": "ANALYSIS_ONLY",
        "qualification": (
            "No stability, thermal, USB compliance, EMC, or hardware "
            "qualification. No SPICE, no bench measurement, no effective-"
            "capacitance qualification. All numbers are conditional on the "
            "stated assumptions."
        ),
        "board": {
            "path": str(board_path.relative_to(REPO_ROOT)),
            "sha256": sha256(board_path),
        },
        "netlist": {
            "path": str(netlist_path.relative_to(REPO_ROOT)),
            "sha256": sha256(netlist_path),
        },
        "sources": {
            "tps25947": TPS25947,
            "tps2553": TPS2553,
            "tps62932": TPS62932,
            "max38902": MAX38902,
            "sk6805": SK6805,
        },
        "inputs": {
            "components": {
                ref: components[ref] for ref in sorted(expected_values)
            },
            "led_count": led_count,
            "led_refs": led_refs,
        },
        "input_capacitance": input_capacitance,
        "inrush": inrush,
        "uvlo_ovlo": uvlo_ovlo,
        "soft_start": soft_start,
        "led_limiter": led_limiter,
        "sequencing": sequencing,
        "findings": findings,
        "unknowns": unknowns,
        "bench_measurements": bench_measurements,
        "recommendation": recommendation,
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    result = round_floats(analyze(args.netlist, args.board))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    ic = result["input_capacitance"]
    inr = result["inrush"]
    led = result["led_limiter"]
    ss = result["soft_start"]
    uv = result["uvlo_ovlo"]
    print(f"wrote {args.out}")
    print(
        "input: "
        f"{ic['nominal_uf']:.3f} uF nominal, "
        f"{ic['effective_uf_at_5v']:.3f} uF effective at 5 V, "
        f"{ic['effective_ratio_to_ti_typical']*100:.1f}% of TI 10 uF typical"
    )
    print(
        "inrush: "
        f"{inr['slew_v_per_ms']:.3f} V/ms, "
        f"{inr['capacitor_current_ma']:.3f} mA, "
        f"{inr['capacitor_energy_uj']:.3f} uJ"
    )
    print(
        "UVLO rising: "
        f"{uv['uvlo_rising']['min']['v']:.3f}/"
        f"{uv['uvlo_rising']['typ']['v']:.3f}/"
        f"{uv['uvlo_rising']['max']['v']:.3f} V; "
        "OVLO rising: "
        f"{uv['ovlo_rising']['min']['v']:.3f}/"
        f"{uv['ovlo_rising']['typ']['v']:.3f}/"
        f"{uv['ovlo_rising']['max']['v']:.3f} V"
    )
    print(
        "soft-start: "
        f"{ss['nominal_ms']:.3f} ms nominal, "
        f"{ss['min_ms']:.3f}-{ss['max_ms']:.3f} ms 8-corner"
    )
    print(
        "LED limiter: "
        f"{led['currents_ma']['min']:.3f}/"
        f"{led['currents_ma']['nom']:.3f}/"
        f"{led['currents_ma']['max']:.3f} mA; "
        f"full white {led['full_white_current_a']:.3f} A at "
        f"{led['per_channel_current_assumption_ma']:.1f} mA/channel"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
