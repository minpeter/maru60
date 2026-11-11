"""Public generator contract: an optional bore change must not redesign the case."""
import unittest

import manifold3d as md

import build_bottomcase_draft as bottom
import build_topcase_draft as top
import rule60_spec as spec


class StrikeInsertOptionTest(unittest.TestCase):
    def test_only_eight_original_pilots_change(self):
        board = spec.default_board()
        original = top.build_halves(board)
        disabled = top.build_halves(board, inserts=False)
        enabled = top.build_halves(board, inserts=True)
        alias_enabled = top.build_halves(board, strike_inserts=True)
        bores = md.Manifold()
        for _, sx, sy in top.strike_centers_p():
            x, y = top.pw(sx, sy)
            for dx in (-6.5, 6.5):
                bores += md.Manifold.cylinder(3.57, 1.6, circular_segments=96).translate([x + dx, y, 2.0])
        for stock, off, on, alias in zip(original, disabled, enabled, alias_enabled):
            self.assertLess(abs((stock - off).volume()) + abs((off - stock).volume()), 0.001)
            self.assertLess(abs((on - alias).volume()) + abs((alias - on).volume()), 0.001)
            expected = stock - bores
            self.assertLess(abs((on - expected).volume()) + abs((expected - on).volume()), 0.001)
            self.assertGreater(stock.volume() - on.volume(), 25.0)

    def test_luban_upper_inserts_change_only_eight_bores(self):
        board = spec.default_board()
        off_halves = top.build_halves(board, luban_catches=True, inserts=False)
        on_halves = top.build_halves(board, luban_catches=True, inserts=True)
        bores = md.Manifold()
        half_pitch = top.LUBAN["strike"]["screw_pitch"] / 2
        for _, sx, sy in top.strike_centers_p(luban=True):
            x, y = top.pw(sx, sy)
            for dx in (-half_pitch, half_pitch):
                bores += md.Manifold.cylinder(top.LUBAN_BORE_DEPTH + 0.02, 1.6, circular_segments=96).translate(
                    [x + dx, y, top.LUBAN_STRIKE_Z - top.LUBAN_BORE_DEPTH]
                )
        for off, on in zip(off_halves, on_halves):
            expected = off - bores
            self.assertLess(abs((on - expected).volume()) + abs((expected - on).volume()), 0.001)
            self.assertGreater(off.volume() - on.volume(), 25.0)

    def test_bottom_inserts_change_only_eight_bores(self):
        board = spec.default_board()
        for luban in (False, True):
            with self.subTest(luban=luban):
                off, _ = bottom.build(board, battery_bay=False, inserts=False, luban_catches=luban)
                on, _ = bottom.build(board, battery_bay=False, inserts=True, luban_catches=luban)
                catch_floor = top.LUBAN_CATCH_Z if luban else bottom.CATCH_FLOOR_ZP
                envelopes = md.Manifold()
                for site in bottom.catch_sites_p(luban=luban):
                    for xp, yp in site["screws_p"]:
                        xw, yw = bottom.pw(xp, yp)
                        envelopes += md.Manifold.cylinder(4.10, 1.61, circular_segments=96).translate(
                            [xw, yw, catch_floor - 0.05]
                        )
                self.assertLess(((off - on) - envelopes).volume(), 0.001)
                self.assertLess(((on - off) - envelopes).volume(), 0.001)
                self.assertGreater(off.volume() - on.volume(), 30.0)


if __name__ == '__main__':
    unittest.main()
