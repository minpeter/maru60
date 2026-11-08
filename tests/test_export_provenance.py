"""Publishing must reject evidence from a different or modified build."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from maru60.provenance import input_fingerprint

ROOT = Path(__file__).resolve().parents[1]


class ExportProvenanceTest(unittest.TestCase):
    def test_bottom_export_rejects_previous_board_before_writing_models(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in (
                "export_bottomcase.py",
                "rule60_spec.py",
                "build_topcase_draft.py",
                "build_bottomcase_draft.py",
                "verify_topcase.py",
                "verify_bottomcase.py",
            ):
                shutil.copy2(ROOT / name, root / name)
            shutil.copytree(ROOT / "spec", root / "spec")
            shutil.copytree(ROOT / "maru60", root / "maru60")
            output = root / "bottomcase-draft"
            output.mkdir()
            top = root / "topcase-draft"
            top.mkdir()
            (top / "draft-report.json").write_text("{}")
            models = root / "models"
            models.mkdir()
            (root / "evidence").mkdir()
            (output / "draft-report.json").write_text(
                json.dumps({"board": "ph60-rev3", "battery_bay": True})
            )
            (output / "maru60-hhkb-bottomcase-left.3mf").write_bytes(b"new PH60 model")
            (output / "verification.json").write_text(
                json.dumps(
                    {
                        "status": "ALL_PASSED",
                        "board": "6095-trimode",
                        "battery_bay": True,
                        "input_sha256": input_fingerprint(output, (top,)),
                    }
                )
            )
            environment = dict(os.environ)
            environment.pop("MARU60_TOPCASE_DIR", None)
            environment.pop("MARU60_BOTTOMCASE_DIR", None)
            result = subprocess.run(
                [sys.executable, str(root / "export_bottomcase.py")],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("current board/battery-bay variant", result.stderr)
            self.assertEqual(list(models.iterdir()), [])

    def test_export_accepts_matching_inputs_and_rejects_changes_to_any_input(self):
        for change in (
            None,
            "model",
            "report",
            "spec",
            "source",
            "mating-gauge",
            "removed-model",
        ):
            with (
                self.subTest(change=change),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                for name in (
                    "export_bottomcase.py",
                    "rule60_spec.py",
                    "build_topcase_draft.py",
                    "build_bottomcase_draft.py",
                    "verify_topcase.py",
                    "verify_bottomcase.py",
                ):
                    shutil.copy2(ROOT / name, root / name)
                shutil.copytree(ROOT / "spec", root / "spec")
                shutil.copytree(ROOT / "maru60", root / "maru60")
                top, bottom = root / "topcase-draft", root / "bottomcase-draft"
                top.mkdir()
                bottom.mkdir()
                (root / "models").mkdir()
                (root / "evidence").mkdir()
                (top / "draft-report.json").write_text(
                    json.dumps({"board": "ph60-rev3"})
                )
                (top / "halves-world.3mf").write_bytes(b"original mating gauge")
                (bottom / "draft-report.json").write_text(
                    json.dumps({"board": "ph60-rev3", "battery_bay": True})
                )
                for name in ("left", "right", "fit-coupon", "joint-test"):
                    (bottom / f"maru60-hhkb-bottomcase-{name}.3mf").write_bytes(
                        b"original print artifact"
                    )
                receipt = {
                    "status": "ALL_PASSED",
                    "board": "ph60-rev3",
                    "battery_bay": True,
                    "input_sha256": input_fingerprint(bottom, (top,)),
                }
                (bottom / "verification.json").write_text(json.dumps(receipt))
                targets = {
                    "model": bottom / "maru60-hhkb-bottomcase-left.3mf",
                    "report": bottom / "draft-report.json",
                    "spec": root / "spec/rule60-v3.json",
                    "source": root / "build_topcase_draft.py",
                    "mating-gauge": top / "halves-world.3mf",
                }
                if change == "removed-model":
                    (bottom / "maru60-hhkb-bottomcase-right.3mf").unlink()
                elif change is not None:
                    target = targets[change]
                    target.write_bytes(target.read_bytes() + b" ")
                environment = {
                    **os.environ,
                    "MARU60_TOPCASE_DIR": str(top),
                    "MARU60_BOTTOMCASE_DIR": str(bottom),
                }
                result = subprocess.run(
                    [sys.executable, str(root / "export_bottomcase.py")],
                    cwd=root,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if change is None:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(
                        (root / "models/maru60-hhkb-bottomcase-left.3mf").read_bytes(),
                        b"original print artifact",
                    )
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("stale verification fingerprint", result.stderr)
                    self.assertEqual(list((root / "models").iterdir()), [])

    def test_optimized_python_cannot_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "verification.json").write_text('{"status":"ALL_PASSED"}')
            command = "from pathlib import Path; from maru60.provenance import require_verified; require_verified(Path(__import__('sys').argv[1]))"
            result = subprocess.run(
                [sys.executable, "-O", "-c", command, str(directory)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("optimization disables geometry assertions", result.stderr)
