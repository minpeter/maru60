"""SI extraction must preserve real via-land contacts without bridging gaps."""
import json
from pathlib import Path
import tempfile
import unittest

from pcb.tools.signal_integrity.geom import Board


class ViaContactTest(unittest.TestCase):
    def route(self, endpoint_x, via_net="SIG"):
        def pad(ref, x, y, layer):
            return {"ref": ref, "pads": [{"num": "1", "net": "SIG", "x": x, "y": y,
                    "sx": .4, "sy": .4, "drill": [0, 0], "layers": [layer],
                    "poly": [[[x-.2, y-.2], [x+.2, y-.2], [x+.2, y+.2], [x-.2, y+.2]]]}]}
        board = {"fps": [pad("A", endpoint_x, 1, "F.Cu"), pad("B", 2, 0, "B.Cu")],
                 "tracks": [dict(x1=endpoint_x, y1=1, x2=endpoint_x, y2=0, w=.15, layer="F.Cu", net="SIG"),
                            dict(x1=1, y1=0, x2=2, y2=0, w=.15, layer="B.Cu", net="SIG")],
                 "vias": [dict(x=1, y=0, d=.5, drill=.25, net=via_net)], "zones": []}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "board.json"
            path.write_text(json.dumps(board))
            return Board(path).route("SIG", ("A", "1"), ("B", "1"))

    def test_endpoint_inside_via_land(self):
        self.assertIsNotNone(self.route(1.04))

    def test_gap_does_not_connect(self):
        self.assertIsNone(self.route(1.5))

    def test_different_net_barrel_does_not_connect(self):
        self.assertIsNone(self.route(1.04, "GND"))


if __name__ == "__main__":
    unittest.main()
