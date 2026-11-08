"""Exercise the selected mating gauge and failure reporting through real subprocesses."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from maru60.pipeline import PipelineStepError, build_lock, run_step

ROOT = Path(__file__).resolve().parents[1]


class HousingWorkflowTest(unittest.TestCase):
    def test_failed_step_survives_lock_cleanup_with_its_original_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            failing = directory / "fail.py"
            failing.write_text("raise SystemExit(7)\n")
            with (
                self.assertRaises(PipelineStepError) as raised,
                build_lock(directory / ".lock"),
            ):
                run_step(str(failing), [], directory, dict(os.environ))
            self.assertEqual(raised.exception.returncode, 7)
            self.assertTrue(raised.exception.log.is_file())

    def test_6095_pair_uses_its_selected_topcase_instead_of_legacy_ph60_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            top, bottom = directory / "topcase", directory / "bottomcase"
            environment = {
                **os.environ,
                "MARU60_TOPCASE_DIR": str(top),
                "MARU60_BOTTOMCASE_DIR": str(bottom),
            }
            for script, args in (
                ("build_topcase_draft.py", ["--board", "6095-trimode"]),
                ("build_bottomcase_draft.py", ["--board", "6095-trimode"]),
                ("verify_topcase.py", []),
                ("verify_bottomcase.py", []),
            ):
                result = subprocess.run(
                    [sys.executable, str(ROOT / script), *args],
                    cwd=directory,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"{script}: {result.stdout[-1000:]}\n{result.stderr}",
                )
            report = json.loads((bottom / "verification.json").read_text())
            self.assertEqual(report["status"], "ALL_PASSED")
            self.assertEqual(report["board"], "6095-trimode")
