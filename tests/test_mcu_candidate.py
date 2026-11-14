"""Keep manufacturing files, population choices and evidence bound to final CAD."""
import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "pcb/experiments/resume-20261113-mcu-near-usb-zero-opens"


def read(name):
    return json.loads((CANDIDATE / name).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class McuCandidateTest(unittest.TestCase):
    def test_pdn_has_physical_scale_and_consistent_temperature_scaling(self):
        results = read("qa/pdn/results.json")
        for case in results["led_rail"].values():
            self.assertGreaterEqual(case["max_drop_mv"], 0)
            self.assertLess(case["max_drop_mv"], 100)
        for label, cold in results["paths"].items():
            if label.endswith("@20C"):
                hot = results["paths"][label.replace("@20C", "@60C")]
                self.assertGreater(cold["resistance_mohm"], 0)
                self.assertAlmostEqual(hot["resistance_mohm"], cold["resistance_mohm"] * 1.1572, delta=.02)

    def test_manifest_and_archived_reports_match_delivered_cad(self):
        manifest = read("MANIFEST.json")
        self.assertFalse(manifest["manufacturing_ready"])
        for path, expected in manifest["files"].items():
            self.assertEqual(digest(ROOT / path), expected, path)
        board = digest(CANDIDATE / "pcb/maru60.kicad_pcb")
        for path in ("qa/native/RESULT.json", "qa/native/net-identity.json",
                     "qa/dfm-per-rule.json", "qa/backspace-fit.json"):
            self.assertEqual(read(path)["board_sha256"], board, path)
        native = read("qa/native/RESULT.json")
        self.assertTrue(native["pass"])
        for key in ("open_pairs", "warnings", "other_errors", "ERC", "schematic_parity"):
            self.assertEqual(native[key], 0, key)
        dfm = read("qa/dfm-per-rule.json")["rules"]
        self.assertEqual(len(dfm), 32)
        self.assertTrue(all(r["violations"] == r["unconnected"] == 0 for r in dfm))

    def test_package_preserves_exclusive_backspace_population(self):
        order = CANDIDATE / "order"
        with (order / "cpl-jlcpcb.csv").open() as stream:
            cpl = list(csv.DictReader(stream))
        with (order / "bom-jlcpcb.csv").open() as stream:
            bom = list(csv.DictReader(stream))
        bom_refs = [ref for row in bom for ref in row["Designator"].split(",")]
        refs = [row["Designator"] for row in cpl]
        self.assertEqual(len(refs), 336)
        self.assertEqual(len(refs), len(set(refs)))
        self.assertEqual(Counter(refs), Counter(bom_refs))
        self.assertEqual(len(bom), 55)
        self.assertEqual(Counter(row["Layer"] for row in cpl), {"Top": 136, "Bottom": 200})
        self.assertFalse({"SW14", "SW15", "LED14", "LED15"} & set(refs))
        self.assertTrue({"R189", "R190", "R191", "R192", "R193"} <= set(refs))
        prov = read("order/PROVENANCE.json")
        self.assertEqual(digest(CANDIDATE / "pcb/maru60.kicad_pcb"), prov["board"]["sha256"])
        self.assertEqual(digest(order / "parts.json"), prov["parts_database"]["sha256"])
        self.assertTrue(all(c["pass"] for c in prov["checks"]))
        for path, expected in prov["files"].items():
            self.assertEqual(digest(order / path), expected, path)
        readback = read("qa/gerber-readback.json")
        self.assertTrue(readback["pass"])
        self.assertEqual(len(readback["checks"]), 24)

    def test_signal_results_use_the_archived_geometry(self):
        geometry = gzip.decompress((CANDIDATE / "qa/geometry.json.gz").read_bytes())
        geometry_hash = hashlib.sha256(geometry).hexdigest()
        board_hash = digest(CANDIDATE / "pcb/maru60.kicad_pcb")
        equivalence = read("qa/geometry-equivalence.json")
        self.assertTrue(equivalence["pass"])
        self.assertEqual(equivalence["final_board_sha256"], board_hash)
        self.assertEqual(equivalence["source_geometry_sha256"], geometry_hash)
        self.assertEqual(equivalence["final_geometry_sha256"], geometry_hash)
        source = gzip.decompress((CANDIDATE / equivalence["source_board_archive"]).read_bytes())
        self.assertEqual(hashlib.sha256(source).hexdigest(), equivalence["source_board_sha256"])
        edit = equivalence["literal_replacement"]
        self.assertEqual(source.decode().count(edit["before"]), 1)
        self.assertEqual(source.decode().replace(edit["before"], edit["after"]),
                         (CANDIDATE / "pcb/maru60.kicad_pcb").read_text())
        for step in ("extract_geometry", "sim_led", "sim_usb", "sim_xtal", "sim_matrix", "check_misc"):
            report = read(f"qa/signal-integrity/{step}-provenance.json")
            self.assertEqual(report["board_sha256"], equivalence["source_board_sha256"])
            self.assertEqual(report["geometry_sha256"], geometry_hash)
        backspace = read("qa/signal-integrity/backspace-led.json")
        self.assertEqual(backspace["board_sha256"], equivalence["source_board_sha256"])
        self.assertEqual(backspace["geometry_sha256"], geometry_hash)
        self.assertTrue(backspace["pass"])
        self.assertEqual(len(backspace["cases"]), 54)
        self.assertTrue(read("qa/signal-integrity/convergence/results.json")["pass"])

    def test_populated_led_circuit_passes_recorded_corners(self):
        assessment = read("qa/signal-integrity/assessment.json")["led"]
        for key in ("timing_or_recrossing_failures", "strong_driver_screen_failures",
                    "strength_sweep_noise_margin_failures"):
            self.assertEqual(assessment[key], [], key)
        led = read("qa/signal-integrity/led.json")
        for row in led["strong_driver_screen"]:
            for case in row["cases"].values():
                self.assertGreaterEqual(case["NM_high_V"], 0, row["net"])
                self.assertGreaterEqual(case["NM_low_V"], 0, row["net"])
                self.assertEqual(case["extra_threshold_crossings"], 0, row["net"])
                self.assertGreaterEqual(case["minimum_timing_budget_ns"], 0, row["net"])
        damping = read("qa/signal-integrity/led-damping/results.json")
        self.assertTrue(damping["pass"])
        self.assertEqual(len(damping["cases"]), 24)
        self.assertTrue(all(case["pass"] for case in damping["cases"]))
        self.assertEqual(damping["routes"]["UG_LED_6/default"]["ohm"], 150)
        for site in ("window", "stepped"):
            self.assertEqual(damping["routes"][f"KEY_RGB_CHAIN_29/{site}"]["resistor"], "R193")
        with (CANDIDATE / "order/bom-jlcpcb.csv").open() as stream:
            resistor = next(row for row in csv.DictReader(stream)
                            if "R115" in row["Designator"].split(","))
        self.assertEqual(resistor["LCSC Part #"], "C25082")

    def test_polarised_placements_keep_supplier_fit_and_bottom_mirroring(self):
        order = CANDIDATE / "order"
        with (order / "cpl-jlcpcb.csv").open() as stream:
            cpl = {row["Designator"]: row for row in csv.DictReader(stream)}
        with (order / "bom-full.csv").open() as stream:
            full = list(csv.DictReader(stream))
        fitted = read("order/jlcpcb-placement.json")["placements"]
        polarised = [r["Reference"] for r in full
                     if r["Polarised"] == "yes" and r["Assembled by JLCPCB"] == "yes"]
        self.assertGreater(len(polarised), 150)
        for ref in polarised:
            fit, placement = fitted[ref], cpl[ref]
            self.assertEqual(fit["status"], "fitted", ref)
            self.assertEqual(placement["Layer"], fit["side"], ref)
            self.assertAlmostEqual(float(placement["Rotation"]), fit["rotation"], places=2, msg=ref)
            self.assertAlmostEqual(float(placement["Mid X"]), fit["x"], places=3, msg=ref)
            self.assertAlmostEqual(float(placement["Mid Y"]), -fit["y"], places=3, msg=ref)

    def test_fit_hold_is_not_hidden_by_electrical_pass(self):
        status = read("qa/status.json")
        self.assertFalse(status["manufacturing_ready"])
        self.assertFalse(status["physical_fit_verified"])
        raw = read("qa/mechanical-fit/fit.json")["summary"]
        self.assertEqual(raw["overall"], "ATTENTION")
        self.assertEqual(raw["stabilizer_7u_status"], "fail")
        selected = read("qa/mechanical-fit/selected-assembly.json")
        self.assertFalse(selected["raw_7u_probe_applicable_to_selected_assembly"])
        self.assertFalse(selected["product_fit_verified"])
        material = read("qa/native/material-summary.json")
        self.assertEqual(material["nets_with_multiple_pad_partitions"], {})
        self.assertFalse(material["strict_baseline_promoted"])


if __name__ == "__main__":
    unittest.main()
