"""Thermal-pad classification must not hide missing or changed barrels."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "dfm", Path(__file__).resolve().parents[1] / "pcb/tools/check_dfm_jlcpcb.py")
dfm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dfm)


class ThermalBarrelsTest(unittest.TestCase):
    def setUp(self):
        pads = [{"num": "61", "drill": [0, 0],
                 "poly": [[[-2, -2], [2, -2], [2, 2], [-2, 2]]]}]
        pads += [{"num": "61", "drill": [.25, .25], "sx": .6, "sy": .6,
                  "x": x, "y": y, "net": "GND",
                  "layers": ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]}
                 for x in (-1.2, 0, 1.2) for y in (-1.2, 0, 1.2)]
        self.board = {"fps": [{"ref": "U1", "pads": pads}]}

    def test_expected_array(self):
        result = dfm.thermal_barrels(self.board)
        self.assertTrue(result["pass"])
        self.assertEqual(result["barrels"][0]["annular_mm"], .175)

    def test_missing_barrel(self):
        self.board["fps"][0]["pads"].pop()
        self.assertFalse(dfm.thermal_barrels(self.board)["pass"])

    def test_changed_barrel_fails_closed(self):
        for change in ({"net": "+3V3"}, {"drill": [.5, .5]},
                       {"sx": .3}, {"x": 3}, {"layers": ["F.Cu", "B.Cu"]}):
            with self.subTest(change=change):
                board = copy.deepcopy(self.board)
                board["fps"][0]["pads"][1].update(change)
                self.assertFalse(dfm.thermal_barrels(board)["pass"])


if __name__ == "__main__":
    unittest.main()
