#!/usr/bin/env python3
"""Generate an engineering-only population variant from pinned CAD and prices.

Native positions are deliberately not advertised as supplier-fitted CPL files.
No board, schematic, Gerber, historical report or root order package is changed.
"""
import csv
import hashlib
import json
import math
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
ROOT = BASE.parents[2]
SOURCE = ROOT / "pcb/firmware/qmk/keyboards/maru60/rp2350"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_csv(name, fields, rows):
    with (HERE / name).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate():
    policy = json.loads((BASE / "design/assembly-policy.json").read_text())
    for name, expected in policy["source_inputs"].items():
        assert digest(BASE / name) == expected, f"Stale design input: {name}"
    excluded = set(policy["exclude_from_assembly"])
    snapshot = json.loads((BASE / "evidence/cost-review-20261114/parts-snapshot.json").read_text())
    led_part = json.loads((BASE / "design/led-part.json").read_text())
    for part in snapshot["parts"]:
        if part["code"] == led_part["lcsc"]:
            part["mpn"] = led_part["mpn"]
    fps = {fp["ref"]: fp for fp in json.loads((BASE / "evidence/final-geometry.json").read_text())["fps"]}
    netlist = ET.parse(BASE / "evidence/simulation-suite-20261114/inputs/netlist.xml")
    components = {c.get("ref"): c for c in netlist.findall("./components/comp")}
    dedicated = {ref for ref, c in components.items() if "gpio-isolation" in c.find("sheetpath").get("names", "")}
    assert dedicated == excluded and len(excluded) == 19
    all_refs = {ref for part in snapshot["parts"] for ref in part["refs"]}
    selected = all_refs - excluded
    assert len(all_refs) == 338 and len(selected) == 319
    assert {"R126", "C138", "C139", "U7", "U8", "U18", "J1"} <= selected
    assert all(fps[ref]["layer"] == "B.Cu" for ref in selected)
    boundary = []
    for net in netlist.findall("./nets/net"):
        nodes = net.findall("node")
        removed = [n for n in nodes if n.get("ref") in excluded]
        remaining = [n for n in nodes if n.get("ref") not in excluded]
        if not removed or not remaining:
            continue
        name = net.get("name")
        if name not in {"GND", "+3V3"}:
            assert name in {f"MCU_GPIO{gp}" for gp in policy["unused_mcu_gpio"]}, name
            assert len(remaining) == 1 and remaining[0].get("ref") == "U1", name
        boundary.append({"net": name, "remaining": [dict(n.attrib) for n in remaining],
                         "removed": [dict(n.attrib) for n in removed]})
    write_json("net-boundary.json", boundary)

    definition = json.loads((SOURCE / "keyboard.json").read_text())
    matrix = set(sum(definition["matrix_pins"].values(), []))
    free = {f"GP{gp}" for gp in policy["unused_mcu_gpio"]}
    assert not (free & matrix) and not (free & {"GP20", "GP21", "GP22", "GP23"})
    assert len(matrix) == 20 and len(free) == 6

    # One BOM entry per actual part code; alternate sites never double quantities.
    bom, priced, full = [], [], []
    part_by_ref = {ref: p for p in snapshot["parts"] for ref in p["refs"]}
    for p in snapshot["parts"]:
        refs = sorted(set(p["refs"]) & selected)
        if not refs:
            continue
        qty = 5 * len(refs) + p["published_attrition_qty"]
        tiers = [t for t in p["price_tiers_usd"] if t["start"] <= qty and (t["end"] in (-1, None) or qty <= t["end"])]
        assert len(tiers) == 1
        cost = Decimal(str(tiers[0]["price"])) * qty
        bom.append({"Comment": p["mpn"], "Designator": ",".join(refs),
                    "Footprint": " | ".join(sorted({fps[r]["fpid"] for r in refs})), "LCSC Part #": p["code"]})
        priced.append({"code": p["code"], "refs": refs, "count_per_board": len(refs),
                       "purchase_quantity": qty, "usd": str(cost), "class": p["library_type"]})
    assert len(bom) == 50
    assert sum(p["count_per_board"] for p in priced if p["code"] == "C5149201") == 64
    assert sum(p["count_per_board"] for p in priced if p["code"] == "C2890035") == 12
    for ref, fp in sorted(fps.items()):
        p = part_by_ref.get(ref, {})
        reason = "" if ref in selected else ("authorized expansion omission" if ref in excluded else "outside supplier assembly scope; unchanged")
        full.append({"Reference": ref, "Value": fp["value"], "Footprint": fp["fpid"],
                     "Assemble": "yes" if ref in selected else "no", "Reason": reason, "LCSC": p.get("code", "")})
    write_csv("bom-review.csv", ["Comment", "Designator", "Footprint", "LCSC Part #"], bom)
    write_csv("population-all.csv", ["Reference", "Value", "Footprint", "Assemble", "Reason", "LCSC"], full)

    # Keep a rule overlay that does not pretend the retained CAD footprints are DNP.
    rules = json.loads((ROOT / "pcb/experiments/resume-20261113-mcu-near-usb-zero-opens/order/parts.json").read_text())
    rules["note"] = "Engineering no-expansion variant. All selected refs are exact overrides; do not export a production package without resolving reverse-LED placement qualification."
    overrides = [{"refs": sorted(excluded), "assemble": False, "kind": "variant_omission", "notes": "User-authorized no-expansion default population; CAD lands remain."}]
    for p in snapshot["parts"]:
        refs = sorted(set(p["refs"]) & selected)
        if refs:
            overrides.append({"refs": refs, "assemble": True, "lcsc": p["code"], "mpn": p["mpn"],
                              "class": p["library_type"], "stock": p["stock_snapshot"],
                              "polarised": any(ref.startswith(("LED", "D", "U", "J", "L")) for ref in refs),
                              "notes": "Match design/led-part.json datasheet revision and pin functions. LED14/15: exactly one site per reference; select one complete placement variant." if "LED14" in refs else ""})
    rules["rules"] = overrides + rules["rules"]
    rules["stock_snapshot_date"] = snapshot["observation_date"]
    write_json("parts.json", rules)

    variants = {}
    for variant, site in [("split", 0), ("2u", 1)]:
        positions = []
        for ref in sorted(selected):
            fp = fps[ref]
            x, y, rotation = fp["x"], fp["y"], fp["rot"]
            if ref in {"LED14", "LED15"}:
                pads = {}
                for num in ("1", "2", "3", "4"):
                    candidates = [p for p in fp["pads"] if p["num"] == num]
                    assert len(candidates) == 2
                    candidates.sort(key=lambda p: math.hypot(p["x"] - fp["x"], p["y"] - fp["y"]))
                    pads[num] = candidates[site]
                x, y = (sum(p[k] for p in pads.values()) / 4 for k in ("x", "y"))
                rotation = -math.degrees(math.atan2(pads["4"]["y"] - pads["1"]["y"], pads["4"]["x"] - pads["1"]["x"]))
                if site == 0:
                    assert math.hypot(x - fp["x"], y - fp["y"]) < .02
                assert all(math.hypot(p["x"] - x, p["y"] - y) < 3.4 for p in pads.values())
            positions.append({"Reference": ref, "X_mm_KiCad": f"{x:.6f}", "Y_mm_KiCad": f"{y:.6f}",
                              "Rotation_deg_KiCad": f"{rotation:.6f}", "Layer": "B.Cu",
                              "Site": variant if ref in {"LED14", "LED15"} else "fixed"})
        write_csv(f"placements-native-{variant}.csv", list(positions[0]), positions)
        variants[variant] = {r["Reference"]: r for r in positions if r["Reference"] in {"LED14", "LED15"}}
        assert len(positions) == len({r["Reference"] for r in positions}) == 319
        assert {r["Reference"] for r in positions} == selected

    # Candidate-specific overlay: baseline firmware continues to support populated ports.
    firmware = HERE / "firmware"
    firmware.mkdir(exist_ok=True)
    source_hashes = {}
    for source in SOURCE.rglob("*"):
        if source.is_file():
            relative = source.relative_to(SOURCE)
            target = firmware / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            source_hashes[str(relative)] = digest(source)
    c = firmware / "maru60.c"
    text = c.read_text()
    needle = "    keyboard_pre_init_user();"
    assert text.count(needle) == 1
    additions = ["    // No-expansion population only: these nets end at U1 and empty lands.",
                 "    // Preload LOW before enabling the output; never drive an attached module."]
    for gp in policy["unused_mcu_gpio"]:
        additions.append(f"    gpio_write_pin_low(GP{gp}); gpio_set_pin_output(GP{gp});")
    text = text.replace(needle, "\n".join(additions) + "\n" + needle)
    c.write_text(text)
    with (firmware / "config.h").open("a") as stream:
        stream.write("\n// Engineering assembly variant: J3 and its complete interface are absent.\n#define MARU60_NO_EXPANSION 1\n")
    assert "#    define MARU60_LED_POWER_QUALIFIED 0" in (firmware / "config.h").read_text()
    changed = sorted(name for name, sha in source_hashes.items() if digest(firmware / name) != sha)
    assert changed == ["config.h", "maru60.c"]
    write_json("firmware-source.json", {"baseline": str(SOURCE.relative_to(ROOT)), "baseline_sha256": source_hashes,
                                       "changed_files": changed, "variant_sha256": {name: digest(firmware / name) for name in source_hashes}})

    parts_total = sum(Decimal(p["usd"]) for p in priced)
    fees = Decimal("25.56") + Decimal("8.21") + Decimal("1.53") * len(bom)
    prior = json.loads((BASE / "evidence/cost-review-20261114/calculation.json").read_text())
    delta = Decimal(str(prior["current"]["parts_usd"])) + Decimal(str(prior["current"]["standard_setup_stencil_feeders_usd"])) - parts_total - fees
    report = {"status": "Engineering population variant applied; NOT ORDER READY", "cad_unchanged": True,
              "excluded_refs": sorted(excluded), "assembled_per_board": len(selected), "unique_parts": len(bom),
              "library_types": dict(Counter(p["class"] for p in priced)), "all_assembled_on_bottom": True,
              "parts_5_boards_usd": str(parts_total), "standard_fixed_usd": str(fees),
              "parts_plus_standard_fixed_krw_assumed": round((parts_total + fees) * 1540),
              "parts_and_standard_fixed_savings_5_boards_krw_assumed": round(delta * 1540),
              "parts_and_standard_fixed_savings_per_board_krw_assumed": round(delta * 1540 / 5),
              "fx_assumption": 1400, "tax_reserve_assumption": .1, "procurement_savings_realized": False,
              "unused_gpio": policy["unused_mcu_gpio"], "preserved_gpio_count": 24,
              "backspace_population_sites": variants, "bom_matches_both_position_lists": True,
              "firmware_build_qualification": "See separate build evidence; no hardware qualification",
              "cpl_status": "KiCad axes/angles only; not fitted to supplier rotation/origin; do not upload as final CPL",
              "release_blockers": ["Unresolved LED PWM power and signal findings", "Supplier reverse-LED placement and aperture approval", "Final complete landed quote"]}
    assert parts_total == Decimal("132.3270") and fees == Decimal("110.27")
    write_json("summary.json", report)
    write_json("priced-parts.json", priced)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    generate()
