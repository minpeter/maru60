import json
import math
import random
import time
import unittest
from fractions import Fraction as F
from positive_witness import *


def rect(x0, y0, x1, y1):
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


class ExactControls(unittest.TestCase):
    def setUp(self):
        self.a = prepare_rings(rect(0, 0, 100, 100))

    def test_disjoint_touching_and_one_nm_sliver_reject(self):
        for x in (101, 100, 99):
            b = prepare_rings(rect(x, 0, 200, 100))
            self.assertFalse(find_positive_witness(self.a, b).found)
            with self.assertRaises(NoPositiveWitness):
                require_positive_witness(self.a, b)
        self.assertFalse(verify_positive_witness(self.a, self.a, (0, 50)))

    def test_robust_overlap_and_serialization(self):
        b = prepare_rings(rect(50, 10, 150, 90))
        w = require_positive_witness(self.a, b)
        self.assertTrue(verify_positive_witness(self.a, b, w.point))
        rec = json.loads(json.dumps(w.to_dict()))
        self.assertTrue(verify_witness_record(self.a, b, rec))
        rec['point']['x_num'] = 1000000000
        self.assertFalse(verify_witness_record(self.a, b, rec))

    def test_hole_reject_and_boundary(self):
        ring = prepare_rings(rect(0, 0, 100, 100), (rect(20, 20, 80, 80),))
        hole_inside = prepare_rings(rect(30, 30, 70, 70))
        self.assertFalse(find_positive_witness(ring, hole_inside).found)
        for pt in ((50, 50), (20, 50), (19, 50)):
            self.assertFalse(verify_positive_witness(ring, self.a, pt))
        self.assertTrue(verify_positive_witness(ring, self.a, (18, 50)))
        self.assertTrue(require_positive_witness(ring, self.a))

    def test_exact_guard_threshold_and_fractional_points(self):
        # Shared 4 nm strip has exactly one allowed x coordinate.
        b = prepare_rings(rect(96, 0, 200, 100))
        w = require_positive_witness(self.a, b)
        self.assertEqual(w.point, ExactPoint(98, 50))
        self.assertFalse(verify_positive_witness(self.a, b, (F(979, 10), 50)))
        self.assertFalse(verify_positive_witness(self.a, b, (F(981, 10), 50)))
        self.assertTrue(verify_positive_witness(self.a, self.a, (F(5, 2), F(99, 2))))
        with self.assertRaises(TypeError):
            verify_positive_witness(self.a, b, (98.0, 50))
        with self.assertRaises(ValueError):
            verify_positive_witness(self.a, b, (98, 50), 1)

    def test_diagonal_distance_not_axis_distance(self):
        diamond = prepare_rings(((0, 10), (10, 0), (20, 10), (10, 20)))
        # (1.5,10) is 1.5/sqrt(2) from each adjoining diagonal, not 2.
        self.assertFalse(verify_positive_witness(diamond, diamond, (F(3, 2), 10)))
        self.assertFalse(verify_positive_witness(diamond, diamond, (F(14, 5), 10)))
        self.assertTrue(verify_positive_witness(diamond, diamond, (3, 10)))

    def test_big_translation_and_negative_coordinates(self):
        for shift in (-(10**20), 10**20):
            a = prepare_rings(rect(shift, shift, shift+100, shift+100))
            self.assertTrue(verify_positive_witness(a, a, (shift+2, shift+2)))
            self.assertFalse(verify_positive_witness(a, a, (F(shift)+F(19, 10), shift+50)))

    def test_orientation_and_repeated_endpoint(self):
        a = prepare_rings(tuple(reversed(rect(0, 0, 100, 100)))+((0, 100),))
        self.assertTrue(verify_positive_witness(a, self.a, (50, 50)))

    def test_concave_scanline_search(self):
        # Two symmetric vertical legs: bbox center and polygon mean are in gap.
        u = prepare_rings(((0,0),(100,0),(100,100),(80,100),(80,20),(20,20),(20,100),(0,100)))
        b = prepare_rings(rect(-10, 40, 110, 60))
        self.assertTrue(require_positive_witness(u, b))
        self.assertFalse(verify_positive_witness(u, b, (50, 50)))

    def test_budget_explicit_failure(self):
        a = prepare_rings(rect(0, 0, 100, 100), (rect(20, 20, 80, 80),))
        r = find_positive_witness(a, self.a, max_candidates=1, max_scanlines=0)
        self.assertFalse(r.found)
        self.assertEqual(r.reason, 'candidate_budget_exhausted')
        self.assertEqual(r.candidates_checked, 1)

    def test_against_independent_fraction_oracle(self):
        # Independent direct ray intersections and direct rational distances.
        random.seed(1729)
        c = prepare_rings(((0, 0), (40, -20), (90, 10), (100, 80), (30, 100), (-20, 40)),
                          (rect(20, 20, 40, 40),))
        def oracle(p):
            x, y = p
            for rid, ring in enumerate(c.rings):
                crossings = 0
                for a, b in zip(ring, ring[1:]+ring[:1]):
                    ax, ay = a; bx, by = b
                    dx, dy = bx-ax, by-ay
                    t = max(F(0), min(F(1), ((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy)))
                    if (x-ax-t*dx)**2+(y-ay-t*dy)**2 < 4:
                        return False
                    if (ay > y) != (by > y):
                        crossings += ax+(y-ay)*F(dx, dy) > x
                if bool(crossings % 2) != (rid == 0):
                    return False
            return True
        for _ in range(1500):
            pt = (F(random.randrange(-70, 331), 3), F(random.randrange(-70, 331), 3))
            self.assertEqual(verify_positive_witness(c, c, pt), oracle(pt), pt)


try:
    import pcbnew as pcb
except ImportError:
    pcb = None


@unittest.skipIf(pcb is None, 'KiCad unavailable')
class NativeSyntheticControls(unittest.TestCase):
    def poly(self, outer, holes=()):
        def chain(points):
            c = pcb.SHAPE_LINE_CHAIN()
            for x, y in points:
                c.Append(x, y)
            c.SetClosed(True)
            return c
        p = pcb.SHAPE_POLY_SET()
        p.AddOutline(chain(outer))
        for hole in holes:
            p.AddHole(chain(hole), 0)
        return p

    def test_native_component_selection_and_holes(self):
        p = self.poly(rect(0, 0, 100, 100), (rect(20, 20, 80, 80),))
        p.Append(self.poly(rect(200, 0, 300, 100)))
        with self.assertRaises(ValueError):
            prepare_polyset(p)
        a = prepare_polyset(p, 0)
        b = prepare_polyset(p, 1)
        self.assertTrue(a.contains_with_clearance((10, 50)))
        self.assertFalse(a.contains_with_clearance((50, 50)))
        self.assertFalse(a.contains_with_clearance((250, 50)))
        self.assertTrue(b.contains_with_clearance((250, 50)))
        self.assertFalse(b.contains_with_clearance((50, 50)))
        with self.assertRaises(IndexError):
            prepare_polyset(p, 2)

    def test_native_boolean_is_untrusted_seed_only(self):
        pa = self.poly(rect(0, 0, 100, 100))
        pb = self.poly(rect(50, 10, 150, 90))
        native = pcb.SHAPE_POLY_SET()
        native.BooleanIntersection(pa, pb)
        a, b = prepare_polyset(pa), prepare_polyset(pb)
        self.assertTrue(require_positive_witness(a, b, seed_polyset=native))
        # Intentionally false positive native seed polygon cannot produce proof.
        ring = prepare_polyset(self.poly(rect(0, 0, 100, 100), (rect(20, 20, 80, 80),)))
        inside = prepare_rings(rect(30, 30, 70, 70))
        self.assertFalse(find_positive_witness(ring, inside, seed_polyset=pa).found)


if __name__ == '__main__':
    unittest.main(verbosity=2)
