"""A power model must not hide disconnected loads or omit colocated loads."""
import math
import unittest

from pcb.tools.analyze_pdn import Net, distribute_current, resistance, TEMPCO


def track(a, b, layer="F.Cu"):
    return dict(net="P", x1=a, y1=0, x2=b, y2=0, w=.2, layer=layer)


def pad(x, layer="F.Cu"):
    return dict(num="2", net="P", x=x, y=0, drill=[0, 0], layers=[layer],
                poly=[[[x-.05, -.05], [x+.05, -.05], [x+.05, .05], [x-.05, .05]]])


class PdnNetworkTest(unittest.TestCase):
    def test_pad_edge_meeting_middle_of_track_carries_load(self):
        load = pad(1)
        load["y"] = .15
        load["poly"] = [[[.8,.05],[1.2,.05],[1.2,.25],[.8,.25]]]
        board = dict(fps=[dict(ref="LOAD", pads=[load])], vias=[], zones=[], tracks=[track(0,2)])
        net = Net(board, "P")
        source = net.pts.index(("F.Cu", 0, 0))
        self.assertGreater(resistance(net, source, net.pad("LOAD", "2"))[0], 0)

    def test_zone_hole_does_not_short_an_isolated_load_to_supply(self):
        outer = [[-1,-1],[5,-1],[5,1],[-1,1]]
        hole = [[2.5,-.5],[4.5,-.5],[4.5,.5],[2.5,.5]]
        board = dict(fps=[dict(ref="A", pads=[pad(1)]), dict(ref="B", pads=[pad(4)])],
                     vias=[], tracks=[], zones=[dict(net="P", fill={"F.Cu": [[outer,hole]]})])
        net = Net(board, "P")
        with self.assertRaisesRegex(ValueError, "disconnected"):
            net.solve({net.pad("A", "2"): None}, {net.pad("B", "2"): .1})

    def test_round_caps_overlap_without_centerline_contact(self):
        for gap, connected in [(.15, True), (.21, False)]:
            net = Net(dict(fps=[], vias=[], zones=[], tracks=[track(0, 1), track(1+gap, 2)]), "P")
            end = net.pts.index(("F.Cu", 2, 0))
            if connected:
                self.assertGreater(resistance(net, 0, end)[0], 0)
            else:
                with self.assertRaisesRegex(ValueError, "disconnected"):
                    resistance(net, 0, end)

    def test_unloaded_island_is_excluded_but_loaded_island_is_rejected(self):
        net = Net(dict(fps=[], vias=[], zones=[], tracks=[track(0, 1), track(3, 4)]), "P")
        value, _ = resistance(net, 0, 1)
        self.assertTrue(math.isfinite(value) and value > 0)
        with self.assertRaisesRegex(ValueError, "disconnected"):
            net.solve({0: None}, {3: .1})

    def test_endpoint_inside_via_land_connects_and_temperature_scales(self):
        board = dict(fps=[], zones=[], tracks=[track(0, 1), track(1.2, 2.2, "B.Cu")],
                     vias=[dict(net="P", x=1.2, y=0, d=.5, drill=.25)])
        results = []
        for temperature in [20, 60]:
            net = Net(board, "P", temperature)
            a = net.pts.index(("F.Cu", 0, 0))
            b = net.pts.index(("B.Cu", 2.2, 0))
            results.append(resistance(net, a, b)[0])
        self.assertGreater(results[0], 0)
        self.assertAlmostEqual(results[1] / results[0], 1 + 40 * TEMPCO, places=9)

    def test_alternative_same_number_lands_are_selected_by_position(self):
        board = dict(fps=[dict(ref="LED1", pads=[pad(1), pad(4)])], vias=[], zones=[],
                     tracks=[track(0, 1), track(3, 4)])
        net = Net(board, "P")
        first = net.pad_at("LED1", "2", "F.Cu", 1, 0)
        other = net.pad_at("LED1", "2", "F.Cu", 4, 0)
        self.assertNotEqual(first, other)
        net.solve({0: None}, {first: .1})
        with self.assertRaisesRegex(ValueError, "disconnected"):
            net.solve({0: None}, {other: .1})

    def test_loads_sharing_a_node_keep_their_total_current(self):
        loads = distribute_current([10, 10, 20], .3)
        self.assertAlmostEqual(loads[10], .2)
        self.assertAlmostEqual(loads[20], .1)
        self.assertAlmostEqual(sum(loads.values()), .3)


if __name__ == "__main__":
    unittest.main()
