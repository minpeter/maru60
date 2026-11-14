#!/usr/bin/env python3
"""Reproduce the cost screen from retained public prices; never edits CAD/BOM."""
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent.parent
D = lambda value: Decimal(str(value))


def main():
    snapshot = json.loads((HERE / "parts-snapshot.json").read_text())
    for relative, expected in snapshot["current_inputs"].items():
        actual = hashlib.sha256((CANDIDATE / relative).read_bytes()).hexdigest()
        assert actual == expected, f"Stale cost review input: {relative}"
    rows = snapshot["parts"]
    quantity = snapshot["quantity"]
    fees = {k: D(v) for k, v in snapshot["fees_usd"].items()}
    conversion = D(snapshot["fx_usdkrw_assumption"]) * (1 + D(snapshot["tax_reserve_assumption"]))
    money = lambda value: float(value.quantize(D("0.0001"), rounding=ROUND_HALF_UP))
    krw = lambda value: int((value * conversion).quantize(D("1"), rounding=ROUND_HALF_UP))
    netlist = ET.parse(CANDIDATE / "evidence/simulation-suite-20261114/inputs/netlist.xml")
    components = {c.get("ref"): c for c in netlist.findall("./components/comp")}
    refs = [ref for row in rows for ref in row["refs"]]
    assert len(refs) == len(set(refs)) == 338
    assert all(ref in components for ref in refs)
    assert len(rows) == len({row["code"] for row in rows}) == 56
    reverse = next(row for row in rows if row["code"] == "C5149201")
    assert len(reverse["refs"]) == 64
    assert {"LED14", "LED15"}.issubset(reverse["refs"])
    assert all(components[ref].findtext("value") == "SK6812MINI-E-012" for ref in reverse["refs"])
    expansion = set(snapshot["expansion_refs"])
    actual_expansion = {
        ref for ref, comp in components.items()
        if "gpio-isolation" in comp.find("sheetpath").get("names", "")
    }
    assert expansion == actual_expansion and len(expansion) == 19
    assert "R126" not in expansion
    assert snapshot["expansion_population_change_authorized"] is False

    def price_rows(excluded=frozenset()):
        priced = []
        for row in rows:
            assert row["count_per_board"] == len(row["refs"])
            selected = sorted(set(row["refs"]) - excluded)
            if not selected:
                continue
            purchased = quantity * len(selected) + row["published_attrition_qty"]
            tiers = [t for t in row["price_tiers_usd"] if t["start"] <= purchased and
                     (t["end"] in (-1, None) or purchased <= t["end"])]
            assert len(tiers) == 1, (row["code"], purchased, tiers)
            unit = D(tiers[0]["price"])
            priced.append({
                "code": row["code"], "mpn": row["mpn"], "refs": selected,
                "count_per_board": len(selected), "purchase_quantity": purchased,
                "unit_usd": money(unit), "line_usd": money(unit * purchased),
                "library_type": row["library_type"], "pcba_type": row["pcba_type"],
                "stock": row["stock_snapshot"], "stock_sufficient": row["stock_snapshot"] >= purchased,
                "numbered_pads_per_board": sum(row["numbered_pads_by_ref"][r] for r in selected),
            })
        return priced

    def scenario(priced):
        parts = sum(D(row["line_usd"]) for row in priced)
        classes = Counter(row["library_type"] for row in priced)
        standard = fees["standard_setup"] + fees["standard_stencil"] + len(priced) * fees["standard_per_part"]
        economic = fees["economic_setup"] + fees["economic_stencil"] + classes["extended"] * fees["economic_per_extended_part"]
        pads = sum(row["numbered_pads_per_board"] for row in priced)
        return {
            "parts_usd": money(parts), "parts_with_tax_reserve_krw": krw(parts),
            "placements_per_board": sum(row["count_per_board"] for row in priced),
            "unique_parts": len(priced), "library_types": dict(classes),
            "standard_setup_stencil_feeders_usd": money(standard),
            "economic_setup_stencil_extended_usd_hypothetical": money(economic),
            "economic_eligible_as_is": False,
            "numbered_pad_proxy_per_board": pads,
            "smt_pad_proxy_usd": money(pads * quantity * fees["smt_per_joint"]),
            "parts_plus_standard_fixed_only_krw": krw(parts + standard),
            "floor_if_L2_free_krw": krw(parts + standard - next(D(r["line_usd"]) for r in priced if r["code"] == "C19191688")),
            "stock_shortages": [{"code": r["code"], "required": r["purchase_quantity"], "stock": r["stock"]} for r in priced if not r["stock_sufficient"]],
        }

    original = price_rows()
    omitted = price_rows(expansion)
    current = scenario(original)
    no_expansion = scenario(omitted)
    eliminated = sorted({row["code"] for row in original} - {row["code"] for row in omitted})
    assert len(eliminated) == 6
    assert sum(snapshot["budget_allocation_krw"].values()) == snapshot["target_total_krw"]
    part_savings = D(current["parts_usd"]) - D(no_expansion["parts_usd"])
    fixed_savings = D(current["standard_setup_stencil_feeders_usd"]) - D(no_expansion["standard_setup_stencil_feeders_usd"])
    result = {
        "status": "Cost screen only; no CAD/BOM substitutions; no supplier quote or manufacturing release",
        "basis": "5 fully assembled boards; catalog tiers plus published fixed attrition quantities; USD/KRW 1400 and 10% tax reserve are assumptions",
        "target_krw": snapshot["target_total_krw"],
        "pretax_usd_ceiling": money(D(snapshot["target_total_krw"]) / conversion),
        "current": current,
        "expansion_omission_option": {
            "applied": False, "requires_user_feature_choice": True,
            "excluded_refs": sorted(expansion), "eliminated_part_codes": eliminated,
            "scenario": no_expansion, "parts_savings_usd": money(part_savings),
            "standard_fixed_savings_usd": money(fixed_savings),
            "parts_and_fixed_savings_krw": krw(part_savings + fixed_savings),
            "shared_parts_remaining": [
                {"code": row["code"], "refs_remaining": sorted(set(row["refs"]) - expansion)}
                for row in rows if set(row["refs"]) & expansion and set(row["refs"]) - expansion
            ],
        },
        "budget_allocation_krw_targets_not_quotes": snapshot["budget_allocation_krw"],
        "limitations": [
            "Cost floors omit fabrication, shipping, SMT labor, X-ray, fixtures, handling, storage and special reverse-mount operations; they are not landed quotes.",
            "Free-L2 cases are deliberately optimistic impossibility screens for this supplier/fee structure, not viable designs or market-wide lower bounds.",
            "Economic fixed fees are hypothetical because both installed LED codes are Standard Only.",
            "Stock and prices are snapshots; price publication does not make insufficient-stock parts orderable.",
            "Numbered pad count is a billing proxy, not a supplier joint-count quote; repeated USB shell pads may be billed differently.",
        ],
    }
    (HERE / "calculation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    columns = ["code", "mpn", "refs", "count_per_board", "purchase_quantity", "unit_usd", "line_usd", "library_type", "pcba_type", "stock", "stock_sufficient", "numbered_pads_per_board"]
    with (HERE / "priced-bom-review.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in sorted(original, key=lambda r: r["line_usd"], reverse=True):
            writer.writerow({**row, "refs": ",".join(row["refs"])})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
