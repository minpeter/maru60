"""Rule 60 V3 interface spec: stock-part values (spec/rule60-v3.json), INKC plate outlines (spec/rule60-v3-outlines.json)
and GH60-class board profiles (spec/boards.json), shared by build_topcase_draft.py and verify_topcase.py."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

SPEC = Path(__file__).resolve().parent / "spec"
_VALUES: dict[str, Any] = {k: v["value"] for k, v in json.loads((SPEC / "rule60-v3.json").read_text())["values"].items()}
_OUTLINES: dict[str, Any] = json.loads((SPEC / "rule60-v3-outlines.json").read_text())
_BOARDS: dict[str, Any] = json.loads((SPEC / "boards.json").read_text())
UNIVERSAL = "universal"


def value(key: str) -> Any:
    return _VALUES[key]


def outline(name: str) -> dict[str, Any]:
    """Outline record `name` from spec/rule60-v3-outlines.json (bbox, thickness, label, verts)."""
    return next(o for o in _OUTLINES["outlines"] if o["name"] == name)


def point(name: str) -> tuple[float, float]:
    """Named point from spec/rule60-v3-outlines.json (plate frame), e.g. `esc_switch_centre`."""
    x, y = _OUTLINES["points"][name]
    return x, y


def bulge_arc(x0: float, y0: float, x1: float, y1: float, bulge: float) -> tuple[float, float, float, float]:
    """Arc (centre x, centre y, radius, swept angle; positive = counter-clockwise) of a DWG bulge segment."""
    theta = 4.0 * math.atan(bulge)
    chord = math.hypot(x1 - x0, y1 - y0)
    r = chord / (2.0 * abs(math.sin(theta / 2.0)))
    nx, ny = -(y1 - y0) / chord, (x1 - x0) / chord
    if bulge < 0:
        nx, ny = -nx, -ny
    d = r * math.cos(theta / 2.0)
    return (x0 + x1) / 2 + nx * d, (y0 + y1) / 2 + ny * d, r, theta


def verts_points(verts: list[list[float]], arc_steps: int = 12) -> list[tuple[float, float]]:
    """Closed [x, y, bulge] loop as points, arcs split into `arc_steps` chords; first point not repeated."""
    pts: list[tuple[float, float]] = []
    for k, (x0, y0, bulge) in enumerate(verts):
        x1, y1, _ = verts[(k + 1) % len(verts)]
        pts.append((x0, y0))
        if abs(bulge) < 1e-9:
            continue
        cx, cy, r, theta = bulge_arc(x0, y0, x1, y1, bulge)
        a0 = math.atan2(y0 - cy, x0 - cx)
        pts.extend((cx + r * math.cos(a0 + theta * t / arc_steps), cy + r * math.sin(a0 + theta * t / arc_steps))
                   for t in range(1, arc_steps))
    return pts


def outline_points(name: str, arc_steps: int = 12) -> list[tuple[float, float]]:
    """Closed outline `name` in the plate frame, arcs (DWG bulges) split into `arc_steps` chords; first point not repeated."""
    return verts_points(outline(name)["verts"], arc_steps)


def gasket_outlines_plate(arc_steps: int = 16) -> list[list[tuple[float, float]]]:
    """Plan outlines (plate frame) of the 12 gasket caps (`gasket.cap_free`) pushed fully onto the gas-plate tab ends,
    two per tab: the rounded end stands `length - slot_depth` past the tab end, the cap centred on the tab centre line.
    First point not repeated; winding not normalised."""
    cap = value("gasket.cap_free")
    r, over = cap["width"] / 2, cap["length"] - cap["slot_depth"]
    outlines = []
    for y, tabs in zip(value("plate.tab_mid_y"), (value("plate.front_tabs_x"), value("plate.back_tabs_x"))):
        for x_left, x_right in tabs:
            for x_end, inward in ((x_left, 1.0), (x_right, -1.0)):
                x_open, xc = x_end + inward * cap["slot_depth"], x_end - inward * (over - r)  # open end, tip arc centre
                arc = [(xc - inward * r * math.cos(t), y + r * math.sin(t))
                       for t in (math.pi * (k / arc_steps - 0.5) for k in range(arc_steps + 1))]
                outlines.append([(x_open, y - r), *arc, (x_open, y + r)])
    return outlines


def board_ids() -> list[str]:
    return [b["id"] for b in _BOARDS["boards"]] + [UNIVERSAL]


def default_board() -> str:
    return _BOARDS["default"]


def board(board_id: str) -> dict[str, Any]:
    return next(b for b in _BOARDS["boards"] if b["id"] == board_id)


def usb_centre_plate_x(board_id: str) -> float | None:
    """Plate X of a board's on-board USB connector at the back edge, or None (unknown, daughterboard, other edge)."""
    usb = board(board_id)["usb"]
    if usb is None or usb["centre_x"] is None or usb.get("edge") not in (None, "back") or usb.get("daughterboard") is True:
        return None
    if usb["frame"] == "plate":
        return usb["centre_x"]
    assert usb["frame"] == "gh60", usb["frame"]
    return round(usb["centre_x"] + _BOARDS["frames"]["pcb_to_plate"]["dx"], 4)


def usb_notch(board_id: str) -> tuple[float, float]:
    """USB notch centre (plate X) and width for a board. `universal` widens the stock notch by the spread of every
    measured on-board USB centre (fit verdict not `no`; `inferred` guesses such as a centre read off a cable plug are left
    out) and centres it on that spread, so each of those boards keeps at least the stock clearance."""
    width = value("top.usb_notch")["width"]
    if board_id != UNIVERSAL:
        centre = usb_centre_plate_x(board_id)
        if centre is None:
            raise SystemExit(f"Board {board_id!r} has no on-board USB position in spec/boards.json; use --board {UNIVERSAL}")
        return centre, width
    xs = [x for b in _BOARDS["boards"]
          if b["fit"]["verdict"] != "no" and b["usb"] and b["usb"].get("status") != "inferred"
          and (x := usb_centre_plate_x(b["id"])) is not None]
    return round((min(xs) + max(xs)) / 2, 4), round(width + max(xs) - min(xs), 4)
