"""Native regression: a milled LED window severs copper on the actual board.

Run: tools/run_kicad9.sh python3 tests/test_board_cutout_material.py
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    import pcbnew as p
except ImportError:
    p = None

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(p is None, "requires the pinned KiCad 9 environment")
class CutoutMaterialTest(unittest.TestCase):
    def board(self, path, detour):
        b = p.BOARD()
        b.SetCopperLayerCount(4)
        def xy(x, y):
            return p.VECTOR2I(round(x*1e6), round(y*1e6))
        def rectangle(parent, points):
            for a, c in zip(points, points[1:]+points[:1]):
                s = p.PCB_SHAPE(parent)
                s.SetShape(p.SHAPE_T_SEGMENT)
                s.SetLayer(p.Edge_Cuts)
                s.SetWidth(50000)
                s.SetStart(xy(*a)); s.SetEnd(xy(*c))
                parent.Add(s)
        rectangle(b, [(0, 0), (10, 0), (10, 10), (0, 10)])
        cut = p.FOOTPRINT(b)
        cut.SetReference("WINDOW")
        b.Add(cut)
        rectangle(cut, [(4.5, 4), (5.5, 4), (5.5, 6), (4.5, 6)])
        net = p.NETINFO_ITEM(b, "SIG")
        b.Add(net)
        for ref, x in (("A", 2), ("B", 8)):
            f = p.FOOTPRINT(b)
            f.SetReference(ref)
            b.Add(f)
            pad = p.PAD(f)
            pad.SetNumber("1")
            pad.SetAttribute(p.PAD_ATTRIB_SMD)
            layers = p.LSET()
            layers.AddLayer(p.F_Cu)
            pad.SetLayerSet(layers)
            pad.SetShape(p.F_Cu, p.PAD_SHAPE_RECT)
            pad.SetSize(p.F_Cu, xy(.8, .8))
            pad.SetPosition(xy(x, 5)); pad.SetNet(net)
            f.Add(pad)
        route = [(2, 5), (2, 7), (8, 7), (8, 5)] if detour else [(2, 5), (8, 5)]
        for a, c in zip(route, route[1:]):
            t = p.PCB_TRACK(b)
            t.SetStart(xy(*a)); t.SetEnd(xy(*c))
            t.SetLayer(p.F_Cu); t.SetWidth(200000); t.SetNet(net)
            b.Add(t)
        p.SaveBoard(str(path), b)

    def run_case(self, detour):
        with tempfile.TemporaryDirectory(dir=ROOT/"build") as temp:
            root = Path(temp)
            board = root/"probe.kicad_pcb"
            self.board(board, detour)
            out = root/"material.json"
            subprocess.run([sys.executable, str(ROOT/"pcb/tools/export_material_graph.py"), str(board), str(out)],
                           check=True, capture_output=True, text=True)
            report = json.loads(out.read_text())
            self.assertEqual(report["scope_assumptions"]["internal_routed_window_count"], 1)
            self.assertTrue(report["unchanged"])
            geom = root/"geometry.json"
            subprocess.run([sys.executable, str(ROOT/"pcb/tools/dump_board_geometry.py"), str(board), str(geom)],
                           check=True, capture_output=True, text=True)
            geometry = json.loads(geom.read_text())
            self.assertEqual(len(geometry["edges"]), 8)
            self.assertEqual(len(geometry["board_material"][0])-1, 1)
            return report

    def test_track_across_window_is_physically_disconnected(self):
        report = self.run_case(False)
        self.assertEqual(len(report["pad_partitions_by_net"]["SIG"]), 2)
        self.assertEqual(len(report["multiple_component_object_layers"]), 1)

    def test_route_around_window_retains_connection(self):
        report = self.run_case(True)
        self.assertEqual(len(report["pad_partitions_by_net"]["SIG"]), 1)
        self.assertEqual(report["multiple_component_object_layers"], [])


if __name__ == "__main__":
    unittest.main()
