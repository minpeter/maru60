"""Public generator contract: the LUBAN catch option changes only the four catch sites."""
import unittest

import manifold3d as md

import build_bottomcase_draft as bottom
import build_topcase_draft as top
import rule60_spec as spec


def solid(m):
    return [p for p in m.decompose() if p.volume() > 1e-3]


class LubanCatchOptionTest(unittest.TestCase):
    def test_changes_stay_inside_the_catch_sites(self):
        board = spec.default_board()
        sites = md.Manifold()
        for _, sx, sy in top.strike_centers_p():
            x, y = top.pw(sx, sy)
            sites += md.Manifold.cube([40.0, 18.0, 21.0]).translate([x - 20.0, y - 9.0, 0.0])
        stock = [*top.build_halves(board), bottom.build(board)[0]]
        luban = [*top.build_halves(board, luban_catches=True), bottom.build(board, luban_catches=True)[0]]
        for before, after in zip(stock, luban):
            changes = solid(before - after) + solid(after - before)
            self.assertTrue(changes)
            for piece in changes:
                self.assertLess((piece - sites).volume(), 1e-3)

    def test_rejects_other_catch_options(self):
        with self.assertRaises(ValueError):
            top.build_halves(spec.default_board(), luban_catches=True, strike_inserts=True)


if __name__ == '__main__':
    unittest.main()
