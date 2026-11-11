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

    def test_parts_under_switch_housings_are_not_assembled(self):
        full = {row["Reference"]: row for row in csv.DictReader((ORDER / "bom-full.csv").open())}
        self.assertEqual(full["C200"]["Assembled by JLCPCB"], "no")
        self.assertEqual(full["LED75"]["Side"], "Bottom")
        self.assertEqual(len(full), self.prov["summary"]["footprints"])


if __name__ == "__main__":
    unittest.main()
