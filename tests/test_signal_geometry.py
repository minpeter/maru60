"""SI extraction must preserve real via-land contacts without bridging gaps."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pcb.tools.signal_integrity.geom import Board


class ViaContactTest(unittest.TestCase):
    def test_pad_edge_on_middle_of_track_without_endpoint(self):
        for offset, expected in [(.15, True), (.20, False)]:
            fps = []
            for ref, x, y in [("A", 0, 0), ("B", 1, offset)]:
                fps.append(dict(ref=ref,pads=[dict(num="1",net="SIG",x=x,y=y,drill=[0,0],layers=["F.Cu"],poly=[[[x-.1,y-.1],[x+.1,y-.1],[x+.1,y+.1],[x-.1,y+.1]]])]))
            board = dict(fps=fps,vias=[],zones=[],tracks=[dict(net="SIG",layer="F.Cu",w=.15,x1=0,y1=0,x2=2,y2=0)])
            with tempfile.TemporaryDirectory() as temp:
                path=Path(temp)/"board.json";path.write_text(json.dumps(board))
                self.assertEqual(Board(path).route("SIG",("A","1"),("B","1")) is not None,expected)

    def test_stub_assignment_is_independent_of_python_hash_seed(self):
        def pad(ref, x):
            return {"ref": ref, "pads": [{"num": "1", "net": "SIG", "x": x, "y": 0,
                    "sx": .2, "sy": .2, "drill": [0, 0], "layers": ["F.Cu"],
                    "poly": [[[x-.1, -.1], [x+.1, -.1], [x+.1, .1], [x-.1, .1]]]}]}
        points = [(0,0,3,0), (1,0,1,.4), (1,.4,2,.4), (2,.4,2,0)]
        data = {"fps": [pad("A",0), pad("B",3)], "vias": [], "zones": [],
                "tracks": [dict(net="SIG", layer="F.Cu", w=.15, x1=a,y1=b,x2=c,y2=d)
                           for a,b,c,d in points]}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "board.json"
            path.write_text(json.dumps(data))
            code = "import json,sys; from pcb.tools.signal_integrity.geom import Board; print(json.dumps(Board(sys.argv[1]).route('SIG',('A','1'),('B','1')),sort_keys=True))"
            results = [subprocess.check_output([sys.executable,"-c",code,str(path)],
                       env=dict(os.environ, PYTHONHASHSEED=str(seed)),
                       cwd=Path(__file__).resolve().parents[1]) for seed in (0,1,17)]
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0], results[2])

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
        route = self.route(1.04)
        self.assertIsNotNone(route)
        self.assertEqual(route["vias"], 1)
        self.assertEqual(sum(e[0] == "via" for e in route["elements"]), 1)

    def test_gap_does_not_connect(self):
        self.assertIsNone(self.route(1.5))

    def test_different_net_barrel_does_not_connect(self):
        self.assertIsNone(self.route(1.04, "GND"))

    def test_inner_layer_excursion_counts_both_barrels(self):
        def pad(x):
            return {"ref": str(x), "pads": [{"num": "1", "net": "SIG", "x": x, "y": 0,
                    "sx": .4, "sy": .4, "drill": [0, 0], "layers": ["B.Cu"],
                    "poly": [[[x-.2, -.2], [x+.2, -.2], [x+.2, .2], [x-.2, .2]]]}]}
        for inner in ("In1.Cu", "In2.Cu"):
            with self.subTest(inner=inner), tempfile.TemporaryDirectory() as temp:
                board = {"fps": [pad(0), pad(3)], "zones": [],
                         "tracks": [dict(x1=a, y1=0, x2=b, y2=0, w=.15, layer=layer, net="SIG")
                                    for a, b, layer in [(0, 1, "B.Cu"), (1, 2, inner), (2, 3, "B.Cu")]],
                         "vias": [dict(x=x, y=0, d=.5, drill=.25, net="SIG") for x in (1, 2)]}
                path = Path(temp) / "board.json"
                path.write_text(json.dumps(board))
                route = Board(path).route("SIG", ("0", "1"), ("3", "1"))
                self.assertEqual(route["vias"], 2)
                self.assertEqual(sum(e[0] == "via" for e in route["elements"]), 2)


if __name__ == "__main__":
    unittest.main()
