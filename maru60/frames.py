"""Plate-to-underside coordinates shared by housing generators and mating gauges."""

from dataclasses import dataclass

import numpy as np
import shapely.geometry as sg
from numpy.typing import NDArray

import rule60_spec as spec


@dataclass(frozen=True, slots=True)
class PlateFrame:
    offset_x: float
    offset_y: float
    x_sign: float

    def point(self, x: float, y: float) -> tuple[float, float]:
        return self.x_sign * (x + self.offset_x), y + self.offset_y


def plate_gas_world(frame: PlateFrame) -> NDArray[np.float64]:
    world = np.asarray(
        [frame.point(x, y) for x, y in spec.outline_points("plate_gas")],
        dtype=np.float64,
    )
    return world if sg.LinearRing(world).is_ccw else world[::-1]


OPENING_P = tuple(
    spec.value("top.keycap_opening_hhkb")
)  # HHKB keycap opening bounds (plate frame); front edge = bottom-row middle
BEZEL_SIDE, BEZEL_BACK, BEZEL_FRONT = (
    spec.value("top.bezel")[k] for k in ("side", "back", "front")
)  # Top-face bezel
SKIRT_WALL = spec.value("top.skirt_wall")[
    "side_back"
]  # Skirt wall thickness, sides and back (caliper, flipped)
FRONT_WALL = spec.value("top.skirt_wall")[
    "front"
]  # Skirt wall thickness, front (caliper, flipped)
RIM_SEAT_W = spec.value(
    "top.rim_seat_w"
)  # Floor ledge (bottom-case rim seat) inside the skirt: short side 4.90 - 2.85 mm
STOCK_OUTER_P = (
    round(OPENING_P[0] - BEZEL_SIDE, 3),
    round(OPENING_P[1] - BEZEL_FRONT, 3),
    round(OPENING_P[2] + BEZEL_SIDE, 3),
    round(OPENING_P[3] + BEZEL_BACK, 3),
)  # Caliper outline (-6.10, -4.82, 292.00, 112.55)
STOCK_INNER_P = (
    round(STOCK_OUTER_P[0] + SKIRT_WALL, 3),
    round(STOCK_OUTER_P[1] + FRONT_WALL, 3),
    round(STOCK_OUTER_P[2] - SKIRT_WALL, 3),
    round(STOCK_OUTER_P[3] - SKIRT_WALL, 3),
)  # Caliper inner skirt faces: the strikes and the Maru bottom-case rails are placed from these
# The caliper pocket left the stock bottom case (111.63 wide, owner) 0.05 mm per side, and both bottom cases pressed in
# hard, grinding (owner, 2026-11-10); the stock pair has play. The skirt grows outward by `POCKET_GROW` on every side,
# walls kept at the caliper thickness, so the pocket and the outline both grow while everything inside stays put.
POCKET_GROW = 0.20
OUTER_P = (
    round(STOCK_OUTER_P[0] - POCKET_GROW, 3),
    round(STOCK_OUTER_P[1] - POCKET_GROW, 3),
    round(STOCK_OUTER_P[2] + POCKET_GROW, 3),
    round(STOCK_OUTER_P[3] + POCKET_GROW, 3),
)  # (-6.30, -5.02, 292.20, 112.75)
INNER_P = (
    round(OUTER_P[0] + SKIRT_WALL, 3),
    round(OUTER_P[1] + FRONT_WALL, 3),
    round(OUTER_P[2] - SKIRT_WALL, 3),
    round(OUTER_P[3] - SKIRT_WALL, 3),
)  # Inner skirt faces (the bottom-case pocket)
LEDGE_P = (
    round(STOCK_INNER_P[0] + RIM_SEAT_W, 3),
    round(STOCK_INNER_P[1] + RIM_SEAT_W, 3),
    round(STOCK_INNER_P[2] - RIM_SEAT_W, 3),
    round(STOCK_INNER_P[3] - RIM_SEAT_W, 3),
)  # Inner edge of the floor ledge (caliper position)
CASE_W = round(OUTER_P[2] - OUTER_P[0], 3)  # 298.50
CASE_D = round(OUTER_P[3] - OUTER_P[1], 3)  # 117.77
WRIST_D = 80.00  # Integrated honeycomb wrist-rest depth
DX_PW = round(-(OUTER_P[0] + OUTER_P[2]) / 2, 3)  # -142.95
DY_PW = round(WRIST_D - OUTER_P[1], 3)  # 84.82
PW_SX = -1.0  # Plate X -> print X sign (underside view)


PLATE_FRAME = PlateFrame(DX_PW, DY_PW, PW_SX)


def pw(xp: float, yp: float) -> tuple[float, float]:
    x, y = PLATE_FRAME.point(xp, yp)
    return round(x, 4), round(y, 4)
