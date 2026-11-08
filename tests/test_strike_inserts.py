"""Public generator contract: an optional bore change must not redesign the case."""
import unittest

import manifold3d as md

import build_topcase_draft as top
import rule60_spec as spec


class StrikeInsertOptionTest(unittest.TestCase):
    def test_only_eight_original_pilots_change(self):
        original = top.build_halves(spec.default_board())
        disabled = top.build_halves(spec.default_board(), strike_inserts=False)
        enabled = top.build_halves(spec.default_board(), strike_inserts=True)
        bores = md.Manifold()
        for _, sx, sy in top.strike_centers_p():
            x, y = top.pw(sx, sy)
            for dx in (-6.5, 6.5):
                bores += md.Manifold.cylinder(3.57, 1.6, circular_segments=96).translate([x + dx, y, 2.0])
        for stock, off, on in zip(original, disabled, enabled):
            self.assertLess(abs((stock - off).volume()) + abs((off - stock).volume()), 0.001)
            expected = stock - bores
            self.assertLess(abs((on - expected).volume()) + abs((expected - on).volume()), 0.001)
            self.assertGreater(stock.volume() - on.volume(), 30.0)


if __name__ == '__main__':
    unittest.main()
