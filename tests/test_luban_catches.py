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

    def test_defaults_to_self_tapping_and_combines_with_inserts(self):
        board = spec.default_board()
        top_self = top.build_halves(board, luban_catches=True)
        top_ins = top.build_halves(board, luban_catches=True, inserts=True)
        bot_self, rep_self = bottom.build(board, luban_catches=True)
        bot_ins, rep_ins = bottom.build(board, luban_catches=True, inserts=True)
        self.assertFalse(rep_self["inserts"])
        self.assertTrue(rep_ins["inserts"])
        self.assertEqual(rep_self["luban32"]["bore_d"], bottom.PILOT_D)
        self.assertEqual(rep_ins["luban32"]["bore_d"], top.CANOT_INSERT["hole_d"])
        for s_half, i_half in zip(top_self, top_ins):
            self.assertGreater(s_half.volume() - i_half.volume(), 25.0)
        self.assertGreater(bot_self.volume() - bot_ins.volume(), 30.0)

    def test_rejects_other_catch_options(self):
        with self.assertRaises(ValueError):
            top.build_halves(spec.default_board(), luban_catches=True, catch_inserts=True)
        with self.assertRaises(ValueError):
            bottom.build(spec.default_board(), luban_catches=True, catch_inserts=True)


if __name__ == '__main__':
    unittest.main()
