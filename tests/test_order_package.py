"""The JLCPCB order package must stay consistent with the board it was exported from."""
import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDER = ROOT / "pcb/order"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OrderPackage(unittest.TestCase):
    def setUp(self):
        self.prov = json.loads((ORDER / "PROVENANCE.json").read_text())

    def test_exported_from_the_pinned_order_candidate(self):
        board = ROOT / self.prov["board"]["path"]
        self.assertEqual(sha256(board), self.prov["board"]["sha256"])
        manifest = json.loads((ROOT / "pcb/current.json").read_text())
        pinned = {f["path"]: f["sha256"] for f in manifest["order_candidate"]["files"]}
        self.assertEqual(pinned[self.prov["board"]["path"]], self.prov["board"]["sha256"])

    def test_every_export_check_passed(self):
        self.assertEqual(self.prov["status"], "ORDER_CANDIDATE")
        self.assertEqual([c["check"] for c in self.prov["checks"] if not c["pass"]], [])

    def test_files_match_recorded_hashes(self):
        for rel, digest in self.prov["files"].items():
            self.assertEqual(sha256(ORDER / rel), digest, rel)
        self.assertEqual(sha256(ORDER / "parts.json"), self.prov["parts_database"]["sha256"])

    def test_bom_and_cpl_agree(self):
        bom = list(csv.DictReader((ORDER / "bom-jlcpcb.csv").open()))
        cpl = list(csv.DictReader((ORDER / "cpl-jlcpcb.csv").open()))
        bom_refs = [d for row in bom for d in row["Designator"].split(",")]
        self.assertEqual(len(bom_refs), len(set(bom_refs)), "a designator appears twice in the BOM")
        self.assertEqual(set(bom_refs), {row["Designator"] for row in cpl})
        self.assertEqual(len(cpl), self.prov["summary"]["assembled_parts"])
        for row in bom:
            self.assertRegex(row["LCSC Part #"], r"^C\d+$", row["Designator"])
        for row in cpl:
            self.assertIn(row["Layer"], ("Top", "Bottom"))
            float(row["Mid X"]), float(row["Mid Y"]), float(row["Rotation"])

    def test_polarised_parts_use_rotations_fitted_to_jlcpcb_footprints(self):
        fit = json.loads((ORDER / "jlcpcb-placement.json").read_text())["placements"]
        cpl = {row["Designator"]: row for row in csv.DictReader((ORDER / "cpl-jlcpcb.csv").open())}
        full = {row["Reference"]: row for row in csv.DictReader((ORDER / "bom-full.csv").open())}
        polarised = [r for r, row in full.items() if row["Polarised"] == "yes" and row["Assembled by JLCPCB"] == "yes"]
        self.assertGreater(len(polarised), 150)
        for ref in polarised:
            self.assertEqual(fit[ref]["status"], "fitted", ref)
            self.assertAlmostEqual(float(cpl[ref]["Rotation"]), fit[ref]["rotation"], places=2, msg=ref)
            self.assertAlmostEqual(float(cpl[ref]["Mid X"]), fit[ref]["x"], places=3, msg=ref)
            self.assertAlmostEqual(float(cpl[ref]["Mid Y"]), -fit[ref]["y"], places=3, msg=ref)

    def test_relocated_parts_are_on_the_bottom(self):
        full = {row["Reference"]: row for row in csv.DictReader((ORDER / "bom-full.csv").open())}
        # C200 left its under-switch site for B.Cu beside the +4V_LED via, and
        # LED75 relays the Caps chain from the bottom; neither sits under an MX
        # housing any more.
        self.assertEqual(full["C200"]["Side"], "Bottom")
        self.assertEqual(full["C200"]["Assembled by JLCPCB"], "yes")
        self.assertEqual(full["LED75"]["Side"], "Bottom")
        self.assertEqual(len(full), self.prov["summary"]["footprints"])


if __name__ == "__main__":
    unittest.main()
