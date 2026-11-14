"""Extend the case-envelope check to every relocated bottom-side part."""
import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "pcb/tools"))
import check_mechanical_fit as fit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("geometry", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    baseline = ROOT / "pcb/experiments/resume-20261112-backspace-2u/qa/geometry.json.gz"
    old = {f["ref"]: f for f in json.loads(gzip.decompress(baseline.read_bytes()))["fps"]}
    current = json.loads(args.geometry.read_text())["fps"]
    changed = [f for f in current if f["ref"] not in old or any(
        f[key] != old[f["ref"]][key] for key in ("x", "y", "rot", "layer")
    )]
    bottom = [f["ref"] for f in changed if f["layer"] == "B.Cu"]
    fit.RELOCATED_REFS = sorted(set(fit.RELOCATED_REFS + bottom))
    for ref in bottom:
        height = {"U1": 1.0, "U3": 1.75, "Y1": 1.0, "L1": 1.2, "D16": 1.35}.get(ref, 1.0)
        fit.PART_HEIGHTS[ref] = (
            height, "Conservative package-height envelope for relocated MCU block; assumed, not measured"
        )
    args.output.mkdir(parents=True, exist_ok=True)
    delta = {
        "changed_refs": [f["ref"] for f in changed],
        "bottom_checked": bottom,
        "top_changed": [f["ref"] for f in changed if f["layer"] == "F.Cu"],
        "height_assumptions": {ref: fit.PART_HEIGHTS[ref] for ref in bottom},
    }
    (args.output / "placement-delta.json").write_text(json.dumps(delta, indent=2) + "\n")
    sys.argv = [
        "check_mechanical_fit", "--board", str(args.board.resolve()),
        "--output-dir", str(args.output.resolve()), "--plate-dxf",
        str(ROOT / "models/maru60-hhkb-plate-7u-plate-mount-2u-backspace.dxf"),
    ]
    fit.main()


if __name__ == "__main__":
    main()
