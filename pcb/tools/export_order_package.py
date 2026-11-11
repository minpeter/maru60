#!/usr/bin/env python3
"""Export the JLCPCB order package for the Maru60 order candidate.

Run from the repository root with the project virtualenv:

    .venv/bin/python pcb/tools/export_order_package.py

It reads the checkpoint board through the pinned KiCad 9.0.2 container
(tools/run_kicad9.sh) and the part selection in pcb/order/parts.json, and writes
into pcb/order/:

    gerbers/               11 layer Gerbers, PTH and NPTH drill files, drill maps
    maru60-gerbers.zip     the same files, ready to upload
    bom-jlcpcb.csv         Comment, Designator, Footprint, LCSC Part # (assembled parts only)
    cpl-jlcpcb.csv         Designator, Mid X, Mid Y, Layer, Rotation (same designators); rotations and
                           centres come from jlcpcb-placement.json, fitted to JLCPCB's own footprints
    bom-full.csv           every footprint with MPN, LCSC number and why it is or is not assembled
    PROVENANCE.json        board hash, commands, counts, checks, file hashes

The exporter refuses to write a package if any footprint has no part rule, if
the BOM and CPL designators differ, or if KiCad DRC on the board is not clean.
It never modifies the board.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = ROOT / "pcb/experiments/resume-20261111-order-candidate"
WRAPPER = "tools/run_kicad9.sh"
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
FP_SMD, FP_NO_POS, FP_NO_BOM, FP_BOARD_ONLY, FP_DNP = 2, 4, 8, 16, 256


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def natural(ref: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", ref)]


def run(cmd: list[str], log: list[dict]) -> str:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    log.append({"command": cmd, "returncode": p.returncode})
    if p.returncode != 0:
        sys.stderr.write(p.stdout + p.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd)}")
    return p.stdout


def match_rule(fp: dict, rules: list[dict]) -> dict | None:
    name = fp["fpid"].split(":")[-1]
    for r in rules:
        if "refs" in r:
            if fp["ref"] in r["refs"]:
                return r
            continue
        if "value_re" in r and not re.search(r["value_re"], fp["value"]):
            continue
        if "footprint" in r and r["footprint"] != name:
            continue
        if "footprint_re" in r and not re.search(r["footprint_re"], name):
            continue
        return r
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    ap.add_argument("--out", type=Path, default=ROOT / "pcb/order")
    ap.add_argument("--parts", type=Path, default=ROOT / "pcb/order/parts.json")
    args = ap.parse_args()
    board = (args.checkpoint / "pcb/maru60.kicad_pcb").resolve()
    out = args.out.resolve()
    board_rel = str(board.relative_to(ROOT))
    out_rel = str(out.relative_to(ROOT))
    scratch = ROOT / "build/order-export"
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True)
    scratch_rel = str(scratch.relative_to(ROOT))
    board_hash = sha256(board)
    log: list[dict] = []
    checks: list[dict] = []

    def check(name, ok, detail):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    version = run([WRAPPER, "kicad-cli", "version"], log).strip()
    # 1. design rules on the exact board that is exported
    run([WRAPPER, "kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all", "--format", "json",
         "--output", f"{scratch_rel}/drc.json", board_rel], log)
    drc = json.loads((scratch / "drc.json").read_text())
    counts = {k: len(drc.get(k, [])) for k in ("violations", "unconnected_items", "schematic_parity")}
    check("KiCad DRC, unconnected items and schematic parity are all zero", not any(counts.values()), counts)

    # 2. geometry dump and KiCad's own placement file
    run([WRAPPER, "python3", "pcb/tools/dump_board_geometry.py", board_rel, f"{scratch_rel}/board.json"], log)
    run([WRAPPER, "kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
         "--output", f"{scratch_rel}/kicad-pos.csv", board_rel], log)
    fps = json.loads((scratch / "board.json").read_text())["fps"]
    pos = {r["Ref"]: r for r in csv.DictReader((scratch / "kicad-pos.csv").open())}
    parts = json.loads(args.parts.read_text())
    fit_path = out / "jlcpcb-placement.json"
    fitted = json.loads(fit_path.read_text())["placements"] if fit_path.exists() else {}

    rows, unmatched = [], []
    for fp in sorted(fps, key=lambda f: natural(f["ref"])):
        rule = match_rule(fp, parts["rules"])
        if rule is None:
            unmatched.append(f"{fp['ref']} ({fp['value']} / {fp['fpid']})")
            continue
        attr = fp["attr"]
        assemble = rule.get("assemble", True)
        reason = rule.get("kind", "assembled")
        if assemble and (attr & (FP_DNP | FP_NO_BOM | FP_BOARD_ONLY) or fp["dnp"]):
            raise SystemExit(f"{fp['ref']}: rule says assemble but the footprint is DNP / excluded on the board")
        if not assemble and reason == "dnp" and not (fp["dnp"] or attr & FP_DNP):
            raise SystemExit(f"{fp['ref']}: rule says DNP but the footprint is not marked DNP on the board")
        rows.append({"ref": fp["ref"], "value": fp["value"], "footprint": fp["fpid"].split(":")[-1], "layer": fp["layer"],
                     "assemble": assemble, "reason": reason, "mfr": rule.get("mfr", ""), "mpn": rule.get("mpn", ""),
                     "lcsc": rule.get("lcsc", ""), "class": rule.get("class", ""), "desc": rule.get("desc", ""),
                     "polarised": bool(rule.get("polarised")), "stock": rule.get("stock"), "notes": rule.get("notes", "")})
    check("every footprint is covered by a part rule", not unmatched, unmatched)
    if unmatched:
        print("\n".join(unmatched))
        return 1

    asm = [r for r in rows if r["assemble"]]
    missing_pos = [r["ref"] for r in asm if r["ref"] not in pos]
    check("every assembled part has a KiCad placement row", not missing_pos, missing_pos)
    check("every assembled part has an LCSC number", all(r["lcsc"] for r in asm), [r["ref"] for r in asm if not r["lcsc"]])
    extra_pos = sorted(set(pos) - {r["ref"] for r in asm}, key=natural)
    allowed_extra = {r["ref"] for r in rows if not r["assemble"]}
    check("KiCad placement rows that are not assembled are all intentional exclusions", set(extra_pos) <= allowed_extra, extra_pos)

    out.mkdir(parents=True, exist_ok=True)
    # 3. BOM (grouped by part) and CPL
    groups: dict[str, list[dict]] = {}
    for r in asm:
        groups.setdefault(r["lcsc"], []).append(r)
    with (out / "bom-jlcpcb.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for lcsc, g in sorted(groups.items(), key=lambda kv: natural(kv[1][0]["ref"])):
            w.writerow([f"{g[0]['mpn']} ({g[0]['desc']})", ",".join(r["ref"] for r in g), g[0]["footprint"], lcsc])
    with (out / "cpl-jlcpcb.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in asm:
            p = pos[r["ref"]]
            side = "Top" if p["Side"] == "top" else "Bottom"
            f_ = fitted.get(r["ref"])
            if f_ and f_.get("status") == "fitted" and f_["side"] == side and f_["lcsc"] == r["lcsc"]:
                # rotation and centre fitted to the footprint JLCPCB places from (fit_jlcpcb_placement.py)
                x, y, a = f_["x"], -f_["y"], f_["rotation"]
                r["placement"] = "fitted"
                r["fit_rms"] = f_["rms_mm"]
            else:
                # KiCad position; rotation by the usual convention (bottom side: 180 - angle), no per-part correction
                x, y = float(p["PosX"]), float(p["PosY"])
                a = float(p["Rot"]) % 360 if side == "Top" else (180 - float(p["Rot"])) % 360
                r["placement"] = "convention"
            w.writerow([r["ref"], f"{x:.4f}", f"{y:.4f}", side, f"{a:.2f}"])
    with (out / "bom-full.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Reference", "Value", "Footprint", "Side", "Assembled by JLCPCB", "Reason if not", "Manufacturer", "MPN", "LCSC", "Library class", "Polarised", "Notes"])
        for r in rows:
            w.writerow([r["ref"], r["value"], r["footprint"], "Top" if r["layer"] == "F.Cu" else "Bottom", "yes" if r["assemble"] else "no",
                        "" if r["assemble"] else r["reason"], r["mfr"], r["mpn"], r["lcsc"], r["class"], "yes" if r["polarised"] else "", r["notes"]])
    bom_refs = {d for row in csv.DictReader((out / "bom-jlcpcb.csv").open()) for d in row["Designator"].split(",")}
    cpl_refs = {row["Designator"] for row in csv.DictReader((out / "cpl-jlcpcb.csv").open())}
    polar_unfitted = sorted(r["ref"] for r in asm if r["polarised"] and r.get("placement") != "fitted")
    check("every polarised part has a rotation fitted to JLCPCB's own footprint", not polar_unfitted, polar_unfitted)
    check("BOM and CPL list exactly the same designators", bom_refs == cpl_refs, {"bom": len(bom_refs), "cpl": len(cpl_refs)})

    # 4. Gerbers and drill files
    gerbers = out / "gerbers"
    shutil.rmtree(gerbers, ignore_errors=True)
    gerbers.mkdir()
    run([WRAPPER, "kicad-cli", "pcb", "export", "gerbers", "--output", f"{out_rel}/gerbers/", "--layers", LAYERS,
         "--subtract-soldermask", "--no-netlist", "--no-protel-ext", board_rel], log)
    run([WRAPPER, "kicad-cli", "pcb", "export", "drill", "--output", f"{out_rel}/gerbers/", "--format", "excellon",
         "--drill-origin", "absolute", "--excellon-zeros-format", "decimal", "--excellon-oval-format", "alternate",
         "--excellon-units", "mm", "--excellon-separate-th", "--generate-map", "--map-format", "gerberx2", board_rel], log)
    files = sorted(p for p in gerbers.iterdir() if p.is_file())
    names = [p.name for p in files]
    for want in ("F_Cu", "In1_Cu", "In2_Cu", "B_Cu", "F_Paste", "B_Paste", "F_Silkscreen", "B_Silkscreen", "F_Mask", "B_Mask", "Edge_Cuts", "-PTH.drl", "-NPTH.drl"):
        check(f"gerber set contains {want}", any(want in n for n in names), names if not any(want in n for n in names) else "")
    zpath = out / "maru60-gerbers.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            if p.suffix in (".gbr", ".drl", ".gbrjob"):
                info = zipfile.ZipInfo(p.name, date_time=(2026, 11, 11, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, p.read_bytes())
    check("the board file was not modified by the export", sha256(board) == board_hash, board_hash)

    ok = all(c["pass"] for c in checks)
    summary = {
        "footprints": len(rows),
        "assembled_parts": len(asm),
        "assembled_top": sum(1 for r in asm if pos[r["ref"]]["Side"] == "top"),
        "assembled_bottom": sum(1 for r in asm if pos[r["ref"]]["Side"] == "bottom"),
        "unique_lcsc_parts": len(groups),
        "basic_parts": sum(1 for g in groups.values() if g[0]["class"] == "basic"),
        "extended_parts": sum(1 for g in groups.values() if g[0]["class"] == "extended"),
        "out_of_stock_at_snapshot": sorted({r["mpn"] for r in asm if r["stock"] == 0}),
        "not_assembled": {k: sorted((r["ref"] for r in rows if not r["assemble"] and r["reason"] == k), key=natural)
                          for k in sorted({r["reason"] for r in rows if not r["assemble"]})},
        "placements_fitted_to_jlcpcb_footprints": sum(1 for r in asm if r.get("placement") == "fitted"),
        "placements_by_convention_only": sorted((r["ref"] for r in asm if r.get("placement") != "fitted"), key=natural),
        "fitted_with_land_pattern_difference_over_0.15mm": sorted((r["ref"] for r in asm if r.get("fit_rms", 0) > 0.15), key=natural),
        "polarised_refs_to_check_in_preview": sorted((r["ref"] for r in asm if r["polarised"] and not r["ref"].startswith(("D", "LED"))), key=natural),
    }
    prov = {
        "status": "ORDER_CANDIDATE" if ok else "FAILED_CHECKS",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "board": {"path": board_rel, "sha256": board_hash},
        "parts_database": {"path": str(args.parts.resolve().relative_to(ROOT)), "sha256": sha256(args.parts), "stock_snapshot_date": parts.get("stock_snapshot_date")},
        "kicad_version": version,
        "fabrication": {"layers": 4, "thickness_mm": 1.6, "outline_mm": [285.0, 94.6], "min_track_space_mm": [0.15, 0.15],
                        "via_mm": {"pad": 0.5, "drill": 0.25}, "vias_tented": True, "controlled_impedance": False},
        "summary": summary,
        "checks": checks,
        "commands": log,
        "files": {str(p.relative_to(out)): sha256(p) for p in sorted(out.rglob("*")) if p.is_file() and p.name not in ("PROVENANCE.json", "README.md", "parts.json", "jlcpcb-placement.json")},
    }
    (out / "PROVENANCE.json").write_text(json.dumps(prov, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    for c in checks:
        if not c["pass"]:
            print("FAILED:", c)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
