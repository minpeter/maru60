"""Routing must account for material holes and clearance beyond its search box."""
import sys
from pathlib import Path
import unittest
from shapely.geometry import LineString, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"pcb/tools"))
from local_router import Layout
from route_component_pair import Maps


def part(ref, net, bounds):
    x0, y0, x1, y1 = bounds
    return dict(ref=ref, layer="B.Cu", x=(x0+x1)/2, y=(y0+y1)/2,
                pads=[dict(num="1", net=net, x=(x0+x1)/2, y=(y0+y1)/2,
                           drill=[0, 0], layers=["B.Cu"], poly=[[[x0, y0], [x1, y0], [x1, y1], [x0, y1]]])])


def board(parts, holes=()):
    outer = [[-10, -10], [10, -10], [10, 10], [-10, 10]]
    return dict(fps=parts, tracks=[], vias=[], zones=[],
                edges=[dict(x1=aa[0], y1=aa[1], x2=bb[0], y2=bb[1]) for aa, bb in zip(outer, outer[1:]+outer[:1])],
                board_material=[[outer, *holes]])


class LocalRouterClearanceTest(unittest.TestCase):
    def test_component_map_keeps_obstacles_outside_window(self):
        parts = [part("OUTSIDE", "OTHER", (.25, 1.6, .65, 1.9))]
        maps = Maps(board(parts), {"SIG"}, [-1.5, -1.5, 1.5, 1.5])
        cy, cx = maps.cell(.45, 1.5)
        self.assertLess(maps.dist_all["B.Cu"][cy, cx], .15)

    def test_own_via_barrel_reserves_drill_space(self):
        g = board([])
        g["vias"] = [dict(x=0, y=0, d=.5, drill=.25, net="SIG")]
        maps = Maps(g, {"SIG"}, [-1.5, -1.5, 1.5, 1.5])
        cy, cx = maps.cell(.3, 0)
        self.assertLess(maps.dist_holes[cy, cx], .25)

    def test_copper_outside_search_box_still_blocks_wide_track(self):
        parts = [part("A", "SIG", (-.1, -.1, .1, .1)),
                 part("B", "SIG", (1.1, -.1, 1.3, .1)),
                 part("WALL", "OTHER", (.3, -2, .6, 1.1))]
        self.assertIsNotNone(Layout(board(parts)).route("B.Cu", (0, 0), "SIG", width=.25, half=1.5))
        # This pad begins 0.1 mm beyond the centerline search boundary; the
        # track width and clearance still extend into it.
        parts.append(part("OUTSIDE", "OTHER", (.25, 1.6, .65, 1.9)))
        self.assertIsNone(Layout(board(parts)).route("B.Cu", (0, 0), "SIG", width=.25, half=1.5))

    def test_route_preserves_half_mm_from_internal_window(self):
        hole = [[-.5, -.5], [.5, -.5], [.5, .5], [-.5, .5]]
        parts = [part("A", "SIG", (-2.1, -.1, -1.9, .1)), part("B", "SIG", (1.9, -.1, 2.1, .1))]
        route = Layout(board(parts, [hole])).route("B.Cu", (-2, 0), "SIG", width=.20, half=5)
        self.assertIsNotNone(route)
        for t in route:
            shape = LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"]/2)
            self.assertGreaterEqual(shape.distance(Polygon(hole)), .5)


if __name__ == "__main__":
    unittest.main()
