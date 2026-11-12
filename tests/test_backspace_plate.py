"""The plate-mount 7U option must retain its original clip geometry and arcs."""
import sys
import unittest
from pathlib import Path

import ezdxf
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'pcb/tools'))
import build_plate_backspace_2u as build
from build_plate_pcb_mount import SEVEN_U_INDEX
import rule60_spec as spec


class BackspacePlateTest(unittest.TestCase):
    def test_only_backspace_changes_in_plate_mount_variant(self):
        rec, _, _, _, plate, _, loops, removed = build.geometry('plate')
        self.assertEqual(removed, [60, 61])
        self.assertTrue(plate.is_valid)
        self.assertEqual(loops[0], rec['verts'])
        for i, vertices in enumerate(rec['cutouts']):
            if i not in removed:
                self.assertEqual(loops[i+1], vertices, f'cutout {i}')
        self.assertEqual(len(loops), 62)  # outer + 61 openings (split pair replaced)

    def test_pcb_relief_is_not_used_for_plate_mount(self):
        stock = build.geometry('plate')
        pcb = build.geometry('pcb')
        a = Polygon(spec.verts_points(stock[6][SEVEN_U_INDEX+1], 48))
        b = Polygon(spec.verts_points(pcb[6][SEVEN_U_INDEX+1], 48))
        self.assertGreater(b.area-a.area, 1.)
        self.assertLess(stock[3].symmetric_difference(pcb[3]).area, 1e-9)

    def test_delivered_dxf_retains_seven_u_arcs(self):
        rec = spec.outline('plate_gas_hhkb')
        doc = ezdxf.readfile(ROOT/'models'/f'{build.NAMES["plate"]}.dxf')
        polylines = list(doc.modelspace().query('POLYLINE'))
        vertices = polylines[SEVEN_U_INDEX+1].vertices
        expected = rec['cutouts'][SEVEN_U_INDEX]
        self.assertEqual(len(vertices), len(expected))
        for v, (x,y,bulge) in zip(vertices, expected):
            self.assertAlmostEqual(v.dxf.location.x, x, places=4)
            self.assertAlmostEqual(v.dxf.location.y, y, places=4)
            self.assertAlmostEqual(v.dxf.bulge, bulge, places=6)
        self.assertTrue(any(v.dxf.bulge for v in vertices))


if __name__ == '__main__':
    unittest.main()
