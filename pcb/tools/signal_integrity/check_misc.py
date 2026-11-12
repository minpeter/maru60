"""QSPI flash, SWD, RUN / BOOTSEL and the expansion port: hand calculations from the
routed geometry (geometry.json), the 2-D field solve and datasheet values.
Nothing here is simulated in ngspice; every figure is labelled computed / datasheet / assumed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fieldsolve as fs  # noqa: E402
import spice  # noqa: E402

PIN_C = 5.0          # pF, ASSUMED for an RP2350 pad (not in the datasheet)
RPU = (32e3, 86e3)   # RP2350 Table 1683, IOVDD 3.3 V
VIL, VIH = 0.8, 2.0


def cm_per_mm(gap, w=0.15):
    return fs.coupled(w, w, gap)["Cm_pF_per_mm"]


def crosstalk(victim, geo, swing, exclude=()):
    """Capacitive step on a high-impedance victim if every listed neighbour switches at once."""
    cv = geo[victim]["cap"]["C_copper_pF"] + PIN_C
    rows, total = [], 0.0
    for other, nb in geo[victim]["neighbours"].items():
        if other in exclude or other.startswith("+") or other in ("GND", "RESET_GND"):
            continue
        # coupled length within 0.6 mm, weighted with the mutual capacitance at the closest gap for the
        # part within 0.35 mm and at 0.5 mm for the rest
        near = nb["len_le_0p35"]
        far = nb["len_le_0p6"] - near
        c = near * cm_per_mm(max(nb["min_gap"], 0.15)) + far * cm_per_mm(0.5)
        total += c
        rows.append({"aggressor": other, "min_gap_mm": nb["min_gap"], "len_le_0p35_mm": near, "Cm_pF": round(c, 4),
                     "step_mV": round(swing * c / (cv + c) * 1e3, 1)})
    return {"victim_C_pF": round(cv, 2), "aggressors": rows, "Cm_total_pF": round(total, 4),
            "step_all_at_once_mV": round(swing * total / (cv + total) * 1e3, 1)}


def main():
    g = spice.geometry()
    n = g["nets"]
    table = spice.lines()
    ps = table["single"]["0.15"]["delay_ps_per_mm"]
    out = {}

    # ---- QSPI ----
    q = {}
    for k in ("QSPI_SCLK", "QSPI_SD0", "QSPI_SD1", "QSPI_SD2", "QSPI_SD3", "QSPI_SS"):
        q[k] = {"length_mm": n[k]["length_mm"], "vias": n[k]["vias"], "delay_ps": round(n[k]["length_mm"] * ps, 1),
                "stubs_mm": [(s["length_mm"], s["pads"]) for s in n[k]["stubs"] if s["length_mm"] > 0.3],
                "C_copper_pF": n[k]["cap"]["C_copper_pF"], "C_load_pF": round(n[k]["cap"]["C_copper_pF"] + 6.0, 2)}
    data = [q[k]["length_mm"] for k in ("QSPI_SD0", "QSPI_SD1", "QSPI_SD2", "QSPI_SD3")]
    sclk = q["QSPI_SCLK"]["length_mm"]
    worst = max(abs(x - sclk) for x in data)
    rt = (sclk + max(data)) * ps * 1e-3   # ns, clock out + data back
    rates = {}
    for name, f in (("boot ROM and this firmware: clk_sys / 6, 03h read (25 MHz at 150 MHz)", 25e6),
                    ("fastest the QMI allows: clk_sys / 2 (75 MHz), not configured by this firmware", 75e6)):
        half = 0.5e9 / f
        rates[name] = {"half_period_ns": round(half, 2), "flash_tCLQV_max_ns": 6.0, "board_round_trip_ns": round(rt, 3),
                       "slack_to_next_rising_edge_ns": round(half - 6.0 - rt, 2),
                       "board_share_of_half_period_pct": round(100 * rt / half, 2)}
    out["qspi"] = {"nets": q, "data_vs_clock_mismatch_mm_max": round(worst, 2), "mismatch_ps_max": round(worst * ps, 1),
                   "data_to_data_mismatch_mm": round(max(data) - min(data), 2), "rates": rates,
                   "flash_limits": {"FR_MHz": 133, "fR_03h_MHz": 50, "tCLQV_ns": 6, "CIN_pF": 6, "COUT_pF": 8},
                   "electrical_length_note": "longest net 23.5 mm = 0.14 ns; a 1 ns edge is 7 times longer, so the nets are lumped"}

    # ---- BOOTSEL / QSPI_SS ----
    out["bootsel"] = {
        "QSPI_SS_branches_mm": q["QSPI_SS"]["stubs_mm"], "BOOT_BUTTON_net_mm": n["BOOT_BUTTON"]["net_total"]["length_mm"],
        "BOOT_BUTTON_C_pF": n["BOOT_BUTTON"]["cap"]["C_copper_pF"],
        "isolation": "R106 1 k between QSPI_SS and the 39 mm BOOT_BUTTON net: tau = 1 k x 5.3 pF = 5 ns, load on /CS is 1 k in series",
        "level_with_button_pressed_V": round(3.3 * 1.0 / (10.0 + 1.0), 2), "VIL_V": VIL,
        "esd_note": "IEC 61000-4-2 source is 330 ohm / 150 pF; through R106 the peak current is V / 1.33 k. 2 kV gives 1.5 A, about the 1.33 A of the 2 kV HBM rating (RP2350 Table 1681). The pad is not protected beyond that.",
        "neighbours": n["BOOT_BUTTON"]["neighbours"],
    }

    # ---- SWD ----
    out["swd"] = {k: {"length_mm": n[k]["length_mm"], "vias": n[k]["vias"], "C_copper_pF": n[k]["cap"]["C_copper_pF"],
                      "delay_ps": round(n[k]["length_mm"] * ps, 1), "plane_openings_mm": n[k]["plane_openings_not_own_via_mm"],
                      "crosstalk_if_idle_high_Z": crosstalk(k, n, 3.3)} for k in ("SWCLK", "SWDIO")}
    out["swd"]["limit"] = "RP2350 Table 1687: SWCLK 10 MHz typ, 50 MHz max. 67 mm = 0.4 ns one way, 2.5 % of a 16 ns half period at 30 MHz."

    # ---- RUN ----
    run = crosstalk("RUN", n, 3.3)
    buck = g["buck_switch_node"]["nets_within_6mm"].get("RUN", {})
    cp = fs.coupled(0.15, 2.4, buck.get("min_distance_mm_B.Cu", 1.72))
    cm_buck = cp["Cm_pF_per_mm"] * 6.0
    out["run"] = {
        "length_mm": n["RUN"]["net_total"]["length_mm"], "vias": n["RUN"]["vias"], "C_copper_pF": n["RUN"]["cap"]["C_copper_pF"],
        "pull_up_ohm": RPU, "RC_us": [round(r * (n["RUN"]["cap"]["C_copper_pF"] + PIN_C) * 1e-6, 2) for r in RPU],
        "crosstalk": run,
        "drop_needed_for_reset_V": round(3.3 - VIL, 2),
        "crosstalk_margin_x": round((3.3 - VIL) * 1e3 / max(run["step_all_at_once_mV"], 1e-3), 1),
        "buck_switch_node": {"distance_mm": buck.get("min_distance_mm_B.Cu"), "Cm_fF_over_6mm": round(cm_buck * 1e3, 3),
                             "step_mV_for_5V_edge": round(5.0 * cm_buck / (run["victim_C_pF"] + cm_buck) * 1e3, 3)},
        "reset_button_low_level_V": round(3.3 * 1e3 / (1e3 + RPU[0]), 3),
        "note": "RUN has only the internal pull-up, no capacitor, an exposed 1 mm test pad (TP6) and 87 mm of track. The datasheet states no glitch filter, so none is assumed.",
    }

    # ---- expansion port ----
    exp = {}
    for gp in ("3", "10", "24", "25", "26", "27"):
        mcu, iso, ext = n[f"MCU_GPIO{gp}"], n[f"GPIO{gp}_ISO"], n[f"EXT_GPIO{gp}"]
        c_mcu = mcu["cap"]["C_copper_pF"] + PIN_C
        c_out = iso["cap"]["C_copper_pF"] + 5.0 + ext["cap"]["C_copper_pF"] + 0.47   # switch Cio 5 pF typ, TPD6E05U06 0.47 pF
        exp[f"GPIO{gp}"] = {
            "mcu_side_mm": mcu["length_mm"], "ext_side_mm": ext["net_total"]["length_mm"],
            "C_mcu_side_pF": round(c_mcu, 2), "C_connector_side_pF": round(c_out, 2),
            "tau_in_ns_ext_drives_mcu": round(1e3 * c_mcu * 1e-3, 1),
            "tau_out_ns_mcu_drives_20pF_cable": round(1e3 * (c_out + 20.0) * 1e-3, 1),
            "neighbours_mcu_side": {k: v for k, v in list(mcu["neighbours"].items())[:3]},
        }
    div = 39.0 / 40.0
    out["expansion"] = {
        "per_line": exp,
        "switch_off_or_board_unpowered": {
            "SN74CB3T3245 IOZ_uA_max": 10, "Ioff_uA_max_VCC_0": 10, "TPD6E05U06_leak_nA_max_at_2V5": 10,
            "MCU_pin_offset_from_IOZ_V_max": round(10e-6 * 39e3, 2), "VIL_V": VIL,
            "back_power_path": "none: the switch isolates with Ioff, and U13 has clamp diodes to GND only (no supply pin)",
            "load_on_external_driver_pF": "about 12-13 (5 pF switch + 0.47 pF U13 + 6-7.5 pF track)",
        },
        "switch_on": {
            "pass_voltage_note": "SN74CB3T3245 Figure 8-3 (VCC 3.0 V, 1 uA): output 2.8 V for inputs 2-3.9 V, 3.15 V for inputs above 4.5 V; Figure 5-2 (25 C, VI 5.5 V, 100 uA): 3.15-3.2 V at VCC 3.3 V. Scaled to VCC 3.3 V below.",
            "ext_3V3": {"switch_out_V": [2.9, 3.1], "at_MCU_pin_V": [round(2.9 * div, 2), round(3.1 * div, 2)], "margin_to_VIH_V": round(2.9 * div - VIH, 2)},
            "ext_5V0": {"switch_out_V": [3.1, 3.45], "at_MCU_pin_V": [round(3.1 * div, 2), round(3.45 * div, 2)],
                        "IOVDD_plus_0V3_limit_V": 3.6, "current_from_5V_source_uA": round(3.3 / 40e3 * 1e6 + 20, 0)},
            "ext_0V": {"at_MCU_pin_V": 0.0},
            "mcu_drives_out": "3.3 V through 1 k + about 5 ohm; a 5 V CMOS input (VIH 3.5 V) is not met, 5 V TTL (2.0 V) is",
            "adc_pins": "GPIO26/27 are standard (not fault-tolerant) pads, abs. max IOVDD + 0.5 V: the switch keeps them below 3.45 V x 39/40",
        },
        "pull_downs": "R140-R145 39 k: with stepping A2 erratum RP2350-E9 needs 8.2 k or less; on A4 (required by the BOM) 39 k holds a floating line at 0 V (1 uA leakage -> 39 mV)",
        "enable": "U11 /OE is driven by U12 TLV810E (active-high reset, 2.93 V) with R128 100 k to +3V3: the switch is off below 2.93 V and on whenever the rail is up; firmware cannot turn it off",
    }
    (spice.OUT / "misc.json").write_text(json.dumps(out, indent=1))
    print("wrote", spice.OUT / "misc.json")


if __name__ == "__main__":
    main()
