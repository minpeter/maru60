#!/usr/bin/env python3
"""Draft GH60 bottom-row layout envelope model.

Only models switch/key centers and nominal key widths. It intentionally does not
claim footprint, socket, LED, stabilizer, plate, or case collision clearance.
Run: python pcb/feasibility/layout_model.py --svg pcb/feasibility/bottom-row.svg
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PITCH = 19.05
BOARD = (285.0, 94.6)
PLATE_X_OFFSET = 0.4525
PLATE_Y0 = 101.06775
BOTTOM_ROW_Y_PLATE = 6.544


def row(widths: list[tuple[str, float]], *, y: float, label: str) -> list[dict]:
    total = sum(width for _, width in widths)
    x = (BOARD[0] - total * PITCH) / 2
    out = []
    for name, width in widths:
        out.append({
            "name": name, "width_u": width, "x_pcb": round(x + width * PITCH / 2, 3),
            "y_pcb": round(PLATE_Y0 - y, 3), "x_plate": round(x + width * PITCH / 2 + PLATE_X_OFFSET, 3),
            "y_plate": y, "source": label,
        })
        x += width * PITCH
    return out


def make_layout(space: float, split_space: bool, split_backspace: bool,
                split_rshift: bool, stepped_caps: bool) -> list[dict]:
    # Standard centered row envelope. Modifier widths are deliberately explicit;
    # alternate switch sites are draft positions pending a full layout source.
    if space == 6.25:
        widths = [("L_Ctrl", 1.25), ("L_Mod", 1.25), ("L_Alt", 1.25),
                  ("Space", 6.25), ("R_Alt", 1.25), ("R_Mod", 1.25), ("R_Ctrl", 1.25)]
    elif space == 7.0:
        widths = [("L_Ctrl", 1.5), ("L_Mod", 1.5), ("L_Alt", 1.5),
                  ("Space", 7.0), ("R_Alt", 1.5), ("R_Mod", 1.5), ("R_Ctrl", 1.5)]
    else:
        raise ValueError("space must be 6.25 or 7.0")
    keys = row(widths, y=BOTTOM_ROW_Y_PLATE, label=f"{space}U nominal bottom row")

    if split_space:
        space_key = next(k for k in keys if k["name"] == "Space")
        space_key["name"] = "Space_L"
        space_key["width_u"] = 2.75
        second = dict(space_key, name="Space_R", x_pcb=round(space_key["x_pcb"] + 3.5 * PITCH, 3),
                      x_plate=round(space_key["x_plate"] + 3.5 * PITCH, 3))
        space_key["x_pcb"] = round(space_key["x_pcb"] - 3.5 * PITCH, 3)
        space_key["x_plate"] = round(space_key["x_plate"] - 3.5 * PITCH, 3)
        keys.append(second)

    # Optional alternatives are shown as sites, not asserted to be compatible
    # with the base sites. Their centers follow conventional 1U pitch positions.
    if split_backspace:
        keys.extend([
            {"name": "Backspace_L", "width_u": 1.5, "x_pcb": 256.4, "y_pcb": 18.5,
             "x_plate": 256.853, "y_plate": 82.568, "source": "illustrative split Backspace"},
            {"name": "Backspace_R", "width_u": 1.5, "x_pcb": 275.45, "y_pcb": 18.5,
             "x_plate": 275.903, "y_plate": 82.568, "source": "illustrative split Backspace"},
        ])
    if split_rshift:
        keys.extend([
            {"name": "RShift_L", "width_u": 1.75, "x_pcb": 237.35, "y_pcb": 37.55,
             "x_plate": 237.803, "y_plate": 63.518, "source": "illustrative split right Shift"},
            {"name": "RShift_R", "width_u": 1.0, "x_pcb": 263.55, "y_pcb": 37.55,
             "x_plate": 264.003, "y_plate": 63.518, "source": "illustrative split right Shift"},
        ])
    if stepped_caps:
        keys.append({"name": "Caps_Stepped", "width_u": 1.75, "x_pcb": 28.197, "y_pcb": 56.6,
                     "x_plate": 28.65, "y_plate": 44.468, "source": "illustrative stepped Caps Lock"})
    return keys


def validate_bounds(keys: list[dict]) -> list[str]:
    problems = []
    for k in keys:
        # A nominal keycap envelope only; all centers must be on the board.
        x, y = k["x_pcb"], k["y_pcb"]
        if not (0 <= x <= BOARD[0] and 0 <= y <= BOARD[1]):
            problems.append(f"{k['name']}: center outside nominal board: ({x}, {y})")
    return problems


def svg(keys: list[dict], path: Path) -> None:
    scale, margin = 3.0, 30
    w, h = int(BOARD[0] * scale + margin * 2), int(BOARD[1] * scale + margin * 2)
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
              '<rect width="100%" height="100%" fill="#f7f8fa"/>',
              f'<rect x="{margin}" y="{margin}" width="{BOARD[0]*scale}" height="{BOARD[1]*scale}" rx="8" fill="#14202b" stroke="#e69b3a" stroke-width="3"/>',
              '<text x="30" y="20" font-family="sans-serif" font-size="14" fill="#263746">Maru60 RP2350A — bottom-row envelope draft; NOT a clearance check</text>']
    for k in keys:
        x = margin + k["x_pcb"] * scale
        y = margin + (BOARD[1] - k["y_pcb"]) * scale
        rw, rh = k["width_u"] * PITCH * scale, 14 * scale
        pieces.append(f'<rect x="{x-rw/2:.1f}" y="{y-rh/2:.1f}" width="{rw:.1f}" height="{rh:.1f}" rx="5" fill="#5b9bd5" fill-opacity=".75" stroke="#b6dcff"/>')
        pieces.append(f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-family="sans-serif" font-size="10" fill="white">{k["name"]}</text>')
    pieces.append('</svg>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(pieces), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", type=float, choices=(6.25, 7.0), default=6.25)
    ap.add_argument("--split-space", action="store_true")
    ap.add_argument("--split-backspace", action="store_true")
    ap.add_argument("--split-rshift", action="store_true")
    ap.add_argument("--stepped-caps", action="store_true")
    ap.add_argument("--svg", type=Path, default=Path("pcb/feasibility/bottom-row.svg"))
    args = ap.parse_args()
    keys = make_layout(args.space, args.split_space, args.split_backspace, args.split_rshift, args.stepped_caps)
    problems = validate_bounds(keys)
    svg(keys, args.svg)
    print(json.dumps({"space_u": args.space, "key_sites": len(keys), "board_mm": BOARD,
                      "bounds": "PASS" if not problems else problems,
                      "clearance": "NOT CHECKED: footprints, sockets, LEDs, stabs, plate, case"},
                     indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
