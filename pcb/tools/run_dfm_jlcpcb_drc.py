#!/usr/bin/env python3
"""Run KiCad DRC once per rule of the JLCPCB rule deck and collect the results.

usage (repository root, KiCad 9 image built):
    .venv/bin/python pcb/tools/run_dfm_jlcpcb_drc.py CHECKPOINT/pcb DECK.kicad_dru OUT.json

KiCad applies only the last matching rule of each constraint type, so a deck
with a minimum and a recommended tier cannot be checked in one run, and a run
with the whole deck takes about an hour on this board.  Each rule is therefore
run alone on a scratch copy of the project (build/dfm-jlcpcb-drc/NN), which
takes a few seconds, shadows nothing and is run in parallel.  The project's own
rule file is replaced by the single rule in each copy; the minimums in the
project file stay in force.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / "build" / "dfm-jlcpcb-drc"


def run(job):
    n, name, rule, src = job
    d = SCRATCH / f"{n:02d}"
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(src, d)
    (d / "maru60.kicad_dru").write_text("(version 1)\n" + rule)
    out = d / "drc.json"
    r = subprocess.run([str(ROOT / "tools/run_kicad9.sh"), "kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "--output", str(out.relative_to(ROOT)),
                        str((d / "maru60.kicad_pcb").relative_to(ROOT))], capture_output=True, text=True)
    if not out.exists():
        raise SystemExit(f"{name}: DRC wrote nothing\n{r.stdout}{r.stderr}")
    res = json.loads(out.read_text())
    rows = []
    for v in res["violations"]:
        m = re.search(r"actual ([\d.]+)", v["description"])
        rows.append({"type": v["type"], "severity": v["severity"], "actual_mm": float(m.group(1)) if m else None,
                     "items": [{"what": i["description"], "at": [i["pos"]["x"], i["pos"]["y"]]} for i in v["items"]]})
    return {"rule": name, "constraint": re.search(r"\(constraint (\w+)", rule).group(1), "violations": len(rows),
            "min_actual_mm": min((x["actual_mm"] for x in rows if x["actual_mm"] is not None), default=None),
            "unconnected": len(res.get("unconnected_items", [])), "kicad_version": res["kicad_version"], "found": rows}


def main():
    src, deck, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), Path(sys.argv[3])
    rules = re.findall(r'(?ms)^\(rule ".*?\)\)\n', deck.read_text())
    jobs = [(n, re.search(r'"(.*?)"', r).group(1), r, src) for n, r in enumerate(rules)]
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(run, jobs))
    doc = {"board": str((src / "maru60.kicad_pcb").relative_to(ROOT)), "board_sha256": hashlib.sha256((src / "maru60.kicad_pcb").read_bytes()).hexdigest(),
           "deck": str(deck), "kicad_version": results[0]["kicad_version"], "rules": results}
    for r in results:
        del r["kicad_version"]
    out.write_text(json.dumps(doc, indent=1) + "\n")
    for r in results:
        print(f"{r['rule']:45} {r['violations']:4}  min {r['min_actual_mm']}")


if __name__ == "__main__":
    main()
