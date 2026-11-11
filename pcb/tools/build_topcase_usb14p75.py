#!/usr/bin/env python3
"""Build a top-case variant with the 14.75 mm USB-C notch centred on the J1.

The stock Rule60 V3 top case has a 12.8 mm notch centred at plate X 19.35.
The Maru60 J1 is at board (18.0, 3.8) -> plate X 18.4525, so a 12.35 mm plug
overhangs the stock notch by 0.67 mm.  The current default build
(`build_topcase_draft.py --board ph60-rev3`) already cuts 14.75 mm at plate
X 18.65 (1.00 mm per side).  This wrapper keeps the 14.75 mm width but centres
it on the actual J1 (18.4525), giving 1.20 mm per side, and writes the right
half to `models/` under a new name.  It does not overwrite any existing file.

Usage:
    .venv/bin/python pcb/tools/build_topcase_usb14p75.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import build_topcase_draft as tc  # noqa: E402

J1_PLATE_X = 18.4525
NOTCH_WIDTH = 14.75
PLUG_WIDTH = 12.35
OUT_NAME = "maru60-hhkb-topcase-right-usb-14p75-j1centred.3mf"
BUILD_DIR = ROOT / "build/topcase-usb14p75"
QA = ROOT / "pcb/experiments/resume-20261109-relocated-expansion-zero-opens/qa/mechanical-fit"


def main() -> None:
    tc.OUT = BUILD_DIR
    tc.usb_notch_print = lambda board_id: (J1_PLATE_X, NOTCH_WIDTH)
    sys.argv = ["build_topcase_usb14p75.py", "--board", "ph60-rev3"]
    tc.main()

    src = BUILD_DIR / "maru60-hhkb-right-plate.3mf"
    dst = ROOT / "models" / OUT_NAME
    if not src.exists():
        raise SystemExit(f"top-case build did not produce {src}")
    shutil.copy2(src, dst)

    left, right = J1_PLATE_X - NOTCH_WIDTH / 2, J1_PLATE_X + NOTCH_WIDTH / 2
    plug_left, plug_right = J1_PLATE_X - PLUG_WIDTH / 2, J1_PLATE_X + PLUG_WIDTH / 2
    report = {
        "variant": "usb-14p75-j1centred",
        "source_builder": "build_topcase_draft.py",
        "board": "ph60-rev3",
        "j1_plate_x_mm": J1_PLATE_X,
        "notch_width_mm": NOTCH_WIDTH,
        "notch_x_range_plate_mm": [round(left, 4), round(right, 4)],
        "plug_12p35_x_range_plate_mm": [round(plug_left, 4), round(plug_right, 4)],
        "plug_min_side_clearance_mm": round(min(plug_left - left, right - plug_right), 4),
        "stock_notch_width_mm": 12.80,
        "stock_notch_centre_plate_x_mm": 19.35,
        "stock_plug_min_side_clearance_mm": round(min(plug_left - (19.35 - 6.4), (19.35 + 6.4) - plug_right), 4),
        "default_printed_notch_centre_plate_x_mm": 18.65,
        "default_printed_plug_min_side_clearance_mm": round(min(plug_left - (18.65 - 7.375), (18.65 + 7.375) - plug_right), 4),
        "files": [f"models/{OUT_NAME}"],
        "build_dir": str(BUILD_DIR.relative_to(ROOT)),
        "note": "The notch is cut in the right half; the left half is unchanged. The 3MF is the X2D print-frame right half.",
    }
    QA.mkdir(parents=True, exist_ok=True)
    (QA / "topcase-usb14p75-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
